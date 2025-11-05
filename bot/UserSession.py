import time
from typing import Dict, List

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