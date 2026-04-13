<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Calendar,
  Overview,
  DropDownWhite,
  DropDownBlack,
  GenerateConfigTime,
  TaskSquareIcon,
} from '@/icons'

type TabKey = 'overview' | 'calendar'

const router = useRouter()
const route = useRoute()
const isGenerateMenuOpen = ref(false)

const openGenerateMenu = () => {
  isGenerateMenuOpen.value = true
}

const closeGenerateMenu = () => {
  isGenerateMenuOpen.value = false
}

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
]

const dropdownRef = ref<HTMLElement | null>(null)
const isDropdownOpen = ref(false)

const formatDateLocal = (date: Date) => {
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

const parseQueryDate = (value: unknown) => {
  if (typeof value !== 'string' || !value) return null
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return null
  parsed.setHours(0, 0, 0, 0)
  return parsed
}

const activeDate = computed(() => {
  const queryDate = parseQueryDate(route.query.date)
  if (queryDate) return queryDate

  const fallback = new Date()
  fallback.setHours(0, 0, 0, 0)
  return fallback
})

const displayMonth = ref(new Date(activeDate.value))

const syncDisplayMonthWithActiveDate = () => {
  displayMonth.value = new Date(
    activeDate.value.getFullYear(),
    activeDate.value.getMonth(),
    1
  )
}

const getWeekBlockRange = (date: Date) => {
  const year = date.getFullYear()
  const month = date.getMonth()
  const day = date.getDate()

  const startDay = Math.floor((day - 1) / 7) * 7 + 1
  const lastDayOfMonth = new Date(year, month + 1, 0).getDate()
  const endDay = Math.min(startDay + 6, lastDayOfMonth)

  const start = new Date(year, month, startDay)
  const end = new Date(year, month, endDay)

  start.setHours(0, 0, 0, 0)
  end.setHours(0, 0, 0, 0)

  return { start, end }
}

const currentWeekRange = computed(() => getWeekBlockRange(activeDate.value))

const navbarWeekRange = computed(() => {
  const { start, end } = currentWeekRange.value

  const format = (date: Date) =>
    date.toLocaleDateString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    })

  return `${format(start)} - ${format(end)}`
})

const dropdownMonthLabel = computed(() =>
  displayMonth.value.toLocaleDateString('en-US', {
    month: 'long',
    year: 'numeric',
  })
)

const weekBlocksOfMonth = computed(() => {
  const year = displayMonth.value.getFullYear()
  const month = displayMonth.value.getMonth()
  const daysInMonth = new Date(year, month + 1, 0).getDate()

  const blocks: Array<{
    key: string
    start: Date
    end: Date
    label: string
    isActive: boolean
  }> = []

  for (let startDay = 1; startDay <= daysInMonth; startDay += 7) {
    const endDay = Math.min(startDay + 6, daysInMonth)
    const start = new Date(year, month, startDay)
    const end = new Date(year, month, endDay)
    start.setHours(0, 0, 0, 0)
    end.setHours(0, 0, 0, 0)

    const activeStart = currentWeekRange.value.start
    const isActive =
      formatDateLocal(start) === formatDateLocal(activeStart)

    blocks.push({
      key: `${year}-${month + 1}-${startDay}`,
      start,
      end,
      label: `${String(startDay).padStart(2, '0')} - ${String(endDay).padStart(2, '0')}`,
      isActive,
    })
  }

  return blocks
})

const activeTab = computed<TabKey>(() => {
  const name = route.name
  if (name === 'scheduler-calendar') return 'calendar'
  return 'overview'
})

const updateSelectedWeek = (date: Date) => {
  const { start } = getWeekBlockRange(date)

  router.replace({
    query: {
      ...route.query,
      date: formatDateLocal(start),
    },
  })
}

const toggleDropdown = () => {
  syncDisplayMonthWithActiveDate()
  isDropdownOpen.value = !isDropdownOpen.value
}

const closeDropdown = () => {
  isDropdownOpen.value = false
}

const selectWeekBlock = (start: Date) => {
  updateSelectedWeek(start)
  closeDropdown()
}

const goPrevMonth = () => {
  displayMonth.value = new Date(
    displayMonth.value.getFullYear(),
    displayMonth.value.getMonth() - 1,
    1
  )
}

const goNextMonth = () => {
  displayMonth.value = new Date(
    displayMonth.value.getFullYear(),
    displayMonth.value.getMonth() + 1,
    1
  )
}

const goToTab = (tab: (typeof tabs)[number]) => {
  router.push({
    name: tab.routeName,
    query: route.query,
  })
}

