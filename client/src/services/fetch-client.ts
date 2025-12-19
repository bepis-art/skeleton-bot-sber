import type {HttpClient} from "@/interfaces";

class FetchClient {
    private static client: HttpClient | null = null;

    async getHttpClient(): Promise<HttpClient> {
        if (!FetchClient.client) {
            FetchClient.client = {
                async request(url: string, options: RequestInit = {}) {
                    const fullUrl = `${url ?? ''}`;
                    return fetch(fullUrl, {
                        ...options,
                        headers: {
                            'Authorization': `Bearer ${sessionStorage.getItem('access_token')}`
                        },
                    });
                }
            };
        }
        return FetchClient.client;
    }
}

const fetchClient = new FetchClient();
export default fetchClient;
