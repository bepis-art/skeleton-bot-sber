<script lang="ts">
export default {
    name: 'AppFooter'
}
</script>

<template>
    <div class="navbar footer d-flex flex-column justify-content-center align-items-center text-secondary">
        <div class="nouser-select">
            В критической ситуации всегда звоните
            <a class="text-secondary" href="tel:112" >112</a>
        </div>
    </div>
</template>

<style scoped>

.footer {
    border-top: 1px solid var(--bs-gray-200);
}

</style>
