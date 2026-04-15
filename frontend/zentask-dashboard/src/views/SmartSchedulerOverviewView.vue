<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import TimeConfigPanel from '@/components/scheduler/TimeConfigPanel.vue'
import SubjectListPanel from '@/components/scheduler/SubjectListPanel.vue'
import GenerateSchedulerPopup from '@/components/scheduler/GenerateSchedulerPopup.vue'
import {
  ChevronLeft,
  ChevronRight,
  RatioDotPurple,
  RatioDotYellow,
  RatioDotRed,
  ButtonAdd,
} from '@/icons'

type VisibleDay = {
  day: string
  date: string
  fullDate: string
  isSunday: boolean
  isSelected: boolean
}

const props = defineProps<{
  isTimeConfigOpen?: boolean
  isSubjectListOpen?: boolean
  isGeneratePopupOpen?: boolean
  generatedSummary?: any
  subjects?: any[]
}>()

const emit = defineEmits<{
  (e: 'close-time-config'): void
  (e: 'open-time-config'): void
  (e: 'open-subject-list'): void
  (e: 'close-subject-list'): void
  (e: 'save-subjects', payload: any[]): void
  (e: 'close-generate-popup'): void
  (e: 'generated-summary', payload: any): void
}>()

const router = useRouter()
const route = useRoute()

const dayLabels = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'] as const
const savedWeekConfigs = ref<Record<string, any>>({})

function handleSaveTimeConfig(payload: any) {
  savedWeekConfigs.value[payload.weekStart] = payload
  console.log('Saved week config:', payload)
  emit('close-time-config')
}

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

const selectedDate = computed(() => {
  const fromQuery = parseDateFromQuery(route.query.date)
  if (fromQuery) return fromQuery

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return today
})

const weekStart = computed(() => getStartOfWeekMonday(selectedDate.value))

const visibleWeekDays = computed<VisibleDay[]>(() => {
  const start = new Date(weekStart.value)

  return Array.from({ length: 7 }, (_, index) => {
    const date = new Date(start)
    date.setDate(start.getDate() + index)

    const fullDate = formatDateLocal(date)

    return {
      day: dayLabels[index] ?? 'MO',
      date: `${date.getDate()}`.padStart(2, '0'),
      fullDate,
      isSunday: date.getDay() === 0,
      isSelected: fullDate === formatDateLocal(selectedDate.value),
    }
  })
})

const scheduleHeaderDays = computed(() =>
  visibleWeekDays.value.map((item) => ({
    ...item,
    weekend: item.day === 'SA' || item.day === 'SU',
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

const monthYearLabel = computed(() =>
  selectedDate.value.toLocaleDateString('en-US', {
    month: 'long',
    year: 'numeric',
  })
)

function updateSelectedDate(date: Date) {
  router.replace({
    query: {
      ...route.query,
      date: formatDateLocal(normalizeDate(date)),
    },
  })
}

function selectDate(fullDate: string) {
  updateSelectedDate(new Date(fullDate))
}

function goPrevWeek() {
  const next = new Date(selectedDate.value)
  next.setDate(next.getDate() - 7)
  updateSelectedDate(next)
}

function goNextWeek() {
  const next = new Date(selectedDate.value)
  next.setDate(next.getDate() + 7)
  updateSelectedDate(next)
}

const selectedDaySummary = computed(() =>
  props.generatedSummary?.daily?.find((day: any) => day.date === formatDateLocal(selectedDate.value)) || null
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
    <div
      v-if="props.isGeneratePopupOpen"
      class="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 px-6"
    >
      <div class="w-[980px] max-w-full">
        <GenerateSchedulerPopup
          :open="true"
          :selected-date="formatDateLocal(selectedDate)"
          @close="emit('close-generate-popup')"
          @open-time-config="emit('close-generate-popup'); emit('open-time-config')"
          @open-subject-list="emit('close-generate-popup'); emit('open-subject-list')"
          @generated="emit('generated-summary', $event)"
        />
      </div>
    </div>
    <div
      v-if="props.isTimeConfigOpen"
      class="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 px-6"
    >
      <div class="w-[760px] max-w-full">
        <TimeConfigPanel
          :open="true"
          :selected-date="formatDateLocal(selectedDate)"
          @close="emit('close-time-config')"
          @save="handleSaveTimeConfig"
        />
      </div>
    </div>
    <div
      v-if="props.isSubjectListOpen"
      class="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 px-6"
    >
      <div class="w-[900px] max-w-full">
        <SubjectListPanel
          :open="true"
          :subjects="props.subjects || []"
          :week-start="formatDateLocal(weekStart)"
          @close="emit('close-subject-list')"
          @save="emit('save-subjects', $event)"
        />
      </div>
    </div>
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
          <button type="button" class="rounded-md p-1 hover:bg-gray-100" @click="goPrevWeek">
            <img :src="ChevronLeft" class="h-5 w-5" alt="prev" />
          </button>

          <div class="flex flex-col items-center">
            <div class="text-base leading-6 text-[#171717]">
              {{ monthYearLabel }}
            </div>
          </div>

          <button type="button" class="rounded-md p-1 hover:bg-gray-100" @click="goNextWeek">
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
              :class="item.isSelected ? 'bg-amber-50' : ''"
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
          v-if="selectedDaySummary?.assigned_subjects?.length"
          class="flex min-h-[320px] flex-col gap-3 rounded-[16px] border border-[#e5e5e5] bg-[#fafafa] p-4"
        >
          <div
            v-for="subject in selectedDaySummary.assigned_subjects"
            :key="`${selectedDaySummary.date}-${subject.id}-${subject.name}`"
            class="rounded-xl border border-[#d4d4d4] bg-white px-4 py-3 text-left"
          >
            <div class="text-[16px] font-semibold text-[#404040]">{{ subject.name }}</div>
            <div class="mt-1 text-sm text-[#737373]">Scheduled for {{ selectedDaySummary.weekday }}</div>
          </div>
        </div>

        <div
          v-else
          class="flex min-h-[320px] flex-col items-center justify-center rounded-[16px] border border-dashed border-[#e5e5e5] bg-[#fafafa] px-6 text-center"
        >
          <div class="text-[16px] font-semibold text-[#171717]">
            No tasks for this day
          </div>
          <p class="mt-2 text-sm leading-6 text-[#737373]">
            Apply scheduler to show subjects for the selected day.
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