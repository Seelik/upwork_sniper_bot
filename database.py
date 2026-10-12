import sqlite3
from typing import Optional


def init_db(db_path: str = "jobs.db") -> None:
  """Инициализирует базу данных и создает таблицу jobs, если она не существует."""
  with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                link TEXT NOT NULL,
                published_at TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.commit()


def is_job_exists(job_id: str, db_path: str = "jobs.db") -> bool:
  """Проверяет, существует ли вакансия с таким ID в базе данных."""
  with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM jobs WHERE id = ?", (job_id,))
    return cursor.fetchone() is not None


def add_job(
    job_id: str, title: str, link: str, published_at: str, db_path: str = "jobs.db"
) -> None:
  """Добавляет новую вакансию в базу данных."""
  with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()
    cursor.execute(
        """
            INSERT OR IGNORE INTO jobs (id, title, link, published_at)
            VALUES (?, ?, ?, ?)
        """,
        (job_id, title, link, published_at),
    )
    conn.commit()


if __name__ == "__main__":
  # Простая проверка работоспособности модуля
  init_db()
  print("База данных успешно инициализирована!")

  # Тестовая запись
  test_id = "test-job-123"
  if not is_job_exists(test_id):
    add_job(
        test_id,
        "Python Backend Developer",
        "https://upwork.com/test",
        "2026-10-12",
    )
    print("Тестовая вакансия добавлена.")
  else:
    print("Тестовая вакансия уже существует в базе.")

  print(
      "Проверка существования (должно быть True):", is_job_exists(test_id)
  )