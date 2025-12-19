<script lang="ts">
import { ref, onMounted } from 'vue';
import BaseButton from "@/components/BaseButton.vue";
import { FileService } from "@/services/file-service.ts";
import type { IFile } from "@/interfaces/front";

const fileService = new FileService();

export default {
    name: 'AdminPanel',
    components: { BaseButton },
    setup() {
        const files = ref<IFile[]>([]);
        const loading = ref(true);
        const showUploadModal = ref(false);
        const fileInputRef = ref<HTMLInputElement | null>(null);
        const isUploadInvalid = ref(false);
        const isDraggingOver = ref(false);

        const deleteConfirmation = ref<{
            show: boolean;
            fileId: string | null;
        }>({ show: false, fileId: null });

        const loadFiles = async () => {
            loading.value = true;
            files.value = await fileService.getFiles();
            loading.value = false;
        };

        const onFileDownload = async (file: IFile) => {
            loading.value = true;
            await fileService.getFile(file);
            loading.value = false;
        };

        const onFileDelete = (id: string) => {
            deleteConfirmation.value = { show: true, fileId: id };
        };

        const confirmDelete = async () => {
            const id = deleteConfirmation.value.fileId;
            if (!id) return;

            deleteConfirmation.value = { show: false, fileId: null };
            loading.value = true;
            const isDeleted = await fileService.deleteFile(id);
            if (isDeleted) {
                files.value = files.value.filter(f => f.id !== id);
            }
            loading.value = false;
        };

        const cancelDelete = () => {
            deleteConfirmation.value = { show: false, fileId: null };
        };

        const onFileAdd = async (file: File) => {
            const validExtensions = ['.txt', '.docx'];
            const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();

            if (!validExtensions.includes(ext)) {
                isUploadInvalid.value = true;
                return;
            }

            isUploadInvalid.value = false;
            loading.value = true;
            const loadedFile: IFile | null = await fileService.uploadFile(file);
            if (loadedFile) {
                files.value = [loadedFile, ...files.value];
            }
            loading.value = false;
            showUploadModal.value = false;
        };

        const triggerFileInput = () => {
            if (fileInputRef.value) {
                fileInputRef.value.click();
            }
        };

        const onFileSelected = async (event: Event) => {
            const input = event.target as HTMLInputElement;
            const file = input.files?.[0];
            if (file) {
                await onFileAdd(file);
                input.value = '';
            }
        };

        let dragCounter = 0;

        function onDragEnter(event: DragEvent) {
            event.preventDefault();
            dragCounter++;
            isDraggingOver.value = true;
        }

        function onDragLeave(event: DragEvent) {
            event.preventDefault();
            dragCounter--;
            if (dragCounter === 0) {
                isDraggingOver.value = false;
            }
        }

        async function onFileDrop(event: DragEvent) {
            event.preventDefault();
            dragCounter = 0;
            isDraggingOver.value = false;

            const file = event.dataTransfer?.files?.[0];
            if (file) {
                await onFileAdd(file);
            }
        }

        const closeUploadModal = () => {
            showUploadModal.value = false;
            isUploadInvalid.value = false;
        };

        onMounted(() => {
            loadFiles();

            const preventDefaults = (e: DragEvent) => {
                e.preventDefault();
                e.stopPropagation();
            };

            window.addEventListener('dragover', preventDefaults);
            window.addEventListener('drop', preventDefaults);
        });

        return {
            files,
            loading,
            showUploadModal,
            fileInputRef,
            isUploadInvalid,
            deleteConfirmation,
            isDraggingOver,
            onFileDelete,
            confirmDelete,
            cancelDelete,
            triggerFileInput,
            onFileSelected,
            onFileDrop,
            onFileDownload,
            onDragLeave,
            onDragEnter,
            closeUploadModal
        };
    }
};
</script>

