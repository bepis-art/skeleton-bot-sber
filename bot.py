import os
import getpass
import time
import asyncio
import json
import re
from typing import Dict
from dotenv import find_dotenv, load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ChatAction

from langchain.tools import tool
from langchain_gigachat.chat_models import GigaChat
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_community.tools import TavilySearchResults

# Импортируем RAG модуль
from rag_module import RAGManager


def clean_markdown(text: str) -> str:
    """
    Очищает текст от Markdown разметки
    
    Args:
        text: Исходный текст с Markdown разметкой
        
    Returns:
        str: Очищенный текст без разметки
    """
    if not text:
        return text
    
    # Убираем заголовки (# ## ###)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Убираем жирный текст (**text** или __text__)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    
    # Убираем курсив (*text* или _text_)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    
    # Убираем зачеркнутый текст (~~text~~)
    text = re.sub(r'~~(.*?)~~', r'\1', text)
    
    # Убираем код в бэктиках (`code`)
    text = re.sub(r'`(.*?)`', r'\1', text)
    
    # Убираем ссылки [text](url)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # Убираем горизонтальные линии (--- или ***)
    text = re.sub(r'^[-*_]{3,}$', '', text, flags=re.MULTILINE)
    
    # Убираем лишние пробелы и переносы строк
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()
    
    return text


# Загружаем переменные окружения
load_dotenv()

async def keep_typing(chat_id: int):
    """Поддерживает статус 'печатает...' во время работы агента"""
    try:
        while True:
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            await asyncio.sleep(4)  # Telegram автоматически скрывает статус через 5 секунд
    except asyncio.CancelledError:
        # Задача была отменена - это нормально
        pass
    except Exception as e:
        print(f"Ошибка в keep_typing: {e}")

print(f"Using token: {os.getenv('TELEGRAM_TOKEN')}")
print(f"Using token2: {os.getenv('GIGACHAT_CREDENTIALS')}")

# Конфигурация
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN не установлен!")

# Инициализация GigaChat
GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")
if not GIGACHAT_CREDENTIALS:
    raise RuntimeError("GIGACHAT_CREDENTIALS не установлен!")

#if "GIGACHAT_CREDENTIALS" not in os.environ:
   # os.environ["GIGACHAT_CREDENTIALS"] = getpass.getpass("Введите ключ авторизации GigaChat API: ")

model = GigaChat(
    model="GigaChat-2-Max",
    verify_ssl_certs=False,
    scope="GIGACHAT_API_B2B"
)

# Инициализация RAG системы
print("🔄 Инициализация RAG системы...")
rag_manager = RAGManager(
    gigachat_credentials=GIGACHAT_CREDENTIALS,
    documents_path="documents"
)

# Загружаем базу знаний из CSV файла
knowledge_base_path = "documents/legal_knowledge_base.csv"
if os.path.exists(knowledge_base_path):
    print("📚 Загружаем базу знаний с парами вопрос-ответ...")
    success = rag_manager.add_documents_from_csv(
        csv_path=knowledge_base_path,
        text_columns=["question", "answer"]
    )
    if success:
        print("✅ База знаний с парами вопрос-ответ успешно загружена")
    else:
        print("❌ Ошибка при загрузке базы знаний")
else:
    print("⚠️ Файл базы знаний не найден, RAG будет работать без предзагруженных данных")

