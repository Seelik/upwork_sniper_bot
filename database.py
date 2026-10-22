import sqlite3

def init_db():
    """Инициализирует базу данных и создает таблицу с полной структурой."""
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            title TEXT,
            link TEXT,
            published_at TEXT,
            status TEXT,
            ai_reason TEXT,
            description TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_prefs (
            user_id INTEGER PRIMARY KEY,
            language TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def is_job_exists(job_id: str) -> bool:
    """Проверяет, есть ли вакансия в базе данных."""
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM jobs WHERE job_id = ?", (job_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def add_job(job_id: str, title: str, link: str, published_at: str, status: str, ai_reason: str, description: str = ""):
    """Добавляет вакансию в базу данных."""
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO jobs (job_id, title, link, published_at, status, ai_reason, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (job_id, title, link, published_at, status, ai_reason, description))
    conn.commit()
    conn.close()


def get_user_language(user_id: int) -> str | None:
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT language FROM user_prefs WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def set_user_language(user_id: int, language: str) -> None:
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO user_prefs (user_id, language)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET language = excluded.language
        """,
        (user_id, language),
    )
    conn.commit()
    conn.close()


def update_job_status(job_id: str, status: str) -> bool:
    """Обновляет статус вакансии (matched, rejected, applied)."""
    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE jobs SET status = ? WHERE job_id = ?", (status, job_id))
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated