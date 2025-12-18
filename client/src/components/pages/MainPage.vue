<script lang="ts">
import { useRouter } from 'vue-router';
import BaseButton from "@/components/BaseButton.vue";
export default {
    name: 'AppMain',
    components: {BaseButton},
    setup() {
        const router = useRouter();

        const onOpenChat = () => {
            router.push('/chat');
        };

        const onOpenAdmin = () => {
            router.push('/admin');
        };

        return {
            goToChat: onOpenChat,
            goToAdmin: onOpenAdmin,
        };
    }
};
</script>

<template>
    <div class="container-fluid flex-grow-1 d-flex flex-column justify-content-center align-items-center px-3">
        <div class="d-flex flex-column gap-3 w-100 max-width-content input-group-lg">

            <BaseButton
                :label="'Что делать при ЧС?'"
                :on-click="goToChat"
            />

            <BaseButton
                :label="'Сообщить о проблеме'"
            />

<!--            <BaseButton-->
<!--                :label="'Админ панель'"-->
<!--                :on-click="goToAdmin"-->
<!--            />-->

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
