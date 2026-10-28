# Upwork Sniper Bot

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-26A5E4?style=flat&logo=telegram&logoColor=white)](https://docs.aiogram.dev/)
[![SQLite](https://img.shields.io/badge/SQLite-local-003B57?style=flat&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Groq](https://img.shields.io/badge/Groq-LLM%20API-F55036?style=flat)](https://console.groq.com/)
[![Telegram Bot API](https://img.shields.io/badge/Telegram-Bot%20API-26A5E4?style=flat&logo=telegram&logoColor=white)](https://core.telegram.org/bots/api)

An **automated AI job filtering tool** for Upwork freelancers. This Telegram bot scrapes fresh job listings on demand, filters them with an LLM (Groq), tracks outcomes in SQLite, and generates English cover letters for proposals.

![Bot UI preview](docs/ui.png)

---

## Overview & Problem Statement

Freelancers on Upwork waste time refreshing search results and reading irrelevant posts. **Upwork Sniper Bot** centralizes monitoring in Telegram:

1. You define a **search query** and **AI filter** (natural-language criteria).
2. The bot fetches new jobs via **Playwright**, skips duplicates, and applies a **stop-word pre-filter**.
3. **Groq** returns a localized verdict (`MATCHED` / `REJECTED` or Russian equivalents) with a short reason.
4. You review **Matched**, **Rejected**, and **Applied** lists and generate **cover letters** in one tap.

Search is **manual** (button-triggered)—no infinite background loops.

---

## Tech Stack & Key Features

| Category | Details |
| --- | --- |
| **Language** | Python 3.11+, Asyncio |
| **Bot** | aiogram 3, Telegram Bot API |
| **Scraping** | Playwright, BeautifulSoup |
| **Storage** | SQLite (`jobs`, `user_prefs`) |
| **AI** | Groq API (OpenAI-compatible chat completions) |
| **Config** | python-dotenv (`.env`) |

**Features**

- Real-time Upwork search on demand  
- AI-powered job evaluation with **EN/RU UI and localized AI reasons**  
- English cover letters always (Upwork-ready)  
- Smart query normalization (`OR` expansion for Upwork AND semantics)  
- Pre-filter stop words before LLM calls  
- Job workflow: Matched → Applied / Not a fit  
- i18n via `locales/en.py` & `locales/ru.py`  

---

## Quick Start Guide

### 1. Clone

```bash
git clone https://github.com/Seelik/upwork_sniper_bot.git
cd upwork_sniper_bot
```

### 2. Virtual environment

```bash
python -m venv .venv
```

**Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

**macOS / Linux:**

```bash
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 3. Configure `.env`

```bash
cp .env.example .env
```

Edit `.env`:

```env
TELEGRAM_TOKEN=your_telegram_bot_token
GROQ_API_KEY=your_groq_api_key
```

| Variable | Source |
| --- | --- |
| `TELEGRAM_TOKEN` | [@BotFather](https://t.me/BotFather) |
| `GROQ_API_KEY` | [Groq Console](https://console.groq.com/) |

> Never commit `.env`. It is listed in `.gitignore`.

### 4. Run the bot

```bash
python bot.py
```

In Telegram: `/start` → choose **English** or **Русский** → use the reply keyboard.

### 5. Development checks (optional)

```bash
pip install -r requirements-dev.txt
ruff check bot.py ai_filter.py database.py parser.py locales tests
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## Project Architecture & Folder Structure

```text
Telegram Bot → Parser → DB Check → Pre-filter → Groq AI → UI
```

```text
upwork_sniper_bot/
├── .github/workflows/main.yml   # CI: lint, compile, unit tests
├── .env.example                 # Environment template (no secrets)
├── bot.py                       # Telegram handlers, i18n, orchestration
├── parser.py                    # Upwork HTML scraping (Playwright + BS4)
├── ai_filter.py                 # Groq filtering & cover letter generation
├── database.py                  # SQLite: jobs + user language prefs
├── locales/
│   ├── en.py                    # English UI strings
│   └── ru.py                    # Russian UI strings
├── tests/
│   └── test_ai_filter.py        # Verdict parsing unit tests
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

Runtime artifacts (`jobs.db`, `.env`, `__pycache__/`) are gitignored.

---

## CI/CD (GitHub Actions)

Workflow: [`.github/workflows/main.yml`](.github/workflows/main.yml)

On each push/PR to `main` or `master`:

- `compileall` syntax check  
- **Ruff** lint  
- **unittest** suite  
- Optional smoke step if `TELEGRAM_TOKEN` and `GROQ_API_KEY` are set in **GitHub → Settings → Secrets and variables → Actions**

---

## Security

- All secrets load from **environment variables** only.  
- Use **`.env.example`** as the public template; keep real keys in local `.env` or GitHub Secrets for CI.  
- Do not commit database files or tokens.  

---

## License

Use and adapt for your freelance workflow. Respect **Upwork Terms of Service** when accessing their platform.
