<script setup lang="ts">
import {useRouter} from 'vue-router';
import {ref, onMounted} from 'vue';
import {ChatService} from "@/services/chat-service";
import type {IMessage} from "@/interfaces/front";
import type {IObject} from "@/interfaces";

const router = useRouter();
const chatService = new ChatService(); // Создаём экземпляр сервиса

// Состояние голосового ввода
const isListening = ref(false);
const userInput = ref('');
const recognition = ref(null);

const responseLoading = ref(false);

// Состояние сообщений чата
const messages = ref([
    {
        text: 'Здравствуйте! Я ИИ-агент Спасатель. Опишите вашу ситуацию, и я подскажу, что делать. Например: пожар, затопление, утечка газа, землетрясение, ДТП.',
        sender: 'system'
    }
]);

// Инициализация SpeechRecognition при монтировании компонента
onMounted(() => {
    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition.value = new SpeechRecognition();
        recognition.value.continuous = false;
        recognition.value.interimResults = false;
        recognition.value.lang = 'ru-RU';

        recognition.value.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            userInput.value = transcript.trim();
            stopListening();
        };

        recognition.value.onerror = (event) => {
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
});

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
    // Очищаем поле ввода
    userInput.value = '';

    // Отправляем сообщение через сервис
    responseLoading.value = true;
    console.log("responseLoading: ", responseLoading);
    const responseText: IMessage | null = await chatService.sendMessage(userMessage);
    const text = responseText ? responseText.text : 'Ошибка получения ответа.';
    // Добавляем ответ системы в чат
    messages.value.push({text: text, sender: 'system'});
    responseLoading.value = false;
    console.log("responseLoading: ", responseLoading);
};
</script>

<template>
    <div class="d-flex flex-column h-100">
        <!-- Шапка -->
        <div class="d-flex align-items-center p-3 border-bottom">
            <button class="btn btn-link p-0 me-2" @click="router.back()" aria-label="Назад">
                <i class="bi bi-arrow-left fs-4 text-orange"></i>
            </button>
            <div>
                <h5 class="mb-0 nouser-select">Что делать при ЧС?</h5>
                <small class="text-muted nouser-select">ИИ-агент на связи</small>
            </div>
        </div>

        <!-- Окно сообщений -->
        <div class="flex-grow-1 overflow-auto p-3 bg-white">
            <div
                v-for="(msg, index) in messages"
                :key="index"
                class="alert mb-2"
                :class="{
                    'alert-danger text-start': msg.sender === 'user',
                    'alert-light text-start': msg.sender === 'system',
                    'alert-warning text-start': msg.sender === 'system' && msg.text === 'Ошибка получения ответа.'
                }"
                role="alert"
                v-html="msg.text"
            ></div>
        </div>

        <!-- Панель ввода -->
        <div class="d-flex p-3 border-top bg-light position-relative">
            <div class="flex-grow-1 me-2 position-relative">
                <input
                    v-model="userInput"
                    type="text"
                    class="form-control"
                    :placeholder="responseLoading ? 'Пожалуйста, подождите...' : 'Обработка сообщения...'"
                    :disabled="isListening || responseLoading"
                    aria-label="Сообщение"
                    @keyup.enter="onSendMessage()"
                />
            </div>

            <!-- Кнопочки отправки и голосового -->
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
</template>

<style scoped>
/* Дополнительные стили для сообщений, если нужно */
</style>
