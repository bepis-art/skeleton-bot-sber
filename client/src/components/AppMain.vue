<script lang="ts">
import { useRouter } from 'vue-router';
import AppHeader from "@/components/AppHeader.vue";
export default {
    name: 'AppMain',
    components: {
        AppHeader
    },
    setup() {
        const router = useRouter();

        const goToChat = () => {
            router.push('/chat');
        };
        return {
            goToChat,
        };
    }
};
</script>

<template>
    <AppHeader/>

    <div class="d-flex container-fluid flex-column justify-content-center align-items-center h-75">
        <div class="d-flex flex-column gap-4 justify-content-between align-items-center h-auto">
            <button @click="goToChat" class="btn btn-danger button-orange w-100 h-5">
                Что делать при ЧС?
            </button>

            <button class="btn btn-danger button-orange w-100 h-5">
                Сообщить о проблеме
            </button>

            <span class="text-secondary nouser-select">
                Нажмите "Что делать при ЧС?" для получения помощи от ИИ-агента
            </span>
            <span class="text-secondary nouser-select">
                Для экстренной связи нажмите "Сообщить о ЧС"
            </span>
        </div>
    </div>
</template>

<style scoped>
</style>