# Инициализация Telegram-бота
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Системный промпт для юридического помощника
system_prompt = """
1. Амплуа
- Будь опытным юристом, работающим в Профсоюзе. Ты консульствуешь только сотрудников ПАО Сбербанк и компаний, входящих в экосистему Сбербанка.

2. Определение отрасли права
- Анализировать вопрос и определять отрасль права (трудовое, гражданское, административное и т. д.).  
- Не указывать отрасль в ответе, но учитывать при анализе.  

3. Сбор необходимой информации
- Определить, каких документов/данных не хватает для ответа (например, трудовой договор, приказ, локальные акты банка).  
- Если информации недостаточно, не делать категоричных выводов. Предложи варианты. 
- Не запрашивать у сотрудника внутренние документы банка (исходить из того, что Профсоюз знает их содержание). Самостоятельно проанализируй их.

4. Работа с законодательством и судебной практикой
- ОБЯЗАТЕЛЬНО использовать инструмент search_laws_and_regulations для проверки актуальности законов и получения свежей информации
- Поиск проводится через Tavily Search на специализированных юридических сайтах:  
  - [Право.ру](https://pravo.gov.ru/) - официальный портал правовой информации
  - [КонсультантПлюс](https://www.consultant.ru/) - справочно-правовая система
  - [Гарант](https://base.garant.ru/) - справочно-правовая система
- При необходимости получения детального текста закона использовать инструмент get_law_text_by_url
- Анализировать судебную практику (особенно Верховного Суда Российской Федерации за последние 5 лет), ссылаться на выводы суда
- Всегда указывать источники информации и ссылки на актуальные законы

5. Формирование проекта ответа
- После анализа сформулировать проект ответа. Выводить проект ответа не нужно.
- Проверить его на соответствие законодательству (как профессор, доктор юридических наук).  
- Учесть рекомендации и сформировать итоговый ответ.  

6. Структура итогового ответа  
- Писать вопрос в итоговом ответе не нужно.
- Полный, мотивированный и практичный ответ с вариантами действий (четко, без лишних отступлений).  
- Ссылки на законы и судебную практику.  
- Рекомендации по действиям 
- Смягчение эмоций (если сотрудник возмущен).  
- Просьба оставить обратную связь ("Пожалуйста, сообщите, помогла ли вам эта консультация"). 
- Напоминание, что твои ответы не заменяют профессиональную юридическую консультацию.  

7. Важные уточнения  
- Если вопрос связан с работой в Сбербанке, предложи сначала обратиться в подразделение по работе с персоналом (HR) или HR бизнес-партнёру подразделения в АС «Друг» - «HR бизнес-партнёр».
Укажи, что если подразделение по работе с персоналом (HR) или HR бизнес-партнёр вопрос решить не смогли, предложить обратиться центр поддержки «Люди и культура» в АС «Друг» - «Оставить жалобу в Центр поддержки «Люди и культура» или в службу корпоративного омбудсмена в АС «Друг» «Обратиться в службу корпоративного омбудсмена». 
- если и это не помогло, предложи обратиться в «Друг» - «Профсоюз.Поддержка» - «со мной поступили несправедливо» или «задать вопрос»). 
  - Если требуется обращение в суд → предложить помощь в составлении иска/претензии.  
- учти, что когда вопрос касается оценки работы сотрудника по 5+, то речь идет о системе оценки премирования в Сбербанке.  Если оценка со стороны руководителя, по мнению сотрудника, не выглядит объективной или ставилась без качественной обратной связи, сотрудник может её оспорить. Для этого он может обратиться к HR бизнес-партнёру или вышестоящему руководителю. Сотрудник может последовательно обращаться к руководителям следующих уровней, вплоть до руководства функционального блока, а после в службу корпоративного омбудсмена в АС «Друг».

8. Правила работы:
1. Отвечай на русском языке
2. Обязательно приветствуй пользователя
3. Давай практические советы, основанные на российском законодательстве
4. Если вопрос требует детального анализа документов, рекомендует обратиться к юристу лично
5. Всегда указывай на то, что это общая консультация, а не официальная юридическая помощь
6. Использование Markdown в ответе запрещено
7. Веди диалог в дружелюбном, но профессиональном тоне
8. Если нужно уточнить детали для более точного ответа, задавай уточняющие вопросы
9. Отвечай ПРЯМО на вопрос пользователя, не создавай резюме или структурированные отчеты
10. Используй инструменты для получения справочной информации и актуальных данных о законах
- search_laws_and_regulations - для поиска актуальной информации о законах
- get_law_text_by_url - для получения детального текста закона
- get_current_date - для получения текущей даты и времени (важно для понимания актуальности законов)
11. Всегда анализируй полученную информацию перед следующим поиском
12. При анализе законов обязательно учитывай текущую дату для понимания их актуальности

Важно: Твои ответы не заменяют профессиональную юридическую консультацию.
"""

