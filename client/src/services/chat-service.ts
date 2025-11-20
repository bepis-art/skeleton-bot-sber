import apiService from "@/services/api-service.ts";
import type {ApiMessage} from "@/interfaces/api";
import type {IMessage} from "@/interfaces/front";
import {ConfigService} from "@/services/config-service.ts";
export class ChatService {
    async sendMessage(msg: string, history: IMessage[]): Promise<IMessage | null> {
        // fixme без хардока
        const link: string = ConfigService.baseUrl + 'ask'
        const mappedHistory = this.mapToHistory(history);
        return apiService.post(link, { text: msg, history: mappedHistory})
            .then((response: ApiMessage) => this.mapToMessage(response))
            .catch((error: Error) => {
                console.log(error);
                return null;
            });
    }

    private mapToMessage(data: ApiMessage): IMessage {
        return {
            text: data.text.replace(/\n/g, '<br/>'),
            sender: 'system'
        };
    }

    private mapToHistory(data: IMessage[]): string {
        return data.map(msg => `${msg.sender}: ${msg.text.replace(/<br\s*\/?>/gi, '\n')}`).join('\n');
    }
}
