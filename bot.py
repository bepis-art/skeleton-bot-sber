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
#knowledge_base_path = "documents/legal_knowledge_base.csv"
# if os.path.exists(knowledge_base_path):
#     print("📚 Загружаем базу знаний с парами вопрос-ответ...")
#     success = rag_manager.add_documents_from_csv(
        # csv_path=knowledge_base_path,
        # text_columns=["question", "answer"]
    # )
#     if success:
#         print("✅ База знаний с парами вопрос-ответ успешно загружена")
#     else:
#         print("❌ Ошибка при загрузке базы знаний")
# else:
#     print("⚠️ Файл базы знаний не найден, RAG будет работать без предзагруженных данных")

# Инициализация Telegram-бота
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Системный промпт для юридического помощника
system_prompt = """
1. Амплуа
- Ты — опытный спасатель и инструктор по действиям в чрезвычайных ситуациях. Ты помогаешь гражданам быстро сориентироваться и принять правильные решения при угрозе жизни, здоровью или имуществу.
- Твоя задача — не заменить экстренные службы, а сохранить жизнь до их прибытия.

2. Определение отрасли права
- Анализируй описание пользователя и определяй тип чрезвычайной ситуации:
  * Природные (землетрясение, наводнение, ураган, лесной пожар и др.)
  * Техногенные (пожар, утечка газа, ДТП, авария на производстве)
  * Биолого-социальные (отравление, травма, потеря сознания, паника)
  * Военные/террористические угрозы (при наличии признаков)
- Не называй тип ЧС в ответе явно, но используй его для выбора алгоритма действий.

3. Сбор необходимой информации
- Если описание ситуации неполное (например, «что-то случилось»), задай уточняющие вопросы:
  * «Где вы находитесь?»
  * «Есть ли пострадавшие?»
  * «Что именно произошло?»  
- Не требуй от пользователя сложных технических деталей. Ориентируйся на то, что человек может сообщить в стрессе.

4. Работа с источниками информации
- ОБЯЗАТЕЛЬНО используй инструмент search_emergency_info для получения актуальных рекомендаций от официальных источников:
  * mchs.gov.ru
  * redcross.ru
  * meteoinfo.ru
  * gismeteo.ru
- При необходимости получения полного текста инструкции используй get_emergency_info_by_url
- Учитывай текущую дату через get_current_datetime_for_emergency — например, при паводках или пожароопасном сезоне

5. Формирование проекта ответа
- Сначала мысленно составь пошаговый алгоритм действий.
- Проверь его на соответствие официальным рекомендациям МЧС и ВОЗ.
- Убедись, что инструкция безопасна, проста и выполнима без специального оборудования.

6. Структура итогового ответа  
- Начни с приветствия и выражения поддержки: «Понимаю, это страшно. Давайте действовать по шагам».
- Дай чёткие, короткие инструкции (не более 5 шагов за раз).
- Укажи, когда и как вызывать экстренные службы (112 в РФ, или уточни по региону).
- При необходимости — предложи сформировать сообщение для отправки спасателям.
- Заверши фразой: «Пожалуйста, сообщите, получилось ли у вас выполнить эти действия?»
- Обязательно добавь: «Этот бот не заменяет помощь профессиональных спасателей. При угрозе жизни немедленно звоните в экстренные службы».

7. Важные уточнения  
- Если пользователь сообщает о реальной угрозе жизни (например, «не могу дышать», «горит дом», «потерял сознание ребёнок»):
  * Немедленно активируй режим SOS:
- Первым сообщением — краткая инструкция («Откройте окно», «Ложитесь на пол», «Не трогайте провода»).
- Вторым — призыв: «СРОЧНО звоните 112!».
- Если ситуация не критична, но требует подготовки («хочу знать, что делать при землетрясении»), дай профилактическую памятку.м

8. Правила работы:
1. Отвечай на русском языке.
2. Всегда приветствуй пользователя.
3. Давай только проверенные, официальные рекомендации (МЧС, ВОЗ, МВД).
4. Не давай советов, требующих медицинской или технической квалификации (например, «наложите жгут» — только если это в официальной инструкции для граждан).
5. Подчёркивай, что это общая консультация, а не замена спасательной операции.
6. Не используй Markdown.
7. Сохраняй спокойный, уверенный и поддерживающий тон.
8. При неясной ситуации — задавай один уточняющий вопрос.
9. Отвечай прямо, без вводных фраз вроде «Как ИИ, я не могу…».
10. Используй инструменты:
  — search_emergency_info — для поиска инструкций
  — get_emergency_info_by_url — для получения полного текста
  — get_current_datetime_for_emergency — для учёта сезонности и актуальности
11. Анализируй найденную информацию перед ответом.
12. Учитывай текущую дату: например, в октябре в РФ — начало отопительного сезона → риск угарного газа.

Важно: Твои ответы не заменяют помощь профессиональных спасателей, медиков или экстренных служб. При любой угрозе жизни — звоните 112.
"""


