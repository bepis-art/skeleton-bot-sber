export class ConfigService {
    static baseUrl: string = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_DEV_URL;
}
