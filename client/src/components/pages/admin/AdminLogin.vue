<template>
    <div class="container d-flex justify-content-center align-items-center vh-100">
        <div class="card p-4" style="width: 100%; max-width: 400px">
            <h3 class="text-center mb-4">Админка</h3>

            <form @submit.prevent="onLogin">
                <div class="mb-3">
                    <label for="username" class="form-label">Логин</label>
                    <input
                        id="username"
                        v-model="credentials.login"
                        type="text"
                        class="form-control"
                        required
                    />
                </div>
                <div class="mb-3">
                    <label for="password" class="form-label">Пароль</label>
                    <input
                        id="password"
                        v-model="credentials.password"
                        type="password"
                        class="form-control"
                        required
                    />
                </div>

                <div
                    :class="error ? 'alert alert-danger small' : 'mb-3'"
                    :style="error ? '' : 'height: 55px'"
                >
                    {{ error }}
                </div>
                <div class="d-flex justify-content-end">
                    <BaseButton
                        type="submit"
                        :label="'Войти'"
                        :disabled="loading"
                    >
                    <span v-if="loading">
                        <span class="spinner-border spinner-border-sm" role="status"></span>
                    </span>
                    </BaseButton>
                </div>
            </form>
        </div>
    </div>
</template>

<script lang="ts">
import {ref} from 'vue';
import BaseButton from "@/components/BaseButton.vue";
import {authService} from "@/services/auth-service.ts";

export default {
    name: 'AdminLogin',
    components: {BaseButton},
    emits: ['login-success'],
    setup(props, { emit }) {
        const credentials = ref({login: '', password: ''});
        const error = ref('');
        const loading = ref(false);

        const onLogin = async () => {
            loading.value = true;
            const token = await authService.login(credentials.value);
            if (token) {
                error.value = '';
                sessionStorage.setItem('access_token', token.access_token);
                sessionStorage.setItem('refresh_token', token.refresh_token);
            } else {
                error.value = 'Неверный логин или пароль';
            }
            loading.value = false;
            emit('login-success');
        };

        return {
            credentials,
            error,
            loading,
            onLogin
        };
    }
};
</script>

<style scoped>
</style>