# Инструменты для работы с чрезвычайными ситуациями
@tool
def get_emergency_guidance(emergency_type: str) -> str:
    """
    Возвращает краткое руководство по действиям при конкретном типе чрезвычайной ситуации.

    Args:
        emergency_type (str): Тип ЧС (пожар, землетрясение, наводнение, химическая угроза, теракт, потеря ориентации, обморожение, тепловой удар, атака БПЛА и др.)

    Returns:
        str: Краткое руководство по действиям в ЧС
    """
    print(f"\033[92mBot requested get_emergency_guidance({emergency_type})\033[0m")

    guidance = {
        "пожар": (
            "1. Немедленно покиньте помещение. Не пользуйтесь лифтом!\n"
            "2. Пригнитесь к полу — дым поднимается вверх.\n"
            "3. Закройте рот и нос влажной тканью.\n"
            "4. Если не можете выйти — запритесь в комнате, заклейте щели под дверью, звоните 101 или 112."
        ),
        "землетрясение": (
            "1. Укройтесь под прочным столом или в дверном проёме.\n"
            "2. Держитесь подальше от окон, зеркал, тяжёлой мебели.\n"
            "3. Не пользуйтесь лифтом после толчков.\n"
            "4. После окончания — проверьте газ, воду, электричество; покиньте здание, если есть повреждения."
        ),
        "наводнение": (
            "1. Немедленно поднимайтесь на верхние этажи или возвышенность.\n"
            "2. Не пытайтесь перейти поток воды — даже 15 см могут сбить с ног.\n"
            "3. Отключите электричество, если есть риск короткого замыкания.\n"
            "4. Звоните 112 и ожидайте спасателей."
        ),
        "химическая угроза": (
            "1. Немедленно покиньте зону или закройте все окна и вентиляцию.\n"
            "2. Наденьте маску, марлевую повязку или влажную ткань на лицо.\n"
            "3. Снимите одежду, которая могла контактировать с веществом.\n"
            "4. Примите душ и вызовите скорую (112). Не ешьте/пейте до проверки."
        ),
        "теракт": (
            "1. Немедленно покиньте опасную зону. Не останавливайтесь снимать видео!\n"
            "2. Следуйте указаниям полиции и спасателей.\n"
            "3. Не трогайте подозрительные предметы.\n"
            "4. Сообщите в службу 112 только проверенную информацию."
        ),
        "потеря ориентации": (
            "1. Остановитесь. Не двигайтесь наугад.\n"
            "2. Оцените окружение: есть ли дороги, реки, следы цивилизации?\n"
            "3. Используйте компас или солнце для определения сторон света.\n"
            "4. Подавайте сигналы (свисток, зеркало, костёр днём — дым, ночью — огонь)."
        ),
        "обморожение": (
            "1. Переместитесь в тёплое место.\n"
            "2. Не растирайте поражённые участки снегом или руками!\n"
            "3. Согревайте пострадавшего постепенно — тёплой (не горячей!) водой или телом.\n"
            "4. Немедленно обратитесь за медпомощью (112)."
        ),
        "тепловой удар": (
            "1. Переместите человека в тень или прохладное место.\n"
            "2. Снимите лишнюю одежду, приложите холод к шее, подмышкам, паху.\n"
            "3. Давайте пить воду маленькими глотками (если в сознании).\n"
            "4. Вызовите скорую — 112."
        ),
        "атака бпла": (
            "1. Немедленно укройтесь в укрытии (здание, овраг, бетонное сооружение). Избегайте открытых пространств.\n"
            "2. Не пользуйтесь мобильной связью и GPS — это может выдать ваше местоположение.\n"
            "3. Не снимайте БПЛА на камеру — излучение может быть зафиксировано.\n"
            "4. Сообщите координаты угрозы в экстренные службы (112) только после выхода из зоны риска."
        )
    }

    emergency_key = emergency_type.lower().strip()
    return guidance.get(
        emergency_key,
        "Тип ЧС не распознан. Доступные: пожар, землетрясение, наводнение, химическая угроза, теракт, потеря ориентации, обморожение, тепловой удар, атака БПЛА.\n"
        "Если вы в опасности — немедленно звоните 112!"
    )


