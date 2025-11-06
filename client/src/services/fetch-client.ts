import { ConfigService } from "./config-service.ts";
import type {HttpClient} from "@/interfaces";

class FetchClient {
    private static client: HttpClient | null = null;

    async getHttpClient(): Promise<HttpClient> {
        if (!FetchClient.client) {
            console.error("baseUrl из env: ", import.meta);
            FetchClient.client = {
                async request(url: string, options: RequestInit = {}) {
                    const fullUrl = `/api/${url}`;
                    return fetch(fullUrl, {
                        ...options
                    });
                }
            };
        }
        return FetchClient.client;
    }
}

const fetchClient = new FetchClient();
export default fetchClient;
