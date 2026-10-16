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