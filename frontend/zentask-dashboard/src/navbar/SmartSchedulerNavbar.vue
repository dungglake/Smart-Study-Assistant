<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Calendar,
  Overview,
  DropDownWhite,
  DropDownBlack,
  DropUp,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  GenerateConfigTime,
  TaskSquareIcon,
} from '@/icons'

type TabKey = 'overview' | 'calendar'

type CalendarCell = {
  key: string
  date: Date
  dayNumber: string
  isCurrentMonth: boolean
  isSelected: boolean
  isInSelectedWeek: boolean
  isWeekStart: boolean
  isWeekEnd: boolean
}

const router = useRouter()
const route = useRoute()
const emit = defineEmits<{
  (e: 'open-time-config'): void
  (e: 'open-subject-list'): void
  (e: 'open-generate-popup'): void
}>()

const isGenerateMenuOpen = ref(false)
function openTimeConfig() {
  emit('open-time-config')
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

const calendarDropdownRef = ref<HTMLElement | null>(null)
const generateMenuRef = ref<HTMLElement | null>(null)

const isCalendarOpen = ref(false)
const weekdayLabels = ['M', 'T', 'W', 'T', 'F', 'S', 'S']

function formatDateLocal(date: Date): string {
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

function parseQueryDate(value: unknown): Date | null {
  if (typeof value !== 'string' || !value) return null
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return null
  parsed.setHours(0, 0, 0, 0)
  return parsed
}

function normalizeDate(date: Date): Date {
  const next = new Date(date)
  next.setHours(0, 0, 0, 0)
  return next
}

function getStartOfWeekMonday(date: Date): Date {
  const next = normalizeDate(date)
  const day = next.getDay()
  const diff = day === 0 ? -6 : 1 - day
  next.setDate(next.getDate() + diff)
  return next
}

function getEndOfWeekSunday(date: Date): Date {
  const start = getStartOfWeekMonday(date)
  const end = new Date(start)
  end.setDate(start.getDate() + 6)
  end.setHours(0, 0, 0, 0)
  return end
}

function isSameDate(a: Date, b: Date): boolean {
  return formatDateLocal(a) === formatDateLocal(b)
}

function isDateInRange(date: Date, start: Date, end: Date): boolean {
  const current = normalizeDate(date).getTime()
  return current >= start.getTime() && current <= end.getTime()
}

const selectedDate = computed(() => {
  const fromQuery = parseQueryDate(route.query.date)
  if (fromQuery) return fromQuery

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return today
})

const selectedWeekStart = computed(() => getStartOfWeekMonday(selectedDate.value))
const selectedWeekEnd = computed(() => getEndOfWeekSunday(selectedDate.value))

const displayMonth = ref(
  new Date(selectedDate.value.getFullYear(), selectedDate.value.getMonth(), 1)
)

watch(
  selectedDate,
  (value) => {
    displayMonth.value = new Date(value.getFullYear(), value.getMonth(), 1)
  },
  { immediate: true }
)

const navbarWeekRange = computed(() => {
  const format = (date: Date) =>
    date.toLocaleDateString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    })

  return `${format(selectedWeekStart.value)} - ${format(selectedWeekEnd.value)}`
})

const displayMonthLabel = computed(() =>
  displayMonth.value.toLocaleDateString('en-US', {
    month: 'long',
    year: 'numeric',
  })
)

const calendarCells = computed<CalendarCell[]>(() => {
  const monthStart = new Date(
    displayMonth.value.getFullYear(),
    displayMonth.value.getMonth(),
    1
  )
  monthStart.setHours(0, 0, 0, 0)

  const monthEnd = new Date(
    displayMonth.value.getFullYear(),
    displayMonth.value.getMonth() + 1,
    0
  )
  monthEnd.setHours(0, 0, 0, 0)

  const gridStart = getStartOfWeekMonday(monthStart)
  const gridEnd = getEndOfWeekSunday(monthEnd)

  const cells: CalendarCell[] = []
  const cursor = new Date(gridStart)

  while (cursor <= gridEnd) {
    const cellDate = new Date(cursor)
    const inSelectedWeek = isDateInRange(
      cellDate,
      selectedWeekStart.value,
      selectedWeekEnd.value
    )

    cells.push({
      key: formatDateLocal(cellDate),
      date: cellDate,
      dayNumber: `${cellDate.getDate()}`.padStart(2, '0'),
      isCurrentMonth: cellDate.getMonth() === displayMonth.value.getMonth(),
      isSelected: isSameDate(cellDate, selectedDate.value),
      isInSelectedWeek: inSelectedWeek,
      isWeekStart: inSelectedWeek && isSameDate(cellDate, selectedWeekStart.value),
      isWeekEnd: inSelectedWeek && isSameDate(cellDate, selectedWeekEnd.value),
    })

    cursor.setDate(cursor.getDate() + 1)
  }

  return cells
})

