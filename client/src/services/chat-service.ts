import apiService from "@/services/api-service.ts";
import type {ApiMessage} from "@/interfaces/api";
import type {IMessage} from "@/interfaces/front";
export class ChatService {
    async sendMessage(msg: string): Promise<IMessage | null> {
        // fixme без хардока
        return apiService.post({ text: msg })
            .then((response: ApiMessage) => this.mapToMessage(response))
            .catch((error: Error) => {
                console.log(error);
                return null;
            });
    }

    private mapToMessage(data: ApiMessage): IMessage {
        return {
            text: data.text.replace(/\n/g, '<br/>'),
        };
    }
}
