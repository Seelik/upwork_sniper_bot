import asyncio
import hashlib
import logging
import os
import re
import sqlite3
from urllib.parse import quote_plus
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from dotenv import load_dotenv

from ai_filter import analyze_job_with_groq, generate_cover_letter_with_groq, is_job_matched
from database import (
    init_db,
    is_job_exists,
    add_job,
    update_job_status,
    get_user_language,
    set_user_language,
)
from locales import t, btn, all_button_texts, SUPPORTED_LANGS
from parser import parse_upwork_rss

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

user_settings = {
    "query": "python OR javascript OR html OR css OR bot",
    "filters": (
        "Нужны заказы на Python, веб-разработку, HTML/CSS/JS, скрипты, парсинг сайтов, "
        "автоматизацию и Telegram ботов. Подходят любые мелкие и быстрые задачи для набора отзывов. "
        "Пропускай только тяжелый Enterprise, сложный дизайн в Figma и мобильную разработку с нуля."
    ),
}

user_states = {}

BLACKLIST_KEYWORDS = [
    "phd", "professor", "university", "academic", "thesis",
    "tiktok", "smm", "manychat", "chatrace", "video creator",
    "unpaid", "equity only", "growth manager", "content writer",
]


def user_lang(user_id: int) -> str:
    return get_user_language(user_id) or "ru"


def passes_prefilter(title: str, description: str) -> bool:
    text = f"{title} {description}".lower()
    for kw in BLACKLIST_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", text):
            return False
    return True


def build_upwork_search_query(raw_query: str) -> str:
    query = " ".join(raw_query.strip().split())
    if not query:
        return "python"
    upper = query.upper()
    if " OR " in upper or " AND " in upper or '"' in query:
        return query
    words = query.split()
    if len(words) == 1:
        return query
    return " OR ".join(words)


def build_upwork_rss_url(raw_query: str) -> str:
    search_query = build_upwork_search_query(raw_query)
    encoded = quote_plus(search_query)
    return f"https://www.upwork.com/nx/search/jobs/rss?q={encoded}&sort=recency"


logging.basicConfig(level=logging.INFO)
dp = Dispatcher()


def job_safe_id(job_id: str) -> str:
    return hashlib.md5(job_id.encode()).hexdigest()[:16]


def resolve_job_id_by_safe_id(safe_id: str) -> str | None:
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT job_id FROM jobs")
    rows = cursor.fetchall()
    conn.close()
    for (job_id,) in rows:
        if job_safe_id(job_id) == safe_id:
            return job_id
    return None


def sanitize_markdown(text: str, limit: int | None = None) -> str:
    cleaned = text.replace("*", "").replace("_", "").replace("`", "")
    if limit is not None:
        return cleaned[:limit]
    return cleaned


def get_language_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="English 🇬🇧", callback_data="lang_en"),
                InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru"),
            ]
        ]
    )


def get_main_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=btn(lang, "start_search"))],
            [
                KeyboardButton(text=btn(lang, "matched")),
                KeyboardButton(text=btn(lang, "rejected")),
            ],
            [KeyboardButton(text=btn(lang, "applied"))],
            [KeyboardButton(text=btn(lang, "settings"))],
            [
                KeyboardButton(text=btn(lang, "change_query")),
                KeyboardButton(text=btn(lang, "change_filter")),
            ],
            [KeyboardButton(text=btn(lang, "language"))],
        ],
        resize_keyboard=True,
    )


def get_job_inline_keyboard(link: str, job_id: str, lang: str) -> InlineKeyboardMarkup:
    safe_id = job_safe_id(job_id)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t(lang, "btn_job_link"), url=link),
                InlineKeyboardButton(
                    text=t(lang, "btn_cover_letter"),
                    callback_data=f"cover_{safe_id}",
                ),
            ]
        ]
    )


def get_matched_job_keyboard(link: str, job_id: str, lang: str) -> InlineKeyboardMarkup:
    safe_id = job_safe_id(job_id)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t(lang, "btn_job_link"), url=link),
                InlineKeyboardButton(
                    text=t(lang, "btn_cover_letter"),
                    callback_data=f"cover_{safe_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "btn_mark_applied"),
                    callback_data=f"applied_job_{safe_id}",
                ),
                InlineKeyboardButton(
                    text=t(lang, "btn_mark_reject"),
                    callback_data=f"reject_job_{safe_id}",
                ),
            ],
        ]
    )


@dp.message(Command("start"))
async def cmd_start(message: Message):
    init_db()
    uid = message.from_user.id
    lang = get_user_language(uid)
    if lang is None:
        await message.answer(
            t("ru", "choose_language"),
            reply_markup=get_language_inline_keyboard(),
        )
        return
    await message.answer(
        t(lang, "welcome"),
        reply_markup=get_main_keyboard(lang),
        parse_mode="Markdown",
    )


