import os
import asyncio
import logging
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from handlers import common, response



load_dotenv()
# Запуск бота
async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )

    token = os.getenv('PRICE_CATEGORY_TOKEN')
    bot = Bot(token=token)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(common.router)
    dp.include_router(response.router)
    

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())