# Инструменты для работы с юридическими вопросами
@tool
def get_legal_reference(category: str) -> str:
    """
    Возвращает справочную информацию по юридическим категориям.
    
    Args:
        category (str): Категория права (гражданское, трудовое, семейное, уголовное, административное)
    
    Returns:
        str: Справочная информация по категории
    """
    print(f"\033[92mBot requested get_legal_reference({category})\033[0m")
    
    references = {
        "гражданское": "Гражданское право регулирует имущественные и личные неимущественные отношения. Основной закон - Гражданский кодекс РФ.",
        "трудовое": "Трудовое право регулирует отношения между работником и работодателем. Основной закон - Трудовой кодекс РФ.",
        "семейное": "Семейное право регулирует брачно-семейные отношения. Основной закон - Семейный кодекс РФ.",
        "уголовное": "Уголовное право определяет преступления и наказания. Основной закон - Уголовный кодекс РФ.",
        "административное": "Административное право регулирует отношения в сфере государственного управления. Основной закон - КоАП РФ."
    }
    
    return references.get(category.lower(), "Категория не найдена. Доступные: гражданское, трудовое, семейное, уголовное, административное")





@tool
def search_laws_and_regulations(query: str) -> str:
    """
    Ищет актуальную информацию о законах и нормативных актах на специализированных юридических сайтах.
    Используется для проверки актуальности законодательства и получения свежей информации.
    
    Args:
        query (str): Поисковый запрос по законам, нормативным актам или юридическим вопросам
    
    Returns:
        str: Результаты поиска с ссылками на источники
    """
    print(f"\033[92mBot requested search_laws_and_regulations: {query}\033[0m")
    
    try:
        # Используем Tavily для поиска
        search_tool = TavilySearchResults(
            max_results=3,
            include_content=True,
            include_answer=True,
            search_kwargs={
                "include_domains": [
                    "pravo.gov.ru", 
                    "consultant.ru", 
                    "base.garant.ru",
                    "www.consultant.ru"
                ]
            }
        )
        
        # Выполняем поиск
        search_results = search_tool.invoke(query)
        
        # Логируем результаты в терминал
        print(f"\033[94m=== РЕЗУЛЬТАТЫ ПОИСКА TAVILY ===\033[0m")
        print(f"Запрос: {query}")
        print(f"Найдено результатов: {len(search_results)}")
        
        for i, result in enumerate(search_results, 1):
            print(f"\n{i}. {result.get('title', 'Без заголовка')}")
            print(f"   URL: {result.get('url', 'Нет ссылки')}")
            print(f"   Источник: {result.get('source', 'Неизвестно')}")
            if result.get('content'):
                content_preview = result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
                print(f"   Содержание: {content_preview}")
        print(f"\033[94m=== КОНЕЦ РЕЗУЛЬТАТОВ ===\033[0m")
        
        # Формируем ответ для пользователя
        if not search_results:
            return "По вашему запросу ничего не найдено."
        
        response = f"🔍 Результаты поиска по запросу: '{query}'\n\n"
        
        for i, result in enumerate(search_results, 1):
            title = result.get('title', 'Без заголовка')
            url = result.get('url', '')
            source = result.get('source', 'Неизвестно')
            content = result.get('content', '')
            
            response += f"{i}. **{title}**\n"
            if content:
                content_preview = content[:300] + "..." if len(content) > 300 else content
                response += f"   {content_preview}\n"
            response += f"   Источник: {source}\n"
            if url:
                response += f"   Ссылка: {url}\n"
            response += "\n"
        
        response += f"📊 Найдено результатов: {len(search_results)}"
        return response
        
    except Exception as e:
        error_msg = f"Ошибка при поиске: {str(e)}"
        print(f"\033[91mОшибка поиска: {error_msg}\033[0m")
        return f"Произошла ошибка при поиске: {error_msg}"

