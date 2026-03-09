<template>
  <div class="min-h-screen bg-[#f5f5f5]">
    <div class="flex">
      <AppSidebar />

      <main class="flex-1 p-8">
        <h1 class="text-2xl font-bold">Content page</h1>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import AppSidebar from './components/AppSidebar.vue'
</script>