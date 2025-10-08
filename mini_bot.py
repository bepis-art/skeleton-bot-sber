"""
🤖 Упрощенная версия AI Telegram-бота для обучения
Этот файл содержит минимальный код для создания работающего AI-бота

Что нужно для запуска:
1. pip install aiogram langchain-gigachat python-dotenv
2. Создать файл .env с токенами:
   TELEGRAM_TOKEN=your_telegram_bot_token
   GIGACHAT_CREDENTIALS=your_gigachat_credentials
3. Запустить: python bot_simple_example.py
"""

import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ChatAction
from langchain_gigachat.chat_models import GigaChat
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain.tools import tool

# Загружаем переменные окружения
load_dotenv()

# Проверяем наличие необходимых токенов
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")

if not TELEGRAM_TOKEN:
    raise RuntimeError("❌ TELEGRAM_TOKEN не установлен в файле .env!")
if not GIGACHAT_CREDENTIALS:
    raise RuntimeError("❌ GIGACHAT_CREDENTIALS не установлен в файле .env!")

print("✅ Токены загружены успешно")

# Инициализация Telegram-бота
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Инициализация GigaChat модели
model = GigaChat(
    model="GigaChat-2-Max",  # Используем максимальную модель
    verify_ssl_certs=False,
    scope="GIGACHAT_API_B2B"
)
print("✅ GigaChat модель инициализирована")

# ============================================================================
# СИСТЕМНЫЙ ПРОМПТ - здесь определяется роль и поведение вашего бота
# ============================================================================
system_prompt = """
Ты - дружелюбный AI-помощник, который помогает пользователям с различными вопросами.

Правила работы:
1. Отвечай на русском языке
2. Будь вежливым и дружелюбным
3. Давай полезные и конкретные ответы
4. Если не знаешь ответа, честно признайся в этом
5. Не используй Markdown разметку (жирный текст, заголовки и т.д.)

Твоя цель - помогать пользователям и отвечать на их вопросы максимально полезно.
"""

# ============================================================================
# ИНСТРУМЕНТЫ - функции, которые может использовать ваш бот
# ============================================================================

@tool
def get_current_time() -> str:
    """
    Возвращает текущее время.
    Используй этот инструмент, когда пользователь спрашивает про время.
    
    Returns:
        str: Текущее время в формате ЧЧ:ММ:СС
    """
    from datetime import datetime
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"🔧 Вызван инструмент get_current_time: {current_time}")
    return f"⏰ Текущее время: {current_time}"

@tool
def calculate_sum(a: float, b: float) -> str:
    """
    Складывает два числа.
    
    Args:
        a: Первое число
        b: Второе число
        
    Returns:
        str: Результат сложения
    """
    result = a + b
    print(f"🔧 Вызван инструмент calculate_sum: {a} + {b} = {result}")
    return f"Результат сложения: {result}"

# Список всех доступных инструментов
tools = [get_current_time, calculate_sum]

# ============================================================================
# СОЗДАНИЕ АГЕНТА
# ============================================================================
agent = create_react_agent(
    model,
    tools=tools,
    checkpointer=MemorySaver(),  # Сохраняет историю диалога
    prompt=system_prompt
)
print("✅ Агент создан успешно")

# ============================================================================
# ХРАНИЛИЩЕ ИСТОРИИ ДИАЛОГОВ
# ============================================================================
user_threads = {}  # Словарь для хранения thread_id каждого пользователя

# ============================================================================
# ОБРАБОТЧИКИ КОМАНД
# ============================================================================

@dp.message(Command("start"))
async def start_command(message: Message):
    """Обработчик команды /start"""
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    await asyncio.sleep(0.3)
    
    welcome_text = """
👋 Привет! Я простой AI-помощник.

Я могу:
• Отвечать на ваши вопросы
• Показать текущее время (спроси "Сколько сейчас времени?")
• Складывать числа (попроси "Сложи 5 и 3")

Просто напиши мне сообщение!
    """
    await message.reply(welcome_text.strip())

@dp.message(Command("help"))
async def help_command(message: Message):
    """Обработчик команды /help"""
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    await asyncio.sleep(0.3)
    
    help_text = """
📋 Доступные команды:

/start - Начать работу с ботом
/help - Показать эту справку
/clear - Очистить историю диалога

💡 Просто напиши мне любой вопрос, и я постараюсь помочь!
    """
    await message.reply(help_text.strip())

@dp.message(Command("clear"))
async def clear_command(message: Message):
    """Обработчик команды /clear - очистка истории диалога"""
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    await asyncio.sleep(0.3)
    
    user_id = message.from_user.id
    if user_id in user_threads:
        del user_threads[user_id]
    await message.reply("✅ История диалога очищена!")

# ============================================================================
# ОСНОВНОЙ ОБРАБОТЧИК СООБЩЕНИЙ
# ============================================================================

@dp.message()
async def handle_message(message: Message):
    """Основной обработчик всех текстовых сообщений"""
    user_id = message.from_user.id
    user_text = message.text
    
    # Создаем уникальный thread_id для пользователя (для сохранения истории)
    if user_id not in user_threads:
        import time
        user_threads[user_id] = f"user_{user_id}_{int(time.time())}"
    
    thread_id = user_threads[user_id]
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        # Показываем статус "печатает..."
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        
        # Логируем запрос пользователя
        print(f"\n📨 Получено сообщение от пользователя {user_id}: {user_text}")
        
        # Отправляем запрос агенту
        response = agent.invoke(
            {"messages": [("user", user_text)]}, 
            config=config
        )
        
        # Получаем ответ от агента
        assistant_message = response["messages"][-1].content
        print(f"💬 Ответ агента: {assistant_message[:100]}...")  # Первые 100 символов
        
        # Отправляем ответ пользователю
        await message.reply(assistant_message)
        
    except Exception as e:
        # Обработка ошибок
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        error_message = f"😔 Произошла ошибка при обработке вашего сообщения. Попробуйте позже.\n\nОшибка: {str(e)}"
        await message.reply(error_message)
        print(f"❌ Ошибка для пользователя {user_id}: {e}")

# ============================================================================
# ЗАПУСК БОТА
# ============================================================================

async def main():
    """Главная функция для запуска бота"""
    print("\n" + "="*50)
    print("🤖 Простой AI Telegram-бот запущен!")
    print("📱 Найдите вашего бота в Telegram и начните диалог")
    print("🛑 Для остановки нажмите Ctrl+C")
    print("="*50 + "\n")
    
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")

