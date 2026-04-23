<script setup lang="ts">
import { computed, ref, watch, onBeforeUnmount, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authJson } from '@/api/authFetch'
import TimeConfigPanel from '@/components/scheduler/TimeConfigPanel.vue'
import SubjectListPanel from '@/components/scheduler/SubjectListPanel.vue'
import GenerateSchedulerPopup from '@/components/scheduler/GenerateSchedulerPopup.vue'
import {
  ChevronLeft,
  ChevronRight,
  EditSubject,
  MoreSubject,
  EditIcon,
  DeleteIcon,
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
const openMoreMenuFor = ref<string | null>(null)
const openEditMenuFor = ref<string | null>(null)
const deleteConfirmSlot = ref<any | null>(null)
const renameSlot = ref<any | null>(null)
const renameValue = ref('')
const actionLoading = ref(false)
const scheduleStartHour = 6
const scheduleEndHour = 23
const scheduleRowHeight = 80
const dayLabels = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'] as const
const savedWeekConfigs = ref<Record<string, any>>({})
const dbGeneratedSummary = ref<any | null>(null)
const weekPlanSlots = ref<any[]>([])
const weekBusyBlocks = ref<any[]>([])
const activeGeneratedSummary = computed(() => {
  return props.generatedSummary || dbGeneratedSummary.value
})

const subjectPalette = [
  '#5C01D5',
  '#F4D40F',
  '#FF253A',
  '#20B2AA',
  '#4169E1',
  '#FF8C42',
  '#2DBE70',
  '#A855F7',
  '#EC4899',
  '#0EA5E9',
]

const MAX_VISIBLE_SUBJECTS = 6

const subjectRatioData = computed(() => {
  const subjectMinutesMap = new Map<string, number>()

  for (const slot of weekPlanSlots.value) {
    const name = slot.subject_name || 'Unknown Subject'
    const minutes = getSlotDurationMinutes(slot)

    subjectMinutesMap.set(name, (subjectMinutesMap.get(name) || 0) + minutes)
  }

  const entries = Array.from(subjectMinutesMap.entries())
    .map(([name, minutes]) => ({ name, minutes }))
    .sort((a, b) => b.minutes - a.minutes)

  const totalMinutes = entries.reduce((sum, item) => sum + item.minutes, 0)

  if (entries.length <= MAX_VISIBLE_SUBJECTS) {
    return entries.map((item, index) => ({
      id: index + 1,
      name: item.name,
      minutes: item.minutes,
      percent: totalMinutes > 0 ? Math.round((item.minutes / totalMinutes) * 100) : 0,
      rawPercent: totalMinutes > 0 ? (item.minutes / totalMinutes) * 100 : 0,
      color: subjectPalette[index % subjectPalette.length],
    }))
  }

  const topSubjects = entries.slice(0, MAX_VISIBLE_SUBJECTS)
  const otherSubjects = entries.slice(MAX_VISIBLE_SUBJECTS)
  const othersMinutes = otherSubjects.reduce((sum, item) => sum + item.minutes, 0)

  const result = topSubjects.map((item, index) => ({
    id: index + 1,
    name: item.name,
    minutes: item.minutes,
    percent: totalMinutes > 0 ? Math.round((item.minutes / totalMinutes) * 100) : 0,
    rawPercent: totalMinutes > 0 ? (item.minutes / totalMinutes) * 100 : 0,
    color: subjectPalette[index % subjectPalette.length],
  }))

  if (othersMinutes > 0) {
    result.push({
      id: result.length + 1,
      name: 'Others',
      minutes: othersMinutes,
      percent: totalMinutes > 0 ? Math.round((othersMinutes / totalMinutes) * 100) : 0,
      rawPercent: totalMinutes > 0 ? (othersMinutes / totalMinutes) * 100 : 0,
      color: '#D4D4D8',
    })
  }

  return result
})

const totalSubjectsCount = computed(() => subjectRatioData.value.length)

function describeDonutArc(
  cx: number,
  cy: number,
  outerR: number,
  innerR: number,
  startAngle: number,
  endAngle: number
) {
  const outerStart = polarToCartesian(cx, cy, outerR, endAngle)
  const outerEnd = polarToCartesian(cx, cy, outerR, startAngle)
  const innerStart = polarToCartesian(cx, cy, innerR, endAngle)
  const innerEnd = polarToCartesian(cx, cy, innerR, startAngle)

  const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1'

  return [
    'M', outerStart.x, outerStart.y,
    'A', outerR, outerR, 0, largeArcFlag, 0, outerEnd.x, outerEnd.y,
    'L', innerEnd.x, innerEnd.y,
    'A', innerR, innerR, 0, largeArcFlag, 1, innerStart.x, innerStart.y,
    'Z',
  ].join(' ')
}

function polarToCartesian(cx: number, cy: number, r: number, angle: number) {
  const angleRad = ((angle - 90) * Math.PI) / 180

  return {
    x: cx + r * Math.cos(angleRad),
    y: cy + r * Math.sin(angleRad),
  }
}

function describeArc(cx: number, cy: number, r: number, startAngle: number, endAngle: number) {
  const start = polarToCartesian(cx, cy, r, endAngle)
  const end = polarToCartesian(cx, cy, r, startAngle)
  const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1'

  return [
    'M',
    cx,
    cy,
    'L',
    start.x,
    start.y,
    'A',
    r,
    r,
    0,
    largeArcFlag,
    0,
    end.x,
    end.y,
    'Z',
  ].join(' ')
}

const subjectRatioSegments = computed(() => {
  const gapAngle = 4
  let currentAngle = 0

  return subjectRatioData.value.map((item) => {
    const sweep = (item.rawPercent / 100) * 360
    const startAngle = currentAngle + gapAngle / 2
    const endAngle = currentAngle + sweep - gapAngle / 2
    const midAngle = (startAngle + endAngle) / 2

    const labelPoint = polarToCartesian(180, 180, 140, midAngle)

    const segment = {
      ...item,
      path: describeDonutArc(180, 180, 135, 85, startAngle, endAngle),
      labelX: labelPoint.x,
      labelY: labelPoint.y,
    }

    currentAngle += sweep
    return segment
  })
})

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

function handleSubjectListChanged(payload: any[]) {
  dbGeneratedSummary.value = null
  emit('generated-summary', null)
  emit('save-subjects', payload)
}

const selectedDate = computed(() => {
  const fromQuery = parseDateFromQuery(route.query.date)
  if (fromQuery) return fromQuery

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return today
})

const weekStart = computed(() => getStartOfWeekMonday(selectedDate.value))
async function loadSavedGeneratedSummary() {
  try {
    const data = await authJson(
      `/api/planner/week/summary?week_start=${formatDateLocal(weekStart.value)}`
    )

    const hasSavedPlan =
      Array.isArray(data?.daily) &&
      data.daily.some((day: any) => day.assigned_subjects?.length > 0)

    if (hasSavedPlan) {
      dbGeneratedSummary.value = data
      emit('generated-summary', data)
    } else {
      dbGeneratedSummary.value = null
    }
  } catch (error) {
    console.error('Failed to load saved generated schedule:', error)
  }
}

watch(
  () => formatDateLocal(weekStart.value),
  () => {
    loadSavedGeneratedSummary()
    loadWeekPlanAndBusy()
  },
  { immediate: true }
)

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
  activeGeneratedSummary.value?.daily?.find(
    (day: any) => day.date === formatDateLocal(selectedDate.value)
  ) || null
)

