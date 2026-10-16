import asyncio
import hashlib
import logging
import os
import re
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from dotenv import load_dotenv

from ai_filter import analyze_job_with_groq
from database import init_db, is_job_exists, add_job
from parser import parse_upwork_rss

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
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
    "unpaid", "equity only", "growth manager", "content writer"
]

def passes_prefilter(title: str, description: str) -> bool:
    text = f"{title} {description}".lower()
    for kw in BLACKLIST_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', text):
            return False
    return True

logging.basicConfig(level=logging.INFO)
dp = Dispatcher()

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Запустить поиск")],
            [KeyboardButton(text="🟢 Одобренные"), KeyboardButton(text="🔴 Отсеянные")],
            [KeyboardButton(text="🛠 Посмотреть настройки")],
            [KeyboardButton(text="⚙️ Изменить запрос"), KeyboardButton(text="🤖 Изменить фильтр")]
        ],
        resize_keyboard=True
    )

def get_job_inline_keyboard(link: str, job_id: str):
    safe_id = hashlib.md5(job_id.encode()).hexdigest()[:16]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔗 Ссылка на вакансию", url=link),
                InlineKeyboardButton(text="📝 Сгенерировать отклик", callback_data=f"cover_{safe_id}")
            ]
        ]
    )

@dp.message(Command("start"))
async def cmd_start(message: Message):
    init_db()
    text = (
        "Привет! Я **Upwork Sniper Bot 2.0**.\n\n"
        "Поиск настроен и готов к работе: жми «Запустить поиск», а результаты смотри по кнопкам ниже!"
    )
    await message.answer(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

@dp.message(F.text == "🛠 Посмотреть настройки")
async def btn_show_settings(message: Message):
    text = (
        f"🛠 **Текущие настройки:**\n\n"
        f"🔎 **Поисковый запрос:** `{user_settings['query']}`\n\n"
        f"🤖 **Фильтр AI:** `{user_settings['filters']}`"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "⚙️ Изменить запрос")
async def btn_change_query(message: Message):
    user_states[message.from_user.id] = "waiting_query"
    await message.answer("✍️ Отправь мне новый поисковый запрос (например: `python OR html`):", parse_mode="Markdown")

@dp.message(F.text == "🤖 Изменить фильтр")
async def btn_change_filter(message: Message):
    user_states[message.from_user.id] = "waiting_filter"
    await message.answer("✍️ Отправь мне новые критерии для AI-фильтра:", parse_mode="Markdown")

@dp.message(F.text == "🟢 Одобренные")
async def btn_show_matched(message: Message):
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT job_id, title, link, ai_reason FROM jobs WHERE status = 'matched' ORDER BY rowid DESC LIMIT 10")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await message.answer("📭 В базе пока нет одобренных вакансий.")
        return
    
    await message.answer("🟢 **Ваши одобренные вакансии:**", parse_mode="Markdown")
    for job_id, title, link, reason in rows:
        safe_title = title.replace("*", "").replace("_", "").replace("`", "")
        safe_reason = reason.replace("*", "").replace("_", "").replace("`", "")[:250]
        text = f"📌 **{safe_title}**\n\n🤖 **Вердикт ИИ:**\n`{safe_reason}...`"
        await message.answer(text, reply_markup=get_job_inline_keyboard(link, job_id), disable_web_page_preview=True, parse_mode="Markdown")

@dp.message(F.text == "🔴 Отсеянные")
async def btn_show_rejected(message: Message):
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT job_id, title, link, ai_reason FROM jobs WHERE status = 'rejected' ORDER BY rowid DESC LIMIT 10")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await message.answer("📭 В базе пока нет отсеянных вакансий.")
        return
    
    await message.answer("🔴 **Последние отсеянные вакансии:**", parse_mode="Markdown")
    for job_id, title, link, reason in rows:
        safe_title = title.replace("*", "").replace("_", "").replace("`", "")
        safe_reason = reason.replace("*", "").replace("_", "").replace("`", "")[:250]
        text = f"📌 **{safe_title}**\n\n❌ **Причина:**\n`{safe_reason}...`"
        await message.answer(text, reply_markup=get_job_inline_keyboard(link, job_id), disable_web_page_preview=True, parse_mode="Markdown")

@dp.message(F.text == "🔍 Запустить поиск")
async def cmd_hunt(message: Message):
    rss_url = f"https://www.upwork.com/nx/search/jobs/rss?q={user_settings['query'].strip().replace(' ', '+')}&sort=recency"
    status_msg = await message.answer(f"🔍 Ищу свежие вакансии по запросу `{user_settings['query']}`...", parse_mode="Markdown")

    init_db()
    jobs = await parse_upwork_rss(rss_url)

    if not jobs:
        await status_msg.edit_text("❌ Не удалось найти вакансии или Upwork временно ограничил доступ.")
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
            add_job(job_id, title, link, job["published_at"], "rejected", "Отсечено пре-фильтром (стоп-слова)", description)
            skipped_by_prefilter += 1
            continue

        ai_response = analyze_job_with_groq(
            title=title,
            description=description,
            user_filters=user_settings["filters"],
            api_key=GROQ_API_KEY,
        )

        is_matched = "ПОДХОДИТ" in ai_response.upper() and "НЕ ПОДХОДИТ" not in ai_response.upper()
        status_str = "matched" if is_matched else "rejected"
        add_job(job_id, title, link, job["published_at"], status_str, ai_response, description)

        if is_matched:
            matched_jobs_count += 1

        await asyncio.sleep(1)

    await status_msg.edit_text(
        f"✅ **Поиск завершен!**\n\n"
        f"• Проверено новых: {new_jobs_count}\n"
        f"• Отсечено пре-фильтром: {skipped_by_prefilter}\n"
        f"• Подходит по версии AI: {matched_jobs_count}\n\n"
        f"👇 Нажми «🟢 Одобренные» или «🔴 Отсеянные», чтобы посмотреть результаты.",
        parse_mode="Markdown"
    )

@dp.message()
async def handle_text_inputs(message: Message):
    user_id = message.from_user.id
    state = user_states.get(user_id)

    if state == "waiting_query":
        user_settings["query"] = message.text.strip()
        user_states.pop(user_id, None)
        await message.answer(f"✅ Поисковый запрос обновлен на: `{user_settings['query']}`", parse_mode="Markdown")
        return

    if state == "waiting_filter":
        user_settings["filters"] = message.text.strip()
        user_states.pop(user_id, None)
        await message.answer(f"✅ Фильтры AI обновлены на:\n`{user_settings['filters']}`", parse_mode="Markdown")
        return

@dp.callback_query(F.data.startswith("cover_"))
async def callback_generate_cover(callback: CallbackQuery):
    await callback.answer("⏳ Генерирую идеальный отклик...")
    
    safe_id = callback.data.replace("cover_", "")
    
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT job_id, title, description, ai_reason FROM jobs")
    rows = cursor.fetchall()
    conn.close()

    target_job = None
    for j_id, title, desc, reason in rows:
        if hashlib.md5(j_id.encode()).hexdigest()[:16] == safe_id:
            target_job = (title, desc, reason)
            break

    if not target_job:
        await callback.message.answer("❌ Не удалось найти данные этой вакансии в базе.")
        return

    title, description, reason = target_job
    # Если описание из базы короткое или пустое, подстраховываемся вердиктом ИИ
    job_context = description if description and len(description) > 20 else reason

    prompt = (
        f"Write a short, professional, and convincing Cover Letter in English to apply for this Upwork job. "
        f"Focus on solving the client's problem, mention relevant web development skills, and get straight to the point. "
        f"Output ONLY the ready-to-send letter text without any intro or meta-commentary.\n\n"
        f"Job Title: {title}\n"
        f"Job Details: {job_context}\n"
    )
    
    ai_cover = analyze_job_with_groq(
        title="Cover Letter Generation",
        description=prompt,
        user_filters="Write a professional Upwork cover letter.",
        api_key=GROQ_API_KEY,
    )

    await callback.message.answer(f"📝 **Готовый отклик на английском для «{title}»:**\n\n{ai_cover}", parse_mode="Markdown")

async def main():
    if not TELEGRAM_TOKEN or not GROQ_API_KEY:
        raise SystemExit(
            "Задайте TELEGRAM_TOKEN и GROQ_API_KEY в файле .env в корне проекта."
        )
    init_db()
    bot = Bot(token=TELEGRAM_TOKEN)
    print("Бот запущен и готов к работе...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())