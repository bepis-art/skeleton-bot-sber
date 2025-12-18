<template>
    <div v-if="isAuthenticated">
        <AdminPanel />
    </div>
    <div v-else>
        <AdminLogin @login-success="onLoginSuccess" />
    </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, ref } from 'vue';
import AdminPanel from "@/components/pages/admin/AdminPanel.vue";
import AdminLogin from "@/components/pages/admin/AdminLogin.vue";
import {authService} from "@/services/auth-service.ts";

export default defineComponent({
    name: 'AdminPage',
    components: { AdminPanel, AdminLogin },
    setup() {
        const isAuthenticated = ref(false);

        const onLoginSuccess = async () => {
            isAuthenticated.value = await authService.ensureValidToken();
        };

        onMounted(async () => {
            const isValid = await authService.ensureValidToken();
            isAuthenticated.value = isValid;
        });

        return {
            isAuthenticated,
            onLoginSuccess
        };
    }
});

</script>

<style scoped>

</style>
