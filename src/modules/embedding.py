from typing import Any, Coroutine, List

from langchain_community.embeddings import HuggingFaceEmbeddings

from src.configs.settings import emd_count_docs


class HuggingFaceE5Embeddings(HuggingFaceEmbeddings):
    def embed_query(self, text: str) -> List[float]:
        """
        Преобразование текста в эмбеддинги.

        :param text: текст
        :return: вектор
        """
        text = f'query: {text}'
        return super().embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Преобразование списка текстов в эмбеддинги.

        :param texts: список из текстов.
        :return: список векторов.
        """
        texts = [f'passage: {text}' for text in texts]
        embed_texts = []
        for i_text in range(0, len(texts), emd_count_docs):
            embed_texts.extend(super().embed_documents(texts[i_text:i_text + emd_count_docs]))
        return embed_texts
        # return super().embed_documents(texts)

    async def aembed_query(self, text: str) -> Coroutine[Any, Any, List[float]]:
        """
        Преобразование текста в эмбеддинги.

        :param text: текст.
        :return: вектор.
        """
        text = f'query: {text}'
        return await super().aembed_query(text)

    async def aembed_documents(
        self, texts: List[str]
    ) -> Coroutine[Any, Any, List[List[float]]]:
        """
        Преобразование списка текстов в эмбеддинги.

        :param texts: список из текстов.
        :return: список векторов.
        """
        texts = [f'passage: {text}' for text in texts]
        return await super().aembed_documents(texts)


def get_embedding():
    """Возвращает модель по созданию эмбедингов."""
    e5_embedding = HuggingFaceE5Embeddings(model_name='intfloat/multilingual-e5-large')  # -> large
    return e5_embedding
