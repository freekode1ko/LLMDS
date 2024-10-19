from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

import string


class TextRefactor:
    """
    Класс TextRefactor предоставляет методы для обработки текста, включая очистку и разбиение на части
    с использованием рекурсивного разбиения по символам. Этот класс используется для подготовки текста
    к дальнейшему анализу и индексации.
    """
    def __init__(self, chunk_size: int = 1250, chunk_overlap: int = 125):
        """
        Инициализирует объект TextRefactor с заданными параметрами разбиения текста.

        :param chunk_size: Максимальный размер одной части текста в символах. По умолчанию 1250.
        :param chunk_overlap: Перекрытие между частями текста в символах. По умолчанию 125.
        """
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )

    @staticmethod
    def _text2doc(text) -> str:
        """
        Очищает текст, удаляя лишние символы, фразы и пробелы, чтобы подготовить его к разбиению.

        :param text: Исходный текст для очистки.
        :return: Очищенный текст, готовый для дальнейшего анализа.
        """
        page_content = text \
            .replace('"', '') \
            .replace('полная версия обзора доступна на нашем портале', '') \
            .replace('подробнее см. в нашем обзоре на портале', '') \
            .replace('полная версия обзора доступна на английском языке', '') \
            .replace('\n\n', ' ') \
            .replace('\n', ' ') \
            .replace('-', ' ') \
            .replace('>', ' ') \
            .replace('   ', ' ') \
            .replace('  ', ' ') \
            .strip(string.punctuation).strip().lower()
        return page_content

    def text_splitter(self, page_text: str, page_context: dict) -> list:
        """
        Разбивает текст на части с учетом перекрытий, добавляя контекстную информацию
        в каждую часть.

        :param page_text: Текст страницы, который нужно разбить на части.
        :param page_context: Метаданные, которые необходимо добавить к каждой части текста.
        :return: Список объектов Document, содержащих части текста и соответствующие метаданные.
        """
        documents = []
        splitted_text = self.splitter.split_text(self._text2doc(page_text))
        for text in splitted_text:
            documents.append(Document(page_content=text, metadata=page_context))
        return documents
