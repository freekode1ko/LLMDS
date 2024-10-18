import validators
import asyncio
import logging
import uuid
import sys

from langchain_community.document_loaders import PyPDFLoader
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.configs import settings
from src.modules.elastic import Elastic, EsHandler
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


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer("Check if index is exist. Clear if exist and create if not")
    # es_handler = elk.EsHandler(es_obj.es, settings.elk_index)
    if es_obj.delete_index(settings.elk_index):
        await message.answer("Index is cleared")
    else:
        await message.answer("Index not found, creating index")
    es_obj.create_index(settings.elk_index)
    await message.answer("Elastic is ready")


def save_token(token: str):
    data_id = str(uuid.uuid4())
    temp_storage[data_id] = token
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
    keyboard = InlineKeyboardBuilder()
    for doc in all_unic_docs:
        token = save_token(doc[1])
        keyboard.add(InlineKeyboardButton(text=doc[0], callback_data=f"@@_{token}"))
    await message.reply("Choose which to remove:", reply_markup=keyboard.as_markup())


@dp.callback_query(F.data.startswith('@@_'))
async def what_to_remove_handler(call: CallbackQuery):
    uid = call.data.replace('@@_', '')
    data_id = temp_storage.get(uid)
    if data_id:
        print(call.from_user.id)
        query = {"query": {"bool": {"must": [{"match": {"metadata.doc_id": data_id}},
                                             {"match": {"metadata.doc_owner": str(call.from_user.id)}}]}}}
        elastic.es.delete_by_query(index=settings.elk_index, body=query)
        del temp_storage[uid]
        print(data_id, ' - removed')
        # TODO del doc from elk

@dp.message()
async def echo_handler(message: Message) -> None:
    try:
        user = message.from_user
        if message.content_type == 'document':
            await message.reply('Принял в обработку, подождите минуту')
            file_id = message.document.file_id
            file = await bot.get_file(file_id)
            file_path = file.file_path
            file_type = file_path.split(".")[-1]
            local_file_path = f'data/input/{user.id}@{file_id}.{file_type}'
            await bot.download_file(file_path=file_path, destination=local_file_path)
            PDF_loader = PyPDFLoader(local_file_path, extract_images=True)
            PDF_pages = PDF_loader.load_and_split()
            for page in PDF_pages:
                page_metadata = {'doc_owner': user.id, 'doc_id': file_id,
                                 'file_name': message.document.file_name, 'page_number': page.metadata['page']}
                splitted_page = transformers_obj.text_splitter(page.page_content, page_metadata)
                await es_handler.vectorstore.aadd_documents(splitted_page)
            print('docs writed to db')
            await message.reply('Файл загружен и готов к использованию')

        # if validators.url(message.text):
        #    logging.info(f'{user}. TRUE: {message.text}')
        # else:
        #    logging.info(f'{user}. FALSE: {message.text}')
    except TypeError:
        await message.answer("Nice try!")


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    asyncio.run(main())
