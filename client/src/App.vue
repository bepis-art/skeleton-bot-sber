<template>
    <AppHeader :mode="currentMode"/>
    <router-view/>
    <AppFooter/>
</template>

<script lang="ts">
import {ref, watch} from 'vue';
import {useRoute} from 'vue-router';
import AppFooter from "@/components/AppFooter.vue";
import AppHeader from "@/components/AppHeader.vue";
import {ERouteMode} from "@/enums";

export default {
    name: 'App',
    components: {
        AppHeader,
        AppFooter: AppFooter
    },
    setup() {
        const route = useRoute();
        const currentMode = ref<ERouteMode>(ERouteMode.MAIN);

        // Следим за изменением маршрута
        watch(
            () => route.path,
            (newPath) => {
                if (newPath === '/chat') {
                    currentMode.value = ERouteMode.CHAT;
                }
                if (newPath === '/main') {
                    currentMode.value = ERouteMode.MAIN;
                }
                if (newPath === '/admin') {
                    currentMode.value = ERouteMode.ADMIN;
                }
                if (newPath === '/') {
                    currentMode.value = ERouteMode.MAIN;
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
