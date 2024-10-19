import os
import logging
from openai import OpenAI
from src.configs.settings import gpt_token

# Инициализация клиента OpenAI с использованием API-ключа
client = OpenAI(
    api_key=gpt_token
)


def ask_gpt_about_fragment(fragment: str, query: str) -> str:
    """
    Отправляет фрагмент с запросом в GPT и возвращает ответ.
    """
    prompt = f"На основе следующего фрагмента: '{fragment}', ответь на вопрос: '{query}'"

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system",
                 "content": "Ты - помощник, который отвечает на вопросы на основе фрагментов текста."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,  # Низкая температура для четкости и точности
            max_tokens=300  # Максимальная длина ответа
        )
        # Извлекаем текст ответа из структуры ответа
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        logging.error(f"Ошибка при запросе к GPT: {e}")
        return "Не удалось получить ответ от GPT."


def summarize_answers(answers: list, query: str) -> str:
    """
    Суммирует ответы GPT на основе всех фрагментов.
    """
    prompt = (
            f"На основе следующих ответов, дай развернутый и детализированный суммарный ответ на запрос: '{query}'. "
            "Ответ должен быть максимально информативным, охватывать все важные детали и быть не короче 1000 символов:\n\n"
            + "\n\n".join(answers)
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system",
                 "content": "Ты - помощник, который суммирует ответы по запросу пользователя и предоставляет максимально развернутый и детализированный ответ."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,  # Низкая температура для точного и детализированного ответа
            max_tokens=1500  # Увеличиваем для более длинного и детализированного ответа
        )
        # Извлекаем текст ответа из структуры ответа
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        logging.error(f"Ошибка при суммаризации ответа с GPT: {e}")
        return "Не удалось создать суммарный ответ."
