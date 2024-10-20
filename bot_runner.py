import uuid
import asyncio

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from langchain_community.document_loaders import PyPDFLoader

from src.configs import settings
from src.modules.elastic import Elastic, BM25Handler, EsHandler
from src.modules.gpt_handler import ask_gpt_about_fragment, summarize_answers, ask_gpt_about_image
from src.modules.whisper_handler import WhisperHandler
from src.modules.transformer import TextRefactor
from src.log.logger_base import selector_logger

bot = Bot(token=settings.bot_token)
dp = Dispatcher()

logger = selector_logger('bot_runner', settings.LOG_LEVEL_INFO)

temp_storage = {}
elastic = Elastic()
transformers_obj = TextRefactor()
whisper_handler = WhisperHandler()
es_handler = EsHandler(elastic.es, settings.elk_index)


def shrink_doc_id(doc_file_id: str):
    """
    Уменьшает длину идентификатора документа для использования в callback_data.

    :param doc_file_id: Идентификатор документа.
    :return: Сокращенный уникальный идентификатор.
    """
    data_id = str(uuid.uuid4())
    temp_storage[data_id] = doc_file_id
    logger.info(f"Файл: {doc_file_id}, записан как: {data_id}")
    return data_id


async def download_file(file_id, user_id):
    file = await bot.get_file(file_id)
    file_type = file.file_path.split(".")[-1]
    file_name = f'{user_id}@{file_id}.{file_type}'
    local_file_path = f'data/input/{file_name}'
    await bot.download_file(file_path=file.file_path, destination=local_file_path)
    return file_name, local_file_path


@dp.message(CommandStart())
async def command_start_handler(message: types.Message):
    """
    Обработка команды /start.
    Проверяет статус индекса в Elasticsearch, очищает или создает его, если необходимо.
    Отправляет пользователю сообщение о статусе подготовки базы данных.

    :param message: Объект сообщения от пользователя. Default
    """
    logger.info("Проверка статуса Elastic")
    await message.answer("Проверка статуса Elastic")
    if elastic.delete_index(settings.elk_index):
        logger.info(f"Индекс {settings.elk_index} очищен")
        await message.answer("Индекс очищен")
    else:
        logger.info(f"Индекс {settings.elk_index} не обнаружен, запущен процесс создания")
        await message.answer("Индекс не обнаружен, запущен процесс создания")
    elastic.create_index(settings.elk_index)
    logger.info("Elastic готов к работе")
    await message.answer("Elastic готов к работе")


@dp.message(F.audio)
async def handle_audio_message(message: types.Message):
    """
    Обработка аудиофайлов, отправленных пользователем.

    :param message: Объект сообщения с аудиофайлом от пользователя.
    """
    user = message.from_user
    try:
        logger.info(f"Пользователь {user.id} отправил аудиофайл для распознавания")
        file_id = message.audio.file_id
        file_name, local_file_path = await download_file(file_id, user.id)
        transcription = whisper_handler.transcribe_audio(local_file_path)
        await message.answer(f"Распознанный текст: {transcription}")
        logger.info(f"Транскрипция аудиофайла {file_name} завершена")
    except Exception as ex:
        logger.error(f"Ошибка при обработке аудиофайла от пользователя {user.id}: {ex}")
        await message.answer("Произошла ошибка во время обработки вашего аудиофайла, попробуйте снова чуть позже.")


@dp.message(Command('delete_doc'))
async def doc_handler(message: types.Message):
    """
    Обработка команды /delete_doc.
    Находит все документы, принадлежащие пользователю, и предлагает удалить один из них.
    Отправляет пользователю клавиатуру с возможностью выбрать документ для удаления.

    :param message: Объект сообщения от пользователя.
    """
    query = {"bool": {"must": [{"term": {"metadata.doc_owner": message.from_user.id}}]}}
    all_users_docs = elastic.es.search(index=settings.elk_index, query=query, size=1000, scroll='3m')
    scroll_id = all_users_docs['_scroll_id']
    hits = all_users_docs['hits']['hits']

    while len(all_users_docs['hits']['hits']) > 0:
        all_users_docs = elastic.es.scroll(scroll_id=scroll_id, scroll='3m')
        scroll_id = all_users_docs['_scroll_id']
        hits.extend(all_users_docs['hits']['hits'])
    temp_storage.clear()  # Очистим временное хранилище во избежание переполнения
    all_unic_docs = set([(hit['_source']['metadata']['file_name'],
                          hit['_source']['metadata']['doc_id']) for hit in hits])
    logger.info(f"{len(hits)} - записей у пользователя: {message.from_user.id}, на {all_unic_docs} документов")
    keyboard = InlineKeyboardBuilder()
    for doc in all_unic_docs:
        token = shrink_doc_id(doc[1])
        keyboard.add(InlineKeyboardButton(text=doc[0], callback_data=f"@@_{token}"))
    await message.answer("Выберете документ для удаления:", reply_markup=keyboard.as_markup())


