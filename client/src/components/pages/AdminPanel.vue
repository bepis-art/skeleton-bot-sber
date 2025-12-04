<script lang="ts">
import { ref, onMounted } from 'vue';
import BaseButton from "@/components/BaseButton.vue";

const fileService = {
    getFiles: async () => {
        await new Promise(resolve => setTimeout(resolve, 800));
        return [
            { id: 1, name: 'report.pdf' },
            { id: 2, name: 'image.jpg' },
            { id: 3, name: 'data.xlsx' }
        ];
    },
    deleteFile: async (id: number) => {
        console.log('Удаление файла с ID:', id);
    }
};

export default {
    name: 'AdminPanel',
    components: {BaseButton},
    setup() {
        const files = ref<{ id: number; name: string }[]>([]);
        const loading = ref(true);

        const loadFiles = async () => {
            loading.value = true;
            try {
                files.value = await fileService.getFiles();
            } catch (error) {
                console.error('Ошибка загрузки файлов:', error);
            } finally {
                loading.value = false;
            }
        };

        const handleDelete = async (id: number) => {
            if (confirm('Вы уверены, что хотите удалить файл?')) {
                await fileService.deleteFile(id);
                files.value = files.value.filter(f => f.id !== id);
            }
        };

        const handleAddFile = () => {

        };

        onMounted(() => {
            loadFiles();
        });

        return {
            files,
            loading,
            handleDelete,
            handleAddFile
        };
    }
};
</script>

<template>
    <div class="container mt-4 vh-100">
        <div class="d-flex justify-content-between align-items-center mb-3 input-group-lg ms-3 me-3">
            <h5>Файлы</h5>
            <BaseButton
                :on-click="handleAddFile"
            >
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
                    <span>{{ file.name }}</span>
                    <BaseButton
                        :on-click="() => handleDelete(file.id)"
                    >
                        <template #icon>
                            <i class="bi bi-trash"></i>
                        </template>
                    </BaseButton>
                </li>
            </ul>
        </div>
    </div>
</template>

<style scoped>
.spinner-color {
    color: var(--color-orange);
}
</style>
