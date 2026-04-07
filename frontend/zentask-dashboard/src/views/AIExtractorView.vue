<template>
  <div class="w-full h-full">
    <AiContentEmptyState v-if="!hasUploadedDocuments" />
    <AiContentLibrary v-else />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import AiContentEmptyState from '@/components/ai-content/AiContentEmptyState.vue'
import AiContentLibrary from '@/components/ai-content/AiContentLibrary.vue'

const uploadedDocuments = ref([])
const hasUploadedDocuments = computed(() => uploadedDocuments.value.length > 0)
</script>