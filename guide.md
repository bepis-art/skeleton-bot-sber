# 🤖 Руководство по созданию своего AI Telegram-бота

## 📋 Содержание
1. [Обзор проекта](#обзор-проекта)
2. [Архитектура бота](#архитектура-бота)
3. [Предварительные требования](#предварительные-требования)
4. [Установка и настройка](#установка-и-настройка)
5. [Структура кода](#структура-кода)
6. [Кастомизация под своего агента](#кастомизация-под-своего-агента)
7. [Запуск и тестирование](#запуск-и-тестирование)
8. [Расширенные возможности](#расширенные-возможности)

---

## 🎯 Обзор проекта

Этот Telegram-бот представляет собой **юридического помощника** на базе AI, который использует:
- **GigaChat** (российская LLM модель) для генерации ответов
- **LangGraph** для создания агента с инструментами
- **RAG (Retrieval-Augmented Generation)** для работы с базой знаний
- **Tavily Search** для поиска актуальной информации в интернете
- **Aiogram 3.x** для работы с Telegram API


---


## 📦 Предварительные требования

### 1. Необходимое ПО:
- **Python 3.10+**
- **pip** (менеджер пакетов Python)
- **Git** (для клонирования репозитория)

### 2. API Ключи:

#### Telegram Bot Token
1. Откройте Telegram и найдите бота [@BotFather](https://t.me/BotFather)
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Сохраните полученный **API Token**

#### GigaChat API Key
1. Получите ключ API в [https://developers.sber.ru/](https://developers.sber.ru/)
2. Либо запросите у Сергея или Виталия

#### Tavily API Key (опционально, но рекомендуется)
1. Зарегистрируйтесь на [https://tavily.com/](https://tavily.com/)
2. Получите бесплатный API ключ
3. Этот ключ нужен для поиска актуальной информации в интернете

> ⚠️ **Важно**: Без Tavily API инструменты `search_laws_and_regulations` и `get_law_text_by_url` не будут работать. Вы можете удалить эти инструменты или заменить их своими.

---

## ⚙️ Установка и настройка

### Шаг 1: Установка зависимостей

```bash
# Установите все необходимые пакеты
pip install -r requirements.txt
```

### Шаг 2: Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```bash
# .env
TELEGRAM_TOKEN=your_telegram_bot_token_here
GIGACHAT_CREDENTIALS=your_gigachat_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

> 📝 **Примечание**: Замените значения на ваши реальные ключи

### Шаг 3: Подготовка базы знаний (опционально)

Если вы хотите использовать RAG с базой знаний:

1. Создайте CSV файл `documents/legal_knowledge_base.csv` со структурой:

```csv
question,answer
"Вопрос 1","Ответ на вопрос 1"
"Вопрос 2","Ответ на вопрос 2"
```

2. Бот автоматически загрузит эти данные при запуске

> 💡 **Совет**: Если файл не создан, бот будет работать без предзагруженной базы знаний

---

## 📂 Структура кода

### Основной файл: `bot.py`

#### 1. **Импорты и зависимости** (строки 1-22)
```python
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from langchain_gigachat.chat_models import GigaChat
from langgraph.prebuilt import create_react_agent
from rag_module import RAGManager
```

#### 2. **Утилиты** (строки 24-64)
- `clean_markdown()` - очищает текст от Markdown разметки
- `keep_typing()` - поддерживает статус "печатает..."

#### 3. **Конфигурация** (строки 86-102)
- Загрузка переменных окружения
- Инициализация GigaChat модели

#### 4. **RAG система** (строки 104-124)
- Инициализация RAG менеджера
- Загрузка базы знаний из CSV

#### 5. **Системный промпт** (строки 130-193)
- Определяет поведение и роль бота
- **ЭТО ГЛАВНОЕ МЕСТО ДЛЯ КАСТОМИЗАЦИИ!**

#### 6. **Инструменты (Tools)** (строки 196-374)
- `get_legal_reference()` - справочная информация
- `search_laws_and_regulations()` - поиск законов через Tavily
- `get_law_text_by_url()` - получение текста закона
- `get_current_date()` - текущая дата

#### 7. **Агент** (строки 376-382)
```python
agent = create_react_agent(
    model,
    tools=tools,
    checkpointer=MemorySaver(),
    prompt=system_prompt
)
```

#### 8. **Обработчики команд** (строки 393-466)
- `/start` - приветствие
- `/help` - справка
- `/clear` - очистка истории

#### 9. **Основной обработчик сообщений** (строки 468-561)
- Обработка пользовательских сообщений
- Интеграция с RAG
- Вызов агента

---

## 🎨 Кастомизация под своего агента

### 1️⃣ **Изменение роли и поведения бота**

**Где:** строки 130-193 (`system_prompt`)

**Что менять:**
```python
system_prompt = """
1. Амплуа
- Будь [ВАША РОЛЬ ЗДЕСЬ]. Ты консультируешь [ВАШУ АУДИТОРИЮ].

2. Определение [ВАШЕЙ СПЕЦИАЛИЗАЦИИ]
- Анализировать вопрос и определять [ЧТО НУЖНО ОПРЕДЕЛЯТЬ].

...

8. Правила работы:
1. Отвечай на [ЯЗЫК] языке
2. Обязательно [ВАШИ ТРЕБОВАНИЯ]
...
"""
```


### 2️⃣ **Замена или добавление инструментов**

**Где:** строки 196-374 (определение `@tool`)

**Как создать свой инструмент:**
```python
@tool
def my_custom_tool(parameter: str) -> str:
    """
    Описание того, что делает инструмент (видно агенту).
    
    Args:
        parameter: Описание параметра
    
    Returns:
        str: Описание возвращаемого значения
    """
    # Ваш код здесь
    result = f"Обработано: {parameter}"
    return result
```

**Не забудьте добавить в список:**
```python
tools = [my_custom_tool, get_current_date]  # Ваши инструменты
```

### 3️⃣ **Изменение приветственного сообщения**

**Где:** строки 402-414 (`start_command`)

```python
welcome_text = """👋 Привет! Я [НАЗВАНИЕ ВАШЕГО БОТА].

Я могу помочь с:
• [ФУНКЦИЯ 1]
• [ФУНКЦИЯ 2]
• [ФУНКЦИЯ 3]

Задай мне вопрос!
"""
```

### 4️⃣ **Настройка RAG системы**

**Где:** строки 104-124

**Отключить RAG:**
```python
# Закомментируйте строки 106-124
# rag_manager = RAGManager(...)
```

**Изменить источник данных:**
```python
# Вместо CSV используйте текстовые документы
texts = ["Документ 1", "Документ 2"]
metadata = [{"source": "doc1"}, {"source": "doc2"}]
rag_manager.add_documents_from_text(texts, metadata)
```

### 5️⃣ **Изменение модели GigaChat**

**Где:** строки 98-102

```python
model = GigaChat(
    model="GigaChat-2-Max",  # или "GigaChat-Pro"
    verify_ssl_certs=False, # в ПРОМе обязательно =True и требуется установить сертификат МинЦифры
    scope="GIGACHAT_API_B2B" # если используете токен от организации
)
```


### 6️⃣ **Удаление поиска в интернете**

Если у вас нет Tavily API ключа:

1. Удалите импорт (строка 18):
```python
# from langchain_community.tools import TavilySearchResults
```

2. Удалите инструменты `search_laws_and_regulations` и `get_law_text_by_url` (строки 223-356)

3. Обновите список инструментов (строка 374):
```python
tools = [get_legal_reference, get_current_date]
```

4. Обновите системный промпт (уберите упоминания о поиске законов)

### 7️⃣ **Изменение справочной информации**

**Где:** строки 196-217 (`get_legal_reference`)

```python
references = {
    "категория1": "Информация о категории 1",
    "категория2": "Информация о категории 2",
    # Добавьте свои категории
}
```

---

## 🚀 Запуск и тестирование

### Запуск бота:

```bash
python bot.py
```

### Ожидаемый вывод:

```
Using token: 123456789:ABCDEF...
Using token2: your_gigachat_credentials
🔄 Инициализация RAG системы...
📚 Загружаем базу знаний с парами вопрос-ответ...
✅ База знаний с парами вопрос-ответ успешно загружена
✅ RAG система инициализирована
🤖 Юридический Telegram-бот запущен!
Для остановки нажмите Ctrl+C
```

### Тестирование:

1. Откройте Telegram и найдите вашего бота
2. Отправьте команду `/start`
3. Задайте вопрос: "Помоги с трудовым правом"
4. Проверьте, что бот отвечает

---

## 🔧 Расширенные возможности

### 1. Добавление кнопок (Inline Keyboard)

```python
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Кнопка 1", callback_data="btn1")],
    [InlineKeyboardButton(text="Кнопка 2", callback_data="btn2")]
])

await message.reply("Выберите действие:", reply_markup=keyboard)
```

### 2. Логирование действий пользователей

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dp.message()
async def handle_message(message: Message):
    logger.info(f"User {message.from_user.id}: {message.text}")
    # Ваш код
```

### 3. Ограничение доступа по ID пользователя

```python
ALLOWED_USERS = [123456789, 987654321]  # ID разрешенных пользователей

@dp.message()
async def handle_message(message: Message):
    if message.from_user.id not in ALLOWED_USERS:
        await message.reply("У вас нет доступа к боту")
        return
    # Ваш код
```

### 4. Сохранение истории в файл

```python
import json
from datetime import datetime

def save_conversation(user_id: int, message: str, response: str):
    data = {
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "message": message,
        "response": response
    }
    with open(f"history_{user_id}.json", "a", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
        f.write("\n")
```


## 📚 Дополнительные ресурсы

- **Aiogram документация:** [https://docs.aiogram.dev/](https://docs.aiogram.dev/)
- **LangChain документация:** [https://python.langchain.com/](https://python.langchain.com/)
- **LangGraph документация:** [https://langchain-ai.github.io/langgraph/](https://langchain-ai.github.io/langgraph/)
- **GigaChat API:** [https://developers.sber.ru/docs/ru/gigachat/api/overview](https://developers.sber.ru/docs/ru/gigachat/api/overview)


