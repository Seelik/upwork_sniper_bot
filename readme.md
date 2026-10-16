# Upwork Lead Sniper 2.0

A Telegram bot that finds fresh Upwork job posts, filters them with Groq AI against your criteria, and helps you respond faster with generated cover letters. Search runs on demand from Telegram—no background scraping loops.

![Upwork Lead Sniper UI](docs/ui.png)

## Key Features (v2.0.1)

- **Smart query normalization** — Upwork treats plain spaces as AND. Multi-word queries are auto-expanded with `OR` unless you already use `OR`, `AND`, or quotes.
- **Pre-filter (stop words)** — Blacklisted keywords are rejected before any LLM call to save API usage and noise.
- **Groq AI filtering** — Each job is scored against your custom filter prompt (`ПОДХОДИТ` / `НЕ ПОДХОДИТ` with a short reason).
- **SQLite deduplication** — Processed jobs are stored in `jobs.db` so you never get duplicate notifications for the same listing.
- **Cover letter generation** — One-tap English proposal draft for matched jobs via inline button.

## Tech Stack

- **Python 3.11**
- **aiogram 3**
- **Playwright**
- **BeautifulSoup**
- **SQLite**
- **Groq API**

## Architecture

End-to-end flow for one search:

```text
Telegram Bot → Parser → DB Check → Pre-filter → Groq AI → UI
```

| Step | Module | What happens |
| --- | --- | --- |
| Telegram Bot | `bot.py` | User triggers search; query is normalized and sent to the parser. |
| Parser | `parser.py` | Playwright loads Upwork search HTML; BeautifulSoup extracts title, link, and description. |
| DB Check | `database.py` | Skip jobs already stored in SQLite. |
| Pre-filter | `bot.py` | Drop listings that match stop-word rules. |
| Groq AI | `ai_filter.py` | Evaluate remaining jobs; persist verdict and reason. |
| UI | `bot.py` | Show summary, matched/rejected lists, settings, and cover-letter actions. |

## Setup

### 1. Clone

```bash
git clone https://github.com/Seelik/upwork_sniper_bot.git
cd upwork_sniper_bot
```

### 2. Virtual environment and dependencies

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

> Playwright must download Chromium once per environment. If search returns no jobs and logs mention a missing browser executable, run `playwright install chromium` again.

### 3. Environment variables

Copy the example file and fill in your tokens:

```bash
cp .env.example .env
```

```env
TELEGRAM_TOKEN=your_telegram_bot_token
GROQ_API_KEY=your_groq_api_key
```

- **Telegram:** create a bot via [@BotFather](https://t.me/BotFather).
- **Groq:** create an API key in the [Groq Console](https://console.groq.com/).

Never commit `.env`—it is listed in `.gitignore`.

### 4. Run

```bash
python bot.py
```

Open your bot in Telegram and send `/start`.

## Telegram usage

| Action | Description |
| --- | --- |
| **Start search** | Fetch and analyze new jobs for the current query. |
| **Matched / Rejected** | Last 10 entries from the database with AI verdict. |
| **View settings** | Current search query and AI filter text. |
| **Change query / filter** | Send new text; the bot updates in-memory settings. |
| **Generate cover letter** | Inline button on a job card—Groq drafts a short English proposal. |

## Project layout

| File | Role |
| --- | --- |
| `bot.py` | Entry point, handlers, keyboards, search orchestration |
| `parser.py` | Upwork HTML scraping (Playwright + BeautifulSoup) |
| `ai_filter.py` | Groq SDK integration for filtering and cover letters |
| `database.py` | SQLite schema and job persistence |
| `jobs.db` | Local database (created at runtime; ignored by Git) |

## License

Use and modify for your own freelance workflow. Upwork’s terms of service apply to how you access their site and data.