const selectedDaySlots = computed(() => {
  return getSlotsForDate(formatDateLocal(selectedDate.value))
})

const hours = Array.from(
  { length: scheduleEndHour - scheduleStartHour + 1 },
  (_, i) => {
    const hour = scheduleStartHour + i
    const suffix = hour < 12 ? 'AM' : 'PM'
    const displayHour = hour === 12 ? 12 : hour > 12 ? hour - 12 : hour

    return {
      hour,
      label: `${displayHour}:00 ${suffix}`,
    }
  }
)

function getSlotDate(slot: any) {
  return String(slot.start || '').slice(0, 10)
}

function getLocalTimeParts(value: any) {
  const text = String(value || '')
  const timeText = (text.includes('T')
    ? text.split('T')[1]
    : text.split(' ')[1]) || '00:00'

  const [hour = '0', minute = '0'] = timeText.slice(0, 5).split(':')

  return {
    hour: Number(hour),
    minute: Number(minute),
  }
}

function toMinutes(value: any) {
  const { hour, minute } = getLocalTimeParts(value)
  return hour * 60 + minute
}

function timeTextToMinutes(value: string) {
  const [hour = '0', minute = '0'] = String(value || '00:00').slice(0, 5).split(':')
  return Number(hour) * 60 + Number(minute)
}
function formatTimeRange(start: any, end: any) {
  const format = (value: any) => {
    const { hour, minute } = getLocalTimeParts(value)

    const suffix = hour < 12 ? 'AM' : 'PM'
    const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour

    return `${displayHour}:${String(minute).padStart(2, '0')} ${suffix}`
  }

  return `${format(start)} - ${format(end)}`
}