@dp.callback_query(F.data.in_({"lang_en", "lang_ru"}))
async def callback_set_language(callback: CallbackQuery):
    lang = callback.data.removeprefix("lang_")
    if lang not in SUPPORTED_LANGS:
        await callback.answer()
        return

    set_user_language(callback.from_user.id, lang)
    await callback.answer(t(lang, "language_updated"))
    try:
        await callback.message.delete()
    except Exception:
        await callback.message.edit_reply_markup(reply_markup=None)

    await callback.message.answer(
        t(lang, "welcome"),
        reply_markup=get_main_keyboard(lang),
        parse_mode="Markdown",
    )


@dp.message(F.text.in_(all_button_texts("language")))
async def btn_change_language(message: Message):
    lang = user_lang(message.from_user.id)
    await message.answer(
        t(lang, "language_prompt"),
        reply_markup=get_language_inline_keyboard(),
    )


@dp.message(F.text.in_(all_button_texts("settings")))
async def btn_show_settings(message: Message):
    lang = user_lang(message.from_user.id)
    text = (
        f"{t(lang, 'settings_title')}\n\n"
        f"{t(lang, 'settings_query')} `{user_settings['query']}`\n\n"
        f"{t(lang, 'settings_filter')} `{user_settings['filters']}`"
    )
    await message.answer(text, parse_mode="Markdown")


@dp.message(F.text.in_(all_button_texts("change_query")))
async def btn_change_query(message: Message):
    lang = user_lang(message.from_user.id)
    user_states[message.from_user.id] = "waiting_query"
    await message.answer(t(lang, "prompt_new_query"), parse_mode="Markdown")


@dp.message(F.text.in_(all_button_texts("change_filter")))
async def btn_change_filter(message: Message):
    lang = user_lang(message.from_user.id)
    user_states[message.from_user.id] = "waiting_filter"
    await message.answer(t(lang, "prompt_new_filter"), parse_mode="Markdown")


@dp.message(F.text.in_(all_button_texts("matched")))
async def btn_show_matched(message: Message):
    lang = user_lang(message.from_user.id)
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT job_id, title, link, ai_reason FROM jobs WHERE status = 'matched' ORDER BY rowid DESC LIMIT 10"
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await message.answer(t(lang, "no_matched"))
        return

    await message.answer(t(lang, "matched_header"), parse_mode="Markdown")
    for job_id, title, link, reason in rows:
        safe_title = sanitize_markdown(title)
        safe_reason = sanitize_markdown(reason, 250)
        text = f"📌 **{safe_title}**\n\n{t(lang, 'matched_verdict')}\n`{safe_reason}...`"
        await message.answer(
            text,
            reply_markup=get_matched_job_keyboard(link, job_id, lang),
            disable_web_page_preview=True,
            parse_mode="Markdown",
        )


@dp.message(F.text.in_(all_button_texts("rejected")))
async def btn_show_rejected(message: Message):
    lang = user_lang(message.from_user.id)
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT job_id, title, link, ai_reason FROM jobs WHERE status = 'rejected' ORDER BY rowid DESC LIMIT 10"
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await message.answer(t(lang, "no_rejected"))
        return

    await message.answer(t(lang, "rejected_header"), parse_mode="Markdown")
    for job_id, title, link, reason in rows:
        safe_title = sanitize_markdown(title)
        safe_reason = sanitize_markdown(reason, 250)
        text = f"📌 **{safe_title}**\n\n{t(lang, 'rejected_reason')}\n`{safe_reason}...`"
        await message.answer(
            text,
            reply_markup=get_job_inline_keyboard(link, job_id, lang),
            disable_web_page_preview=True,
            parse_mode="Markdown",
        )


@dp.message(F.text.in_(all_button_texts("applied")))
async def btn_show_applied(message: Message):
    lang = user_lang(message.from_user.id)
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT job_id, title, link, ai_reason FROM jobs WHERE status = 'applied' ORDER BY rowid DESC LIMIT 10"
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await message.answer(t(lang, "no_applied"))
        return

    await message.answer(t(lang, "applied_header"), parse_mode="Markdown")
    for job_id, title, link, reason in rows:
        safe_title = sanitize_markdown(title)
        safe_reason = sanitize_markdown(reason, 250)
        text = (
            f"📌 **{safe_title}**\n\n{t(lang, 'applied_status')}\n\n"
            f"{t(lang, 'applied_verdict')}\n`{safe_reason}...`"
        )
        await message.answer(
            text,
            reply_markup=get_job_inline_keyboard(link, job_id, lang),
            disable_web_page_preview=True,
            parse_mode="Markdown",
        )


