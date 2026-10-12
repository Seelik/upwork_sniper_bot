# 🤖 Upwork Sniper Bot

An intelligent Telegram bot designed to automatically scrape Upwork job listings, filter them using the **Groq AI SDK** (with lightweight LLMs), and instantly notify you via Telegram about relevant opportunities that match your precise skills and criteria.

## ✨ Features

- **Automated Scraping:** Uses `Playwright` and `BeautifulSoup` to fetch the latest job postings from Upwork RSS/search.
- **AI-Powered Filtering:** Sends job titles and descriptions to the Groq API for smart evaluation based on your custom criteria.
- **Duplicate Prevention:** SQLite database (`jobs.db`) tracks processed jobs to prevent duplicate notifications.
- **Interactive Telegram Commands:** Easily update your search queries and AI filters on the fly.

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **aiogram 3** (Telegram Bot framework)
- **Playwright & BeautifulSoup** (Web scraping & parsing)
- **Groq SDK** (Fast AI inference)
- **SQLite** (Local storage)

---

## 🚀 Quick Start

1. Clone the repository:
   ```bash
   git clone [https://github.com/Seelik/upwork_sniper_bot.git](https://github.com/Seelik/upwork_sniper_bot.git)
   cd upwork_sniper_bot

Install dependencies:   pip install -r requirements.txt
Run the bot:   python bot.py



📋 Example Templates for /set_query & /set_filter
You can customize what jobs the bot hunts for using these templates depending on your seniority and focus:


1. Junior / Quick Review Focus (Fast & Small Tasks)
Query (/set_query): python
Filter (/set_filter):
Нужны заказы на Python: разработка Telegram ботов, парсинг сайтов, веб-скрейпинг, автоматизация и бэкенд на FastAPI. Бюджет значения не имеет, подходят любые мелкие и быстрые задачи для набора отзывов. Пропускай только фронтенд, дизайн и мобильную разработку.


2. Middle Backend Developer (APIs, Bots, Automation)
Query (/set_query): python fastapi backend
Filter (/set_filter):
Ищу заказы на Python уровней Junior+ и Middle. Фокус на бэкенд-разработке (FastAPI, Flask, Django), создании Telegram/Discord ботов, веб-парсерах (BeautifulSoup, Selenium, Playwright) и интеграции сторонних API. Бюджет фиксированный или от $30/час. Пропускай жесткий фронтенд (React, Vue, Next.js) и AI-инженерию уровня Senior (LLM fine-tuning, RAG).


3. Senior AI & Automation Engineer (LLMs, Agents, Advanced APIs)
Query (/set_query): ai agent python groq claude
Filter (/set_filter):
Интересуют сложные и высокооплачиваемые задачи для Senior-разработчика: проектирование бэкенда на Python, создание AI-агентов (LangChain, LlamaIndex, Claude API, Groq), автоматизация рабочих процессов (n8n, Make), интеграция LLM в бизнес-процессы. Бюджет высокий, долгосрочные проекты или сложные технические фиксы. Пропускай простые скрипты на 5 строк и низкобюджетные задачи.