from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

import string


class TextRefactor:
    def __init__(self, chunk_size: int = 1250, chunk_overlap: int = 125):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )

    @staticmethod
    def _text2doc(text) -> str:
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
        documents = []
        splitted_text = self.splitter.split_text(self._text2doc(page_text))
        for text in splitted_text:
            documents.append(Document(page_content=text, metadata=page_context))
        return documents
