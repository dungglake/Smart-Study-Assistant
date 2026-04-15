<script setup lang="ts">
import { ref, watch } from 'vue'
import { AddWhite, DeleteIcon, TimerIcon, FlagIcon, TickSquare, DotsIcon, EditIcon } from '@/icons'
import { authFetch } from '@/api/authFetch'

type Priority = 'Urgent' | 'High' | 'Normal' | 'Low'
type DraftPriority = Priority | ''
type ApiPriority = 'urgent' | 'high' | 'normal' | 'low'

type SubjectItem = {
  id: number
  name: string
  studyTime: string
  priority: Priority
}

const props = defineProps<{
  open: boolean
  subjects?: SubjectItem[]
  weekStart?: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', payload: SubjectItem[]): void
  (e: 'saved', payload: SubjectItem[]): void
  (e: 'error', message: string): void
}>()

const localSubjects = ref<SubjectItem[]>(props.subjects ? [...props.subjects] : [])

watch(
  () => props.subjects,
  (nextSubjects) => {
    localSubjects.value = nextSubjects ? [...nextSubjects] : []
  },
  { deep: true }
)

const isAdding = ref(false)
const isTimeDropdownOpen = ref(false)
const isPriorityDropdownOpen = ref(false)
const openActionId = ref<number | null>(null)
const editingSubjectId = ref<number | null>(null)
const isSaving = ref(false)
const saveError = ref('')

const hour = ref('1')
const minute = ref('00')

const priorityOptions: Priority[] = ['Urgent', 'High', 'Normal', 'Low']

const priorityMap: Record<Priority, ApiPriority> = {
  Urgent: 'urgent',
  High: 'high',
  Normal: 'normal',
  Low: 'low',
}

const priorityFilters: Record<Priority, string> = {
  Urgent:
    'brightness(0) saturate(100%) invert(39%) sepia(92%) saturate(2384%) hue-rotate(336deg) brightness(96%) contrast(94%)',
  High:
    'brightness(0) saturate(100%) invert(68%) sepia(93%) saturate(880%) hue-rotate(358deg) brightness(99%) contrast(94%)',
  Normal:
    'brightness(0) saturate(100%) invert(48%) sepia(80%) saturate(2311%) hue-rotate(202deg) brightness(97%) contrast(96%)',
  Low:
    'brightness(0) saturate(100%) invert(70%) sepia(0%) saturate(0%) hue-rotate(162deg) brightness(91%) contrast(88%)',
}

const draft = ref<{
  name: string
  studyTime: string
  priority: DraftPriority
}>({
  name: '',
  studyTime: '',
  priority: '',
})

function normalizeStudyTime(value: string) {
  if (!value) return '1:00'

  const [rawHour = '0', rawMinute = '00'] = value.split(':')
  const safeHour = String(Math.max(0, Number(rawHour) || 0))
  const safeMinuteNumber = Math.min(59, Math.max(0, Number(rawMinute) || 0))
  const safeMinute = String(safeMinuteNumber).padStart(2, '0')

  return `${safeHour}:${safeMinute}`
}

function buildSubjectPayload(subjects: SubjectItem[]) {
  return subjects.map((subject) => ({
    id: subject.id,
    name: subject.name,
    studyTime: normalizeStudyTime(subject.studyTime),
    priority: priorityMap[subject.priority] || 'normal',
  }))
}

async function saveSubjectsToDb(subjects: SubjectItem[]) {
  emit('save', subjects)

  if (!props.weekStart) {
    return
  }

  isSaving.value = true
  saveError.value = ''

  try {
    const response = await authFetch('/api/planner/week/autosave', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        week_start: props.weekStart,
        subjects: buildSubjectPayload(subjects),
      }),
    })

    if (!response.ok) {
      const errorBody = await response.json().catch(() => null)
      throw new Error(errorBody?.detail || 'Cannot save subjects')
    }

    emit('saved', subjects)
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Cannot save subjects'
    saveError.value = message
    emit('error', message)
  } finally {
    isSaving.value = false
  }
}

function openAddSubject() {
  isAdding.value = true
}

function confirmTime() {
  draft.value.studyTime = normalizeStudyTime(`${hour.value}:${minute.value}`)
  isTimeDropdownOpen.value = false
}

function closeAddForm() {
  isAdding.value = false
  editingSubjectId.value = null
  isTimeDropdownOpen.value = false
  isPriorityDropdownOpen.value = false

  draft.value = {
    name: '',
    studyTime: '',
    priority: '',
  }

  hour.value = '1'
  minute.value = '00'
}

function openActionMenu(id: number) {
  openActionId.value = openActionId.value === id ? null : id
}

function editSubject(subject: SubjectItem) {
  editingSubjectId.value = subject.id
  isAdding.value = true
  openActionId.value = null

  draft.value = {
    name: subject.name,
    studyTime: subject.studyTime,
    priority: subject.priority,
  }

  const [h, m] = subject.studyTime.split(':')
  hour.value = h || '1'
  minute.value = m || '00'
}

