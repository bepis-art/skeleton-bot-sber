import {createRouter, createWebHistory} from 'vue-router';

import AppMain from "@/components/pages/AppMain.vue";
import AppChat from "@/components/pages/AppChat.vue";
import AdminPanel from "@/components/pages/AdminPanel.vue";

const routes = [
  { path: '/', component: AppMain },
  { path: '/main', component: AppMain },
  { path: '/chat', component: AppChat },
  { path: '/admin', component: AdminPanel },
  { path: '/:pathMatch(.*)*', redirect: '/main' }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

export default router;
