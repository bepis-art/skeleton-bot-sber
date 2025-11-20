<script setup lang="ts">
import {ref, onMounted, onUnmounted} from 'vue';
import {ChatService} from "@/services/chat-service";
import type {IMessage} from "@/interfaces/front";
import type {IObject} from "@/interfaces";

const chatService = new ChatService();

// Состояние голосового ввода
const isListening = ref(false);
const userInput = ref('');
const recognition = ref<IObject | null>(null);

const responseLoading = ref(false);

// Состояние сообщений чата
const messages = ref<IMessage[]>([
    {
        text: 'Опишите ситуацию. Я помогу.',
        sender: 'system'
    }
]);

// Инициализация IndexedDB
const DB_NAME = 'ChatDB';
const STORE_NAME = 'messages';
const DB_VERSION = 1;

let db: IDBDatabase | null = null;

// Открываем соединение с базой данных
onMounted(async () => {
    // Инициализация SpeechRecognition
    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition.value = new SpeechRecognition();
        recognition.value.continuous = false;
        recognition.value.interimResults = false;
        recognition.value.lang = 'ru-RU';

        recognition.value.onresult = (event: any) => {
            const transcript = event.results[0][0].transcript;
            userInput.value = transcript.trim();
            stopListening();
        };

        recognition.value.onerror = (event: any) => {
            console.error('Ошибка распознавания:', event.error);
            stopListening();
        };

        recognition.value.onend = () => {
            if (isListening.value) {
                recognition.value.start();
            }
        };
    } else {
        console.warn('SpeechRecognition не поддерживается в этом браузере.');
    }

    // Инициализация IndexedDB
    await initDB();
    // Загружаем сохранённые сообщения
    const savedMessages = await loadMessages();
    if (savedMessages.length > 0) {
        messages.value = savedMessages;
    }

    // Обработчики событий для сохранения данных
    window.addEventListener('beforeunload', saveMessages);
    window.addEventListener('pagehide', saveMessages);
});

onUnmounted(() => {
    // Убираем обработчики при размонтировании
    window.removeEventListener('beforeunload', saveMessages);
    window.removeEventListener('pagehide', saveMessages);
});

// Функция инициализации базы данных
async function initDB(): Promise<void> {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);

        request.onerror = () => {
            console.error('Ошибка открытия IndexedDB:', request.error);
            reject(request.error);
        };

        request.onsuccess = () => {
            db = request.result;
            console.log('IndexedDB успешно открыта');
            resolve();
        };

        request.onupgradeneeded = (event) => {
            const dbInstance = (event.target as IDBOpenDBRequest).result;
            if (!dbInstance.objectStoreNames.contains(STORE_NAME)) {
                const store = dbInstance.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true });
                store.createIndex('timestamp', 'timestamp', { unique: false });
            }
        };
    });
}

// Функция очистки всех сообщений
async function clearMessages(): Promise<void> {
    return new Promise((resolve, reject) => {
        if (!db) {
            reject('База данных не инициализирована');
            return;
        }

        const transaction = db.transaction([STORE_NAME], 'readwrite');
        const store = transaction.objectStore(STORE_NAME);
        const request = store.clear();

        request.onsuccess = () => {
            console.log('Сообщения успешно очищены');
            resolve();
        };

        request.onerror = () => {
            console.error('Ошибка очистки сообщений:', request.error);
            reject(request.error);
        };
    });
}

// Функция сохранения сообщений
async function saveMessages(): Promise<void> {
    if (!db) {
        console.error('База данных не инициализирована');
        return;
    }

    try {
        // Очищаем старые сообщения перед сохранением
        await clearMessages();

        const transaction = db.transaction([STORE_NAME], 'readwrite');
        const store = transaction.objectStore(STORE_NAME);

        // Добавляем текущие сообщения
        for (const message of messages.value) {
            store.add({ ...message, timestamp: Date.now() });
        }

        await new Promise((resolve, reject) => {
            transaction.oncomplete = resolve;
            transaction.onerror = () => reject(transaction.error);
        });

        console.log('Сообщения успешно сохранены');
    } catch (error) {
        console.error('Ошибка сохранения сообщений:', error);
    }
}

// Функция загрузки сообщений
async function loadMessages(): Promise<IMessage[]> {
    if (!db) {
        return [];
    }

    try {
        const transaction = db.transaction([STORE_NAME], 'readonly');
        const store = transaction.objectStore(STORE_NAME);
        const request = store.getAll();

        return new Promise((resolve, reject) => {
            request.onsuccess = () => {
                const result = request.result;
                console.log('Сообщения успешно загружены');
                resolve(result.map((item: IMessage) => ({ text: item.text, sender: item.sender })));
            };

            request.onerror = () => {
                console.error('Ошибка загрузки сообщений:', request.error);
                reject(request.error);
            };
        });
    } catch (error) {
        console.error('Ошибка загрузки сообщений:', error);
        return [];
    }
}

// Функции управления голосовым вводом
const startListening = () => {
    if (!recognition.value) {
        return;
    }

    try {
        recognition.value.start();
        isListening.value = true;
    } catch (err) {
        console.error('Не удалось запустить распознавание:', err);
        isListening.value = false;
    }
};