@tool
def search_emergency_info(query: str) -> str:
    """
    Ищет актуальную информацию о чрезвычайных ситуациях, официальные предупреждения,
    инструкции по выживанию и данные от надёжных спасательных организаций.
    Используется для получения свежих данных в реальном времени (погода, угрозы, эвакуация и т.д.).

    Args:
        query (str): Поисковый запрос по ЧС, угрозам, инструкциям, прогнозам или действиям в кризисе

    Returns:
        str: Результаты поиска с акцентом на официальные и проверенные источники
    """
    print(f"\033[92mBot requested search_emergency_info: {query}\033[0m")

    try:
        # Используем Tavily для поиска, но фокусируемся на авторитетных источниках ЧС
        search_tool = TavilySearchResults(
            max_results=3,
            include_content=True,
            include_answer=True,
            search_kwargs={
                "include_domains": [
                    "mchs.gov.ru",
                    "redcross.ru"
                    "meteoinfo.ru",
                    "gismeteo.ru"
                ]
            }
        )

        # Выполняем поиск
        search_results = search_tool.invoke(query)

        # Логируем результаты в терминал
        print(f"\033[94m=== РЕЗУЛЬТАТЫ ПОИСКА ПО ЧС ===\033[0m")
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
            return (
                "По вашему запросу не найдено актуальной информации.\n"
                "⚠️ Если вы находитесь в опасности — немедленно звоните 112!"
            )

        response = f"🚨 Актуальная информация по запросу: '{query}'\n\n"

        for i, result in enumerate(search_results, 1):
            title = result.get('title', 'Без заголовка')
            url = result.get('url', '')
            source = result.get('source', 'Неизвестно')
            content = result.get('content', '')

            response += f"{i}. **{title}**\n"
            if content:
                # Очищаем текст от лишних переносов и обрезаем до сути
                clean_content = ' '.join(content.split())[:300]
                response += f"   {clean_content}...\n"
            response += f"   Источник: {source}\n"
            if url:
                response += f"   Подробнее: {url}\n"
            response += "\n"

        response += (
            f"📊 Найдено официальных источников: {len(search_results)}\n"
            "❗ Помните: в реальной угрозе — действуйте по базовым правилам выживания и звоните 112."
        )
        return response

    except Exception as e:
        error_msg = f"Ошибка при поиске информации о ЧС: {str(e)}"
        print(f"\033[91mОшибка поиска: {error_msg}\033[0m")
        return (
            "Не удалось получить актуальную информацию.\n"
            "⚠️ В случае реальной угрозы: следуйте базовым правилам безопасности и немедленно звоните 112."
        )


@tool
def get_emergency_info_by_url(url: str) -> str:
    """
    Получает информацию о чрезвычайной ситуации, инструкции или официальные предупреждения по URL.
    Работает ТОЛЬКО с доверенными источниками по безопасности и ЧС.

    Args:
        url (str): URL страницы с информацией (должен принадлежать разрешённому домену)

    Returns:
        str: Краткое извлечение ключевой информации или сообщение об ошибке
    """
    print(f"\033[92mBot requested get_emergency_info_by_url: {url}\033[0m")

    # Доверенные домены для ЧС и безопасности
    trusted_domains = ["mchs.gov.ru", "redcross.ru", "meteoinfo.ru", "gismeteo.ru"]

    # Проверяем, что домен доверенный
    if not any(trusted in url for trusted in trusted_domains):
        return (
            "❌ Этот URL не поддерживается.\n"
            "Разрешены только официальные источники: МЧС, ВОЗ, Красный Крест, Гидрометцентр и др.\n"
            "Если вы в опасности — звоните 112!"
        )

    try:
        # Используем Tavily для извлечения содержимого
        search_tool = TavilySearchResults(
            max_results=1,
            include_content=True,
            search_kwargs={"include_domains": [url]}
        )

        # Запрос: "содержимое этой страницы"
        results = search_tool.invoke(f"site:{url}")

        if not results:
            return "Не удалось загрузить информацию с указанной страницы."

        result = results[0]
        content = result.get('content', '').strip()
        title = result.get('title', 'Без названия')

        # Логирование
        print(f"\033[94m=== СОДЕРЖИМОЕ СТРАНИЦЫ (ЧС) ===\033[0m")
        print(f"URL: {url}")
        print(f"Заголовок: {title}")
        print(f"Длина: {len(content)} символов")
        if content:
            preview = content[:500] + "..." if len(content) > 500 else content
            print(f"Превью: {preview}")
        print(f"\033[94m=== КОНЕЦ ===\033[0m")

        if not content:
            return "Содержимое не найдено. Возможно, страница временно недоступна."

        # Ограничиваем длину для пользователя
        if len(content) > 1200:
            content = content[:1200] + "...\n\n[Информация сокращена. Полный текст — по ссылке выше.]"

        return (
            f"🚨 Официальная информация из источника:\n"
            f"**{title}**\n\n"
            f"{content}\n\n"
            f"🔗 Источник: {url}\n\n"
            f"❗ Если ситуация угрожает жизни — действуйте немедленно и звоните 112."
        )

    except Exception as e:
        error_msg = f"Ошибка при загрузке: {str(e)}"
        print(f"\033[91mОшибка получения ЧС-информации: {error_msg}\033[0m")
        return (
            "Не удалось получить информацию.\n"
            "⚠️ В условиях реальной угрозы полагайтесь на базовые правила выживания и звоните 112."
        )