function getSlotDurationMinutes(slot: any) {
  return Math.max(0, toMinutes(slot.end) - toMinutes(slot.start))
}

function getTaskStatus(slot: any) {
  const slotDate = getSlotDate(slot)
  const today = formatDateLocal(new Date())

  if (slotDate < today) return 'ended'
  if (slotDate > today) return 'not-started'

  const now = new Date()
  const nowMinutes = now.getHours() * 60 + now.getMinutes()
  const startMinutes = toMinutes(slot.start)
  const endMinutes = toMinutes(slot.end)

  if (nowMinutes >= endMinutes) return 'ended'
  if (nowMinutes >= startMinutes && nowMinutes < endMinutes) return 'ongoing'
  return 'not-started'
}

function getTaskStatusLabel(status: string) {
  if (status === 'ended') return 'Ended'
  if (status === 'ongoing') return 'Ongoing'
  return 'Not Started'
}

function getTodayTaskCardClass(status: string) {
  if (status === 'ended') {
    return 'bg-[#f5f5f5] text-black'
  }

  if (status === 'ongoing') {
    return 'bg-[#6460f41a] text-black'
  }

  return 'bg-white border border-[#d9d9d9] text-black'
}

function getTodayTaskBadgeClass(status: string) {
  if (status === 'ended') {
    return 'bg-[#2DBE70] text-white'
  }

  if (status === 'ongoing') {
    return 'bg-[#4169E1] text-white'
  }

  return 'bg-[#6460F4] text-white'
}

function getScheduleBlockClass(slot: any) {
  const duration = getSlotDurationMinutes(slot)

  if (duration >= 120) {
    return 'bg-[#5C01D5]/20 border border-dashed border-[#5C01D5]/40 text-[#404040]'
  }

  return 'bg-[#20B2AA] text-white'
}

function getScheduleBlockStyle(slot: any) {
  const startMinutes = toMinutes(slot.start)
  const endMinutes = toMinutes(slot.end)
  const visibleStart = scheduleStartHour * 60
  const duration = Math.max(30, endMinutes - startMinutes)

  const top = ((startMinutes - visibleStart) / 60) * scheduleRowHeight
  const height = (duration / 60) * scheduleRowHeight

  return {
    top: `${top}px`,
    height: `${height}px`,
  }
}

function getSlotsForDate(date: string) {
  return weekPlanSlots.value
    .filter((slot) => getSlotDate(slot) === date)
    .sort((a, b) => toMinutes(a.start) - toMinutes(b.start))
}

