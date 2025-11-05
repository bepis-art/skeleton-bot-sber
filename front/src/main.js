import { createApp } from 'vue';
import App from './App.vue';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap';
import 'bootstrap-icons/font/bootstrap-icons.css';

import { createBootstrap } from 'bootstrap-vue-next';
import 'bootstrap-vue-next/dist/bootstrap-vue-next.css';
import './assets/styles/themes.css';
import router from "./router/index.ts";

const app = createApp(App);
app.use(router);
app.use(createBootstrap());
app.mount('#app');

if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(() => {})
            .catch(err => console.error('SW failed:', err));
    });
}