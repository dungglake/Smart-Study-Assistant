<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ChevronLeft,
  ChevronRight,
  RatioDotPurple,
  RatioDotYellow,
  RatioDotRed,
  ButtonAdd,
} from '@/icons'

const router = useRouter()
const route = useRoute()

function formatDateLocal(date: Date): string {
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

function parseDateFromQuery(value: unknown): Date | null {
  if (typeof value !== 'string' || !value) return null
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return null
  parsed.setHours(0, 0, 0, 0)
  return parsed
}

function getWeekBlockRange(date: Date) {
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

function getInitialDate(): Date {
  const queryDate = parseDateFromQuery(route.query.date)
  if (queryDate) {
    return getWeekBlockRange(queryDate).start
  }

  const fallback = new Date()
  fallback.setHours(0, 0, 0, 0)
  return getWeekBlockRange(fallback).start
}

function syncDateToQuery(date: Date) {
  const formatted = formatDateLocal(getWeekBlockRange(date).start)

  if (route.query.date === formatted) return

  router.replace({
    query: {
      ...route.query,
      date: formatted,
    },
  })
}

const initialDate = getInitialDate()

const currentBaseDate = ref(initialDate)
const selectedDate = ref(formatDateLocal(initialDate))

const dayLabels = ['SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA']

const weekRange = computed(() => getWeekBlockRange(currentBaseDate.value))
const weekStart = computed(() => weekRange.value.start)
const weekEnd = computed(() => weekRange.value.end)

const visibleWeekDays = computed(() => {
  const start = new Date(weekStart.value)
  const end = new Date(weekEnd.value)
  const selected = selectedDate.value

  const days = []
  const cursor = new Date(start)

  while (cursor <= end) {
    const fullDate = formatDateLocal(cursor)

    days.push({
      day: dayLabels[cursor.getDay()],
      date: `${cursor.getDate()}`.padStart(2, '0'),
      fullDate,
      isSunday: cursor.getDay() === 0,
      isMuted: false,
      isSelected: fullDate === selected,
    })

    cursor.setDate(cursor.getDate() + 1)
  }

  return days
})

const scheduleHeaderDays = computed(() =>
  visibleWeekDays.value.map((item) => ({
    ...item,
    weekend: item.day === 'SU' || item.day === 'SA',
    active: item.isSelected,
    shortDay:
      item.day === 'MO'
        ? 'Mon'
        : item.day === 'TU'
          ? 'Tue'
          : item.day === 'WE'
            ? 'Wed'
            : item.day === 'TH'
              ? 'Thu'
              : item.day === 'FR'
                ? 'Fri'
                : item.day === 'SA'
                  ? 'Sat'
                  : 'Sun',
  }))
)

const monthYearLabel = computed(() => {
  return currentBaseDate.value.toLocaleDateString('en-US', {
    month: 'long',
    year: 'numeric',
  })
})

const weekRangeLabel = computed(() => {
  const format = (date: Date) =>
    date.toLocaleDateString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    })

  return `${format(weekStart.value)} - ${format(weekEnd.value)}`
})

function selectDate(fullDate: string) {
  selectedDate.value = fullDate

  const clicked = new Date(fullDate)
  clicked.setHours(0, 0, 0, 0)

  currentBaseDate.value = getWeekBlockRange(clicked).start
  syncDateToQuery(clicked)
}

function goPrevWeek() {
  const previousBlockDate = new Date(weekStart.value)
  previousBlockDate.setDate(previousBlockDate.getDate() - 1)
  previousBlockDate.setHours(0, 0, 0, 0)

  const nextStart = getWeekBlockRange(previousBlockDate).start
  currentBaseDate.value = nextStart
  selectedDate.value = formatDateLocal(nextStart)
  syncDateToQuery(nextStart)
}

function goNextWeek() {
  const nextBlockDate = new Date(weekEnd.value)
  nextBlockDate.setDate(nextBlockDate.getDate() + 1)
  nextBlockDate.setHours(0, 0, 0, 0)

  const nextStart = getWeekBlockRange(nextBlockDate).start
  currentBaseDate.value = nextStart
  selectedDate.value = formatDateLocal(nextStart)
  syncDateToQuery(nextStart)
}

