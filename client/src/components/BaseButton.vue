<template>
    <button
        v-if="isVisible"
        @click="handleClick"
        class="btn btn-danger button-orange d-flex align-items-center justify-content-center gap-1"
    >
        <slot name="icon"></slot>
        {{ label }}
    </button>
</template>

<script setup lang="ts">
const props = defineProps({
    label: {
        type: String,
        default: ''
    },
    onClick: {
        type: Function,
        default: null
    },
    isVisible: {
        type: Boolean,
        default: true
    }
});

const handleClick = (event: MouseEvent) => {
    if (props.onClick) {
        props.onClick(event);
    }
};
</script>

<style>
</style>
