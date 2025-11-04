<script setup>
import {useRouter} from 'vue-router';
import {ref, onMounted} from 'vue';

const router = useRouter();

// Состояние голосового ввода
const isListening = ref(false);
const userInput = ref('');
const recognition = ref(null);

// Инициализация SpeechRecognition при монтировании компонента
onMounted(() => {
    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition.value = new SpeechRecognition();
        recognition.value.continuous = false; // Останавливаем после первого слова/фразы
        recognition.value.interimResults = false; // Не показываем промежуточные результаты
        recognition.value.lang = 'ru-RU'; // Язык — русский

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
                // Если пользователь всё ещё хочет слушать — перезапускаем
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

// Отправка сообщения (можно будет расширить позже)
const sendMessage = () => {
    if (!userInput.value.trim()) {
        return;
    }
    // Здесь можно отправить сообщение на сервер или добавить в историю
    console.log('Отправлено:', userInput.value);
    userInput.value = '';
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
            <div class="alert alert-light border rounded-3 mb-0">
                Здравствуйте! Я ИИ-агент Спасатель. Опишите вашу ситуацию, и я подскажу, что делать. Например: пожар, затопление, утечка газа, землетрясение, ДТП.
            </div>
        </div>

        <!-- Панель ввода -->
        <div class="d-flex p-3 border-top bg-light position-relative">
            <div class="flex-grow-1 me-2 position-relative">
                <input
                    v-if="!isListening"
                    v-model="userInput"
                    type="text"
                    class="form-control"
                    placeholder="Опишите вашу ситуацию..."
                    aria-label="Сообщение"
                />
                <!-- Имитация инпута с лоадером -->
                <div
                    v-else
                    class="form-control d-flex align-items-center justify-content-center"
                    style="cursor: not-allowed; background-color: #f8f9fa; color: #6c757d;"
                >
                    <div class="spinner-border spinner-border-sm text-orange" role="status">
                        <span class="visually-hidden">Идёт запись...</span>
                    </div>
                </div>
            </div>

            <!-- Кнопочки отправки и голосового -->
            <button class="btn button-orange d-flex align-items-center justify-content-center" style="width: 44px">
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
            >
                <i class="bi bi-mic"></i>
            </button>
        </div>
    </div>
</template>

<style scoped>
</style>