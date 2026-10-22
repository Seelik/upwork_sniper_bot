# 🤖 Upwork Job Monitor Telegram Bot

An **async Python Telegram bot** for on-demand **Upwork job monitoring**, **AI-powered filtering**, and **instant proposal drafts**—delivered straight to your chat.

![Bot UI preview](docs/ui.png)

---

## ✨ Key Features

- 🔍 **Real-time Upwork monitoring** — Playwright loads fresh search results when you tap **Start Search**.
- 🧠 **AI-powered evaluation** — LLM scoring via **Groq API** (OpenAI-compatible chat completions).
- 🌍 **Multi-language UI & AI analysis** — English / Russian i18n (`locales/`) with per-user language in SQLite `user_prefs`; filter **verdict & reason** follow the user's language.
- 📝 **Instant cover letter generation** — always **English** (Upwork-ready), regardless of UI language.
- ⚡ **Async architecture** — `asyncio` + **aiogram 3** handlers, non-blocking search flow.
- 🛡️ **Smart pre-filter** — stop-word rejection before LLM calls.
- 🔁 **Query normalization** — auto-`OR` for multi-word Upwork queries (spaces = AND on Upwork).
- 💾 **SQLite deduplication** — track matched / rejected / applied jobs without duplicates.
- 📨 **Job workflow** — mark **Applied** or **Not a fit** from matched cards.

---

## 🛠 Tech Stack

| Layer | Technology |
| --- | --- |
| Language | **Python 3.11+** |
| Runtime | **Asyncio** |
| Bot framework | **aiogram 3** |
| Scraping | **Playwright**, **BeautifulSoup** |
| Database | **SQLite** (`jobs.db`, `user_prefs`) |
| AI | **Groq API** (LLM; swap-friendly for OpenAI/Gemini-style providers) |
| Config | **python-dotenv** (`.env`) |
| Deploy | **Docker** *(optional — add your own `Dockerfile`)* |

---

## 🏗 Architecture

```text
Telegram Bot → Parser → DB Check → Pre-filter → Groq AI → UI
```

| Step | Module | Description |
| --- | --- | --- |
| 1 | `bot.py` | Telegram UI, i18n, orchestration |
| 2 | `parser.py` | Upwork HTML fetch & parse |
| 3 | `database.py` | Duplicate check & persistence |
| 4 | `bot.py` | Keyword pre-filter |
| 5 | `ai_filter.py` | Localized AI verdict + English cover letters |
| 6 | `bot.py` | Lists, inline actions, keyboards |

---

## 🚀 Quick Start

### 1️⃣ Clone

```bash
git clone https://github.com/Seelik/upwork_sniper_bot.git
cd upwork_sniper_bot
```

### 2️⃣ Virtual environment & dependencies

```bash
python -m venv .venv
```

**Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
pip install aiogram groq beautifulsoup4 playwright python-dotenv
playwright install chromium
```

**macOS / Linux:**

```bash
source .venv/bin/activate
pip install aiogram groq beautifulsoup4 playwright python-dotenv
playwright install chromium
```

### 3️⃣ Environment (`.env`)

```bash
cp .env.example .env
```

```env
TELEGRAM_TOKEN=your_telegram_bot_token
GROQ_API_KEY=your_groq_api_key
```

| Variable | Where to get it |
| --- | --- |
| `TELEGRAM_TOKEN` | [@BotFather](https://t.me/BotFather) |
| `GROQ_API_KEY` | [Groq Console](https://console.groq.com/) |

> ⚠️ Never commit `.env` — it is listed in `.gitignore`.

### 4️⃣ Run

```bash
python bot.py
```

Send **`/start`** in Telegram → choose **English 🇬🇧** or **Русский 🇷🇺** → use the reply keyboard.

---

## 📁 Project Layout

| Path | Purpose |
| --- | --- |
| `bot.py` | Entry point, handlers, i18n wiring |
| `parser.py` | Upwork scraper |
| `ai_filter.py` | Groq filtering (localized) & cover letters (EN) |
| `database.py` | SQLite jobs + `user_prefs` |
| `locales/en.py`, `locales/ru.py` | UI strings |
| `jobs.db` | Created at runtime (gitignored) |

---

## 📜 License

Use and adapt for your freelance workflow. Comply with **Upwork Terms of Service** when accessing their platform.
