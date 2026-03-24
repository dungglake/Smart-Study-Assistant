<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  Logo,
  SidebarToggle,
  ArrowUpRight,
  HomeIcon,
  CalendarIcon,
  BookOpenIcon,
  ChatboxIcon,
  InfoCircleIcon,
  SearchIcon,
} from '@/icons'

const router = useRouter()
const route = useRoute()

const menuItems = [
  {
    key: 'dashboard',
    label: 'Dashboard',
    icon: HomeIcon,
    path: '/dashboard',
  },
  {
    key: 'scheduler',
    label: 'Smart Scheduler',
    icon: CalendarIcon,
    path: '/scheduler',
  },
  {
    key: 'extractor',
    label: 'AI Content Extractor',
    icon: BookOpenIcon,
    path: '/extractor',
  },
]

const bottomItems = [
  {
    key: 'feedback',
    label: 'Feedback',
    icon: ChatboxIcon,
    external: true,
  },
  {
    key: 'support',
    label: 'Support',
    icon: InfoCircleIcon,
    external: true,
  },
]

const activeKey = computed(() => {
  if (route.path.startsWith('/scheduler')) return 'scheduler'
  if (route.path.startsWith('/extractor')) return 'extractor'
  return 'dashboard'
})

const goToPage = (path: string) => {
  router.push(path)
}
</script>

<template>
  <aside class="flex h-screen w-[280px] flex-col rounded-r-[32px] bg-[#f7f7f8] px-6 py-7 border-r border-gray-200">
    <div class="flex items-center justify-between">
      <img :src="Logo" alt="Zentask Logo" class="h-7 w-auto" />
      <button class="flex h-10 w-10 items-center justify-center rounded-xl pl-3">
        <img :src="SidebarToggle" alt="Toggle sidebar" class="h-6.5 w-6.5" />
      </button>
    </div>

    <div class="mt-10">
      <div class="flex items-center gap-3 rounded-2xl border border-[#d8d8d8] bg-white px-4 py-3">
        <img :src="SearchIcon" alt="Search" class="h-6 w-6 shrink-0" />
        <input
          type="text"
          placeholder="Search..."
          class="min-w-0 flex-1 bg-transparent text-[15px] text-[#3a3a3a] outline-none placeholder:text-[#7d7d7d]"
        />
        <div class="flex items-center gap-2">
          <span class="flex h-7 min-w-[28px] items-center justify-center rounded-md border border-[#d8d8d8] px-2 text-xs text-[#666]">
            ⌘
          </span>
          <span class="flex h-7 min-w-[28px] items-center justify-center rounded-md border border-[#d8d8d8] px-2 text-xs text-[#666]">
            K
          </span>
        </div>
      </div>
    </div>

    <nav class="mt-12 flex-1">
      <ul class="space-y-4">
        <li v-for="item in menuItems" :key="item.key">
          <button
            type="button"
            @click="goToPage(item.path)"
            class="group relative flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left transition"
            :class="
              activeKey === item.key
                ? 'text-[#6d28ff]'
                : 'text-[#8b8b8b] hover:bg-white hover:text-[#5f5f5f]'
            "
          >
            <span
              v-if="activeKey === item.key"
              class="absolute left-0 top-1/2 h-10 w-[2px] -translate-y-1/2 rounded-full bg-[#6d28ff]"
            />

            <img
              :src="item.icon"
              :alt="item.label"
              class="h-6 w-6 shrink-0"
              :class="activeKey === item.key ? '' : 'opacity-70'"
            />

            <span class="text-[18px] font-medium">
              {{ item.label }}
            </span>
          </button>
        </li>
      </ul>
    </nav>

    <div class="space-y-3 pb-2">
      <button
        v-for="item in bottomItems"
        :key="item.key"
        type="button"
        class="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-[#7e7e7e] transition hover:bg-white hover:text-[#5f5f5f]"
      >
        <img :src="item.icon" :alt="item.label" class="h-6 w-6 shrink-0 opacity-75" />
        <span class="text-[18px] font-medium">{{ item.label }}</span>
        <img
          v-if="item.external"
          :src="ArrowUpRight"
          alt="External link"
          class="ml-1 h-3.5 w-3.5 opacity-70"
        />
      </button>
    </div>
  </aside>
</template>