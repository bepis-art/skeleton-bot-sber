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
#app {
    height: 100vh;
    width: 100vw;
    overflow: hidden; /* опционально, если не хотите скролл */
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
