<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  DeleteIcon,
  TickSquare,
  GenerateConfigTime,
  ButtonAdd,
  WarningIcon,
} from '@/icons'
import { authJson } from '@/api/authFetch'

type DaySummary = {
  date: string
  weekday: string
  assigned_subjects: { id: number | null; name: string }[]
  scheduled_count: number
  target_count: number
  busy_all_day: boolean
}

type WeekSummary = {
  week_start: string
  total_scheduled_subjects: number
  total_subjects_in_list: number
  daily: DaySummary[]
}

type GenerateWarning = {
  type: string
  date?: string
  subject_id?: number
  subject_name?: string
  required_minutes?: number
  available_minutes?: number
  message: string
}

type ConfirmTarget = 'config-time' | 'subject-list'

const props = defineProps<{
  open: boolean
  selectedDate: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'open-time-config'): void
  (e: 'open-subject-list'): void
  (e: 'generated', payload: WeekSummary): void
  (e: 'applied', payload: WeekSummary): void
}>()

const loading = ref(false)
const applying = ref(false)
const errorMessage = ref('')
const summary = ref<WeekSummary | null>(null)
const generateWarnings = ref<GenerateWarning[]>([])
const hasApplied = ref(false)
const confirmPopup = ref<ConfirmTarget | null>(null)

const confirmCopy = computed(() => {
  if (confirmPopup.value === 'subject-list') {
    return {
      title: 'Access Add subject',
      message: 'Your data will not be saved. Are you sure you want to access Add subject?',
    }
  }

  return {
    title: 'Access Config time',
    message: 'Your data will not be saved. Are you sure you want to access Config time?',
  }
})

function normalizeDate(date: Date): Date {
  const next = new Date(date)
  next.setHours(0, 0, 0, 0)
  return next
}

function formatDateLocal(date: Date): string {
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

function getStartOfWeekMonday(date: Date): Date {
  const next = normalizeDate(date)
  const day = next.getDay()
  const diff = day === 0 ? -6 : 1 - day
  next.setDate(next.getDate() + diff)
  return next
}

const weekStart = computed(() => {
  const base = new Date(props.selectedDate)
  return formatDateLocal(getStartOfWeekMonday(base))
})

async function previewScheduler() {
  if (!props.open) return

  loading.value = true
  errorMessage.value = ''
  generateWarnings.value = []
  hasApplied.value = false

  try {
    const data = await authJson('/api/planner/plan/preview-week', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ week_start: weekStart.value }),
    })

    summary.value = data?.summary || null
    generateWarnings.value = data?.warnings || []
    hasApplied.value = false

    if (data?.summary) {
      emit('generated', data.summary)
    }
  } catch (error: any) {
    summary.value = null
    errorMessage.value = error?.message || 'Cannot preview scheduler.'
  } finally {
    loading.value = false
  }
}

async function applyScheduler() {
  applying.value = true
  errorMessage.value = ''
  generateWarnings.value = []

  try {
    const data = await authJson('/api/planner/plan/apply-week', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ week_start: weekStart.value }),
    })

    summary.value = data?.summary || null
    generateWarnings.value = data?.warnings || []
    hasApplied.value = true

    if (data?.summary) {
      emit('generated', data.summary)
      emit('applied', data.summary)
    }
    window.dispatchEvent(new CustomEvent('planner-plan-updated', {
      detail: { weekStart: weekStart.value }
    }))
  } catch (error: any) {
    errorMessage.value = error?.message || 'Cannot apply scheduler.'
  } finally {
    applying.value = false
  }
}

function requestOpenTimeConfig() {
  if (!hasApplied.value) {
    confirmPopup.value = 'config-time'
    return
  }
  emit('open-time-config')
}

function requestOpenSubjectList() {
  if (!hasApplied.value) {
    confirmPopup.value = 'subject-list'
    return
  }
  emit('open-subject-list')
}

function confirmAccess() {
  const target = confirmPopup.value
  confirmPopup.value = null

  if (target === 'config-time') {
    emit('open-time-config')
    return
  }

  if (target === 'subject-list') {
    emit('open-subject-list')
  }
}

function cancelAccess() {
  confirmPopup.value = null
}

watch(
  () => [props.open, props.selectedDate],
  ([open]) => {
    if (open) {
      confirmPopup.value = null
      previewScheduler()
    }
  },
  { immediate: true }
)
</script>

