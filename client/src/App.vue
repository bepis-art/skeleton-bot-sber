<template>
    <AppHeader :mode="currentMode"/>
    <router-view/>
    <AppFooter/>
</template>

<script lang="ts">
import { ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import AppFooter from "@/components/AppFooter.vue";
import AppHeader from "@/components/AppHeader.vue";

export default {
    name: 'App',
    components: {
        AppHeader,
        AppFooter: AppFooter
    },
    setup() {
        const route = useRoute();
        const currentMode = ref<'main' | 'chat'>('main');

        // Следим за изменением маршрута
        watch(
            () => route.path,
            (newPath) => {
                if (newPath === '/chat') {
                    currentMode.value = 'chat';
                } else {
                    currentMode.value = 'main';
                }
            },
            { immediate: true }
        );

        return {
            currentMode
        };
    }
};
</script>
<style>
html, body {
    height: 100%;
    margin: 0;
    padding: 0;
}

#app {
    display: flex;
    flex-direction: column;
    height: 100%;
    width: 100%;
}

.text-orange {
    color: var(--color-orange);
}

.button-orange {
    background-color: var(--color-orange) !important;
    border: none !important;
}

.nouser-select {
    user-select: none;
}

input:focus {
    border-color: var(--color-orange) !important;
    box-shadow: none !important;
}
</style>
