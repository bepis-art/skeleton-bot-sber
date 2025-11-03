<template>
    <div>
        <button
            v-if="showInstallPrompt"
            @click="installApp"
            class="install-btn"
        >
            📱 Установить приложение
        </button>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const deferredPrompt = ref(null)
const showInstallPrompt = ref(false)

// Функция для проверки, установлено ли приложение
const isPWAInstalled = () => {
    // Современные браузеры (Chrome, Edge и др.)
    if (window.matchMedia('(display-mode: standalone)').matches) {
        return true
    }
    // iOS Safari
    if (window.navigator.standalone === true) {
        return true
    }
    return false
}

onMounted(() => {
    // Если приложение уже установлено — не показываем кнопку
    if (isPWAInstalled()) {
        showInstallPrompt.value = false
        return
    }

    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault()
        deferredPrompt.value = e
        showInstallPrompt.value = true
    })
})

const installApp = async () => {
    if (!deferredPrompt.value) return

    deferredPrompt.value.prompt()
    const { outcome } = await deferredPrompt.value.userChoice

    if (outcome === 'accepted') {
        console.log('Пользователь установил PWA')
    } else {
        console.log('Пользователь отклонил установку')
    }

    deferredPrompt.value = null
    showInstallPrompt.value = false
}
</script>

<style scoped>
.install-btn {
    padding: 10px 16px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
}
</style>