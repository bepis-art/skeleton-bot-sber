import os
import time
import asyncio
import re
import json
from typing import Dict, List
from dotenv import find_dotenv, load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ChatAction

# Импортируем наш RAG
from simple_rag import SimpleRAG as RAGManager

# Импортируем GigaChat
from gigachat import GigaChat

def clean_markdown(text: str) -> str:
    """Очищает текст от Markdown разметки"""
    if not text:
        return text
    
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    text = re.sub(r'~~(.*?)~~', r'\1', text)
    text = re.sub(r'`(.*?)`', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'^[-*_]{3,}$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()
    
    return text

# Загружаем переменные окружения
load_dotenv()

async def keep_typing(chat_id: int):
    """Поддерживает статус 'печатает...'"""
    try:
        while True:
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            await asyncio.sleep(4)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Ошибка в keep_typing: {e}")

print(f"Using token: {os.getenv('TELEGRAM_TOKEN')}")
print(f"Using GigaChat credentials: {os.getenv('GIGACHAT_CREDENTIALS')}")

# Конфигурация
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN не установлен!")

GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")
if not GIGACHAT_CREDENTIALS:
    print("⚠️ GIGACHAT_CREDENTIALS не установлен! Бот будет работать только с RAG")
    GIGACHAT_ENABLED = False
else:
    GIGACHAT_ENABLED = True

# Инициализация RAG системы
print("🔄 Инициализация RAG системы для ЧС...")
rag_manager = RAGManager(documents_path="documents")

# Загружаем документы
print("📚 Загружаем инструкции по ЧС...")
success = rag_manager.load_all_documents()
if success:
    stats = rag_manager.get_stats()
    print(f"✅ RAG система загружена: {stats['total_documents']} документов")
    for category, count in stats['categories'].items():
        print(f"   {category}: {count} документов")
else:
    print("❌ Ошибка загрузки RAG системы")

# Инициализация Telegram-бота
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Системный промпт для бота-спасателя
SYSTEM_PROMPT = """Ты — опытный спасатель и инструктор по действиям в чрезвычайных ситуациях. Ты помогаешь гражданам быстро сориентироваться и принять правильные решения при угрозе жизни, здоровью или имуществу.
Твоя задача — не заменить экстренные службы, а сохранить жизнь до их прибытия.

ВАЖНО: Всегда сначала используй информацию из БАЗЫ ЗНАНИЙ. Эти инструкции проверены и содержат конкретные шаги действий.

СТРУКТУРА РАБОТЫ:

1. АНАЛИЗ КОНТЕКСТА:
- Внимательно изучи предоставленные инструкции из базы знаний
- Определи самые важные и релевантные шаги
- Учти категорию ЧС (бытовая, БПЛА, природная, техногенная)
- Не называй тип ЧС в ответе явно, но используй его для выбора алгоритма действий

2. ФОРМИРОВАНИЕ ПРОЕКТА ОТВЕТА
- Сначала мысленно составь пошаговый алгоритм действий.
- Проверь его на соответствие предоставленным инструкциям.
- Убедись, что инструкция безопасна, проста и выполнима без специального оборудования.

3. СТРУКТУРА ИТОГОВОГО ОТВЕТА
- Дай чёткие, короткие инструкции (не более 5 шагов за раз).
- Укажи, когда и как вызывать экстренные службы.
- При необходимости — предложи сформировать сообщение для отправки спасателям.
- Заверши фразой: «Пожалуйста, сообщите, получилось ли у вас выполнить эти действия?»
- Обязательно добавь: «Этот бот не заменяет помощь профессиональных спасателей. При угрозе жизни немедленно звоните в экстренные службы».

4. ВАЖНЫЕ УТОЧНЕНИЯ
- Если пользователь сообщает о реальной угрозе жизни (например, «не могу дышать», «горит дом», «потерял сознание ребёнок»):
  * Немедленно активируй режим SOS:
- Первым сообщением — краткая инструкция («Откройте окно», «Ложитесь на пол», «Не трогайте провода»).
- Вторым — призыв: «СРОЧНО звоните 112!».
- Если ситуация не критична, но требует подготовки («хочу знать, что делать при землетрясении»), дай профилактическую памятку.

5. Правила работы:
1) Отвечай на русском языке.
2) Всегда приветствуй пользователя.
3) Давай только проверенные, официальные рекомендации (МЧС, ВОЗ, МВД).
4) Не давай советов, требующих медицинской или технической квалификации (например, «наложите жгут» — только если это в официальной инструкции для граждан).
5) Подчёркивай, что это общая консультация, а не замена спасательной операции.
6) Не используй Markdown.
7) Сохраняй спокойный, уверенный и поддерживающий тон.
8) Отвечай прямо, без вводных фраз вроде «Как ИИ, я не могу…».
9) Анализируй найденную информацию перед ответом.

Важно: Твои ответы не заменяют помощь профессиональных спасателей, медиков или экстренных служб. При любой угрозе жизни — звоните 112."""

# Хранилище истории диалогов
user_sessions = {}

class UserSession:
    """Класс для хранения сессии пользователя"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.history: List[Dict] = []
        self.created_at = time.time()
        self.last_activity = time.time()
        
    def add_message(self, role: str, content: str):
        """Добавляет сообщение в историю"""
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })
        self.last_activity = time.time()
        
        # Ограничиваем историю последними 10 сообщениями чтобы не перегружать контекст
        if len(self.history) > 10:
            self.history = self.history[-10:]
    
    def get_conversation_history(self) -> str:
        """Возвращает историю диалога в текстовом формате"""
        if not self.history:
            return ""
        
        history_text = "ИСТОРИЯ ДИАЛОГА:\n\n"
        for msg in self.history[-6:]:  # Берем последние 6 сообщений
            role = "Пользователь" if msg["role"] == "user" else "Спасатель"
            history_text += f"{role}: {msg['content']}\n\n"
        
        return history_text
    
    def clear_history(self):
        """Очищает историю диалога"""
        self.history = []

def get_user_session(user_id: int) -> UserSession:
    """Возвращает сессию пользователя, создает новую если нет"""
    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession(user_id)
    return user_sessions[user_id]

def generate_gigachat_response_sync(user_query: str, rag_results: list, conversation_history: str = "") -> str:
    """Синхронная функция для работы с GigaChat с учетом истории"""
    if not GIGACHAT_ENABLED:
        return generate_fallback_response(user_query, rag_results)
    
    # Формируем контекст для GigaChat
    context = "БАЗА ЗНАНИЙ ПО ЧС:\n\n"
    
    if rag_results:
        context += "Используй эти проверенные инструкции как ОСНОВУ для ответа:\n\n"
        for i, result in enumerate(rag_results, 1):
            content = result["content"]
            category = result["category"]
            score = result["score"]
            
            # Ограничиваем длину
            if len(content) > 400:
                content = content[:400] + "..."
                
            context += f"ИНСТРУКЦИЯ {i} [{category}] (релевантность: {score:.3f}):\n{content}\n\n"
    else:
        context += "В базе знаний не найдено релевантных инструкций. Используй общие принципы безопасности.\n\n"
    
    # Формируем полный промпт с историей
    full_prompt = f"{SYSTEM_PROMPT}\n\n"
    
    if conversation_history:
        full_prompt += f"{conversation_history}\n\n"
    
    full_prompt += f"{context}\n\nТЕКУЩИЙ ЗАПРОС ПОЛЬЗОВАТЕЛЯ: {user_query}\n\nОТВЕТ СПАСАТЕЛЯ:"
    
    try:
        print(f"🔧 Отправка запроса в GigaChat...")
        
        # СОЗДАЕМ НОВЫЙ КЛИЕНТ ДЛЯ КАЖДОГО ЗАПРОСА
        gigachat_client = GigaChat(
            credentials=GIGACHAT_CREDENTIALS,
            scope="GIGACHAT_API_B2B",
            verify_ssl_certs=False
        )
        
        # Используем контекстный менеджер для этого клиента
        with gigachat_client:
            response = gigachat_client.chat(full_prompt)
        
        print(f"✅ GigaChat ответил успешно")
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"❌ Ошибка GigaChat: {e}")
        return generate_fallback_response(user_query, rag_results)

async def generate_response_with_gigachat(user_query: str, rag_results: list, conversation_history: str = "") -> str:
    """Асинхронная обертка для GigaChat"""
    # Запускаем в thread pool executor чтобы избежать блокировки
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, 
        generate_gigachat_response_sync, 
        user_query, 
        rag_results,
        conversation_history
    )

def generate_fallback_response(user_query: str, rag_results: list) -> str:
    """Резервный ответ если GigaChat не работает"""
    if not rag_results:
        return """🚨 НЕ НАЙДЕНО ИНСТРУКЦИЙ

В базе знаний нет подходящих инструкций для вашей ситуации.

❗ НЕМЕДЛЕННЫЕ ДЕЙСТВИЯ:
1. 📞 Вызовите службу спасения по номеру 112
2. 🗣️ Четко опишите что произошло и где вы находитесь
3. 📍 Сообщите точный адрес

📞 ЭКСТРЕННЫЕ НОМЕРА:
112 - Единая служба спасения
101 - Пожарные
102 - Полиция
103 - Скорая помощь
104 - Газовая служба

⚠️ В реальной угрозе всегда следуйте указаниям спасателей!"""
    
    response = "🚨 НАЙДЕНЫ ИНСТРУКЦИИ ДЛЯ ВАШЕЙ СИТУАЦИИ\n\n"
    response += "❗ НЕМЕДЛЕННЫЕ ДЕЙСТВИЯ:\n"
    response += "1. 📞 Вызовите службу спасения 112\n"
    response += "2. 🗣️ Сообщите оператору точную информацию\n\n"
    
    response += "📋 ПРОВЕРЕННЫЕ ИНСТРУКЦИИ:\n\n"
    
    for i, result in enumerate(rag_results, 1):
        category = result['category']
        content = result['content']
        
        response += f"🔹 {category}:\n"
        
        # Извлекаем ключевые шаги
        lines = content.split('\n')
        steps = []
        
        for line in lines:
            line_clean = line.strip()
            if (line_clean.startswith(('1.', '2.', '3.', '4.', '5.')) or
                'вызовите' in line_clean.lower() or
                'позвоните' in line_clean.lower() or
                'покиньте' in line_clean.lower()):
                steps.append(line_clean)
        
        if steps:
            for step in steps[:5]:
                response += f"   {step}\n"
        else:
            sentences = re.split(r'[.!?]+', content)
            meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
            for sentence in meaningful_sentences[:2]:
                response += f"   • {sentence}.\n"
        
        response += "\n"
    
    response += "⚠️ Это общие рекомендации. В реальной угрозе следуйте указаниям спасателей!"
    return response

@dp.message(Command("start"))
async def start_command(message: Message):
    """Обработчик команды /start"""
    await asyncio.sleep(0.3)
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    user_session = get_user_session(message.from_user.id)
    user_session.clear_history()  # Очищаем историю при старте
    
    giga_status = "✅ с GigaChat" if GIGACHAT_ENABLED else "❌ без GigaChat (только RAG)"
    
    welcome_text = f"""🚨 ДОБРО ПОЖАЛОВАТЬ В БОТА-СПАСАТЕЛЯ!

Работаю {giga_status}

📂 КАТЕГОРИИ ИНСТРУКЦИЙ:
📝 БЫТОВЫЕ - пожары, утечки газа, затопления
🚁 БПЛА/ДРОНЫ - атаки беспилотников  
🌍 ПРИРОДНЫЕ - землетрясения, наводнения, ураганы
⚡ ТЕХНОГЕННЫЕ - аварии, химические угрозы

❗ ЕСЛИ ВЫ В ОПАСНОСТИ СЕЙЧАС:
НЕМЕДЛЕННО звоните 112!

💡 Просто опишите ситуацию, и я найду релевантные инструкции.

🔄 Бот помнит контекст предыдущих сообщений (до 10 последних)."""

    user_session.add_message("assistant", welcome_text)
    await message.reply(welcome_text)

@dp.message(Command("help"))
async def help_command(message: Message):
    """Обработчик команды /help"""
    await asyncio.sleep(0.3)
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    help_text = """🆘 ПОМОЩЬ В ЧРЕЗВЫЧАЙНОЙ СИТУАЦИИ

📋 КОМАНДЫ:
/start - начать работу
/help - эта справка
/categories - категории инструкций
/rag_stats - статистика базы
/status - статус системы
/history - показать историю диалога
/clear - очистить историю диалога

📞 ЭКСТРЕННЫЕ НОМЕРА:
112 - Единая служба спасения
101 - Пожарные
102 - Полиция
103 - Скорая помощь
104 - Газовая служба

💡 ПРИМЕРЫ ЗАПРОСОВ:
• "Пожар на кухне"
• "Атака дрона"
• "Землетрясение"
• "Запах газа"

⚠️ В РЕАЛЬНОЙ ОПАСНОСТИ:
НЕМЕДЛЕННО звоните 112!"""

    user_session = get_user_session(message.from_user.id)
    user_session.add_message("assistant", help_text)
    await message.reply(help_text)

@dp.message(Command("categories"))
async def categories_command(message: Message):
    """Показать доступные категории инструкций"""
    categories_text = """📂 КАТЕГОРИИ ИНСТРУКЦИЙ В БАЗЕ ЗНАНИЙ:

📝 БЫТОВЫЕ ЧС
• Пожары в квартирах и домах
• Утечки газа и запахи
• Затопления и протечки
• Электрические проблемы

🚁 БПЛА/ДРОНЫ  
• Атаки беспилотников
• Обнаружение дронов
• Действия при угрозе с воздуха

🌍 ПРИРОДНЫЕ КАТАСТРОФЫ
• Землетрясения
• Наводнения и паводки
• Ураганы и штормы

⚡ ТЕХНОГЕННЫЕ АВАРИИ
• Промышленные аварии
• Химические угрозы
• Радиационные аварии

💡 Опишите ситуацию - я найду подходящие инструкции!"""
    
    user_session = get_user_session(message.from_user.id)
    user_session.add_message("assistant", categories_text)
    await message.reply(categories_text)

@dp.message(Command("rag_stats"))
async def rag_stats_command(message: Message):
    """Показать статистику RAG системы"""
    try:
        stats = rag_manager.get_stats()
        
        stats_text = f"""📊 СТАТИСТИКА БАЗЫ ЗНАНИЙ:

• Всего документов: {stats['total_documents']}
• Загруженные категории:"""

        for category, count in stats['categories'].items():
            stats_text += f"\n• {category}: {count} документов"

        stats_text += "\n\n✅ Система готова к работе!"
        
        user_session = get_user_session(message.from_user.id)
        user_session.add_message("assistant", stats_text)
        await message.reply(stats_text)
    except Exception as e:
        await message.reply(f"❌ Ошибка получения статистики: {e}")

@dp.message(Command("status"))
async def status_command(message: Message):
    """Показать статус системы"""
    giga_status = "✅ РАБОТАЕТ" if GIGACHAT_ENABLED else "❌ НЕ РАБОТАЕТ"
    stats = rag_manager.get_stats()
    
    status_text = f"""📊 СТАТУС СИСТЕМЫ:

GigaChat: {giga_status}
RAG: {stats['total_documents']} документов

Категории:"""
    
    for category, count in stats['categories'].items():
        status_text += f"\n• {category}: {count}"
    
    user_session = get_user_session(message.from_user.id)
    user_session.add_message("assistant", status_text)
    await message.reply(status_text)

@dp.message(Command("history"))
async def history_command(message: Message):
    """Показать историю диалога"""
    user_session = get_user_session(message.from_user.id)
    
    if not user_session.history:
        response = "📝 История диалога пуста."
    else:
        response = "📝 ИСТОРИЯ ДИАЛОГА (последние 10 сообщений):\n\n"
        for i, msg in enumerate(user_session.history[-10:], 1):
            role = "👤 Вы" if msg["role"] == "user" else "🤖 Бот"
            time_str = time.strftime("%H:%M:%S", time.localtime(msg["timestamp"]))
            response += f"{i}. {role} ({time_str}):\n{msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}\n\n"
    
    user_session.add_message("assistant", response)
    await message.reply(response)

@dp.message(Command("clear"))
async def clear_command(message: Message):
    """Очистка истории диалога"""
    user_session = get_user_session(message.from_user.id)
    user_session.clear_history()
    
    response = "✅ История диалога очищена! Начинаем новый разговор."
    user_session.add_message("assistant", response)
    await message.reply(response)

@dp.message()
async def handle_message(message: Message):
    """Основной обработчик сообщений"""
    user_id = message.from_user.id
    user_text = message.text
    
    try:
        await asyncio.sleep(0.5)
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        
        typing_task = asyncio.create_task(keep_typing(message.chat.id))
        
        # Получаем сессию пользователя
        user_session = get_user_session(user_id)
        
        # Добавляем сообщение пользователя в историю
        user_session.add_message("user", user_text)
        
        # 🔍 ПОИСК В RAG СИСТЕМЕ
        relevant_instructions = []
        try:
            relevant_instructions = rag_manager.search_emergency_instructions(user_text, max_results=3)
            print(f"🔍 RAG нашел {len(relevant_instructions)} инструкций для: '{user_text}'")
            
            # Логируем что нашли
            for i, result in enumerate(relevant_instructions):
                print(f"   {i+1}. {result['category']} (релевантность: {result['score']:.3f})")
                
        except Exception as e:
            print(f"⚠️ Ошибка поиска в RAG: {e}")
        
        # Получаем историю диалога для контекста
        conversation_history = user_session.get_conversation_history()
        
        # 🧠 ГЕНЕРИРУЕМ ОТВЕТ С GIGACHAT (с историей)
        response = await generate_response_with_gigachat(
            user_text, 
            relevant_instructions, 
            conversation_history
        )
        
        # Добавляем ответ ассистента в историю
        user_session.add_message("assistant", response)
        
        # Очищаем от Markdown
        clean_response = clean_markdown(response)
        
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass
        
        # Отправляем ответ
        await message.reply(clean_response)
        
    except Exception as e:
        await asyncio.sleep(0.3)
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        
        error_message = """⚠️ ПРОИЗОШЛА ОШИБКА

Не удалось обработать ваш запрос.

🔄 ПОПРОБУЙТЕ:
• Переформулировать вопрос
• Обратиться позже

❗ ЕСЛИ СИТУАЦИЯ ЭКСТРЕННАЯ:
НЕМЕДЛЕННО звоните 112!"""
        
        user_session = get_user_session(user_id)
        user_session.add_message("assistant", error_message)
        await message.reply(error_message)
        print(f"❌ Ошибка у пользователя {user_id}: {e}")

async def main():
    mode = "GigaChat + RAG" if GIGACHAT_ENABLED else "RAG only"
    print(f"🤖 Бот-спасатель запущен: {mode}")
    print(f"📊 RAG система: {rag_manager.get_stats()['total_documents']} документов")
    print("💾 Включена система памяти диалога")
    print("🔄 Для остановки нажмите Ctrl+C")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")