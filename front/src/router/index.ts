import { createRouter, createWebHistory } from 'vue-router'

// Импортируем компоненты страниц
import Main from "@/components/Main.vue";
import Chat from "@/components/Chat.vue";

// Определяем маршруты
const routes = [
    { path: '/', component: Main },
    { path: '/about', component: Chat },
]

// Создаём роутер
const router = createRouter({
    history: createWebHistory(), // HTML5 History mode
    routes,
})

export default router