function getSlotsStartingAt(date: string, hour: number) {
  return getSlotsForDate(date).filter((slot) => {
    const start = toMinutes(slot.start)
    return Math.floor(start / 60) === hour
  })
}

function isBusyAtHour(date: string, hour: number) {
  const currentStart = hour * 60
  const currentEnd = (hour + 1) * 60

  const currentDate = new Date(date)
  const previousDate = new Date(currentDate)
  previousDate.setDate(currentDate.getDate() - 1)
  const previousDateKey = formatDateLocal(previousDate)

  const currentBusy = weekBusyBlocks.value.filter((block) => block.date === date)
  const previousBusy = weekBusyBlocks.value.filter((block) => block.date === previousDateKey)

  for (const block of currentBusy) {
    const start = timeTextToMinutes(block.start)
    let end = timeTextToMinutes(block.end)

    if (block.start === '00:00' && (block.end === '23:59' || block.end === '00:00')) {
      return true
    }

    if (end <= start) {
      end = 24 * 60
    }

    if (Math.max(start, currentStart) < Math.min(end, currentEnd)) {
      return true
    }
  }

  for (const block of previousBusy) {
    const start = timeTextToMinutes(block.start)
    const end = timeTextToMinutes(block.end)

    if (end <= start) {
      const carryStart = 0
      const carryEnd = end

      if (Math.max(carryStart, currentStart) < Math.min(carryEnd, currentEnd)) {
        return true
      }
    }
  }

  return false
}

function handlePlannerPlanUpdated(event: Event) {
  const customEvent = event as CustomEvent
  if (customEvent.detail?.weekStart === formatDateLocal(weekStart.value)) {
    loadWeekPlanAndBusy()
    loadSavedGeneratedSummary()
  }
}

onMounted(() => {
  window.addEventListener('planner-plan-updated', handlePlannerPlanUpdated)
})

onBeforeUnmount(() => {
  window.removeEventListener('planner-plan-updated', handlePlannerPlanUpdated)
})

async function loadWeekPlanAndBusy() {
  try {
    const weekStartKey = formatDateLocal(weekStart.value)

    const [planData, busyData] = await Promise.all([
      authJson(`/api/planner/plan/week?week_start=${weekStartKey}`),
      authJson(`/api/planner/busyblocks/week?week_start=${weekStartKey}`),
    ])

    weekPlanSlots.value = planData?.plan || []
    weekBusyBlocks.value = busyData?.busy || []
  } catch (error) {
    weekPlanSlots.value = []
    weekBusyBlocks.value = []
    console.error('Failed to load plan or busy blocks:', error)
  }
}

function isSlotLockedForActions(slot: any) {
  const status = getTaskStatus(slot)
  return status === 'ended' || status === 'ongoing'
}

async function confirmDeleteSubject() {
  if (!deleteConfirmSlot.value) return

  try {
    actionLoading.value = true

    await authJson('/api/planner/subject-actions/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        week_start: formatDateLocal(weekStart.value),
        subject_id: deleteConfirmSlot.value.subject_id,
      }),
    })

    deleteConfirmSlot.value = null
    openMoreMenuFor.value = null

    window.dispatchEvent(new CustomEvent('planner-plan-updated', {
      detail: { weekStart: formatDateLocal(weekStart.value) }
    }))
  } catch (error) {
    console.error('Failed to delete subject:', error)
  } finally {
    actionLoading.value = false
  }
}

function openRenameSubject(slot: any) {
  renameSlot.value = slot
  renameValue.value = slot.subject_name || ''
  openEditMenuFor.value = null
}

