import asyncio

from aiogram import Dispatcher

from HelperBot import HelperBot

async def main():
    bot = HelperBot()
    dp = Dispatcher()
    dp.include_router(bot.router)
    await dp.start_polling(bot.bot)

if __name__ == "__main__":
    asyncio.run(main())