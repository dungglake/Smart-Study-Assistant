<script setup lang="ts">
import { ChevronLeft, ChevronRight } from '@/icons'

const calendarDays = [
  { label: 'Mon', date: '29', muted: true },
  { label: 'Tue', date: '30', muted: true },
  { label: 'Wed', date: '31', muted: true },
  { label: 'Thu', date: '01' },
  { label: 'Fri', date: '02' },
  { label: 'Sat', date: '03', active: true },
  { label: 'Sun', date: '04', sunday: true },
]
</script>

<template>
  <div class="px-8 pb-6 pt-8">
    <div class="rounded-[24px] bg-white p-6">
      <div class="mb-6 flex items-center justify-between">
        <div class="text-[18px] font-semibold leading-7 text-[#171717]">
          Calendar
        </div>

        <div class="flex items-center gap-3">
          <button type="button">
            <img :src="ChevronLeft" class="h-5 w-5" alt="prev" />
          </button>
          <div class="text-base leading-6 text-[#171717]">January 2026</div>
          <button type="button">
            <img :src="ChevronRight" class="h-5 w-5" alt="next" />
          </button>
        </div>
      </div>

      <div class="grid grid-cols-7 gap-4">
        <div
          v-for="day in calendarDays"
          :key="`${day.label}-${day.date}`"
          class="rounded-[16px] border border-[#e5e5e5] p-4 text-center"
          :class="[
            day.active ? 'bg-[#f8f5ff] border-[#d7c8ff]' : 'bg-white',
            day.muted ? 'opacity-50' : '',
          ]"
        >
          <div
            class="text-sm font-semibold"
            :class="day.sunday ? 'text-[#ef4444]' : 'text-[#404040]'"
          >
            {{ day.label }}
          </div>
          <div
            class="mt-3 inline-flex h-10 w-10 items-center justify-center rounded-full text-sm font-medium"
            :class="day.active ? 'bg-[#5c01d5] text-white' : 'bg-[#f5f5f5] text-[#171717]'"
          >
            {{ day.date }}
          </div>

          <div class="mt-4 rounded-[12px] border border-dashed border-[#e5e5e5] bg-[#fafafa] px-3 py-6 text-xs text-[#737373]">
            No events yet
          </div>
        </div>
      </div>
    </div>
  </div>
</template>