<template>
    <div class="container mt-4 vh-100">
        <div class="d-flex justify-content-between align-items-center mb-3 input-group-lg ms-3 me-3">
            <h5>Файлы</h5>
            <BaseButton @click="showUploadModal = true">
                <template #icon>
                    <i class="bi bi-cloud-plus"></i>
                </template>
            </BaseButton>
        </div>

        <!-- Прелоадер -->
        <div v-if="loading" class="d-flex align-items-center mb-3">
            <div class="spinner-grow spinner-grow-sm spinner-color" role="status">
                <span class="visually-hidden">Загрузка...</span>
            </div>
            <span class="ms-2">Загрузка файлов...</span>
        </div>

        <!-- Список файлов -->
        <div v-else>
            <div v-if="files.length === 0" class="text-muted">
                Нет файлов
            </div>
            <ul v-else class="list-group">
                <li
                    v-for="file in files"
                    :key="file.id"
                    class="list-group-item d-flex justify-content-between align-items-center input-group-lg"
                >
                    <span>{{ file.filename }}</span>
                    <div class="d-flex gap-3">
                        <BaseButton @click="() => onFileDownload(file)">
                            <template #icon>
                                <i class="bi bi-cloud-arrow-down"></i>
                            </template>
                        </BaseButton>
                        <BaseButton @click="() => onFileDelete(file.id)">
                            <template #icon>
                                <i class="bi bi-trash"></i>
                            </template>
                        </BaseButton>
                    </div>
                </li>
            </ul>
        </div>

        <!-- Модальное окно загрузки -->
        <div v-if="showUploadModal" class="modal-overlay" @click.self="closeUploadModal">
            <div class="upload-modal d-flex flex-column justify-content-center align-items-center gap-4">
                <h4>Загрузите файл</h4>

                <div
                    class="drop-area"
                    :class="{ 'drag-over': isDraggingOver }"
                    @dragenter="onDragEnter"
                    @dragover.prevent
                    @dragleave="onDragLeave"
                    @drop="onFileDrop"
                    @click="triggerFileInput"
                >
                    <p>Перетащите файл сюда или кликните для выбора</p>
                </div>

                <BaseButton @click="triggerFileInput" label="Выбрать файл" />

                <!-- Единая плашка с динамическим цветом -->
                <p
                    class="small mt-1 mb-0"
                    :class="isUploadInvalid ? 'text-danger' : 'text-muted'"
                >
                    Поддерживаются только файлы форматов: <strong>.txt, .docx</strong>
                </p>

                <input
                    ref="fileInputRef"
                    type="file"
                    accept=".txt,.docx"
                    style="display: none"
                    @change="onFileSelected"
                />
            </div>
        </div>

        <!-- Модальное окно подтверждения удаления -->
        <div v-if="deleteConfirmation.show" class="modal-overlay" @click.self="cancelDelete">
            <div class="confirmation-modal text-start">
                <h5 class="mb-5">Подтверждение</h5>
                <div class="mt-4 mb-4">Вы уверены, что хотите удалить файл?</div>
                <div class="d-flex justify-content-end gap-2 mt-4">
                    <BaseButton
                        @click="confirmDelete"
                        :label="'Удалить'"
                    ></BaseButton>
                    <BaseButton
                        @click="cancelDelete"
                        :label="'Отмена'"
                    ></BaseButton>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.spinner-color {
    color: var(--color-orange);
}

.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 10000;
}

.upload-modal {
    background: white;
    padding: 1.5rem;
    border-radius: 0.5rem;
    width: 90%;
    max-width: 400px;
    text-align: center;
}

.confirmation-modal {
    background: white;
    padding: 1.25rem;
    border-radius: 0.5rem;
    width: 90%;
    max-width: 420px;
    text-align: center;
}

.drop-area {
    border: 2px dashed #ccc;
    border-radius: 0.375rem;
    padding: 1.5rem;
    cursor: pointer;
    transition: border-color 0.2s;
}

.drop-area:hover {
    border-color: var(--color-orange);
}

.drop-area.drag-over {
    border-color: var(--color-orange);
    background-color: rgba(255, 165, 0, 0.08);
}

</style>
