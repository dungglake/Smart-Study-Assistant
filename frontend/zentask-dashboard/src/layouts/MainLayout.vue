<script setup lang="ts">
import { ref, computed } from 'vue'
import AppSidebar from '@/components/AppSidebar.vue'
import DashboardNavbar from '@/navbar/DashboardNavbar.vue'
import SmartSchedulerNavbar from '@/navbar/SmartSchedulerNavbar.vue'
import ExtractorNavbar from '@/navbar/ExtractorNavbar.vue'
import { useRouter } from 'vue-router'

const props = defineProps<{
  currentPage: 'dashboard' | 'scheduler' | 'extractor'
}>()

const router = useRouter()
const page = ref(props.currentPage)

watch(
  () => props.currentPage,
  (value) => {
    page.value = value
  },
  { immediate: true }
)

const navbarComponent = computed(() => {
  switch (page.value) {
    case 'scheduler':
      return SmartSchedulerNavbar
    case 'extractor':
      return ExtractorNavbar
    default:
      return DashboardNavbar
  }
})

const handleChangePage = (key: string) => {
  page.value = key as 'dashboard' | 'scheduler' | 'extractor'

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
        <slot />
      </main>
    </div>
  </div>
</template>