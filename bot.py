# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers.order import register_order_handlers
from handlers.admin import register_admin_handlers
from database import init_db
from handlers.users import register_user_handlers
logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Initialize database
    init_db()
    
    # Register handlers
    register_admin_handlers(dp)
    register_user_handlers(dp)
    register_order_handlers(dp)
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())