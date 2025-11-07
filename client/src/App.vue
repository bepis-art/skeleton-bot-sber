<template>
    <router-view/>
    <AppFooter/>
</template>

<script lang="ts">
import AppFooter from "@/components/AppFooter.vue";

export default {
    name: 'App',
    components: {
        AppFooter: AppFooter
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
    height: 100vh;
    width: 100vw;
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
