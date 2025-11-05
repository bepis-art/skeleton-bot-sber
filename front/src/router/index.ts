import { createRouter, createWebHistory } from 'vue-router';

// Импортируем компоненты страниц
import Main from "@/components/Main.vue";
import Chat from "@/components/Chat.vue";

const routes = [
    { path: '/', component: Main },
    { path: '/main', component: Main },
    { path: '/chat', component: Chat },
    { path: '/:pathMatch(.*)*', redirect: '/main' }
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

export default router;