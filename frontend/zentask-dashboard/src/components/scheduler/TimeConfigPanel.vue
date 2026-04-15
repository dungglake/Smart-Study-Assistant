<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { DeleteIcon, TickSquare } from '@/icons'

type TimeRange = {
  start: string
  end: string
}

type DayConfig = {
  dayKey: string
  label: string
  busyTimes: TimeRange[]
  numberOfSubjects: number
}

type WeekConfig = {
  weekStart: string
  days: DayConfig[]
}

type EditingTime = {
  dayKey: string
  index: number | null
  start: string
  end: string
  openList: 'start' | 'end' | null
}

const props = defineProps<{
  open: boolean
  selectedDate: string
  token?: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', value: WeekConfig): void
}>()

const weekDayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

const editingTime = ref<EditingTime | null>(null)
const isSaving = ref(false)
const errorMessage = ref('')

function formatDateLocal(date: Date): string {
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
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

function createEmptyWeekConfig(selectedDate: string): WeekConfig {
  const base = new Date(selectedDate)
  const weekStart = getStartOfWeekMonday(base)

  const days: DayConfig[] = Array.from({ length: 7 }, (_, index) => {
    const date = new Date(weekStart)
    date.setDate(weekStart.getDate() + index)

    return {
      dayKey: formatDateLocal(date),
      label: weekDayNames[index] ?? '',
      busyTimes: [],
      numberOfSubjects: 0,
    }
  })

  return {
    weekStart: formatDateLocal(weekStart),
    days,
  }
}

const form = reactive<WeekConfig>(createEmptyWeekConfig(props.selectedDate))

watch(
  () => props.selectedDate,
  (value) => {
    const next = createEmptyWeekConfig(value)
    form.weekStart = next.weekStart
    form.days.splice(0, form.days.length, ...next.days)
    editingTime.value = null
    errorMessage.value = ''
  },
  { immediate: true }
)

const timeOptions = computed(() => {
  const result: string[] = []
  for (let hour = 0; hour < 24; hour++) {
    for (const minute of [0, 30]) {
      const hh = `${hour}`.padStart(2, '0')
      const mm = `${minute}`.padStart(2, '0')
      result.push(`${hh}:${mm}`)
    }
  }
  result.push('23:59')
  return result
})

function getDay(dayKey: string) {
  return form.days.find((day) => day.dayKey === dayKey)
}

function openAddTime(day: DayConfig) {
  editingTime.value = {
    dayKey: day.dayKey,
    index: null,
    start: '07:30',
    end: '08:00',
    openList: null,
  }
}

function openEditTime(day: DayConfig, time: TimeRange, index: number) {
  editingTime.value = {
    dayKey: day.dayKey,
    index,
    start: time.start,
    end: time.end,
    openList: null,
  }
}

function sortBusyTimes(day: DayConfig) {
  day.busyTimes.sort((a, b) => a.start.localeCompare(b.start))
}

function saveEditingTime() {
  if (!editingTime.value) return

  const day = getDay(editingTime.value.dayKey)
  if (!day) return

  if (!editingTime.value.start || !editingTime.value.end) return

  const payload = {
    start: editingTime.value.start,
    end: editingTime.value.end,
  }

  if (editingTime.value.index === null) {
    day.busyTimes.push(payload)
  } else {
    day.busyTimes.splice(editingTime.value.index, 1, payload)
  }

  sortBusyTimes(day)
  editingTime.value = null
}

function removeTime(day: DayConfig, index: number) {
  day.busyTimes.splice(index, 1)
}

function setAllTime(day: DayConfig) {
  day.busyTimes = [{ start: '00:00', end: '23:59' }]
}

function clearAllTime(day: DayConfig) {
  day.busyTimes = []
}

function isAllTime(day: DayConfig) {
  return (
    day.busyTimes.length === 1 &&
    day.busyTimes[0]?.start === '00:00' &&
    day.busyTimes[0]?.end === '23:59'
  )
}

function getAccessToken() {
  return props.token || localStorage.getItem('access') || localStorage.getItem('accessToken') || ''
}

function buildPayload() {
  return {
    week_start: form.weekStart,
    busy: form.days.flatMap((day) =>
      day.busyTimes.map((time) => ({
        date: day.dayKey,
        start: time.start,
        end: time.end,
        type: time.start === '00:00' && time.end === '23:59' ? 'other' : 'other',
      }))
    ),
    day_configs: form.days.map((day) => ({
      date: day.dayKey,
      number_of_subjects: Number(day.numberOfSubjects) || 0,
    })),
  }
}

async function saveConfig() {
  isSaving.value = true
  errorMessage.value = ''

  try {
    const token = getAccessToken()
    const payload = buildPayload()

    const response = await fetch('/api/planner/week/autosave', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(payload),
    })

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      throw new Error(data?.detail || 'Failed to save time config.')
    }

    emit('save', JSON.parse(JSON.stringify(form)))
    emit('close')
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Failed to save time config.'
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <div
    v-if="open"
    class="w-full rounded-3xl bg-white shadow-[0px_0px_32px_rgba(0,0,0,0.12)] overflow-hidden"
  >
    <div class="flex items-center gap-3 border-b border-[#e5e5e5] px-5 py-3">
      <div class="flex-1 text-[18px] font-semibold leading-7 text-[#404040]">
        Time Config
      </div>

      <button
        type="button"
        class="rounded-md p-1.5 hover:bg-[#f5f5f5] cursor-pointer"
        @click="$emit('close')"
      >
        <img :src="DeleteIcon" class="h-5 w-5 object-contain" alt="Close" />
      </button>
    </div>

    <div class="px-5 pb-3 pt-0">
      <div class="grid grid-cols-[120px_1fr_164px] gap-3 border-b border-[#e5e5e5] py-3 text-[#404040]">
        <div></div>
        <div class="text-sm font-medium">Busy time</div>
        <div class="text-center text-sm font-medium">Number of subjects</div>
      </div>

      <div
        v-for="day in form.days"
        :key="day.dayKey"
        class="grid grid-cols-[120px_1fr_164px] gap-3 border-b border-[#e5e5e5] py-3"
      >
        <div class="flex items-start pt-2 text-[16px] font-medium text-[#404040]">
          {{ day.label }}
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <template v-if="isAllTime(day)">
            <button
              type="button"
              class="flex items-center gap-1.5 rounded-md border border-[#d4d4d4] bg-[#f5f5f5] px-2.5 py-1.5 text-sm font-medium text-[#404040]"
            >
              <span>All time</span>
              <img
                :src="DeleteIcon"
                class="h-5 w-5 object-contain cursor-pointer"
                alt="Clear"
                @click="clearAllTime(day)"
              />
            </button>
          </template>

          <template v-else>
            <button
              v-for="(time, index) in day.busyTimes"
              :key="`${day.dayKey}-${index}`"
              type="button"
              class="flex items-center gap-1.5 rounded-md border border-[#d4d4d4] bg-[#f5f5f5] px-2.5 py-1.5 text-sm font-medium text-[#404040]"
              @click="openEditTime(day, time, index)"
            >
              <span>{{ time.start }}-{{ time.end }}</span>

              <img
                :src="DeleteIcon"
                class="h-5 w-5 object-contain cursor-pointer"
                alt="Remove"
                @click.stop="removeTime(day, index)"
              />
            </button>

            <div
              v-if="editingTime?.dayKey === day.dayKey"
              class="relative flex items-center gap-3 rounded-[10px] bg-[#eef6ff] p-1 text-sm text-[#404040]"
            >
              <div class="flex items-center gap-1">
                <div class="relative">
                  <input
                    v-model="editingTime.start"
                    type="text"
                    class="w-20 rounded-md border border-[#d4d4d4] bg-[#f5f5f5] px-2.5 py-1.5 text-center font-medium outline-none"
                    @focus="editingTime.openList = 'start'"
                  />

                  <div
                    v-if="editingTime.openList === 'start'"
                    class="absolute left-0 top-[44px] z-50 w-[88px] rounded-md border border-[#d4d4d4] bg-[#f5f5f5] p-1 shadow-lg"
                  >
                    <div class="time-scroll max-h-[220px] overflow-y-auto">
                      <button
                        v-for="option in timeOptions"
                        :key="`start-${option}`"
                        type="button"
                        class="mb-1 flex w-full items-center justify-center rounded-[4px] px-2 py-1 text-sm leading-5 text-[#404040]"
                        :class="editingTime.start === option ? 'bg-[#e2e8f0] font-medium' : 'bg-transparent hover:bg-[#e2e8f0]'"
                        @click="editingTime.start = option; editingTime.openList = null"
                      >
                        <span class="w-full text-left">{{ option }}</span>
                      </button>
                    </div>
                  </div>
                </div>

                <div class="font-medium text-black">-</div>

                <div class="relative">
                  <input
                    v-model="editingTime.end"
                    type="text"
                    class="w-20 rounded-md border border-[#d4d4d4] bg-[#f5f5f5] px-2.5 py-1.5 text-center font-medium outline-none"
                    @focus="editingTime.openList = 'end'"
                  />

                  <div
                    v-if="editingTime.openList === 'end'"
                    class="absolute left-0 top-[44px] z-50 w-[88px] rounded-md border border-[#d4d4d4] bg-[#f5f5f5] p-1 shadow-lg"
                  >
                    <div class="time-scroll max-h-[220px] overflow-y-auto">
                      <button
                        v-for="option in timeOptions"
                        :key="`end-${option}`"
                        type="button"
                        class="mb-1 flex w-full items-center justify-center rounded-[4px] px-2 py-1 text-sm leading-5 text-[#404040]"
                        :class="editingTime.end === option ? 'bg-[#e2e8f0] font-medium' : 'bg-transparent hover:bg-[#e2e8f0]'"
                        @click="editingTime.end = option; editingTime.openList = null"
                      >
                        <span class="w-full text-left">{{ option }}</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <button
                type="button"
                class="flex items-center gap-1.5 rounded-md bg-[#5c01d5] px-2.5 py-1.5 text-sm font-medium text-white cursor-pointer"
                @click="saveEditingTime"
              >
                <img :src="TickSquare" class="h-5 w-5 object-contain" alt="Save" />
                <span>Save</span>
              </button>
            </div>

            <button
              v-else
              type="button"
              class="rounded-md px-2.5 py-1.5 text-sm font-medium text-[#737373] hover:bg-[#f5f5f5] cursor-pointer"
              @click="openAddTime(day)"
            >
              + Add time
            </button>

            <button
              type="button"
              class="rounded-md px-2.5 py-1.5 text-sm font-medium text-[#5c01d5] hover:bg-[#f8f5ff] cursor-pointer"
              @click="setAllTime(day)"
            >
              Set all time
            </button>
          </template>
        </div>

        <div class="flex items-start justify-center pt-1">
          <input
            v-model.number="day.numberOfSubjects"
            type="number"
            min="0"
            class="w-[60px] rounded-md border border-[#d4d4d4] px-3 py-1.5 text-center text-sm font-medium text-[#404040] outline-none"
          />
        </div>
      </div>

      <div v-if="errorMessage" class="pt-3 text-sm text-red-500">
        {{ errorMessage }}
      </div>

      <div class="flex justify-end pt-4">
        <button
          type="button"
          class="rounded-md bg-[#5c01d5] px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60 hover:bg-[#4c01b2] transition-colors cursor-pointer"
          :disabled="isSaving"
          @click="saveConfig"
        >
          {{ isSaving ? 'Saving...' : 'Save' }}
        </button>
      </div>
    </div>
  </div>
</template>
<style scoped>
input[type='number']::-webkit-outer-spin-button,
input[type='number']::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

input[type='number'] {
  -moz-appearance: textfield;
}

.time-scroll::-webkit-scrollbar {
  width: 3px;
}

.time-scroll::-webkit-scrollbar-thumb {
  background: #8c8c8c;
  border-radius: 999px;
}

.time-scroll::-webkit-scrollbar-track {
  background: transparent;
}
</style>