const stopListening = () => {
    if (recognition.value) {
        recognition.value.stop();
        isListening.value = false;
    }
};

/**
 * Отправка сообщения
 */
const onSendMessage = async () => {
    if (!userInput.value.trim()) {
        return;
    }

    const userMessage = userInput.value.trim();
    // Добавляем сообщение пользователя в чат
    messages.value.push({text: userMessage, sender: 'user'});
    // Сохраняем сообщения в IndexedDB
    await saveMessages();

    // Очищаем поле ввода
    userInput.value = '';

    // Отправляем сообщение через сервис
    responseLoading.value = true;
    const response: IMessage | null = await chatService.sendMessage(userMessage);
    const text = response ? response.text : 'Ошибка получения ответа.';
    const sender = response ? response.sender : 'system';
    // Добавляем ответ системы в чат
    messages.value.push({text: text, sender: sender});
    // Сохраняем сообщения в IndexedDB
    await saveMessages();
    responseLoading.value = false;
};
</script>

<template>
    <div class="d-flex flex-column vh-100 overflow-hidden">
        <div class="chat-wrapper d-flex justify-content-between flex-column flex-grow-1 w-75 mx-auto h-100">
            <div class="messages-container custom-scroll flex-grow-1 overflow-auto p-3 bg-white d-flex flex-column h-75">
                <div
                    v-for="(msg, index) in messages"
                    :key="index"
                    class="message-bubble mb-2"
                    :class="{
                        'user-message': msg.sender === 'user',
                        'system-message': msg.sender === 'system'
                    }"
                    role="alert"
                    v-html="msg.text"
                ></div>
                <div
                    v-if="responseLoading"
                    role="alert"
                    class="message-bubble system-message"
                >
                    <div class="spinner-grow spinner-grow-sm spinner-color" role="status">
                        <span class="visually-hidden"></span>
                    </div>
                </div>
            </div>

            <div class="input-panel rounded-top rounded-bottom d-flex p-3 border-top border-end border-start border-bottom bg-light position-sticky bottom-0">
                <div class="flex-grow-1 me-2 position-relative">
                    <input
                        v-model="userInput"
                        type="text"
                        class="form-control"
                        :placeholder="responseLoading ? 'Пожалуйста, подождите...' : 'Введите сообщение...'"
                        :disabled="isListening || responseLoading"
                        aria-label="Сообщение"
                        @keyup.enter="onSendMessage()"
                    />
                </div>

                <button
                    class="btn button-orange d-flex align-items-center justify-content-center"
                    @click="onSendMessage()"
                    :disabled="isListening || responseLoading"
                >
                    <i class="bi bi-send text-white"></i>
                </button>

                <button
                    :class="[
                        'btn',
                        'd-flex',
                        'align-items-center',
                        'justify-content-center',
                        'ms-1',
                        { 'btn-outline-secondary': !isListening, 'button-orange btn-danger': isListening }
                    ]"
                    style="width: 44px"
                    @click="isListening ? stopListening() : startListening()"
                    :aria-pressed="isListening"
                    :title="isListening ? 'Остановить запись' : 'Записать голос'"
                    :disabled="responseLoading"
                >
                    <i class="bi bi-mic"></i>
                </button>
            </div>
        </div>
    </div>
</template>

<style scoped>
.custom-scroll {
    &::-webkit-scrollbar {
        width: 0.375rem;
    }

    &::-webkit-scrollbar-track {
        background: transparent;
        border-radius: 1rem;
    }

    &::-webkit-scrollbar-thumb {
        background-color: transparent;
        border-radius: 0.25rem;
    }

    &:hover {
        &::-webkit-scrollbar-thumb {
            background-color: var(--color-orange-light);
        }
    }
}

.chat-wrapper {
    width: 100%;
    display: flex;
    flex-direction: column;
}

.messages-container {
    gap: 0.5rem;
    flex-grow: 1;
}

.input-panel {
    background-color: #f8f9fa;
    border-bottom-left-radius: 0.375rem;
    border-bottom-right-radius: 0.375rem;
}

.message-bubble {
    max-width: 75%;
    padding: 0.75rem 1rem;
    border-radius: 18px;
    word-wrap: break-word;
    margin-bottom: 0.5rem;
    position: relative;
    display: inline-block;
}

.user-message {
    background-color: var(--color-orange) !important;
    color: white;
    align-self: flex-end;
    text-align: left;
    border-bottom-right-radius: 4px;
}

.system-message {
    background-color: #e9ecef;
    color: #212529;
    align-self: flex-start;
    text-align: left;
    border-bottom-left-radius: 4px;
}

.user-message::after {
    content: '';
    position: absolute;
    bottom: -4px;
    right: -3px;
    width: 0;
    height: 0;
    border-left: 8px solid var(--color-orange);
    border-top: 8px solid transparent;
    border-bottom: 8px solid transparent;
    transform: rotate(-90deg);
    z-index: 1;
}

.system-message::after {
    content: '';
    position: absolute;
    bottom: -4px;
    left: -3px;
    width: 0;
    height: 0;
    border-right: 8px solid #e9ecef;
    border-top: 8px solid transparent;
    border-bottom: 8px solid transparent;
    transform: rotate(90deg);
    z-index: 1;
}

.spinner-color {
    color: var(--color-orange);
}
</style>