async function saveNewSubject() {
  if (!draft.value.name.trim()) return

  const payload = {
    name: draft.value.name.trim(),
    studyTime: normalizeStudyTime(draft.value.studyTime || `${hour.value}:${minute.value}`),
    priority: (draft.value.priority || 'Normal') as Priority,
  }

  if (editingSubjectId.value !== null) {
    localSubjects.value = localSubjects.value.map((item) =>
      item.id === editingSubjectId.value
        ? { ...item, ...payload }
        : item
    )
  } else {
    localSubjects.value.push({
      id: Date.now(),
      ...payload,
    })
  }

  closeAddForm()
  await saveSubjectsToDb(localSubjects.value)
}

async function removeSubject(id: number) {
  localSubjects.value = localSubjects.value.filter((item) => item.id !== id)
  openActionId.value = null
  await saveSubjectsToDb(localSubjects.value)
}
</script>

<template>
  <div
    v-if="open"
    class="w-full rounded-3xl bg-white shadow-[0px_0px_32px_rgba(0,0,0,0.12)] overflow-visible flex flex-col gap-5 min-h-[220px]"
  >
    <div class="flex items-center gap-3 border-b border-[#e5e5e5] px-5 py-3">
      <div class="flex-1 text-[18px] font-semibold leading-7 text-[#404040]">
        Subject
      </div>

      <div v-if="isSaving" class="text-xs text-[#737373]">Saving...</div>

      <button
        type="button"
        class="rounded-md p-1 hover:bg-[#f5f5f5] cursor-pointer"
        @click="emit('close')"
      >
        <img :src="DeleteIcon" class="h-6 w-6 object-contain" alt="Close" />
      </button>
    </div>

    <div class="flex flex-col items-center justify-center px-5 pb-10 overflow-visible">
      <div v-if="saveError" class="mb-3 self-stretch rounded-md bg-red-50 px-3 py-2 text-sm text-red-500">
        {{ saveError }}
      </div>

      <div
        v-if="localSubjects.length > 0 || isAdding"
        class="self-stretch border-b border-[#e5e5e5] flex items-center gap-3 pb-1 text-sm text-[#737373]"
      >
        <div class="flex-1 px-3 py-2">Name</div>

        <div class="flex items-center gap-3">
          <div class="w-40 px-2 py-2">Study time (h)</div>
          <div class="w-40 px-2 py-2">Priority</div>
        </div>
      </div>

      <div
        v-if="localSubjects.length === 0 && !isAdding"
        class="self-stretch flex flex-col items-center justify-center gap-3 py-6 text-black"
      >
        <div class="text-[18px] font-semibold leading-7">
          No subjects have been created yet
        </div>

        <button
          type="button"
          class="rounded-md bg-[#5c01d5] flex items-center py-1.5 px-2.5 gap-1.5 text-sm text-white cursor-pointer hover:bg-[#4c01b2] disabled:opacity-60"
          :disabled="isSaving"
          @click="openAddSubject"
        >
          <img :src="AddWhite" class="h-6 w-6 object-contain" alt="Add" />
          <span class="font-medium leading-5">Add subject</span>
        </button>
      </div>

      <div
        v-for="subject in localSubjects"
        :key="subject.id"
        class="self-stretch border-b border-[#e5e5e5] flex items-center gap-3 py-3"
      >
        <div class="flex-1 px-3 py-2 text-[18px] font-bold leading-7 text-[#404040]">
          {{ subject.name }}
        </div>

        <div class="flex items-center text-base text-[#404040]">
          <div class="w-40 px-2 py-2 leading-6">
            {{ subject.studyTime }}
          </div>

          <div class="w-37 px-2 py-2 leading-6 flex items-center gap-2">
            <img
              :src="FlagIcon"
              class="h-5 w-5 object-contain"
              alt="Priority"
              :style="{ filter: priorityFilters[subject.priority] }"
            />
            <span>{{ subject.priority }}</span>
          </div>

          <div class="relative flex w-6 items-center justify-center">
            <button
              type="button"
              class="flex h-6 w-6 items-center justify-center rounded-md hover:bg-[#f5f5f5] cursor-pointer disabled:opacity-60"
              :disabled="isSaving"
              @click="openActionMenu(subject.id)"
            >
              <img :src="DotsIcon" class="h-6 w-6 object-contain" alt="More" />
            </button>

            <div
              v-if="openActionId === subject.id"
              class="absolute right-0 top-8 z-[9999] w-32 rounded-md border border-[#e5e5e5] bg-white p-1 shadow-lg"
            >
              <button
                type="button"
                class="flex w-full items-center gap-2 rounded-md px-2 py-2 text-left text-sm hover:bg-[#f5f5f5] cursor-pointer"
                @click="editSubject(subject)"
              >
                <img :src="EditIcon" class="h-5 w-5 object-contain" alt="Edit" />
                <span>Edit</span>
              </button>

              <button
                type="button"
                class="flex w-full items-center gap-2 rounded-md px-2 py-2 text-left text-sm text-red-500 hover:bg-[#f5f5f5] cursor-pointer"
                @click="removeSubject(subject.id)"
              >
                <img :src="DeleteIcon" class="h-5 w-5 object-contain" alt="Delete" />
                <span>Delete</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div
        v-if="isAdding"
        class="self-stretch flex items-center gap-3 py-2 overflow-visible"
      >
        <div class="flex-1 rounded-md bg-white flex items-center py-2 px-3">
          <input
            v-model="draft.name"
            type="text"
            placeholder="Task Name"
            class="w-full bg-transparent text-[18px] font-medium leading-7 text-[#404040] outline-none placeholder:text-[#a1a1a1]"
          />
        </div>

        <div class="flex w-[368px] items-start text-sm text-[#404040] overflow-visible">
          <div class="relative w-40 overflow-visible">
            <button
              type="button"
              class="w-28 rounded-md bg-white border border-[#d4d4d4] flex items-center py-1.5 px-2.5 gap-1.5 cursor-pointer"
              @click="isTimeDropdownOpen = !isTimeDropdownOpen"
            >
              <img :src="TimerIcon" class="h-5 w-5 object-contain" alt="Time" />
              <span class="leading-5 font-medium">
                {{ draft.studyTime || 'Time' }}
              </span>
            </button>

            <div
              v-if="isTimeDropdownOpen"
              class="absolute left-0 bottom-[42px] z-[9999] w-[190px] rounded-md bg-white border border-[#e5e5e5] shadow-lg p-3"
            >
              <div class="flex items-center gap-1 text-center text-[16px] text-[#404040]">
                <div class="flex items-center">
                  <input
                    v-model="hour"
                    type="number"
                    min="0"
                    class="w-8 bg-transparent text-center outline-none"
                  />
                  <span class="ml-1 text-[12px]">Hour</span>
                </div>

                <span>:</span>

                <div class="flex items-center">
                  <input
                    v-model="minute"
                    type="number"
                    min="0"
                    max="59"
                    class="w-8 bg-transparent text-center outline-none opacity-60"
                  />
                  <span class="text-[12px]">Minute</span>
                </div>
              </div>

              <button
                type="button"
                class="mt-2 w-full rounded-md bg-[#5c01d5] py-1.5 text-white hover:bg-[#4c01b2] cursor-pointer"
                @click="confirmTime"
              >
                Done
              </button>
            </div>
          </div>

          <div class="relative w-40 overflow-visible">
            <button
              type="button"
              class="w-28 rounded-md bg-white border border-[#d4d4d4] flex items-center py-1.5 px-2.5 gap-1.5 cursor-pointer"
              @click="isPriorityDropdownOpen = !isPriorityDropdownOpen"
            >
              <img
                :src="FlagIcon"
                class="h-5 w-5 object-contain"
                alt="Priority"
                :style="{ filter: draft.priority ? priorityFilters[draft.priority] : 'brightness(0)' }"
              />
              <span class="leading-5 font-medium">
                {{ draft.priority || 'Priority' }}
              </span>
            </button>

            <div
              v-if="isPriorityDropdownOpen"
              class="absolute left-0 bottom-[42px] z-[9999] w-44 rounded-md bg-white border border-[#e5e5e5] shadow-lg p-1"
            >
              <button
                v-for="priority in priorityOptions"
                :key="priority"
                type="button"
                class="w-full rounded-md flex items-center gap-2 p-2 hover:bg-[#f5f5f5] cursor-pointer"
                @click="draft.priority = priority; isPriorityDropdownOpen = false"
              >
                <img
                  :src="FlagIcon"
                  class="h-5 w-5 object-contain"
                  alt=""
                  :style="{ filter: priorityFilters[priority] }"
                />
                <span>{{ priority }}</span>
              </button>
            </div>
          </div>

          <button
            type="button"
            class="rounded-md bg-[#5c01d5] flex items-center py-1.5 px-2.5 gap-1.5 -ml-4 text-white hover:bg-[#4c01b2] cursor-pointer disabled:opacity-60"
            :disabled="isSaving"
            @click="saveNewSubject"
          >
            <img :src="TickSquare" class="h-5 w-5 object-contain" alt="Save" />
            <span class="font-medium">Save</span>
          </button>
        </div>
      </div>

      <button
        v-if="localSubjects.length > 0 && !isAdding"
        type="button"
        class="self-stretch flex items-center py-3 text-[#737373] disabled:opacity-60"
        :disabled="isSaving"
        @click="openAddSubject"
      >
        <div class="flex-1 rounded-md bg-white flex items-center py-2 px-3">
          <div class="text-[18px] font-medium leading-7">+ Add Subject</div>
        </div>
      </button>
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
</style>
