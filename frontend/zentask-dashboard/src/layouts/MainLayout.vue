<script setup lang="ts">
import { computed } from 'vue'
import AppSidebar from '@/components/AppSidebar.vue'
import DashboardNavbar from '@/navbar/DashboardNavbar.vue'
import SmartSchedulerNavbar from '@/navbar/SmartSchedulerNavbar.vue'
import ExtractorNavbar from '@/navbar/ExtractorNavbar.vue'
import { useRoute, useRouter } from 'vue-router'

const currentPage = computed(() => {
  if (route.path.startsWith('/scheduler')) return 'scheduler'
  if (route.path.startsWith('/extractor')) return 'extractor'
  return 'dashboard'
})

const router = useRouter()
const route = useRoute()


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

const handleChangePage = (key: string) => {
  if (key === 'dashboard') router.push('/dashboard')
  if (key === 'scheduler') router.push('/scheduler')
  if (key === 'extractor') router.push('/extractor')
}
</script>

<template>
  <div class="flex min-h-screen bg-[#f5f5f5]">
    <AppSidebar @change-page="handleChangePage" />

    <div class="flex min-w-0 flex-1 flex-col bg-white">
      <component :is="navbarComponent" />
      <main class="flex-1">
        <router-view />
      </main>
    </div>
  </div>
</template>