@tool
def get_law_text_by_url(url: str) -> str:
    """
    Получает текст закона или нормативного акта по URL для детального изучения.
    Работает только с разрешенными юридическим сайтам (consultant.ru, base.garant.ru, pravo.gov.ru).
    
    Args:
        url (str): URL страницы с текстом закона
    
    Returns:
        str: Текст закона или сообщение об ошибке
    """
    print(f"\033[92mBot requested get_law_text_by_url: {url}\033[0m")
    
    try:
        # Проверяем, что URL принадлежит разрешенным доменам
        allowed_domains = ['consultant.ru', 'www.consultant.ru', 'base.garant.ru', 'pravo.gov.ru']
        if not any(domain in url for domain in allowed_domains):
            return "❌ Этот URL не поддерживается. Используйте только consultant.ru, base.garant.ru или pravo.gov.ru"
        
        # Используем Tavily для получения содержимого страницы
        search_tool = TavilySearchResults(
            max_results=1,
            search_kwargs={"include_domains": [url.split('/')[2]]}
        )
        
        # Ищем по URL
        results = search_tool.invoke(f"site:{url}")
        
        if not results:
            return "Не удалось получить содержимое страницы."
        
        result = results[0]
        content = result.get('content', '')
        
        # Логируем результат в терминал
        print(f"\033[94m=== СОДЕРЖИМОЕ СТРАНИЦЫ ===\033[0m")
        print(f"URL: {url}")
        print(f"Заголовок: {result.get('title', 'Без заголовка')}")
        print(f"Длина содержимого: {len(content)} символов")
        if content:
            content_preview = content[:500] + "..." if len(content) > 500 else content
            print(f"Содержимое: {content_preview}")
        print(f"\033[94m=== КОНЕЦ СОДЕРЖИМОГО ===\033[0m")
        
        if not content:
            return "Содержимое страницы не найдено."
        
        # Ограничиваем длину для пользователя
        if len(content) > 1000:
            content = content[:1000] + "...\n\n[Текст обрезан для краткости. Полную версию см. по ссылке]"
        
        return f"📋 Содержимое страницы:\n\n{content}"
        
    except Exception as e:
        error_msg = f"Ошибка при получении содержимого: {str(e)}"
        print(f"\033[91mОшибка получения содержимого: {error_msg}\033[0m")
        return f"Произошла ошибка при получении содержимого: {error_msg}"

@tool
def get_current_date() -> str:
    """
    Возвращает текущую дату и время для понимания актуальности информации.
    Используется для определения, какие законы и нормативные акты действуют на текущий момент.
    
    Returns:
        str: Текущая дата и время в читаемом формате
    """
    from datetime import datetime
    current_datetime = datetime.now()
    formatted_date = current_datetime.strftime("%d.%m.%Y %H:%M:%S")
    print(f"\033[92mBot requested get_current_date: {formatted_date}\033[0m")
    return f"📅 Текущая дата и время: {formatted_date}"

# Список доступных инструментов
tools = [get_legal_reference, search_laws_and_regulations, get_law_text_by_url, get_current_date]

# Создание агента
agent = create_react_agent(
    model,
    tools=tools,
    checkpointer=MemorySaver(),
    prompt=system_prompt
)

# RAG система готова к работе
print("✅ RAG система инициализирована")

# Хранилище для истории диалогов пользователей
user_threads = {}

# Хранилище для отслеживания вызовов инструментов пользователями (только для статистики)
user_tool_calls = {}

@dp.message(Command("start"))
async def start_command(message: Message):
    """Обработчик команды /start"""
    # Небольшая задержка для естественности
    await asyncio.sleep(0.3)
    
    # Показываем, что бот печатает
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    
    welcome_text = """👨‍💼 Здравствуйте! Я ваш юридический помощник.

Я могу помочь вам с вопросами по:
• Гражданскому праву
• Трудовому праву  
• Семейному праву
• Уголовному праву
• Административному праву

Просто задайте ваш юридический вопрос, и я постараюсь помочь!

⚠️ Важно: Мои ответы носят информационный характер и не заменяют профессиональную юридическую консультацию."""
    
    await message.reply(welcome_text)

@dp.message(Command("help"))
async def help_command(message: Message):
    """Обработчик команды /help"""
    # Небольшая задержка для естественности
    await asyncio.sleep(0.3)
    
    # Показываем, что бот печатает
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    
    help_text = """📋 Доступные команды:

/start - Начать работу с ботом
/help - Показать эту справку
/clear - Очистить историю диалога

💡 Как пользоваться:
Просто напишите ваш юридический вопрос, и я отвечу на него в формате диалога, учитывая предыдущие сообщения.

🔒 Ваша история диалога сохраняется для контекста."""
    
    await message.reply(help_text)

@dp.message(Command("clear"))
async def clear_command(message: Message):
    """Обработчик команды /clear - очистка истории диалога"""
    # Небольшая задержка для естественности
    await asyncio.sleep(0.3)
    
    # Показываем, что бот печатает
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    
    user_id = message.from_user.id
    if user_id in user_threads:
        del user_threads[user_id]
    await message.reply("✅ История диалога очищена!")


