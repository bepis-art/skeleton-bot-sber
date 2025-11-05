<template>
    <div>
        <button
            v-if="showInstallPrompt"
            @click="installApp"
            class="btn btn-danger button-orange"
        >
            📱 Установить приложение
        </button>
    </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';

const deferredPrompt = ref(null);
const showInstallPrompt = ref(false);

// Проверяем, запущено ли как установленное PWA
const isStandalone = () => {
    return (
        window.matchMedia('(display-mode: standalone)').matches ||
        window.navigator.standalone === true
    );
};

const updateInstallButtonVisibility = () => {
    // Если уже установлено — скрываем кнопку
    if (isStandalone()) {
        showInstallPrompt.value = false;
        return;
    }

    // Иначе: кнопка может появиться позже через beforeinstallprompt
    // Но пока не показываем, пока не получим событие
};

onMounted(() => {
    // Сразу проверяем режим
    updateInstallButtonVisibility();

    // Слушатель: браузер предлагает установку
    const handleBeforeInstallPrompt = (e) => {
        e.preventDefault();
        deferredPrompt.value = e;

        // Дополнительная проверка на всякий случай
        if (!isStandalone()) {
            showInstallPrompt.value = true;
        }
    };

    // Слушатель: пользователь только что установил PWA
    const handleAppInstalled = () => {
        showInstallPrompt.value = false;
        deferredPrompt.value = null;
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    // Очистка
    onBeforeUnmount(() => {
        window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
        window.removeEventListener('appinstalled', handleAppInstalled);
    });
});

const installApp = async () => {
    if (!deferredPrompt.value) {
        return;
    }

    try {
        deferredPrompt.value.prompt();
        const { outcome } = await deferredPrompt.value.userChoice;

        if (outcome === 'accepted') {
            console.log('PWA успешно установлен');
        } else {
            console.log('Установка отклонена');
        }
    } catch (err) {
        console.warn('Ошибка при установке PWA:', err);
    } finally {
        deferredPrompt.value = null;
        showInstallPrompt.value = false;
    }
};
</script>

<style scoped>
</style>