const calendarRows = computed(() => {
  const rows: CalendarCell[][] = []
  for (let i = 0; i < calendarCells.value.length; i += 7) {
    rows.push(calendarCells.value.slice(i, i + 7))
  }
  return rows
})

const activeTab = computed<TabKey>(() => {
  const name = route.name
  if (name === 'scheduler-calendar') return 'calendar'
  return 'overview'
})

function updateSelectedDate(date: Date) {
  router.replace({
    query: {
      ...route.query,
      date: formatDateLocal(normalizeDate(date)),
    },
  })
}

function selectCalendarDate(date: Date) {
  updateSelectedDate(date)
  isCalendarOpen.value = false
}

function changeMonth(amount: number) {
  const next = new Date(selectedDate.value)
  next.setDate(1)
  next.setMonth(next.getMonth() + amount)
  updateSelectedDate(next)
}

function changeYear(amount: number) {
  const next = new Date(selectedDate.value)
  next.setDate(1)
  next.setFullYear(next.getFullYear() + amount)
  updateSelectedDate(next)
}

function goPrevMonth() {
  changeMonth(-1)
}

function goNextMonth() {
  changeMonth(1)
}

function goPrevYear() {
  changeYear(-1)
}

function goNextYear() {
  changeYear(1)
}

function toggleCalendarDropdown() {
  isCalendarOpen.value = !isCalendarOpen.value
}

function closeCalendarDropdown() {
  isCalendarOpen.value = false
}

function toggleGenerateMenu() {
  isGenerateMenuOpen.value = !isGenerateMenuOpen.value
}

function closeGenerateMenu() {
  isGenerateMenuOpen.value = false
}

function goToTab(tab: (typeof tabs)[number]) {
  router.push({
    name: tab.routeName,
    query: route.query,
  })
}

function getTabClass(key: TabKey) {
  return activeTab.value === key
    ? 'border-[#999999] text-[#171717]'
    : 'border-transparent text-[#737373] hover:text-[#171717]'
}

function handleDocumentClick(event: MouseEvent) {
  const target = event.target as Node

  if (
    calendarDropdownRef.value &&
    !calendarDropdownRef.value.contains(target)
  ) {
    closeCalendarDropdown()
  }

  if (generateMenuRef.value && !generateMenuRef.value.contains(target)) {
    closeGenerateMenu()
  }
}

onMounted(() => {
  document.addEventListener('click', handleDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleDocumentClick)
})
</script>