# Убираем команду /reset, так как ограничения больше нет
# @dp.message(Command("reset"))
# async def reset_command(message: Message):
#     """Обработчик команды /reset - сброс счетчиков вызовов инструментов"""
#     user_id = message.from_user.id
#     if user_id in user_tool_calls:
#         user_tool_calls[user_id] = {
#             'total_calls': 0,
#             'search_calls': 0,
#             'last_search_queries': [],
#             'last_request_time': time.time()
#         }
#     await message.reply("✅ Счетчики вызовов инструментов сброшены!")

@dp.message()
async def handle_message(message: Message):
    """Основной обработчик сообщений"""
    user_id = message.from_user.id
    user_text = message.text
    
    # Создаем или получаем thread_id для пользователя
    if user_id not in user_threads:
        user_threads[user_id] = f"user_{user_id}_{int(time.time())}"
    
    thread_id = user_threads[user_id]
    config = {"configurable": {"thread_id": thread_id}}
    
    # Инициализируем счетчики для пользователя (только для статистики)
    if user_id not in user_tool_calls:
        user_tool_calls[user_id] = {
            'total_calls': 0,
            'search_calls': 0
        }
    
    try:
        # Небольшая задержка для естественности
        await asyncio.sleep(0.5)
        
        # Показываем, что бот печатает
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        
        # Создаем задачу для поддержания статуса "печатает..." во время работы агента
        typing_task = asyncio.create_task(keep_typing(message.chat.id))
        
        # Ищем релевантные пары вопрос-ответ в базе знаний для контекста
        qa_pairs = []
        try:
            qa_pairs = rag_manager.search_qa_pairs(user_text, k=2)
            if qa_pairs:
                print(f"🔍 Найдено {len(qa_pairs)} релевантных пар вопрос-ответ для контекста")
        except Exception as e:
            print(f"⚠️ Ошибка поиска в RAG: {e}")
        
        # Формируем сообщение с контекстом из пар вопрос-ответ
        user_message = user_text
        if qa_pairs:
            context_text = "\n\nРелевантные вопросы и ответы из базы знаний:\n"
            for i, qa in enumerate(qa_pairs, 1):
                context_text += f"{i}. Вопрос: {qa['question']}\n"
                context_text += f"   Ответ: {qa['answer']}\n\n"
            user_message = user_text + context_text
        
        # Отправляем сообщение агенту с контекстом
        response = agent.invoke(
            {"messages": [("user", user_message)]}, 
            config=config
        )
        
        # Останавливаем задачу поддержания статуса
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass
        
        # Анализируем ответ агента для статистики (без ограничений)
        response_str = str(response)
        
        # Подсчитываем вызовы инструментов для статистики
        search_calls = response_str.count("Bot requested search_laws_and_regulations")
        law_text_calls = response_str.count("Bot requested get_law_text_by_url")
        date_calls = response_str.count("Bot requested get_current_date")
        total_tool_calls = search_calls + law_text_calls + date_calls
        
        # Обновляем статистику
        user_tool_calls[user_id]['total_calls'] += total_tool_calls
        user_tool_calls[user_id]['search_calls'] += search_calls
        
        # Получаем ответ от агента
        assistant_message = response["messages"][-1].content
        
        # Очищаем ответ от Markdown разметки
        clean_message = clean_markdown(assistant_message)
        
        # Отправляем очищенный ответ от агента
        await message.reply(clean_message)
        
    except Exception as e:
        # Небольшая задержка для естественности
        await asyncio.sleep(0.3)
        
        # Показываем, что бот печатает (обрабатывает ошибку)
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        
        error_message = f"Произошла ошибка при обработке вашего вопроса. Попробуйте переформулировать или обратитесь позже.\n\nОшибка: {str(e)}"
        clean_error_message = clean_markdown(error_message)
        await message.reply(clean_error_message)
        print(f"Error for user {user_id}: {e}")

async def main():
    print("🤖 Юридический Telegram-бот запущен!")
    print("Для остановки нажмите Ctrl+C")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        # Для Jupyter/IPython где уже есть event loop
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main()) 
