<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import AppSidebar from '@/components/AppSidebar.vue'
import DashboardNavbar from '@/navbar/DashboardNavbar.vue'
import SmartSchedulerNavbar from '@/navbar/SmartSchedulerNavbar.vue'
import ExtractorNavbar from '@/navbar/ExtractorNavbar.vue'

const route = useRoute()

const navbarComponent = computed(() => {
  if (route.path.startsWith('/scheduler')) return SmartSchedulerNavbar
  if (route.path.startsWith('/extractor')) return ExtractorNavbar
  return DashboardNavbar
})
</script>

<template>
  <div class="flex min-h-screen bg-[#f5f5f5]">
    <AppSidebar />

    <div class="flex min-w-0 flex-1 flex-col bg-white">
      <component :is="navbarComponent" />

      <main class="flex-1">
        <router-view />
      </main>
    </div>
  </div>
</template>