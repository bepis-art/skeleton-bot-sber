import logging

from dotenv import load_dotenv

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ChatAction

from user_session import UserSession
from consts import *

import os
import time
import asyncio
import httpx


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HelperBot:
    def __init__(self):
        load_dotenv()

        server_url = os.getenv('SERVER_URL')
        token = os.getenv('TELEGRAM_TOKEN')

        if not server_url:
            raise Exception('Не установлена переменная SERVER_URL')
        if not token:
            raise Exception('Не установлена переменная TOKEN')

        self.server_url = server_url
        self.bot = Bot(token=token)
        self.router = Router()
        self.register_handlers()
        self.user_sessions = {}

    def register_handlers(self):
        self.router.message(Command("start"))(self.start_command)
        self.router.message(Command("help"))(self.help_command)
        self.router.message(Command("categories"))(self.categories_command)
        self.router.message(Command("history"))(self.history_command)
        self.router.message(Command("clear"))(self.clear_command)
        self.router.message()(self.handle_message)

    async def keep_typing(self, chat_id: int):
        try:
            while True:
                await self.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
                await asyncio.sleep(4)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning(f"Ошибка в keep_typing: {e}")

    def get_user_session(self, user_id: int) -> UserSession:
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = UserSession(user_id)
        return self.user_sessions[user_id]

    async def start_command(self, message: Message):
        await asyncio.sleep(0.3)
        await self.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

        user_session = self.get_user_session(message.from_user.id)
        user_session.clear_history()

        await message.reply(WELCOME_TEXT)

    async def help_command(self, message: Message):
        await asyncio.sleep(0.3)
        await self.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

        await message.reply(HELP_TEXT)

    async def categories_command(self, message: Message):
        await message.reply(CATEGORIES)

    async def history_command(self, message: Message):
        user_session = self.get_user_session(message.from_user.id)

        if not user_session.history:
            response = EMPTY_HISTORY
        else:
            response = HISTORY
            for i, msg in enumerate(user_session.history[-10:], 1):
                role = "👤 Вы" if msg["role"] == "user" else "🤖 Бот"
                time_str = time.strftime("%H:%M:%S", time.localtime(msg["timestamp"]))
                response += f"{i}. {role} ({time_str}):\n{msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}\n\n"

        await message.reply(response)

    async def clear_command(self, message: Message):
        user_session = self.get_user_session(message.from_user.id)
        user_session.clear_history()

        response = CLEAR_HISTORY
        await message.reply(response)

    async def handle_message(self, message: Message):
        user_id = message.from_user.id
        user_text = message.text

        logger.info(f"{user_id}: {user_text}")

        try:
            await asyncio.sleep(0.5)
            await self.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

            typing_task = asyncio.create_task(self.keep_typing(message.chat.id))

            user_session = self.get_user_session(user_id)

            conversation_history = user_session.get_conversation_history()

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.server_url,
                    json={"text": user_text, "history": conversation_history},
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                result = data["text"]

                user_session.add_message("user", user_text)
                user_session.add_message("assistant", result)

                typing_task.cancel()
                try:
                    await typing_task
                except asyncio.CancelledError:
                    pass

                await message.reply(result)

        except Exception as e:
            await asyncio.sleep(0.3)
            await self.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

            error_message = ERROR_MESSAGE

            await message.reply(error_message)
            logger.error(f"Ошибка у пользователя {user_id}: {e}")