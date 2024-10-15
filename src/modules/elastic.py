from elasticsearch import Elasticsearch
from langchain_elasticsearch.vectorstores import BM25Strategy, ElasticsearchStore

from src.configs import settings
from src.modules.embedding import get_embedding


class Elastic:
    def __init__(self):
        print('Подключение к Elasticsearch')
        self.es = Elasticsearch(
            settings.elk_url,
            ca_certs=settings.ca_certs,
            basic_auth=("elastic", settings.elastic_password))

    def create_index(self, index_name: str):
        print(f'Создание индекса {index_name}')
        if not self.es.indices.exists(index=index_name):
            self.es.indices.create(index=index_name)
            return True
        else:
            print(f'Индекс {index_name} уже существует')
            return False

    def delete_index(self, index_name: str):
        print(f'Очистка индекса {index_name}')
        try:
            self.es.indices.delete(index=index_name)
            print(f'Индекс {index_name} очищен')
            return True
        except Exception as ex:
            print(f'Индекс {index_name} не может быть очищен: {ex}')
            return False


class EsHandler:
    def __init__(self, es: Elasticsearch, index_name: str):
        self.vectorstore = ElasticsearchStore(es_connection=es, embedding=get_embedding(), index_name=index_name)


class BM25Handler:
    def __init__(self, es: Elasticsearch, index_name: str):
        self.vectorstore = ElasticsearchStore(es_connection=es, index_name=index_name, strategy=BM25Strategy())
