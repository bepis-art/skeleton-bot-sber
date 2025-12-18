import { ConfigService } from './config-service';
import apiService from "@/services/api-service.ts";
import type {IObject} from "@/interfaces";

class AuthService {
    async login(credentials: { login: string; password: string }): Promise<IObject | null> {
        const link: string = ConfigService.baseUrl + 'auth/login';
        return apiService.post(link, credentials)
            .then((response) => {
                return {
                    access_token: response.access_token,
                    refresh_token: response.refresh_token
                }
            })
            .catch((error: Error) => {
                console.error(error);
                return null;
            });
    }

    logout() {
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('refresh_token');
    }

    /**
     * Обновление токена
     */
    async refreshToken(): Promise<boolean> {
        const refreshToken = sessionStorage.getItem('refresh_token');
        if (!refreshToken) return false;

        try {
            const link = ConfigService.baseUrl + 'auth/refresh';
            const response = await apiService.post(link, { refresh_token: refreshToken });

            if (response?.access_token) {
                sessionStorage.setItem('access_token', response.access_token);
                if (response.refresh_token) {
                    sessionStorage.setItem('refresh_token', response.refresh_token);
                }
                return true;
            }
            return false;
        } catch (error) {
            console.error('Token refresh failed:', error);
            this.logout();
            return false;
        }
    }

    /**
     * Проверка валидности токена
     */
    async ensureValidToken(): Promise<boolean> {
        const token = sessionStorage.getItem('access_token');
        if (!token) return false;

        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            if (payload.exp * 1000 > Date.now()) {
                return true;
            }
        } catch {

        }

        return await this.refreshToken();
    }

    /**
     * Проверка, просрочен токен или нет
     */
    isAuthenticated(): boolean {
        const token = sessionStorage.getItem('access_token');
        if (!token) return false;
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload.exp * 1000 > Date.now();
        } catch {
            return false;
        }
    }
}

const authService = new AuthService();
export { authService };
