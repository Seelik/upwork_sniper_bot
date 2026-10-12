import os
from typing import Optional
from groq import Groq

# Актуальные модели, доступные для твоего аккаунта
POSSIBLE_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
]


def analyze_job_with_groq(
    title: str,
    description: str,
    user_filters: str,
    api_key: Optional[str] = None,
) -> str:
  """Анализирует вакансию через Groq SDK с автоподбором активной модели."""
  token = api_key or os.getenv("GROQ_API_KEY")
  if not token:
    return "Ошибка: не задан GROQ_API_KEY."

  client = Groq(api_key=token)

  system_prompt = (
      "Ты — профессиональный AI-ассистент для фрилансера. "
      "Твоя задача — проанализировать вакансию с Upwork и решить, подходит ли она под требования пользователя."
  )

  user_prompt = f"""
Критерии/фильтры пользователя:
{user_filters}

Информация о вакансии:
Заголовок: {title}
Описание: {description}

ИНСТРУКЦИЯ ПО ОЦЕНКЕ:
1. Если вакансия подходит под критерии пользователя — пиши 'ПОДХОДИТ'.
2. Если вакансия не подходит — пиши 'НЕ ПОДХОДИТ'.

Дай короткий ответ строго по образцу:
Вердикт: ПОДХОДИТ (или НЕ ПОДХОДИТ)
Причина: (1 короткое предложение)
"""

  last_error = ""

  for model_name in POSSIBLE_MODELS:
    try:
      completion = client.chat.completions.create(
          model=model_name,
          messages=[
              {"role": "system", "content": system_prompt},
              {"role": "user", "content": user_prompt},
          ],
          temperature=0.2,
      )
      return completion.choices[0].message.content.strip()
    except Exception as e:
      last_error = str(e)
      continue

  return f"Ошибка Groq API (все модели недоступны): {last_error}"


if __name__ == "__main__":
  print("Модуль ai_filter.py готов к работе!")