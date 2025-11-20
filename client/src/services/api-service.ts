import fetchClient from "@/services/fetch-client.ts";
import type {HttpClient} from "@/interfaces";

class ApiService {
    /**
     * Отправить GET запрос
     * Ошибки обрабатывать в сервисах
     */
    async get(link: string): Promise<any> {
        const client = await this.getHttpClient();
        return client.request(link, { method: 'GET' })
            .then((response: Response) => response.text())
            .then((body: string) => (!body ? {} : JSON.parse(body)));
    }

    /**
     * Отправить POST запрос
     * Ошибки обрабатывать в сервисах
     */
    async post(link: string, data?: any): Promise<any> {
        const client = await this.getHttpClient()
        const body = data ? JSON.stringify(data) : undefined;
        return client.request(link, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
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
                'Content-Type': 'application/json',
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
        return client.request(link, { method: 'DELETE' })
            .then((response: Response) => response.text())
            .then((body: string) => (!body ? {} : JSON.parse(body)));
    }

    private async getHttpClient(): Promise<HttpClient> {
        return fetchClient.getHttpClient();
    }
}

const apiService = new ApiService();
export default apiService;
