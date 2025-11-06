import {createRouter, createWebHistory} from 'vue-router';

// Импортируем компоненты страниц
import AppMain from "@/components/AppMain.vue";
import AppChat from "@/components/AppChat.vue";

const routes = [
  { path: '/', component: AppMain },
  { path: '/main', component: AppMain },
  { path: '/chat', component: AppChat },
  { path: '/:pathMatch(.*)*', redirect: '/main' }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

export default router;
