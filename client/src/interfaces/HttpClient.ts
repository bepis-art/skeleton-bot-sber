export interface HttpClient {
    request: (url: string, options?: RequestInit) => Promise<Response>;
}
