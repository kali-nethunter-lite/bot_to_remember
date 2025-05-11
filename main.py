import subprocess
import sys
import importlib
import asyncio

required_packages = ['aiogram', 'sqlalchemy', 'aiosqlite']

def check_and_install_packages():
    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            print(f"📦 Встановлення пакету: {package}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
check_and_install_packages()


from aiogram import Bot, Dispatcher
from app.database.models import async_mane
from app.handlers import router
from app.database.system import token
from logger import logger

async def main():
    await async_mane()
    logger.info("\n--------------------Запуск бота--------------------")   
    bot = Bot(token)
    dp = Dispatcher()
    dp.include_router(router)

    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Бот завершує роботу...")
    finally:
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n--------------------Бот вимкнено--------------------\n")
