import fetchClient from "@/services/fetch-client.ts";
import type {HttpClient} from "@/interfaces";

class ApiService {
    /**
     * Отправить GET запрос
     * Ошибки обрабатывать в сервисах
     */
    async get(link: string, options?: { responseType?: 'json' | 'text' | 'blob' }): Promise<any> {
        const client = await this.getHttpClient();

        return client.request(link, { method: 'GET', headers: { 'Authorization': `Bearer ${sessionStorage.getItem('access_token')}` } })
            .then((response: Response) => {
                if (options?.responseType === 'blob') {
                    return response.blob();
                }

                if (options?.responseType === 'text') {
                    return response.text();
                }

                return response.text();
            })
            .then((body: Blob | string | null) => {
                if (options?.responseType && options.responseType !== 'json') {
                    return body;
                }

                return !body ? {} : JSON.parse(<string>body);
            });
    }

    /**
     * Отправить POST запрос
     * Ошибки обрабатывать в сервисах
     */
    async post(link: string, data?: any): Promise<any> {
        const client = await this.getHttpClient()
        const isFormData = data instanceof FormData;
        const body = isFormData
            ? data
            : data
                ? JSON.stringify(data) : undefined;
        return client.request(link, {
            method: 'POST',
            headers: isFormData ? {'Authorization': `Bearer ${sessionStorage.getItem('access_token')}`} : { 'Content-Type': 'application/json', 'Authorization': `Bearer ${sessionStorage.getItem('access_token')}` },
            body,
        })
            .then((response: Response) => response.text())
            .then((body: string) => (!body ? {} : JSON.parse(body)));
    }

    /**
     * Отправить PUT запрос
     * Ошибки обрабатывать в сервисах
     */
    async put(link: string, data?: any): Promise<any> {
        const client = await this.getHttpClient();
        const body = data ? JSON.stringify(data) : undefined;
        return client.request(link, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json', 'Authorization': `Bearer ${sessionStorage.getItem('access_token')}`
            },
            body,
        })
            .then((response: Response) => response.text())
            .then((body: string) => (!body ? {} : JSON.parse(body)));
    }

    /**
     * Отправить DELETE запрос
     * @throws {Error} Если при отправке DELETE запроса произошла ошибка
     */
    async delete(link: string): Promise<any> {
        const client = await this.getHttpClient();
        return client.request(link, { method: 'DELETE', headers: {'Authorization': `Bearer ${sessionStorage.getItem('access_token')}`} })
            .then((response: Response) => response.text())
            .then((body: string) => (!body ? {} : JSON.parse(body)));
    }

    private async getHttpClient(): Promise<HttpClient> {
        return fetchClient.getHttpClient();
    }
}

const apiService = new ApiService();
export default apiService;
