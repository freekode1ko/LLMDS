import validators
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from src.configs import settings
import src.modules.elastic as elk

token = settings.bot_token
es_obj = elk.Elastic()
dp = Dispatcher()


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


@dp.message()
async def echo_handler(message: Message) -> None:
    try:
        user = message.from_user
        if validators.url(message.text):
            print('TRUE', message.text)
        else:
            print('FALSE')
    except TypeError:
        await message.answer("Nice try!")


async def main() -> None:
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())