import os
import requests
from typing import Optional


def analyze_job_with_groq(
    title: str, description: str, user_filters: str, api_key: Optional[str] = None
) -> str:
  """Анализирует вакансию через Groq API и возвращает вердикт: подходит ли под фильтры пользователя."""
  token = api_key or os.getenv("GROQ_API_KEY")
  if not token:
    return (
        "Ошибка: не задан GROQ_API_KEY. Проверь настройки окружения или .env."
    )

  url = "https://api.groq.com/openai/v1/chat/completions"

  headers = {
      "Authorization": f"Bearer {token}",
      "Content-Type": "application/json",
  }

  prompt = f"""
    Ты — профессиональный AI-ассистент для фрилансера. 
    Твоя задача — проанализировать вакансию с Upwork и решить, подходит ли она под требования пользователя.

    Критерии/фильтры пользователя: {user_filters}

    Информация о вакансии:
    Заголовок: {title}
    Описание: {description}

    Дай короткий ответ в формате:
    1. Вердикт: ПОДХОДИТ или НЕ ПОДХОДИТ
    2. Причина (1-2 предложения, почему так решил)
    """

  payload = {
      "model": "llama-3.3-70b-versatile",
      "messages": [{"role": "user", "content": prompt}],
      "temperature": 0.1,
  }

  try:
    response = requests.post(url, json=payload, headers=headers, timeout=15)
    if response.status_code == 200:
      data = response.json()
      return data["choices"][0]["message"]["content"].strip()
    else:
      return f"Ошибка API Groq: статус {response.status_code}"
  except Exception as e:
    return f"Ошибка подключения к Groq API: {e}"


if __name__ == "__main__":
  # Тестовая проверка фильтрации
  print("Модуль ai_filter.py готов к работе!")