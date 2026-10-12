import asyncio
import logging
import os
import urllib.parse
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from ai_filter import analyze_job_with_groq
from database import add_job, init_db, is_job_exists
from parser import parse_upwork_rss

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8682530201:AAE2nbgdo3PpnuMBY7lKCeTFbuFkS0Ww_qI")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")

# Глобальное хранилище настроек (по умолчанию)
user_settings = {
    "query": "python",
    "filters": (
        "Нужны заказы на Python: разработка Telegram ботов, парсинг сайтов,"
        " веб-скрейпинг, автоматизация и бэкенд на FastAPI. Бюджет значения не"
        " имеет, подходят любые мелкие и быстрые задачи для набора отзывов."
        " Пропускай только фронтенд, дизайн и мобильную разработку."
    ),
}

logging.basicConfig(level=logging.INFO)
dp = Dispatcher()


def get_rss_url(query: str) -> str:
  # Заменяем пробелы на + для Upwork RSS
  formatted_query = query.strip().replace(" ", "+")
  return (
      f"https://www.upwork.com/nx/search/jobs/rss?q={formatted_query}&sort=recency"
  )


@dp.message(Command("start"))
async def cmd_start(message: Message):
  text = (
      "Привет! Я **Upwork Sniper Bot**.\n\n"
      "⚙️ **Доступные команды:**\n"
      "• `/hunt` — запустить ручной поиск вакансий\n"
      "• `/settings` — посмотреть текущие настройки\n"
      "• `/set_query <запрос>` — изменить поиск (напр. `/set_query python scraper`)\n"
      "• `/set_filter <текст>` — изменить критерии AI"
  )
  await message.answer(text, parse_mode="Markdown")


@dp.message(Command("settings"))
async def cmd_settings(message: Message):
  text = (
      f"🛠 **Текущие настройки:**\n\n"
      f"🔎 **Поисковый запрос:** `{user_settings['query']}`\n"
      f"🤖 **Фильтр AI:** `{user_settings['filters']}`"
  )
  await message.answer(text, parse_mode="Markdown")


@dp.message(Command("set_query"))
async def cmd_set_query(message: Message):
  new_query = message.text.replace("/set_query", "").strip()
  if not new_query:
    await message.answer(
        "Пример использования: `/set_query python telegram bot`",
        parse_mode="Markdown",
    )
    return
  user_settings["query"] = new_query
  await message.answer(f"✅ Поисковый запрос обновлен на: `{new_query}`", parse_mode="Markdown")


@dp.message(Command("set_filter"))
async def cmd_set_filter(message: Message):
  new_filter = message.text.replace("/set_filter", "").strip()
  if not new_filter:
    await message.answer(
        "Пример использования: `/set_filter Искать только FastAPI и парсинг`",
        parse_mode="Markdown",
    )
    return
  user_settings["filters"] = new_filter
  await message.answer(f"✅ Фильтры AI обновлены на:\n`{new_filter}`", parse_mode="Markdown")


@dp.message(Command("hunt"))
async def cmd_hunt(message: Message):
  rss_url = get_rss_url(user_settings["query"])
  await message.answer(
      f"🔍 Ищу вакансии по запросу `{user_settings['query']}`...",
      parse_mode="Markdown",
  )

  init_db()
  jobs = await parse_upwork_rss(rss_url)

  if not jobs:
    await message.answer(
        "❌ Не удалось найти вакансии или Upwork блокирует прямой RSS-запрос.\nПопробуй изменить запрос через `/set_query`."
    )
    return

  new_jobs_count = 0
  matched_jobs_count = 0

  for job in jobs[:5]:
    job_id = job["id"]

    if is_job_exists(job_id):
      continue

    new_jobs_count += 1

    ai_response = analyze_job_with_groq(
        title=job["title"],
        description=job["description"],
        user_filters=user_settings["filters"],
        api_key=GROQ_API_KEY,
    )

    if "ПОДХОДИТ" in ai_response.upper():
      matched_jobs_count += 1
      add_job(job_id, job["title"], job["link"], job["published_at"])

      text = (
          f"🎯 **Найдена подходящая вакансия!**\n\n"
          f"📌 **{job['title']}**\n\n"
          f"🤖 **Вердикт ИИ:**\n{ai_response}\n\n"
          f"🔗 [Ссылка на вакансию]({job['link']})"
      )
      await message.answer(text, disable_web_page_preview=True, parse_mode="Markdown")

  await message.answer(
      f"✅ Поиск завершен!\n"
      f"• Проверено новых: {new_jobs_count}\n"
      f"• Подходит по версии AI: {matched_jobs_count}"
  )


async def main():
  init_db()
  bot = Bot(token=TELEGRAM_TOKEN)
  print("Бот запущен и готов к работе...")
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())