<template>
    <Teleport to="body">
      <div
        v-if="open && confirmPopup"
        class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/40 px-4"
      >
        <div class="w-full max-w-[620px] rounded-lg bg-[#d99a12] p-4 text-base text-white shadow-xl">
          <div class="flex items-start gap-3">
            <img :src="WarningIcon" class="mt-0.5 h-5 w-5 object-contain" alt="Warning" />

            <div class="flex-1">
              <div class="font-semibold leading-6">
                {{ confirmCopy.title }}
              </div>

              <div class="mt-1 leading-6 text-white/95">
                {{ confirmCopy.message }}
              </div>

              <div class="mt-3 flex items-center gap-2 text-sm">
                <button
                  type="button"
                  class="h-8 min-w-[72px] rounded-md bg-black px-3 font-medium text-white hover:bg-[#262626] cursor-pointer"
                  @click="confirmAccess"
                >
                  Sure
                </button>

                <button
                  type="button"
                  class="h-8 min-w-[72px] rounded-md border border-[#d4d4d4] bg-white px-3 font-medium text-[#404040] hover:bg-[#f5f5f5] cursor-pointer"
                  @click="cancelAccess"
                >
                  Cancel
                </button>
              </div>
            </div>

            <button
              type="button"
              class="rounded p-0.5 hover:bg-white/15 cursor-pointer"
              @click="cancelAccess"
            >
              <img :src="DeleteIcon" class="h-6 w-6 object-contain brightness-0 invert" alt="Close" />
            </button>
          </div>
        </div>
      </div>
    </Teleport>
    <div
      v-if="open && !confirmPopup"
      class="relative w-full rounded-3xl bg-white shadow-[0px_0px_32px_rgba(0,0,0,0.12)] flex max-h-[88vh] min-h-[220px] flex-col overflow-hidden"
    >
    <div class="flex items-center gap-3 border-b border-[#e5e5e5] px-5 py-3">
      <div class="flex-1 text-[18px] font-semibold leading-7 text-[#404040]">
        Generate Scheduler
      </div>

      <button
        type="button"
        class="rounded-md p-1 cursor-pointer hover:bg-[#f5f5f5] transition-colors"
        @click="emit('close')"
      >
        <img :src="DeleteIcon" class="h-6 w-6 object-contain" alt="Close" />
      </button>
    </div>

    <div class="flex-1 overflow-y-auto px-5 pb-2 pt-5">
      <div v-if="loading" class="py-10 text-center text-sm text-[#737373]">
        Generating scheduler preview...
      </div>

      <template v-else>
        <div class="text-[18px] font-semibold leading-7 text-black">
          {{ summary?.total_scheduled_subjects || 0 }} subjects have been scheduled in your timetable:
        </div>

        <div
          v-if="errorMessage"
          class="mt-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600"
        >
          {{ errorMessage }}
        </div>

        <div
          v-if="generateWarnings.length"
          class="mt-3 flex flex-col gap-2 rounded-xl border border-[#f59e0b]/30 bg-[#fffbeb] p-3 text-sm text-[#92400e]"
        >
          <div
            v-for="warning in generateWarnings"
            :key="`${warning.type}-${warning.date || ''}-${warning.subject_id || ''}-${warning.message}`"
          >
            {{ warning.message }}
          </div>
        </div>

        <div class="mt-3 flex flex-col text-[14px] text-[#404040]">
          <div
            v-for="day in summary?.daily || []"
            :key="day.date"
            class="flex items-center gap-3 border-b border-[#e5e5e5] py-2 last:border-b-0"
          >
            <div class="w-[120px] px-3 py-2 text-[16px] leading-6 font-medium text-[#404040]">
              {{ day.weekday }}
            </div>

            <div class="flex-1 flex flex-wrap items-center gap-3">
              <template v-if="day.busy_all_day && day.assigned_subjects.length === 0">
                <div class="px-2.5 py-1.5 text-sm italic text-[#737373]">
                  Busy all day
                </div>
              </template>

              <template v-else-if="day.assigned_subjects.length > 0">
                <div
                  v-for="subject in day.assigned_subjects"
                  :key="`${day.date}-${subject.id}-${subject.name}`"
                  class="rounded-md border border-[#d4d4d4] bg-[#f5f5f5] px-2.5 py-1.5 text-sm font-medium text-[#404040]"
                >
                  {{ subject.name }}
                </div>

                <button
                  v-if="day.scheduled_count < day.target_count"
                  type="button"
                  class="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm font-medium text-[#737373] cursor-pointer hover:bg-[#f5f5f5] transition-colors"
                  @click="requestOpenSubjectList"
                >
                  <img :src="ButtonAdd" class="h-5 w-5 object-contain" alt="Add" />
                  <span>Add Subject</span>
                </button>
              </template>

              <template v-else>
                <button
                  type="button"
                  class="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm font-medium text-[#737373] cursor-pointer hover:bg-[#f5f5f5] transition-colors"
                  @click="requestOpenSubjectList"
                >
                  <img :src="ButtonAdd" class="h-5 w-5 object-contain" alt="Add" />
                  <span>Add Subject</span>
                </button>
              </template>
            </div>

            <div class="px-2.5 py-1.5 text-sm font-medium text-[#404040]">
              {{ day.scheduled_count }}/{{ day.target_count }} Subjects
            </div>
          </div>
        </div>
      </template>
    </div>

    <div class="flex items-center justify-end gap-3 border-t border-[#e5e5e5] p-5">
      <button
        type="button"
        class="flex items-center gap-2 rounded-md border border-[#d4d4d4] bg-white px-3 py-2 text-[16px] font-medium text-[#404040] cursor-pointer hover:bg-[#f5f5f5] transition-colors"
        @click="requestOpenTimeConfig"
      >
        <img :src="GenerateConfigTime" class="h-6 w-6 object-contain" alt="Config time" />
        <span>Config Time</span>
      </button>

      <button
        type="button"
        class="flex items-center gap-2 rounded-md bg-[#5c01d5] px-3 py-2 text-[16px] font-medium text-white cursor-pointer hover:bg-[#4c01b2] disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:bg-[#5c01d5] transition-colors"
        :disabled="applying || loading"
        @click="applyScheduler"
      >
        <img :src="TickSquare" class="h-6 w-6 object-contain" alt="Apply scheduler" />
        <span>{{ applying ? 'Applying...' : 'Apply Scheduler' }}</span>
      </button>
    </div>
  </div>
</template>