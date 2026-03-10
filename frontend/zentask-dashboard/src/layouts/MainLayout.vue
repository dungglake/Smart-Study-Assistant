<script setup lang="ts">
import { ref, computed } from 'vue'
import AppSidebar from '@/components/AppSidebar.vue'
import DashboardNavbar from '@/navbar/DashboardNavbar.vue'
import SmartSchedulerNavbar from '@/navbar/SmartSchedulerNavbar.vue'
import ExtractorNavbar from '@/navbar/ExtractorNavbar.vue'

const currentPage = ref('dashboard')

const navbarComponent = computed(() => {
  switch (currentPage.value) {
    case 'scheduler':
      return SmartSchedulerNavbar
    case 'extractor':
      return ExtractorNavbar
    default:
      return DashboardNavbar
  }
})
</script>

<template>
  <div class="flex min-h-screen bg-[#f5f5f5]">
    <AppSidebar @change-page="currentPage = $event" />

    <div class="flex min-w-0 flex-1 flex-col bg-white">
      <component :is="navbarComponent" />

      <main class="flex-1 p-8">
        <h1 class="text-2xl font-bold">Content page</h1>
      </main>
    </div>
  </div>
</template>