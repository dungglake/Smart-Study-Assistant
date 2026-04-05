<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  SchedulerBannerDocs,
  BannerGlow,
  ChevronLeft,
  ChevronRight,
  RatioDotPurple,
  RatioDotYellow,
  RatioDotRed,
} from '@/icons'

const currentBaseDate = ref(new Date(2026, 0, 1)) // January 1, 2026
const selectedDate = ref(formatDateLocal(new Date(2026, 0, 3))) // chọn sẵn Jan 3, 2026

const dayLabels = ['SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA']

function formatDateLocal(date: Date): string {
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

function getStartOfWeekMonday(date: Date): Date {
  const d = new Date(date)
  const day = d.getDay() // 0 = Sun, 1 = Mon
  const diff = day === 0 ? -6 : 1 - day
  d.setDate(d.getDate() + diff)
  d.setHours(0, 0, 0, 0)
  return d
}

const weekStart = computed(() => getStartOfWeekMonday(currentBaseDate.value))

const visibleWeekDays = computed(() => {
  const start = new Date(weekStart.value)
  const currentMonth = currentBaseDate.value.getMonth()
  const selected = selectedDate.value

  return Array.from({ length: 7 }, (_, i) => {
    const date = new Date(start)
    date.setDate(start.getDate() + i)

    const fullDate = formatDateLocal(date)

    return {
      day: dayLabels[date.getDay()],
      date: `${date.getDate()}`.padStart(2, '0'),
      fullDate,
      isSunday: date.getDay() === 0,
      isMuted: date.getMonth() !== currentMonth,
      isSelected: fullDate === selected,
    }
  })
})
const scheduleHeaderDays = computed(() =>
  visibleWeekDays.value.map((item) => ({
    ...item,
    weekend: item.day === 'SU' || item.day === 'SA',
    active: item.isSelected,
  }))
)
const monthYearLabel = computed(() => {
  return currentBaseDate.value.toLocaleDateString('en-US', {
    month: 'long',
    year: 'numeric',
  })
})

function selectDate(fullDate: string) {
  selectedDate.value = fullDate

  const clicked = new Date(fullDate)
  currentBaseDate.value = new Date(
    clicked.getFullYear(),
    clicked.getMonth(),
    clicked.getDate()
  )
}

function goPrevWeek() {
  const next = new Date(currentBaseDate.value)
  next.setDate(next.getDate() - 7)
  currentBaseDate.value = next

  const selected = new Date(selectedDate.value)
  selected.setDate(selected.getDate() - 7)
  selectedDate.value = formatDateLocal(selected)
}

function goNextWeek() {
  const next = new Date(currentBaseDate.value)
  next.setDate(next.getDate() + 7)
  currentBaseDate.value = next

  const selected = new Date(selectedDate.value)
  selected.setDate(selected.getDate() + 7)
  selectedDate.value = formatDateLocal(selected)
}

const hours = Array.from({ length: 24 }, (_, i) => {
  const hour = i
  const suffix = hour < 12 ? 'AM' : 'PM'
  const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour
  return `${displayHour}:00 ${suffix}`
})
</script>

<template>
  <div class="flex flex-col gap-6 px-8 pb-6 pt-8">
    <!-- Banner -->
    <section
      class="relative isolate flex h-[120px] items-center overflow-visible rounded-[24px] border border-[#cfc2ff] bg-white py-3 pl-6 pr-3 shadow-[inset_0_0_12px_rgba(92,1,213,0.10)]"
    >
      <img
        :src="BannerGlow"
        alt="glow"
        class="absolute right-0 top-1/2 z-[1] h-[120px] -translate-y-1/2 object-contain pointer-events-none"
      />
      <img
        :src="SchedulerBannerDocs"
        alt="docs"
        class="absolute right-30 top-1/2 z-[2] h-[152px] -translate-y-1/2 object-contain pointer-events-none"
      />

      <div class="relative z-10 flex flex-col items-start gap-2.5">
        <h2
          class="bg-[linear-gradient(90deg,#5c01d5,#6460f4)] bg-clip-text text-[20px] font-bold leading-7 text-transparent"
        >
          Create a smart timetable with Smart Scheduler
        </h2>

        <button
          type="button"
          class="cursor-pointer rounded-md bg-[#171717] px-2.5 py-1.5 text-sm font-medium leading-5 text-white"
        >
          Add classes &amp; tasks
        </button>
      </div>
    </section>

    <!-- Row 1 -->
    <section class="grid grid-cols-12 gap-6">
      <!-- Subject ratios -->
      <div class="col-span-6 rounded-[24px] bg-white p-6">
        <div class="mb-6 text-[18px] font-semibold leading-7 text-[#171717]">
          Subject Ratios
        </div>

        <div class="flex min-h-[560px] flex-col items-center justify-center rounded-[16px] border border-dashed border-[#e5e5e5] bg-[#fafafa] px-6 text-center">
          <div class="text-[16px] font-semibold text-[#171717]">
            No ratio data yet
          </div>
          <p class="mt-2 text-sm leading-6 text-[#737373]">
            Subject ratio chart will appear here after the API is connected.
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

      <!-- Calendar + Today -->
      <div class="col-span-6 flex flex-col gap-8 rounded-[24px] bg-white p-6">
        <div class="flex items-center justify-center gap-3">
          <button type="button" class="cursor-pointer" @click="goPrevWeek">
            <img :src="ChevronLeft" class="h-5 w-5" alt="prev" />
          </button>

          <div class="text-base leading-6 text-[#171717]">
            {{ monthYearLabel }}
          </div>

          <button type="button" class="cursor-pointer" @click="goNextWeek">
            <img :src="ChevronRight" class="h-5 w-5" alt="next" />
          </button>
        </div>

        <div class="flex items-start gap-4 overflow-hidden border-b border-[#e5e5e5] pb-6 text-[#404040]">
          <button
            v-for="item in visibleWeekDays"
            :key="item.fullDate"
            type="button"
            class="flex flex-1 justify-center text-center cursor-pointer"
            @click="selectDate(item.fullDate)"
          >
            <div
              class="inline-flex flex-col items-center gap-2 rounded-[999px] px-2.5 py-4 transition"
              :class="[
                item.isMuted ? 'opacity-25' : '',
                item.isSelected ? 'bg-[#fff7d6]' : '',
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

        <div class="text-[18px] font-semibold leading-7 text-[#171717]">
          Today's Schedule &amp; Tasks
        </div>

        <div
          class="flex min-h-[320px] flex-col items-center justify-center rounded-[16px] border border-dashed border-[#e5e5e5] bg-[#fafafa] px-6 text-center"
        >
          <div class="text-[16px] font-semibold text-[#171717]">
            No tasks for today
          </div>
          <p class="mt-2 text-sm leading-6 text-[#737373]">
            Today's schedule and tasks will be shown here after the API is ready.
          </p>
        </div>
      </div>
    </section>

    <!-- Row 2 -->
    <section class="rounded-[24px] bg-white p-6">
      <div class="mb-6 text-[18px] font-semibold leading-7 text-[#171717]">
        Schedule
      </div>

      <div class="overflow-hidden rounded-[12px] border border-[#e5e5e5]">
        <div class="flex h-16 items-center bg-white text-center text-[#404040]">
          <div class="flex h-full w-[100px] items-center justify-center border-r border-[#e5e5e5] text-xs">
            GMT+7
          </div>

          <div
            v-for="item in scheduleHeaderDays"
            :key="`${item.day}-${item.date}`"
            class="flex h-full flex-1 items-center justify-center gap-1 border-r border-[#e5e5e5]"
            :class="item.weekend ? 'bg-[#f5f5f5]' : ''"
          >
            <b class="leading-6">{{ item.day }}</b>
            <div
              class="rounded-full px-2 py-1 text-sm font-medium leading-5"
              :class="
                item.active
                  ? 'bg-[#ede9fe] text-[#5c01d5]'
                  : 'bg-[#f5f5f5] text-[#404040]'
              "
            >
              {{ item.date }}
            </div>
          </div>
        </div>

        <div class="relative h-[960px] overflow-hidden">
          <div
            v-for="hour in hours"
            :key="hour"
            class="relative flex h-16 items-center text-right text-xs text-[#737373]"
          >
            <div class="flex h-full w-[100px] items-center justify-center border-r border-[#e5e5e5]">
              <div class="w-[60px] leading-4">{{ hour }}</div>
            </div>

            <div class="h-full flex-1 border-r border-[#e5e5e5]"></div>
            <div class="h-full flex-1 border-r border-[#e5e5e5]"></div>
            <div class="h-full flex-1 border-r border-[#e5e5e5]"></div>
            <div class="h-full flex-1 border-r border-[#e5e5e5]"></div>
            <div class="h-full flex-1 border-r border-[#e5e5e5]"></div>
            <div class="h-full flex-1 border-r border-[#e5e5e5]"></div>
            <div class="h-full flex-1 border-r border-[#e5e5e5] bg-[#f5f5f5]"></div>

            <div class="absolute left-[100px] right-0 top-1/2 h-px -translate-y-1/2 bg-[#e5e5e5]"></div>
          </div>

          <div class="absolute inset-0 flex items-center justify-center">
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