# Upwork Sniper Bot 2.0

Telegram-бот на Python и **aiogram 3.x**. Он забирает свежие заказы с Upwork, мгновенно оценивает их через **Groq API** и оставляет только те, что совпадают с вашими критериями. Для подходящих вакансий бот готовит готовый **Cover Letter** на английском.

Поиск запускается вручную из Telegram. Повторные вакансии не приходят снова: каждая карточка сохраняется в локальной базе SQLite.

## Технологический стек

- **Python 3.11**
- **aiogram 3.x** — Telegram Bot API
- **SQLite** — локальное хранение вакансий (`jobs.db`)
- **Groq API** — фильтрация заказов и генерация сопроводительного письма
- **Playwright** и **BeautifulSoup** — загрузка страницы поиска Upwork и разбор карточек вакансий

## Установка и запуск

Нужны Python 3.11 и токены Telegram-бота и Groq.

1. Клонируйте репозиторий:

```bash
git clone https://github.com/Seelik/upwork_sniper_bot.git
cd upwork_sniper_bot
```

2. Создайте виртуальное окружение и установите зависимости:

```bash
python -m venv .venv
```

Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
pip install aiogram groq beautifulsoup4 playwright python-dotenv
playwright install chromium
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install aiogram groq beautifulsoup4 playwright python-dotenv
playwright install chromium
```

3. Создайте файл `.env` в корне проекта и укажите токены:

```env
TELEGRAM_TOKEN=your_telegram_bot_token
GROQ_API_KEY=your_groq_api_key
```

`TELEGRAM_TOKEN` выдаёт [@BotFather](https://t.me/BotFather). `GROQ_API_KEY` берётся в [консоли Groq](https://console.groq.com/).

4. Запустите бота из корня проекта:

```bash
python bot.py
```

В консоли появится сообщение, что бот запущен. В Telegram отправьте ему `/start`.

## Архитектура

| Файл | Роль |
| --- | --- |
| `bot.py` | Точка входа. Поднимает aiogram-диспетчер, клавиатуру и сценарии: поиск, настройки, списки одобренных и отсеянных вакансий, генерация Cover Letter. |
| `parser.py` | Открывает страницу поиска Upwork через Playwright и собирает заголовок, ссылку и описание карточки через BeautifulSoup. |
| `ai_filter.py` | Отправляет вакансию в Groq API и возвращает вердикт `ПОДХОДИТ` / `НЕ ПОДХОДИТ` с короткой причиной. Тот же вызов используется для текста отклика. |
| `database.py` | Создаёт SQLite-базу `jobs.db`, проверяет, была ли вакансия уже обработана, и сохраняет статус, причину и описание. |

Поток одного поиска:

1. `bot.py` собирает URL поиска из текущего запроса пользователя.
2. `parser.py` возвращает список карточек.
3. Уже известные `job_id` пропускаются через `database.py`.
4. Стоп-слова отсекают заведомо нерелевантные заказы до обращения к модели.
5. `ai_filter.py` оценивает оставшиеся вакансии по тексту фильтра.
6. Результат пишется в SQLite со статусом `matched` или `rejected`.

## Работа в Telegram

После `/start` доступны кнопки:

- **Запустить поиск** — новая выборка по текущему запросу.
- **Одобренные** / **Отсеянные** — последние 10 записей из базы и вердикт модели.
- **Посмотреть настройки** — активные поисковый запрос и AI-фильтр.
- **Изменить запрос** / **Изменить фильтр** — бот ждёт следующий текст и подставляет его в поиск или в промпт Groq.

Под карточкой вакансии есть ссылка на Upwork и кнопка **Сгенерировать отклик**. Она просит Groq написать короткий Cover Letter на английском по заголовку и описанию заказа.