@dp.message(F.text.in_(all_button_texts("start_search")))
async def cmd_hunt(message: Message):
    lang = user_lang(message.from_user.id)
    raw_query = user_settings["query"]
    upwork_query = build_upwork_search_query(raw_query)
    rss_url = build_upwork_rss_url(raw_query)

    status_text = t(lang, "hunt_searching", query=raw_query)
    if upwork_query != raw_query:
        status_text += "\n" + t(lang, "hunt_upwork_query", upwork_query=upwork_query)
    status_text += "..."

    status_msg = await message.answer(status_text, parse_mode="Markdown")

    init_db()
    jobs = await parse_upwork_rss(rss_url)

    if not jobs:
        await status_msg.edit_text(t(lang, "hunt_failed"), parse_mode="Markdown")
        return

    new_jobs_count = 0
    matched_jobs_count = 0
    skipped_by_prefilter = 0

    for job in jobs:
        job_id = job["id"]

        if is_job_exists(job_id):
            continue

        new_jobs_count += 1
        title = job["title"]
        description = job["description"] if job["description"] else title
        link = job["link"]

        if not passes_prefilter(title, description):
            add_job(
                job_id,
                title,
                link,
                job["published_at"],
                "rejected",
                t(lang, "prefilter_reason"),
                description,
            )
            skipped_by_prefilter += 1
            continue

        ai_response = analyze_job_with_groq(
            title=title,
            description=description,
            user_filters=user_settings["filters"],
            api_key=GROQ_API_KEY,
            user_lang=lang,
        )

        is_matched = is_job_matched(ai_response, user_lang=lang)
        status_str = "matched" if is_matched else "rejected"
        add_job(job_id, title, link, job["published_at"], status_str, ai_response, description)

        if is_matched:
            matched_jobs_count += 1

        await asyncio.sleep(1)

    await status_msg.edit_text(
        f"{t(lang, 'hunt_done_title')}\n\n"
        f"{t(lang, 'hunt_done_new', count=new_jobs_count)}\n"
        f"{t(lang, 'hunt_done_prefilter', count=skipped_by_prefilter)}\n"
        f"{t(lang, 'hunt_done_matched', count=matched_jobs_count)}\n\n"
        f"{t(lang, 'hunt_done_footer')}",
        parse_mode="Markdown",
    )


@dp.message()
async def handle_text_inputs(message: Message):
    user_id = message.from_user.id
    lang = user_lang(user_id)
    state = user_states.get(user_id)

    if state == "waiting_query":
        user_settings["query"] = message.text.strip()
        user_states.pop(user_id, None)
        await message.answer(
            t(lang, "query_updated", query=user_settings["query"]),
            parse_mode="Markdown",
        )
        return

    if state == "waiting_filter":
        user_settings["filters"] = message.text.strip()
        user_states.pop(user_id, None)
        await message.answer(
            t(lang, "filter_updated", filters=user_settings["filters"]),
            parse_mode="Markdown",
        )
        return


@dp.callback_query(F.data.startswith("applied_job_"))
async def callback_applied_job(callback: CallbackQuery):
    lang = user_lang(callback.from_user.id)
    safe_id = callback.data.removeprefix("applied_job_")
    job_id = resolve_job_id_by_safe_id(safe_id)
    if not job_id or not update_job_status(job_id, "applied"):
        await callback.answer(t(lang, "job_not_found"), show_alert=True)
        return

    await callback.answer(t(lang, "applied_toast"))
    try:
        await callback.message.delete()
    except Exception:
        await callback.message.edit_reply_markup(reply_markup=None)


@dp.callback_query(F.data.startswith("reject_job_"))
async def callback_reject_job(callback: CallbackQuery):
    lang = user_lang(callback.from_user.id)
    safe_id = callback.data.removeprefix("reject_job_")
    job_id = resolve_job_id_by_safe_id(safe_id)
    if not job_id or not update_job_status(job_id, "rejected"):
        await callback.answer(t(lang, "job_not_found"), show_alert=True)
        return

    await callback.answer(t(lang, "reject_toast"))
    try:
        await callback.message.delete()
    except Exception:
        await callback.message.edit_reply_markup(reply_markup=None)


@dp.callback_query(F.data.startswith("cover_"))
async def callback_generate_cover(callback: CallbackQuery):
    lang = user_lang(callback.from_user.id)
    await callback.answer(t(lang, "cover_generating"))

    safe_id = callback.data.removeprefix("cover_")
    job_id = resolve_job_id_by_safe_id(safe_id)
    if not job_id:
        await callback.message.answer(t(lang, "job_data_not_found"))
        return

    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT title, description, ai_reason FROM jobs WHERE job_id = ?",
        (job_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        await callback.message.answer(t(lang, "job_data_not_found"))
        return

    title, description, reason = row
    job_context = description if description and len(description) > 20 else reason

    ai_cover = generate_cover_letter_with_groq(
        title=title,
        job_context=job_context,
        api_key=GROQ_API_KEY,
    )

    await callback.message.answer(
        t(lang, "cover_ready", title=title, cover=ai_cover),
        parse_mode="Markdown",
    )


async def main():
    if not BOT_TOKEN or not GROQ_API_KEY:
        raise SystemExit(t("en", "log_missing_env"))
    init_db()
    bot = Bot(token=BOT_TOKEN)
    logging.info(t("en", "log_bot_started"))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