@tool
def get_current_datetime_for_emergency() -> str:
    """
    Возвращает текущую дату, время и временную зону для оценки актуальности ЧС-информации и планирования действий.
    Используется при анализе предупреждений, прогнозов и инструкций по выживанию.

    Returns:
        str: Текущая дата, время и временная зона в читаемом формате
    """
    from datetime import datetime
    import time

    # Получаем текущее время с временной зоной (если доступна)
    try:
        # Попытка получить локальную временную зону
        tz_name = time.tzname[time.daylight]
        tz_offset = time.timezone if not time.daylight else time.altzone
        tz_offset_hours = abs(tz_offset) // 3600
        tz_sign = "+" if tz_offset <= 0 else "-"
        tz_str = f"UTC{tz_sign}{tz_offset_hours:02d}:00 ({tz_name})"
    except Exception:
        tz_str = "UTC±00:00 (временная зона не определена)"

    current_datetime = datetime.now()
    formatted_date = current_datetime.strftime("%d.%m.%Y %H:%M:%S")

    print(f"\033[92mBot requested get_current_datetime_for_emergency: {formatted_date} {tz_str}\033[0m")

    # Дополнительно: определяем время суток для тактических рекомендаций
    hour = current_datetime.hour
    if 6 <= hour < 12:
        time_of_day = "Утро"
    elif 12 <= hour < 18:
        time_of_day = "День"
    elif 18 <= hour < 22:
        time_of_day = "Вечер"
    else:
        time_of_day = "Ночь"

    return (
        f"📅 Текущая дата и время: {formatted_date}\n"
        f"🕒 Временная зона: {tz_str}\n"
        f"🌙 Время суток: {time_of_day}\n\n"
        f"ℹ️ Эта информация помогает оценить актуальность предупреждений и выбрать тактику действий."
    )

# Список доступных инструментов
tools = [get_emergency_guidance, search_emergency_info, get_emergency_info_by_url, get_current_datetime_for_emergency]

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
    """Обработчик команды /start для ИИ-агента-спасателя"""
    # Небольшая задержка для естественности
    await asyncio.sleep(0.3)

    # Показываем, что бот "печатает" — создаёт ощущение живого помощника
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    welcome_text = """🚨 Привет! Я — ваш ИИ-помощник в чрезвычайных ситуациях.

Я помогу вам:
• Действовать при пожаре, землетрясении, наводнении
• Оказать первую помощь при обморожении, тепловом ударе
• Вести себя при химической угрозе или атаке БПЛА
• Найти выход, если вы потерялись
• Получить актуальную информацию от МЧС и других служб

❗ Если вы **сейчас в опасности** —  
немедленно звоните **112** (в России и СНГ) или местной службе спасения.

Опишите ситуацию — и я дам пошаговые инструкции для вашей безопасности.

🫡 Помните: сохраняйте спокойствие. Паника — главный враг в ЧС."""

    await message.reply(welcome_text)


@dp.message(Command("help"))
async def help_command(message: Message):
    """Обработчик команды /help для бота-спасателя"""
    # Небольшая задержка для естественности
    await asyncio.sleep(0.3)

    # Показываем, что бот печатает
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    help_text = """🆘 Помощь в чрезвычайной ситуации

Доступные команды:
/start — Начать работу с ботом
/help — Показать эту справку
/clear — Очистить историю диалога

💡 Как пользоваться:
Опишите ситуацию — например:  
• «Пожар на кухне»  
• «Чувствую запах газа»  
• «Началось землетрясение»  
• «Пострадал в ДТП»  

Я немедленно дам пошаговые инструкции по действиям, чтобы вы остались в безопасности.

⚠️ В случае реальной угрозы жизни — звоните в экстренные службы:  
🇷🇺 Россия: 112 (единый номер спасения)  
(Номера других стран можно уточнить по запросу.)

🔒 История диалога хранится только для контекста и удаляется после /clear."""

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
    print("🤖 Бот-спасатель запущен!")
    print("Для остановки нажмите Ctrl+C")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        # Для Jupyter/IPython где уже есть event loop
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main()) 
