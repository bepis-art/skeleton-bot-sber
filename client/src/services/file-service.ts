import {ConfigService} from "@/services/config-service.ts";
import apiService from "@/services/api-service.ts";
import type {IFile} from "@/interfaces/front";
import type {ApiFile} from "@/interfaces/api";

export class FileService {
    /**
     * Получение файлов
     */
    async getFiles() {
        const link: string = ConfigService.baseUrl + 'document'
        return apiService.get(link)
            .then((response) => response)
            .catch((error: Error) => {
                console.error(error);
                return null;
            });
    }

    /**
     * Получение одного файла
     * @param file
     */
    async getFile(file: IFile): Promise<boolean> {
        const link: string = ConfigService.baseUrl + `document/${file.id}`
        return apiService.get(link, { responseType: 'text' })
            .then((response) => {
                const blob = new Blob([response], {
                    type: 'text/plain;charset=utf-8'
                });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');

                a.href = url;
                a.download = file.filename;
                document.body.appendChild(a);
                a.click();

                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                return true;
            })
            .catch((error: Error) => {
                console.error(error);
                return false;
            });
    }

    /**
     * Загрузка одного файла
     * @param file
     */
    async uploadFile(file: File): Promise<IFile | null> {
        const link: string = ConfigService.baseUrl + 'document/upload'
        const formData = new FormData();
        formData.append('file', file)
        return apiService.post(link, formData)
            .then((response: ApiFile) => this.mapToFile(response))
            .catch((error: Error) => {
                console.error(error);
                return null;
            });
    }

    /**
     * Удаление файла
     * @param id
     */
    async deleteFile(id: string): Promise<boolean> {
        const link: string = ConfigService.baseUrl + `document/${id}`
        return apiService.delete(link)
            .then(() => true)
            .catch((error: Error) => {
                console.error(error);
                return false;
            })
    }

    private mapToFile(data: ApiFile): IFile {
        return data as IFile;
    }
}
