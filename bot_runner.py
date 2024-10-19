import asyncio
import uuid
import os

from langchain_community.document_loaders import PyPDFLoader
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, ContentType
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.configs import settings
from src.modules.elastic import Elastic, EsHandler
from src.modules.gpt_handler import ask_gpt_about_fragment, summarize_answers, ask_gpt_about_image
from src.log.logger_base import Logger, selector_logger
import src.modules.elastic as elk
import src.modules.transformer as transformer

transformers_obj = transformer.TextRefactor()
elastic = Elastic()
es_handler = EsHandler(elastic.es, settings.elk_index)
token = settings.bot_token
es_obj = elk.Elastic()
dp = Dispatcher()
temp_storage = {}
bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
logger = selector_logger('bot_runner', settings.LOG_LEVEL_INFO)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    logger.info("Проверка статуса Elastic")
    await message.answer("Проверка статуса Elastic")
    if es_obj.delete_index(settings.elk_index):
        logger.info(f"Индекс {settings.elk_index} очищен")
        await message.answer("Индекс очищен")
    else:
        logger.info(f"Индекс {settings.elk_index} не обнаружен, запущен процесс создания")
        await message.answer("Индекс не обнаружен, запущен процесс создания")
    es_obj.create_index(settings.elk_index)
    logger.info("Elastic готов к работе")
    await message.answer("Elastic готов к работе")


def save_token(doc_file_id: str):
    data_id = str(uuid.uuid4())
    temp_storage[data_id] = doc_file_id
    logger.info(f"Файл: {doc_file_id}, записан как: {data_id}")
    return data_id


@dp.message(Command('delete_doc'))
async def doc_handler(message: Message) -> None:
    # all_docs = elastic.es.search(index=settings.elk_index, query={"match_all": {}}, size=1000, scroll='10m')
    query = {"bool": {"must": [{"term": {"metadata.doc_owner": message.from_user.id}}]}}
    all_users_docs = elastic.es.search(index=settings.elk_index, query=query, size=1000, scroll='3m')
    scroll_id = all_users_docs['_scroll_id']
    hits = all_users_docs['hits']['hits']

    while len(all_users_docs['hits']['hits']) > 0:
        all_users_docs = elastic.es.scroll(scroll_id=scroll_id, scroll='3m')
        scroll_id = all_users_docs['_scroll_id']
        hits.extend(all_users_docs['hits']['hits'])

    all_unic_docs = set([(hit['_source']['metadata']['file_name'],
                          hit['_source']['metadata']['doc_id']) for hit in hits])
    logger.info(f"{len(hits)} - записей у пользователя: {message.from_user.id}, на {all_unic_docs} документов")
    keyboard = InlineKeyboardBuilder()
    for doc in all_unic_docs:
        token = save_token(doc[1])
        keyboard.add(InlineKeyboardButton(text=doc[0], callback_data=f"@@_{token}"))
    await message.answer("Выберете документ для удаления:", reply_markup=keyboard.as_markup())


@dp.callback_query(F.data.startswith('@@_'))
async def what_to_remove_handler(call: CallbackQuery):
    try:
        uid = call.data.replace('@@_', '')
        data_id = temp_storage.get(uid)
        logger.info(f"{call.from_user.id} хочет удалить документ: {data_id}")
        if data_id:
            query = {"query": {"bool": {"must": [{"match": {"metadata.doc_id": data_id}},
                                                 {"match": {"metadata.doc_owner": str(call.from_user.id)}}]}}}
            elastic.es.delete_by_query(index=settings.elk_index, body=query)
            del temp_storage[uid]
            await bot.send_message(call.from_user.id, f'Документ успешно удален из базы знаний')
            logger.info(f"У пользователя {call.from_user.id} успешно удален документ: {data_id}")
    except Exception as ex:
        await bot.send_message(call.from_user.id, f'Документ удалить не удалось, ошибка: {ex}')
        logger.info(f"Пользователю {call.from_user.id} не удалось удалить документ: {data_id} по причине: {ex}")


@dp.message(F.photo)
async def handle_image_message(message: Message):
    """
    Обработка изображений, отправленных пользователем.
    """
    query = message.caption or "Внимательно изучи и скажи что тут изображено, подмечай все"
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    print('Фото получено')
    image_path = os.path.join('data/input/', f"{photo.file_id}.png")
    await bot.download_file(file_info.file_path, image_path)
    print('Фото скачано')
    response = ask_gpt_about_image(image_path, query)
    print('Получен ответ')
    await message.answer(response, parse_mode=ParseMode.MARKDOWN)


@dp.message(F.document)
async def handle_image_message(message: Message):
    user = message.from_user
    try:
        logger.info(f"Пользователь {user.id} загружает документ в базу знаний")
        await message.reply('Принял в обработку, подождите минуту')
        file_id = message.document.file_id
        file = await bot.get_file(file_id)
        file_type = file.file_path.split(".")[-1]
        file_name = f'{user.id}@{file_id}.{file_type}'
        local_file_path = f'data/input/{file_name}'
        await bot.download_file(file_path=file.file_path, destination=local_file_path)
        logger.info(f"файл {file_name} сохранен локально")
        pdf_loader = PyPDFLoader(local_file_path, extract_images=True)
        pdf_pages = pdf_loader.load_and_split()
        logger.info(f"Начало обработки {file_name}, содержит {len(pdf_pages)}")
        for page in pdf_pages:
            page_metadata = {'doc_owner': user.id, 'doc_id': file_id,
                             'file_name': message.document.file_name, 'page_number': page.metadata['page']}
            splitted_page = transformers_obj.text_splitter(page.page_content, page_metadata)
            await es_handler.vectorstore.aadd_documents(splitted_page)
        await message.reply('Файл загружен и готов к использованию')
        logger.info(f"файл {file_name} обработан и сохранен в ELK")
    except Exception as ex:
        logger.warning(f"Пользователь {user.id} получил ошибку при загрузке документа: {ex.__class__.__name__}")
        await message.answer("Произошла ошибка во время обработки вашего запроса, попробуйте снова чуть позже.")


@dp.message(F.text)
async def echo_handler(message: Message) -> None:
    user = message.from_user
    try:
        logger.info(f"Пользователь {user.id} спросил базу знаний: {message.text}")
        bm25_handler = elk.BM25Handler(es_obj.es, settings.elk_index)
        documents = bm25_handler.vectorstore.similarity_search_with_relevance_scores(query=message.text.lower())
        if not documents:
            await message.answer("Не удалось найти информации в базе знаний")
            logger.warning(f"Пользователь {user.id} не нашел ответа в базе знаний по вопросу: {message.text}")
            return
        answers = []
        for doc, score in documents:
            logger.debug(f"DOC: {doc}, {score}")
            answer = ask_gpt_about_fragment(doc, message.text)
            answers.append(answer)
        await message.reply(summarize_answers(answers, message.text))
    except Exception as ex:
        logger.warning(f"Пользователь {user.id} получил ошибку при работе с ботом: {ex.__class__.__name__}")
        await message.answer("Произошла ошибка во время обработки вашего запроса, попробуйте снова чуть позже.")


async def main() -> None:
    logger.info('Запуск бота')
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
