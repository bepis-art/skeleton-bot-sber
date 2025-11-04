import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
    plugins: [
        vue(),
        VitePWA({
            registerType: 'autoUpdate',
            manifest: {
                name: 'ИИ спасатель',
                short_name: 'Спасатель',
                description: 'Бот ИИ спасатель',
                start_url: '/',
                display: 'standalone',
                background_color: '#ffffff',
                theme_color: '#4DBA87',
                icons: [
                    { src: 'img/icons/72.png', sizes: '72x72', type: 'image/png' },
                    { src: 'img/icons/192.png', sizes: '192x192', type: 'image/png' },
                    { src: 'img/icons/512.png', sizes: '512x512', type: 'image/png' }
                ]
            }
        })
    ]
});