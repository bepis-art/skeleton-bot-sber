<template>
    <router-view/>
    <Footer/>
</template>

<script>
import Header from "@/components/Header.vue";
import Main from "@/components/Main.vue";
import Footer from "@/components/Footer.vue";

export default {
    name: 'App',
    components: {
        Main,
        Header,
        Footer
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