@dp.callback_query(F.data.startswith('@@_'))
async def delete_document(call: types.CallbackQuery):
    """
    Удаляет выбранный документ из базы данных Elasticsearch.

    :param call: Объект callback-запроса от пользователя.
    """
    uid = call.data.replace('@@_', '')
    doc_id = temp_storage.get(uid)
    try:
        query = {"query": {"bool": {"must": [{"match": {"metadata.doc_id": doc_id}},
                                             {"match": {"metadata.doc_owner": str(call.from_user.id)}}]}}}
        elastic.es.delete_by_query(index=settings.elk_index, body=query)
        await bot.send_message(call.from_user.id, f'Документ успешно удален из базы знаний')
        logger.info(f"У пользователя {call.from_user.id} успешно удален документ: {doc_id}")
        del temp_storage[uid]
    except Exception as ex:
        await bot.send_message(call.from_user.id, f'Документ удалить не удалось, ошибка: {ex}')
        logger.error(f"Не удалось удалить документ {doc_id} у пользователя {call.from_user.id}: {ex}")


@dp.message(F.photo)
async def handle_image_message(message: types.Message):
    """
    Обработка изображений, отправленных пользователем.
    Сохраняет изображение, отправляет его в GPT для анализа и возвращает ответ пользователю.

    :param message: Объект сообщения с изображением от пользователя.
    """
    user = message.from_user
    query = message.caption or "Внимательно изучи и скажи что тут изображено, подмечай все"
    logger.info(f"Пользователь {user.id} отправил изображение для распознавания вместе с запросом: {query}")
    file_id = message.photo[-1].file_id
    file_name, local_file_path = await download_file(file_id, user.id)
    response = ask_gpt_about_image(local_file_path, query)
    await message.answer(response, parse_mode='Markdown')
    logger.info(f"Файл {file_name} распознан и ответ сформирован")


@dp.message(F.document)
async def handle_document_message(message: types.Message):
    """
    Обработка документов, отправленных пользователем.
    Загружает документ, обрабатывает его с помощью PyPDFLoader и сохраняет в базу данных Elasticsearch.

    :param message: Объект сообщения с документом от пользователя.
    """
    user = message.from_user
    try:
        logger.info(f"Пользователь {user.id} загружает документ в базу знаний")
        await message.reply('Принял в обработку, подождите минуту')
        file_id = message.document.file_id
        file_name, local_file_path = await download_file(file_id, user.id)
        pdf_loader = PyPDFLoader(local_file_path)
        pdf_pages = pdf_loader.load_and_split()

        for page in pdf_pages:
            page_metadata = {'doc_owner': user.id, 'doc_id': file_id, 'file_name': message.document.file_name,
                             'page_number': page.metadata['page']}
            splitted_page = transformers_obj.text_splitter(page.page_content, page_metadata)
            await es_handler.vectorstore.aadd_documents(splitted_page)

        await message.reply('Файл загружен и готов к использованию')
        logger.info(f"Файл {file_name} обработан и сохранен в Elasticsearch")
    except Exception as ex:
        logger.error(f"Пользователь {user.id} получил ошибку при загрузке документа: {ex}")
        await message.answer("Произошла ошибка во время обработки вашего запроса, попробуйте снова чуть позже.")


@dp.message(F.text)
async def echo_handler(message: types.Message):
    """
    Обработка текстовых сообщений.
    Выполняет поиск по базе данных Elasticsearch, отправляет найденные фрагменты в GPT,
    а затем возвращает суммарный ответ пользователю.

    :param message: Объект текстового сообщения от пользователя.
    """
    user = message.from_user
    try:
        logger.info(f"Пользователь {user.id} спросил базу знаний: {message.text}")
        bm25_handler = BM25Handler(elastic.es, settings.elk_index)
        documents = bm25_handler.vectorstore.similarity_search_with_relevance_scores(query=message.text.lower())

        if not documents:
            await message.answer("Не удалось найти информации в базе знаний")
            return

        answers = [ask_gpt_about_fragment(doc.page_content, message.text) for doc, _ in documents]
        summary = summarize_answers(answers, message.text)

        await message.reply(summary, parse_mode='Markdown')
    except Exception as ex:
        logger.error(f"Пользователь {user.id} получил ошибку при работе с ботом: {ex}")
        await message.answer("Произошла ошибка во время обработки вашего запроса, попробуйте снова чуть позже.")


async def main():
    """
    Основная функция для запуска Telegram-бота.
    Настраивает логгирование и запускает polling для обработки сообщений.
    """
    logger.info('Запуск бота')
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
