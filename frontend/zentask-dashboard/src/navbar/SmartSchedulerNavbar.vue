<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Gantt,
  Calendar,
  Overview,
  DropDownWhite,
  DropDownBlack,
} from '@/icons'

type TabKey = 'overview' | 'calendar' | 'gantt'

const router = useRouter()
const route = useRoute()

const tabs: { key: TabKey; label: string; icon: string; routeName: string }[] = [
  {
    key: 'overview',
    label: 'Overview',
    icon: Overview,
    routeName: 'scheduler-overview',
  },
  {
    key: 'calendar',
    label: 'Calendar',
    icon: Calendar,
    routeName: 'scheduler-calendar',
  },
  {
    key: 'gantt',
    label: 'Gantt',
    icon: Gantt,
    routeName: 'scheduler-gantt',
  },
]

const activeTab = computed<TabKey>(() => {
  const name = route.name
  if (name === 'scheduler-calendar') return 'calendar'
  if (name === 'scheduler-gantt') return 'gantt'
  return 'overview'
})

const goToTab = (tab: (typeof tabs)[number]) => {
  router.push({ name: tab.routeName })
}

const getTabClass = (key: TabKey) => {
  return activeTab.value === key
    ? 'border-[#999999] text-[#171717]'
    : 'border-transparent text-[#737373] hover:text-[#171717]'
}
</script>

<template>
  <div class="w-full bg-white">
    <div
      class="flex w-full items-center gap-6 border-b border-[#e5e5e5] bg-white py-0 pl-8 pr-6 box-border text-left text-[14px] font-inter"
    >
      <!-- Left tabs -->
      <div class="flex flex-1 items-center gap-6">
        <div
          v-for="tab in tabs"
          :key="tab.key"
          class="flex cursor-pointer select-none flex-col items-center border-b-2 pt-3 pb-1.5 transition-all duration-150"
          :class="getTabClass(tab.key)"
          @click="goToTab(tab)"
        >
          <div class="flex items-center justify-center gap-2 rounded-md py-2">
            <img
              :src="tab.icon"
              class="h-5 w-5 object-contain"
              :alt="tab.label"
            />
            <div class="leading-5 font-medium">{{ tab.label }}</div>
          </div>
        </div>
      </div>

      <!-- Date range -->
      <div
        class="flex w-[252px] items-center gap-1.5 rounded-md border border-[#d4d4d4] bg-white px-2.5 py-1.5 box-border text-[#404040]"
      >
        <img :src="Calendar" class="h-5 w-5 object-contain" alt="Calendar" />
        <div class="flex-1 leading-5 font-medium">12/12/2025 - 04/01/2026</div>
        <img
          :src="DropDownBlack"
          class="h-5 w-5 object-contain"
          alt="Dropdown"
        />
      </div>

      <!-- Add schedule button -->
      <div class="flex items-center text-white">
        <button
          type="button"
          class="flex items-center rounded-l-md bg-[#5c01d5] py-1.5 px-2.5"
        >
          <div class="leading-5 font-medium">
            Thêm lịch học &amp; công việc
          </div>
        </button>

        <button
          type="button"
          class="flex items-center justify-center rounded-r-md border-l border-white/20 bg-[#5c01d5] p-1.5"
        >
          <img
            :src="DropDownWhite"
            class="h-5 w-5 object-contain"
            alt="Dropdown"
          />
        </button>
      </div>
    </div>
  </div>
</template>