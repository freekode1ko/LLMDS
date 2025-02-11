import base64
import logging

from openai import OpenAI

from src.configs.settings import gpt_token, gpt_model

client = OpenAI(
    api_key=gpt_token
)


def ask_gpt_about_fragment(fragment: str, query: str) -> str:
    """
    Отправляет фрагмент с запросом в GPT, и возвращает ответ.

    :param fragment: Фрагмент текста, на основе которого необходимо ответить на вопрос.
    :param query: Вопрос, который необходимо задать GPT.
    :return: Ответ GPT на заданный вопрос, основанный на предоставленном фрагменте текста.
    """
    prompt = f"На основе следующего фрагмента: '{fragment}', ответь на вопрос: '{query}'"
    try:
        response = client.chat.completions.create(
            model=gpt_model,
            messages=[
                {"role": "system",
                 "content": "Ты - помощник, который отвечает на вопросы на основе фрагментов текста."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Ошибка при запросе к GPT: {e}")
        return "Не удалось получить ответ от GPT."


def summarize_answers(answers: list, query: str) -> str:
    """
    Суммирует ответы GPT на основе всех фрагментов.

    :param answers: Список ответов от GPT по отдельным фрагментам текста.
    :param query: Вопрос, на который нужно дать суммарный ответ.
    :return: Суммарный ответ на основе всех предоставленных фрагментов.
    """
    prompt = (
            f"На основе следующих ответов, дай развернутый и детализированный суммарный ответ на запрос: '{query}'. "
            "Ответ должен быть максимально информативным, охватывать все важные детали и быть не короче 1000 "
            "символов:\n\n "
            + "\n\n".join(answers)
    )

    try:
        response = client.chat.completions.create(
            model=gpt_model,
            messages=[
                {"role": "system",
                 "content": "Ты - помощник, который суммирует ответы по запросу пользователя и предоставляет "
                            "максимально развернутый и детализированный ответ."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=1500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Ошибка при суммаризации ответа с GPT: {e}")
        return "Не удалось создать суммарный ответ."


def encode_image(image_path):
    """
    Кодирует изображение в формат base64.

    :param image_path: Путь к изображению, которое необходимо закодировать.
    :return: Изображение, закодированное в формате base64.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def ask_gpt_about_image(image_path: str, query: str) -> str:
    """
    Отправляет изображение в GPT и задает вопрос, возвращая ответ.

    :param image_path: Путь к изображению, которое необходимо отправить.
    :param query: Вопрос, который нужно задать GPT в контексте данного изображения.

    :return: Ответ GPT на вопрос, основанный на анализе изображения.
    """
    try:
        base64_image = encode_image(image_path)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system",
                 "content": "Ты - помощник, который суммирует ответы по запросу пользователя и предоставляет "
                            "максимально развернутый и детализированный ответ."},
                {"role": "user", "content":
                    [{"type": "text", "text": query, },
                     {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]
                 }
            ],
            temperature=0.0,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Ошибка при обработке изображения с GPT: {e}")
        return "Не удалось получить ответ на основе изображения."
