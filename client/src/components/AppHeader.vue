<template>
    <nav class="navbar header position-sticky navbar-expand-lg">
        <div v-if="mode === 'main'" class="container-fluid d-flex justify-content-center align-items-center">
            <div class="d-flex gap-1 flex-column justify-content-center align-items-center nouser-select">
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 50 50"
                    class="info-icon"
                >
                    <!-- Оранжевый фон (весь круг) -->
                    <circle cx="25" cy="25" r="20" class="icon-background"/>

                    <!-- Белое кольцо (ободок) — не закрашенное -->
                    <circle
                        cx="25"
                        cy="25"
                        r="10"
                        stroke="var(--bs-white, #ffffff)"
                        stroke-width="2"
                        fill="none"
                    />

                    <!--Белый восклицательный знак внутри кольца -->
                    <g class="icon-symbol">
                        <!-- Точка сверху -->
                        <circle cx="25" cy="20" r="1.5"/>
                        <!-- Вертикальная палочка -->
                        <rect x="24" y="23" width="2" height="8"/>
                    </g>
                </svg>
                <b class="text-orange">ИИ-агент Спасатель</b>
                <span class="text-secondary">
                    Помощь в экстренных ситуациях 24/7
                </span>
                <PwaButton/>
            </div>
        </div>
        <div v-if="mode === 'chat'" class="d-flex align-items-center p-3">
            <button class="btn btn-link p-0 me-2" @click="goBackToMain" aria-label="Назад">
                <i class="bi bi-arrow-left fs-4 text-orange"></i>
            </button>
            <div>
                <h5 class="mb-0 nouser-select">Что делать при ЧС?</h5>
                <small class="text-muted nouser-select">ИИ-агент на связи</small>
            </div>
        </div>
    </nav>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import PwaButton from "@/components/PwaButton.vue";

defineProps<{
    mode: 'main' | 'chat'
}>();

const router = useRouter();

// Метод для возврата в главное меню
const goBackToMain = () => {
    router.push('/');
};
</script>

<style scoped>
.header {
    z-index: 1000;
}
.navbar {
    border-bottom: 1px solid var(--bs-gray-200);
}

.info-icon {
    width: 40px;
    height: 40px;
    max-width: 100%;
}

.icon-background {
    fill: var(--color-orange);
}

.icon-symbol {
    fill: var(--bs-white, #ffffff);
}
</style>
