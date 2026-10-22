import os
import re
from typing import Literal, Optional

from groq import Groq

POSSIBLE_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
]

UserLang = Literal["en", "ru"]


def _build_filter_prompts(user_lang: UserLang, user_filters: str, title: str, description: str) -> tuple[str, str]:
    if user_lang == "en":
        system_prompt = (
            "You are a professional AI assistant for a freelancer. "
            "Analyze Upwork job posts and decide whether they match the user's criteria."
        )
        user_prompt = f"""
User criteria / filters:
{user_filters}

Job information:
Title: {title}
Description: {description}

EVALUATION RULES:
1. If the job matches the user's criteria — verdict is MATCHED.
2. If the job does not match — verdict is REJECTED.

Reply strictly in this format (in English):
Verdict: MATCHED (or REJECTED)
Reason: (one short sentence in English)
"""
        return system_prompt, user_prompt

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

Дай короткий ответ строго по образцу (на русском):
Вердикт: ПОДХОДИТ (или НЕ ПОДХОДИТ)
Причина: (1 короткое предложение на русском)
"""
    return system_prompt, user_prompt


def is_job_matched(ai_response: str, user_lang: UserLang = "ru") -> bool:
    text = ai_response.upper()
    if user_lang == "en":
        if re.search(r"VERDICT\s*:\s*REJECTED", text):
            return False
        if re.search(r"VERDICT\s*:\s*MATCHED", text):
            return True
        if "REJECTED" in text and "MATCHED" not in text:
            return False
        return "MATCHED" in text and "NOT MATCHED" not in text

    if "НЕ ПОДХОДИТ" in text:
        return False
    return "ПОДХОДИТ" in text


def _call_groq(system_prompt: str, user_prompt: str, api_key: Optional[str]) -> str:
    token = api_key or os.getenv("GROQ_API_KEY")
    if not token:
        return "Error: GROQ_API_KEY is not set."

    client = Groq(api_key=token)
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
        except Exception as exc:
            last_error = str(exc)
            continue

    return f"Groq API error (all models unavailable): {last_error}"


def analyze_job_with_groq(
    title: str,
    description: str,
    user_filters: str,
    api_key: Optional[str] = None,
    user_lang: UserLang = "ru",
) -> str:
    """Filter/evaluate a job; verdict and reason follow user_lang (en or ru)."""
    system_prompt, user_prompt = _build_filter_prompts(user_lang, user_filters, title, description)
    return _call_groq(system_prompt, user_prompt, api_key)


def generate_cover_letter_with_groq(
    title: str,
    job_context: str,
    api_key: Optional[str] = None,
) -> str:
    """Cover letters are always generated in English for Upwork proposals."""
    system_prompt = (
        "You write concise, professional Upwork cover letters in English only. "
        "Output only the letter body — no preamble or meta commentary."
    )
    user_prompt = f"""
Write a short, professional, and convincing cover letter in English for this Upwork job.
Focus on solving the client's problem, mention relevant web development skills, and get straight to the point.

Job Title: {title}
Job Details: {job_context}
"""
    return _call_groq(system_prompt, user_prompt, api_key)


if __name__ == "__main__":
    print("ai_filter.py is ready.")