<template>
  <div class="w-full bg-white">
    <div
      class="flex w-full items-center gap-5 border-b border-[#e5e5e5] bg-white py-0 pl-8 pr-6 box-border text-left text-[14px] font-inter"
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
            <img :src="tab.icon" class="h-5 w-5 object-contain" :alt="tab.label" />
            <div class="leading-5 font-medium">{{ tab.label }}</div>
          </div>
        </div>
      </div>

      <div ref="calendarDropdownRef" class="relative">
        <div
          class="flex w-[236px] items-center gap-1 rounded-md border border-[#d4d4d4] bg-white px-2 py-1 box-border text-[#404040]"
        >
          <img :src="Calendar" class="h-5 w-5 object-contain shrink-0" alt="Calendar" />

          <button
            type="button"
            class="flex flex-1 items-center justify-between gap-1 rounded-md px-0.5 py-0.5 text-left hover:bg-[#f5f5f5] cursor-pointer"
            @click.stop="toggleCalendarDropdown"
          >
            <div class="truncate leading-5 font-medium">{{ navbarWeekRange }}</div>
            <img
              :src="DropDownBlack"
              class="h-4 w-4 object-contain shrink-0"
              alt="Dropdown"
            />
          </button>
        </div>

        <div
          v-if="isCalendarOpen"
          class="absolute right-0 top-full z-50 mt-2 w-[272px] rounded-xl border border-[#d9d9d9] bg-white p-3 text-center shadow-[0px_10px_15px_-3px_rgba(0,0,0,0.1),0px_4px_6px_-2px_rgba(0,0,0,0.05)]"
        >
          <div class="w-full">
            <div class="flex items-center">
              <button
                type="button"
                class="rounded-md p-1 hover:bg-[#f5f5f5] cursor-pointer"
                @click.stop="goPrevYear"
              >
                <img :src="ChevronsLeft" class="h-4 w-4" alt="Previous year" />
              </button>

              <button
                type="button"
                class="rounded-md p-1 hover:bg-[#f5f5f5] cursor-pointer"
                @click.stop="goPrevMonth"
              >
                <img :src="ChevronLeft" class="h-4 w-4" alt="Previous month" />
              </button>

              <div class="flex-1 text-[12px] font-medium leading-4 text-[#525252]">
                {{ displayMonthLabel }}
              </div>

              <button
                type="button"
                class="rounded-md p-1 hover:bg-[#f5f5f5] cursor-pointer"
                @click.stop="goNextMonth"
              >
                <img :src="ChevronRight" class="h-4 w-4" alt="Next month" />
              </button>

              <button
                type="button"
                class="rounded-md p-1 hover:bg-[#f5f5f5] cursor-pointer"
                @click.stop="goNextYear"
              >
                <img :src="ChevronsRight" class="h-4 w-4" alt="Next year" />
              </button>
            </div>

            <div class="pt-2">
              <div class="flex w-56 items-center pb-1 text-[10px] text-[#5c01d5]">
                <div
                  v-for="label in weekdayLabels"
                  :key="label"
                  class="w-8 leading-[15px] font-medium flex items-center justify-center shrink-0"
                >
                  {{ label }}
                </div>
              </div>

              <div class="w-56 flex flex-col items-start text-[12px] text-[#525252]">
                <div
                  v-for="(row, rowIndex) in calendarRows"
                  :key="`row-${rowIndex}`"
                  class="self-stretch flex items-center"
                >
                  <button
                    v-for="cell in row"
                    :key="cell.key"
                    type="button"
                    class="h-8 w-8 flex flex-col items-center justify-center p-2 box-border text-center transition"
                    :class="[
                      cell.isInSelectedWeek ? 'bg-[#5c01d533]' : '',
                      cell.isWeekStart ? 'rounded-l-full' : '',
                      cell.isWeekEnd ? 'rounded-r-full' : '',
                      cell.isSelected
                        ? 'text-[#5c01d5] font-bold'
                        : cell.isInSelectedWeek
                          ? 'text-[#737373] font-medium'
                          : !cell.isCurrentMonth
                            ? 'text-[#a3a3a3]'
                            : 'text-[#525252] font-medium',
                    ]"
                    @click.stop="selectCalendarDate(cell.date)"
                  >
                    <div class="self-stretch leading-4 cursor-pointer">
                      {{ cell.dayNumber }}
                    </div>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="relative flex items-center text-white">
        <button
          type="button"
          class="flex items-center rounded-l-md bg-[#5c01d5] py-1.5 px-2.5 cursor-pointer"
          @click="$emit('open-generate-popup')"
        >
          <div class="leading-5 font-medium">
            Generate Scheduler
          </div>
        </button>

        <button
          type="button"
          class="flex items-center justify-center rounded-r-md border-l border-white/20 bg-[#5c01d5] p-1.5"
          @click.stop="toggleGenerateMenu"
        >
          <img
            :src="isGenerateMenuOpen ? DropUp : DropDownWhite"
            class="h-5 w-5 object-contain"
            :alt="isGenerateMenuOpen ? 'Collapse menu' : 'Expand menu'"
          />
        </button>

        <div
          v-if="isGenerateMenuOpen"
          class="absolute right-0 top-full z-50 mt-1 w-44 rounded-xl border border-[#e5e5e5] bg-white p-1 shadow-[0_8px_24px_rgba(0,0,0,0.12)]"
        >
          <button
            type="button"
            class="flex w-full items-center gap-2 rounded-md p-2 text-left text-base text-[#000000] transition hover:bg-[#eeeeee] cursor-pointer"
            @click.stop="openTimeConfig"
          >
          <img :src="GenerateConfigTime" class="h-5 w-5" alt="ConfigTime" />
            <div class="leading-6">Config time</div>
          </button>

          <button
            type="button"
            class="mt-1 flex w-full items-center gap-2 rounded-md p-2 text-left text-base text-[#000000] transition hover:bg-[#eeeeee] cursor-pointer"
            @click="$emit('open-subject-list')"
          >
          <img :src="TaskSquareIcon" class="h-5 w-5" alt="SubjectList" />
            <div class="leading-6">Subject List</div>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>