watch(
  () => route.query.date,
  (newValue) => {
    const parsed = parseDateFromQuery(newValue)
    if (!parsed) return

    const rangeStart = getWeekBlockRange(parsed).start
    const formatted = formatDateLocal(rangeStart)

    if (formatted !== formatDateLocal(currentBaseDate.value)) {
      currentBaseDate.value = rangeStart
    }

    if (
      !visibleWeekDays.value.some((item) => item.fullDate === selectedDate.value)
    ) {
      selectedDate.value = formatted
    } else if (formatDateLocal(currentBaseDate.value) !== formatted) {
      selectedDate.value = formatted
    }
  },
  { immediate: true }
)

const hours = Array.from({ length: 17 }, (_, i) => {
  const hour = i + 7
  const suffix = hour < 12 ? 'AM' : 'PM'
  const displayHour = hour === 12 ? 12 : hour > 12 ? hour - 12 : hour
  return `${displayHour}:00 ${suffix}`
})
</script>

<template>
  <div class="flex flex-col gap-6 px-8 pb-6 pt-8">
    <section class="grid grid-cols-12 gap-6">
      <div class="col-span-6 rounded-[24px] bg-white p-6">
        <div class="mb-6 flex items-center justify-between">
          <div class="text-[18px] font-semibold leading-7 text-[#171717]">
            Subject Ratios
          </div>
        </div>

        <div class="flex min-h-[560px] flex-col items-center justify-center rounded-[16px] border border-dashed border-[#e5e5e5] bg-[#fafafa] px-6 text-center">
          <div class="text-[16px] font-semibold text-[#171717]">
            No ratio data yet
          </div>
          <p class="mt-2 text-sm leading-6 text-[#737373]">
            Subject ratio chart for the selected week will appear here after the API is connected.
          </p>

          <div class="mt-8 flex items-center gap-6 text-black">
            <div class="flex items-center gap-2">
              <img :src="RatioDotPurple" class="h-5 w-5" alt="purple" />
              <div class="leading-6">UI/UX Design</div>
            </div>
            <div class="flex items-center gap-2">
              <img :src="RatioDotYellow" class="h-5 w-5" alt="yellow" />
              <div class="leading-6">UX Foundations</div>
            </div>
            <div class="flex items-center gap-2">
              <img :src="RatioDotRed" class="h-5 w-5" alt="red" />
              <div class="leading-6">Marketing</div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-span-6 flex flex-col gap-8 rounded-[24px] bg-white p-6">
        <div class="flex items-center justify-center gap-3">
          <button type="button" class="cursor-pointer hover:bg-gray-100" @click="goPrevWeek">
            <img :src="ChevronLeft" class="h-5 w-5" alt="prev" />
          </button>

          <div class="flex flex-col items-center">
            <div class="text-base leading-6 text-[#171717]">
              {{ monthYearLabel }}
            </div>
          </div>

          <button type="button" class="cursor-pointer hover:bg-gray-100" @click="goNextWeek">
            <img :src="ChevronRight" class="h-5 w-5" alt="next" />
          </button>
        </div>

        <div class="flex items-start gap-4 overflow-hidden border-b border-[#e5e5e5] pb-6 text-[#404040]">
          <button
            v-for="item in visibleWeekDays"
            :key="item.fullDate"
            type="button"
            class="flex flex-1 cursor-pointer justify-center text-center"
            @click="selectDate(item.fullDate)"
          >
            <div
              class="inline-flex flex-col items-center gap-2 rounded-[999px] px-2.5 py-4 transition hover:bg-violet-50"
              :class="[
                item.isMuted ? 'opacity-25' : '',
                item.isSelected ? 'bg-amber-50' : '',
              ]"
            >
              <div class="flex items-center justify-center">
                <b
                  class="leading-6"
                  :class="item.isSunday ? 'text-[#ef4444]' : 'text-[#404040]'"
                >
                  {{ item.day }}
                </b>
              </div>

              <div
                class="flex h-10 w-10 items-center justify-center rounded-full text-sm leading-6 transition"
                :class="
                  item.isSelected
                    ? 'bg-[#5c01d5] text-white'
                    : item.isSunday
                      ? 'bg-[#f5f5f5] text-[#ef4444] font-bold'
                      : 'bg-[#f5f5f5] text-[#171717]'
                "
              >
                {{ item.date }}
              </div>
            </div>
          </button>
        </div>

        <div class="flex items-center justify-between">
          <div class="text-[18px] font-semibold leading-7 text-[#171717]">
            Today's Schedule &amp; Tasks
          </div>
        </div>

        <div
          class="flex min-h-[320px] flex-col items-center justify-center rounded-[16px] border border-dashed border-[#e5e5e5] bg-[#fafafa] px-6 text-center"
        >
          <div class="text-[16px] font-semibold text-[#171717]">
            No tasks for this week
          </div>
          <p class="mt-2 text-sm leading-6 text-[#737373]">
            Schedule and task items for the selected week will be shown here after the API is ready.
          </p>
        </div>
      </div>
    </section>

    <section class="rounded-[24px] bg-white p-6">
      <div class="mb-6 flex items-center justify-between">
        <div class="text-[18px] font-semibold leading-7 text-[#171717]">
          Schedule
        </div>
      </div>

      <div class="overflow-hidden rounded-[20px] border border-[#e5e5e5] bg-white">
        <div
          class="border-b border-[#e5e5e5]"
          :style="{
            display: 'grid',
            gridTemplateColumns: `110px repeat(${scheduleHeaderDays.length}, minmax(0, 1fr))`,
            height: '72px',
          }"
        >
          <div class="flex items-center justify-center border-r border-[#e5e5e5] text-[14px] font-medium text-[#525252]">
            GMT+7
          </div>

          <div
            v-for="item in scheduleHeaderDays"
            :key="`${item.day}-${item.date}`"
            class="flex items-center justify-center gap-2 border-r border-[#e5e5e5] last:border-r-0"
          >
            <b
              class="text-[16px] leading-6"
              :class="item.day === 'SU' ? 'text-[#ef4444]' : 'text-[#404040]'"
            >
              {{ item.shortDay }}
            </b>

            <div
              class="flex h-8 min-w-8 items-center justify-center rounded-full px-2 text-[16px] font-medium leading-6"
              :class="
                item.active
                  ? 'bg-[#ede9fe] text-[#5c01d5]'
                  : item.day === 'SU'
                    ? 'bg-[#fafafa] text-[#ef4444]'
                    : 'bg-[#fafafa] text-[#525252]'
              "
            >
              {{ Number(item.date) }}
            </div>
          </div>
        </div>

        <div class="relative">
          <div
            v-for="hour in hours"
            :key="hour"
            :style="{
              display: 'grid',
              gridTemplateColumns: `110px repeat(${scheduleHeaderDays.length}, minmax(0, 1fr))`,
              height: '80px',
            }"
          >
            <div class="flex items-start justify-center border-r border-[#e5e5e5] pt-4 text-[14px] leading-5 text-[#525252]">
              {{ hour }}
            </div>

            <div
              v-for="item in scheduleHeaderDays"
              :key="`${item.fullDate}-${hour}`"
              class="group relative border-r border-dashed border-b border-[#e9e9e9] last:border-r-0"
              :class="item.weekend ? 'bg-[#fcfcfc]' : 'bg-white'"
            >
              <button
                type="button"
                class="group-hover:flex absolute bottom-1 right-1 z-[2] hidden h-6 w-6 cursor-pointer items-center justify-center rounded-md bg-white transition hover:bg-[#f8f5ff]"
                :aria-label="`Add task on ${item.fullDate} at ${hour}`"
              >
                <img :src="ButtonAdd" alt="add" class="h-5 w-5 object-contain" />
              </button>
            </div>
          </div>

          <div class="pointer-events-none absolute inset-0 flex items-center justify-center">
            <div class="rounded-[16px] border border-dashed border-[#e5e5e5] bg-white/90 px-6 py-5 text-center shadow-sm">
              <div class="text-[16px] font-semibold text-[#171717]">
                No schedule items yet
              </div>
              <p class="mt-2 text-sm leading-6 text-[#737373]">
                Subject blocks will appear here after you add classes or tasks.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>