async function saveRenamedSubject() {
  if (!renameSlot.value || !renameValue.value.trim()) return

  try {
    actionLoading.value = true

    await authJson('/api/planner/subject-actions/rename', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        week_start: formatDateLocal(weekStart.value),
        subject_id: renameSlot.value.subject_id,
        new_name: renameValue.value.trim(),
      }),
    })

    renameSlot.value = null
    renameValue.value = ''

    window.dispatchEvent(new CustomEvent('planner-plan-updated', {
      detail: { weekStart: formatDateLocal(weekStart.value) }
    }))
  } catch (error) {
    console.error('Failed to rename subject:', error)
  } finally {
    actionLoading.value = false
  }
}

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
          @applied="emit('generated-summary', $event)"
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
          @save="handleSubjectListChanged"
          @saved="handleSubjectListChanged"
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

        <div
          class="flex min-h-[560px] flex-col items-center justify-center rounded-[16px] border border-dashed border-[#e5e5e5] bg-[#fafafa] px-6 text-center"
        >
          <template v-if="subjectRatioData.length">
            <div class="relative h-[420px] w-[420px]">
              <svg viewBox="0 0 360 360" class="h-full w-full">
                <path
                  v-for="segment in subjectRatioSegments"
                  :key="segment.id"
                  :d="segment.path"
                  :fill="segment.color"
                />

                <g v-for="segment in subjectRatioSegments" :key="`label-${segment.id}`">
                  <circle
                    :cx="segment.labelX"
                    :cy="segment.labelY"
                    r="18"
                    fill="#F1F1F1"
                  />
                  <text
                    :x="segment.labelX"
                    :y="segment.labelY + 2"
                    text-anchor="middle"
                    font-size="9"
                    font-weight="600"
                    fill="#404040"
                  >
                    {{ segment.percent }}%
                  </text>
                </g>
              </svg>

              <div class="absolute inset-0 flex flex-col items-center justify-center">
                <div class="text-[30px] font-bold text-[#171717]">
                  {{ totalSubjectsCount }}
                </div>
                <div class="mt-1 text-sm text-[#737373]">
                  Subjects
                </div>
              </div>
            </div>

            <div class="mt-8 flex flex-wrap items-center justify-center gap-6 text-black">
              <div
                v-for="item in subjectRatioData"
                :key="item.id"
                class="flex items-center gap-2"
              >
                <span
                  class="h-4 w-4 rounded-full"
                  :style="{ backgroundColor: item.color }"
                ></span>

                <div class="leading-6">
                  {{ item.name }}
                  <span class="text-[#737373]">({{ item.percent }}%)</span>
                </div>
              </div>
            </div>
          </template>

          <template v-else>
            <div class="text-[16px] font-semibold text-[#171717]">
              No subject ratio data yet
            </div>
            <p class="mt-2 text-sm leading-6 text-[#737373]">
              Apply the scheduler to see subject study ratios for this week.
            </p>
          </template>
        </div>
      </div>

      <div class="col-span-6 flex flex-col gap-8 rounded-[24px] bg-white p-6">
        <div class="flex items-center justify-center gap-3">
          <button type="button" class="rounded-md p-1 hover:bg-gray-100 cursor-pointer" @click="goPrevWeek">
            <img :src="ChevronLeft" class="h-5 w-5" alt="prev" />
          </button>

          <div class="flex flex-col items-center">
            <div class="text-base leading-6 text-[#171717]">
              {{ monthYearLabel }}
            </div>
          </div>

          <button type="button" class="rounded-md p-1 hover:bg-gray-100 cursor-pointer" @click="goNextWeek">
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
          v-if="selectedDaySlots.length"
          class="flex max-h-[360px] min-h-[320px] flex-col gap-3 overflow-y-auto rounded-[16px] border border-[#e5e5e5] bg-[#fafafa] p-4 pr-2"
        >
          <div
            v-for="slot in selectedDaySlots"
            :key="`${slot.id || slot.subject_id}-${slot.start}-${slot.end}`"
            class="w-full relative rounded-xl overflow-visible flex flex-col items-start p-3 box-border gap-2.5 text-center text-[10px] font-inter"
            :class="getTodayTaskCardClass(getTaskStatus(slot))"
          >
            <div class="self-stretch flex items-center justify-center gap-2.5">
              <div class="flex-1 relative text-[16px] leading-5 text-black text-left">
                {{ formatTimeRange(slot.start, slot.end) }}
              </div>

              <div class="rounded-[999px] bg-black flex items-center justify-center py-1 px-1.5">
                <div class="relative leading-3 font-medium text-[11px] text-white">Schedule</div>
              </div>

              <div
                class="rounded-[999px] flex items-center justify-center py-1 px-1.5"
                :class="getTodayTaskBadgeClass(getTaskStatus(slot))"
              >
                <div class="relative leading-3 text-[11px] font-medium text-white">
                  {{ getTaskStatusLabel(getTaskStatus(slot)) }}
                </div>
              </div>
            </div>

            <div class="self-stretch flex items-center justify-center gap-2.5 text-left text-base text-black">
              <div class="flex-1 relative leading-6 text-[20px] font-semibold">
                {{ slot.subject_name || 'Subject' }}
              </div>

              <div class="relative flex items-center gap-2">
                <button
                  type="button"
                  class="rounded-md bg-gray-100 flex items-center p-1.5 cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
                  :disabled="isSlotLockedForActions(slot)"
                  @click="openEditMenuFor = openEditMenuFor === `${slot.subject_id}-${slot.start}` ? null : `${slot.subject_id}-${slot.start}`"
                >
                  <img :src="EditSubject" class="h-5 w-5 relative object-contain" alt="EditIcon" />
                </button>

                <button
                  type="button"
                  class="rounded-md bg-gray-100 flex items-center p-1.5 cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
                  :disabled="isSlotLockedForActions(slot)"
                  @click="openMoreMenuFor = openMoreMenuFor === `${slot.subject_id}-${slot.start}` ? null : `${slot.subject_id}-${slot.start}`"
                >
                  <img :src="MoreSubject" class="h-5 w-5 relative object-contain" alt="MoreIcon" />
                </button>

                <div
                  v-if="openEditMenuFor === `${slot.subject_id}-${slot.start}`"
                  class="absolute right-14 top-10 z-20 min-w-[140px] rounded-lg border border-[#e5e5e5] bg-white p-1.5 shadow-lg"
                >
                  <button
                    type="button"
                    class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm hover:bg-gray-50 cursor-pointer"
                    @click="openRenameSubject(slot)"
                  >
                    <img :src="EditIcon" class="h-4 w-4" alt="Rename" />
                    <span>Rename</span>
                  </button>
                </div>

                <div
                  v-if="openMoreMenuFor === `${slot.subject_id}-${slot.start}`"
                  class="absolute right-0 top-10 z-20 min-w-[140px] rounded-lg border border-[#e5e5e5] bg-white p-1.5 shadow-lg"
                >
                  <button
                    type="button"
                    class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 cursor-pointer"
                    @click="deleteConfirmSlot = slot; openMoreMenuFor = null"
                  >
                    <img :src="DeleteIcon" class="h-4 w-4" alt="Delete" />
                    <span>Delete</span>
                  </button>
                </div>
              </div>
            </div>
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
            v-for="hourItem in hours"
            :key="hourItem.hour"
            :style="{
              display: 'grid',
              gridTemplateColumns: `110px repeat(${scheduleHeaderDays.length}, minmax(0, 1fr))`,
              height: `${scheduleRowHeight}px`,
            }"
          >
            <div class="flex items-start justify-center border-r border-[#e5e5e5] pt-4 text-[14px] leading-5 text-[#525252]">
              {{ hourItem.label }}
            </div>

            <div
              v-for="item in scheduleHeaderDays"
              :key="`${item.fullDate}-${hourItem.hour}`"
              class="relative overflow-visible border-r border-dashed border-b border-[#e9e9e9] last:border-r-0"
              :class="[
                item.weekend ? 'bg-[#fcfcfc]' : 'bg-white',
                isBusyAtHour(item.fullDate, hourItem.hour) ? 'bg-[#f1f1f1]' : ''
              ]"
            >
              <div
                v-for="slot in getSlotsStartingAt(item.fullDate, hourItem.hour)"
                :key="`${slot.id || slot.subject_id}-${slot.start}-${slot.end}`"
                class="absolute left-2 right-2 z-[3] rounded-xl flex flex-col items-start p-2 box-border gap-1 text-left font-inter shadow-sm"
                :class="getScheduleBlockClass(slot)"
                :style="{
                  top: `${(toMinutes(slot.start) % 60) / 60 * scheduleRowHeight}px`,
                  height: `${Math.max(48, (getSlotDurationMinutes(slot) / 60) * scheduleRowHeight)}px`,
                }"
              >
                <div class="self-stretch flex items-center justify-center">
                  <div
                    class="flex-1 relative leading-6 font-medium"
                    :class="getSlotDurationMinutes(slot) < 120 ? 'overflow-hidden text-ellipsis whitespace-nowrap' : ''"
                  >
                    {{ slot.subject_name || 'Subject' }}
                  </div>
                </div>

                <div
                  class="flex items-center justify-center text-right text-xs"
                  :class="getSlotDurationMinutes(slot) >= 120 ? 'text-[#8c8c8c]' : 'text-white'"
                >
                  <div class="relative leading-4">
                    {{ formatTimeRange(slot.start, slot.end) }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div
            v-if="!weekPlanSlots.length"
            class="pointer-events-none absolute inset-0 flex items-center justify-center"
          >
            <div class="rounded-[16px] border border-dashed border-[#e5e5e5] bg-white/90 px-6 py-5 text-center shadow-sm">
              <div class="text-[16px] font-semibold text-[#171717]">
                No schedule items yet
              </div>
              <p class="mt-2 text-sm leading-6 text-[#737373]">
                Subject blocks will appear here after you generate scheduler.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
  <div
    v-if="renameSlot"
    class="fixed inset-0 z-[120] flex items-center justify-center bg-black/40 px-6"
  >
    <div class="w-full max-w-md rounded-[20px] bg-white p-6 shadow-xl">
      <div class="text-lg font-semibold text-[#171717]">
        Rename Subject
      </div>

      <input
        v-model="renameValue"
        type="text"
        class="mt-4 w-full rounded-lg border border-[#d4d4d4] px-4 py-2 outline-none"
        placeholder="Enter new subject name"
      />

      <div class="mt-6 flex justify-end gap-3">
        <button
          type="button"
          class="rounded-lg border border-[#d4d4d4] px-4 py-2 text-sm cursor-pointer"
          @click="renameSlot = null; renameValue = ''"
        >
          Cancel
        </button>

        <button
          type="button"
          class="rounded-lg bg-[#5c01d5] px-4 py-2 text-sm text-white cursor-pointer disabled:opacity-50"
          :disabled="actionLoading || !renameValue.trim()"
          @click="saveRenamedSubject"
        >
          Save
        </button>
      </div>
    </div>
  </div>
  <div
    v-if="deleteConfirmSlot"
    class="fixed inset-0 z-[120] flex items-center justify-center bg-black/40 px-6"
  >
    <div class="w-full max-w-md rounded-[20px] bg-white p-6 shadow-xl">
      <div class="text-lg font-semibold text-[#171717]">
        Are you sure you want to delete this subject?
      </div>

      <p class="mt-2 text-sm text-[#737373]">
        This will remove only this subject from the generated schedule for this week.
      </p>

      <div class="mt-6 flex justify-end gap-3">
        <button
          type="button"
          class="rounded-lg border border-[#d4d4d4] px-4 py-2 text-sm cursor-pointer"
          @click="deleteConfirmSlot = null"
        >
          Cancel
        </button>

        <button
          type="button"
          class="rounded-lg bg-red-600 px-4 py-2 text-sm text-white cursor-pointer disabled:opacity-50"
          :disabled="actionLoading"
          @click="confirmDeleteSubject"
        >
          Delete
        </button>
      </div>
    </div>
  </div>
</template>