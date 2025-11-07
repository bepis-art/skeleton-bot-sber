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

    <div class="container-fluid flex-grow-1 d-flex flex-column justify-content-center align-items-center px-3">
        <div class="d-flex flex-column gap-3 w-100 max-width-content">
            <button
                @click="goToChat"
                class="btn btn-danger button-orange py-2"
            >
                Что делать при ЧС?
            </button>

            <button class="btn btn-danger button-orange py-2">
                Сообщить о проблеме
            </button>

            <span class="text-secondary nouser-select text-center">
                Нажмите "Что делать при ЧС?" для получения помощи от ИИ-агента
            </span>
            <span class="text-secondary nouser-select text-center">
                Для экстренной связи нажмите "Сообщить о проблеме"
            </span>
        </div>
    </div>
</template>

<style scoped>
.max-width-content {
    max-width: 500px;
    width: 100%;
}
</style>