const getTabClass = (key: TabKey) => {
  return activeTab.value === key
    ? 'border-[#999999] text-[#171717]'
    : 'border-transparent text-[#737373] hover:text-[#171717]'
}

const handleClickOutside = (event: MouseEvent) => {
  if (!dropdownRef.value) return
  if (!dropdownRef.value.contains(event.target as Node)) {
    closeDropdown()
  }
}

onMounted(() => {
  syncDisplayMonthWithActiveDate()
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="w-full bg-white">
    <div
      class="flex w-full items-center gap-6 border-b border-[#e5e5e5] bg-white py-0 pl-8 pr-6 box-border text-left text-[14px] font-inter"
    >
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

      <div ref="dropdownRef" class="relative">
        <div
          class="flex w-[260px] items-center gap-1.5 rounded-md border border-[#d4d4d4] bg-white px-2 py-1 box-border text-[#404040]"
        >
          <img :src="Calendar" class="h-5 w-5 object-contain" alt="Calendar" />

          <button
            type="button"
            class="flex flex-1 items-center justify-between gap-2 rounded-md px-1 py-1 text-left hover:bg-[#f5f5f5] cursor-pointer"
            @click.stop="toggleDropdown"
          >
            <div class="leading-5 font-medium">{{ navbarWeekRange }}</div>
            <img
              :src="DropDownBlack"
              class="h-5 w-5 object-contain"
              alt="Dropdown"
            />
          </button>
        </div>

        <div
          v-if="isDropdownOpen"
          class="absolute right-0 top-[calc(100%+8px)] z-50 w-[320px] rounded-2xl border border-[#e5e5e5] bg-white p-4 shadow-xl"
        >
          <div class="mb-4 flex items-center justify-between">
            <button
              type="button"
              class="rounded-md px-2 py-1 text-sm text-[#525252] hover:bg-[#f5f5f5] cursor-pointer"
              @click.stop="goPrevMonth"
            >
              Prev
            </button>

            <div class="text-sm font-semibold text-[#171717]">
              {{ dropdownMonthLabel }}
            </div>

            <button
              type="button"
              class="rounded-md px-2 py-1 text-sm text-[#525252] hover:bg-[#f5f5f5] cursor-pointer"
              @click.stop="goNextMonth"
            >
              Next
            </button>
          </div>

          <div class="grid grid-cols-1 gap-2">
            <button
              v-for="block in weekBlocksOfMonth"
              :key="block.key"
              type="button"
              class="flex items-center justify-between rounded-xl border px-3 py-3 text-left transition"
              :class="
                block.isActive
                  ? 'border-[#5c01d5] bg-[#f5f0ff] text-[#5c01d5]'
                  : 'border-[#e5e5e5] bg-white text-[#171717] hover:bg-[#fafafa] cursor-pointer'
              "
              @click.stop="selectWeekBlock(block.start)"
            >
              <div class="font-medium">
                Week {{ Math.floor((block.start.getDate() - 1) / 7) + 1 }}
              </div>
              <div class="text-sm">
                {{ block.label }}
              </div>
            </button>
          </div>
        </div>
      </div>

      <div
        class="relative flex items-center text-white"
        @mouseenter="openGenerateMenu"
        @mouseleave="closeGenerateMenu"
      >
        <button
          type="button"
          class="flex items-center rounded-l-md bg-[#5c01d5] py-1.5 px-2.5"
        >
          <div class="leading-5 font-medium">
            Generate Scheduler
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

        <div
          v-if="isGenerateMenuOpen"
          class="absolute right-0 top-[calc(100%+8px)] z-50 w-44 rounded-xl border border-[#e5e5e5] bg-white p-1 shadow-[0_8px_24px_rgba(0,0,0,0.12)]"
        >
          <button
            type="button"
            class="flex w-full items-center gap-2 rounded-md bg-[#f5f5f5] p-2 text-left text-base text-[#737373] transition hover:bg-[#eeeeee]"
          >
            <img
              :src="GenerateConfigTime"
              class="h-5 w-5 object-contain"
              alt="Config time"
            />
            <div class="leading-6">Config time</div>
          </button>

          <button
            type="button"
            class="mt-1 flex w-full items-center gap-2 rounded-md p-2 text-left text-base text-[#404040] transition hover:bg-[#f5f5f5]"
          >
            <img
              :src="TaskSquareIcon"
              class="h-5 w-5 object-contain"
              alt="Subject List"
            />
            <div class="leading-6">Subject List</div>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>