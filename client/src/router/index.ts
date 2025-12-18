import {createRouter, createWebHistory} from 'vue-router';
import AdminPage from "@/components/pages/AdminPage.vue";
import MainPage from "@/components/pages/MainPage.vue";
import ChatPage from "@/components/pages/ChatPage.vue";


const routes = [
    { path: '/', redirect: '/main' },
    { path: '/main', component: MainPage },
    { path: '/chat', component: ChatPage },
    {
        path: '/admin',
        name: 'AdminPage',
        component: AdminPage,
    },
    { path: '/:pathMatch(.*)*', redirect: '/main' }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

export default router;
