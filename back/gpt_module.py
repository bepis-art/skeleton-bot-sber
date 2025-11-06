import logging
import os
import asyncio
import re

from dotenv import load_dotenv
from consts import *

from simple_rag import SimpleRAG as RAGManager
from gigachat import GigaChat


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_markdown(text: str) -> str:
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


def generate_fallback_response(rag_results: list) -> str:
    if not rag_results:
        return NO_ANSWER

    response = "🚨 НАЙДЕНЫ ИНСТРУКЦИИ ДЛЯ ВАШЕЙ СИТУАЦИИ\n\n"
    response += "❗ НЕМЕДЛЕННЫЕ ДЕЙСТВИЯ:\n"
    response += "1. 📞 Вызовите службу спасения 112\n"
    response += "2. 🗣️ Сообщите оператору точную информацию\n\n"

    response += "📋 ПРОВЕРЕННЫЕ ИНСТРУКЦИИ:\n\n"

    for i, result in enumerate(rag_results, 1):
        category = result['category']
        content = result['content']

        response += f"🔹 {category}:\n"

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


class GPTModule:
    def __init__(self):
        load_dotenv()

        credentials = os.getenv('GIGACHAT_CREDENTIALS')
        scope = os.getenv('SCOPE')

        if not credentials:
            raise Exception('Не установлена переменная GIGACHAT_CREDENTIALS')
        if not scope:
            raise Exception('Не установлена переменная SCOPE')

        self.credentials = credentials
        self.scope = scope
        self.rag_manager = RAGManager(documents_path="documents")
        self.load_instructions()

    async def process(self, text, history):
        relevant_instructions = []
        try:
            relevant_instructions = self.rag_manager.search_emergency_instructions(text, max_results=3)
        except Exception as e:
            logger.info(f"Ошибка поиска в RAG: {e}")

        response = await self.generate_response_with_gigachat(
            text,
            relevant_instructions,
            history
        )
        return clean_markdown(response)

    def load_instructions(self):
        self.rag_manager.load_all_documents()

    def generate_gigachat_response_sync(self, user_query: str, rag_results: list, conversation_history: str = "") -> str:
        context = "БАЗА ЗНАНИЙ ПО ЧС:\n\n"

        if rag_results:
            context += "Используй эти проверенные инструкции как ОСНОВУ для ответа:\n\n"
            for i, result in enumerate(rag_results, 1):
                content = result["content"]
                category = result["category"]
                score = result["score"]

                if len(content) > 400:
                    content = content[:400] + "..."

                context += f"ИНСТРУКЦИЯ {i} [{category}] (релевантность: {score:.3f}):\n{content}\n\n"

            logger.info(f"Найдено {len(rag_results)} релевантных инструкций")
        else:
            context += "В базе знаний не найдено релевантных инструкций. Используй общие принципы безопасности.\n\n"
            logger.warning(f"Не найдены релевантные инструкции")

        full_prompt = f"{SYSTEM_PROMPT}\n\n"

        if conversation_history:
            full_prompt += f"{conversation_history}\n\n"

        full_prompt += f"{context}\n\nТЕКУЩИЙ ЗАПРОС ПОЛЬЗОВАТЕЛЯ: {user_query}\n\nОТВЕТ СПАСАТЕЛЯ:"

        try:
            gigachat_client = GigaChat(
                credentials=self.credentials,
                scope=self.scope,
                verify_ssl_certs=False
            )

            with gigachat_client:
                response = gigachat_client.chat(full_prompt)

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Ошибка выполнения запроса к Gigachat: {e}")
            return generate_fallback_response(rag_results)

    async def generate_response_with_gigachat(self, user_query: str, rag_results: list,
                                              conversation_history: str = "") -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.generate_gigachat_response_sync,
            user_query,
            rag_results,
            conversation_history
        )

