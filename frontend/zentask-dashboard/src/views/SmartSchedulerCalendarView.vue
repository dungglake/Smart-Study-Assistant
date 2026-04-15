<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ButtonAdd } from '@/icons'
import TimeConfigPanel from '@/components/scheduler/TimeConfigPanel.vue'
import SubjectListPanel from '@/components/scheduler/SubjectListPanel.vue'
import GenerateSchedulerPopup from '@/components/scheduler/GenerateSchedulerPopup.vue'

const route = useRoute()
const router = useRouter()
const weekStart = computed(() => getStartOfWeekMonday(selectedDate.value))
const weekdayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
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

const savedWeekConfigs = ref<Record<string, any>>({})

function handleSaveTimeConfig(payload: any) {
  savedWeekConfigs.value[payload.weekStart] = payload
  console.log('Saved week config:', payload)
  emit('close-time-config')
}

function formatDateLocal(date: Date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function parseQueryDate(value: unknown) {
  if (typeof value !== 'string') {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    return today
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    return today
  }

  date.setHours(0, 0, 0, 0)
  return date
}

function getStartOfWeekMonday(date: Date) {
  const d = new Date(date)
  d.setHours(0, 0, 0, 0)
  const day = d.getDay()
  const diff = day === 0 ? -6 : 1 - day
  d.setDate(d.getDate() + diff)
  return d
}

function isSameDate(a: Date, b: Date) {
  return formatDateLocal(a) === formatDateLocal(b)
}

const selectedDate = computed(() => parseQueryDate(route.query.date))

const displayMonth = computed(() => {
  return new Date(
    selectedDate.value.getFullYear(),
    selectedDate.value.getMonth(),
    1
  )
})

const calendarCells = computed(() => {
  const monthStart = new Date(
    displayMonth.value.getFullYear(),
    displayMonth.value.getMonth(),
    1
  )
  const monthEnd = new Date(
    displayMonth.value.getFullYear(),
    displayMonth.value.getMonth() + 1,
    0
  )

  const gridStart = getStartOfWeekMonday(monthStart)
  const gridEnd = getStartOfWeekMonday(monthEnd)
  gridEnd.setDate(gridEnd.getDate() + 6)

  const cells = []
  const cursor = new Date(gridStart)

  while (cursor <= gridEnd) {
    const date = new Date(cursor)

    cells.push({
      key: formatDateLocal(date),
      date,
      dayNumber: String(date.getDate()).padStart(2, '0'),
      isCurrentMonth: date.getMonth() === displayMonth.value.getMonth(),
      isSelected: isSameDate(date, selectedDate.value),
      isSunday: date.getDay() === 0,
      scheduledSubjects: props.generatedSummary?.daily?.find((day: any) => day.date === formatDateLocal(date))?.assigned_subjects || [],
    })

    cursor.setDate(cursor.getDate() + 1)
  }

  return cells
})

function updateRouteDate(date: Date) {
  router.replace({
    query: {
      ...route.query,
      date: formatDateLocal(date),
    },
  })
}

function selectDate(date: Date) {
  updateRouteDate(date)
}
</script>

<template>
  <div class="bg-[#f5f5f5] px-8 pb-6 pt-8">
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
    <div class="rounded-3xl bg-white p-6">
      <div class="mb-4  text-[18px] font-semibold text-[#404040]">
      </div>

      <div class="overflow-hidden rounded-xl border border-[#e5e5e5]">
        <div class="grid h-16 grid-cols-7 border-[#e5e5e5] text-center text-[16px] font-bold text-[#404040]">
          <div
            v-for="label in weekdayLabels"
            :key="label"
            class="flex items-center justify-center border-r border-[#e5e5e5] last:border-r-0"
            :class="label === 'Sun' ? 'bg-[#f5f5f5]' : 'bg-white'"
          >
            {{ label }}
          </div>
        </div>

        <div class="grid grid-cols-7">
          <button
            v-for="cell in calendarCells"
            :key="cell.key"
            type="button"
            class="group relative h-[133px] border-r border-b border-[#e5e5e5] p-2 text-right text-[12px] transition last:border-r-0"
            :class="[
              cell.isSelected ? 'bg-[#6460f41a] text-[#5c01d5]' : '',
              !cell.isCurrentMonth ? 'text-[#a3a3a3]' : 'text-[#404040]',
              cell.isSunday ? 'bg-[#f5f5f5]' : '',
            ]"
            @click="selectDate(cell.date)"
          >
            <div class="absolute left-2 top-2 right-2 flex flex-col items-start gap-1 text-left">
              <div
                v-for="subject in cell.scheduledSubjects"
                :key="`${cell.key}-${subject.id}-${subject.name}`"
                class="max-w-full truncate rounded-md bg-[#ede9fe] px-2 py-0.5 text-[11px] font-medium text-[#5c01d5]"
              >
                {{ subject.name }}
              </div>
            </div>

            <img
              :src="ButtonAdd"
              alt="Add"
              class="absolute bottom-1 right-8 hidden h-6 w-6 object-contain group-hover:block"
              @click.stop
            />

            <span class="absolute bottom-2 right-2 leading-4">
              {{ cell.dayNumber }}
            </span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
