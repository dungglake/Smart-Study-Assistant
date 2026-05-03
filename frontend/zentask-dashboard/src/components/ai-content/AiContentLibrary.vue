<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import MarkdownIt from 'markdown-it'
import {
  AddCircleIcon,
  AddSourceIcon,
  DeleteIcon,
  EditIcon,
  FlashcardIcon,
  QuizIcon,
  SidebarToggle,
  SourceItemChatIcon,
  SourceItemCheckIcon,
  AddQuizIcon,
  LoadingIcon,
  PrevIcon,
  NextIcon,
  RefreshIcon,
} from '@/icons'

type ConversationItem = {
  id: number
  title: string
  summary: string
  menuOpen?: boolean
}

type MessageItem = {
  id?: number
  role: 'user' | 'assistant'
  mode: 'CHAT' | 'FLASHCARD' | 'QUIZ'
  title?: string
  content: any
  created_at?: string
  menuOpen?: boolean
}

const props = defineProps<{
  conversations: ConversationItem[]
  selectedConversationId: number | null
  currentTitle: string
  currentSummary: string
  messages: MessageItem[]
  isRenamingId: number | null
  renameValue: string
  isRenamingStudioId: number | null
  studioRenameValue: string
  isSending?: boolean
}>()

const emit = defineEmits<{
  (e: 'select-conversation', id: number): void
  (e: 'upload-more', files: File[]): void
  (e: 'open-menu', id: number): void
  (e: 'close-menu'): void
  (e: 'start-rename', item: ConversationItem): void
  (e: 'cancel-rename'): void
  (e: 'update-rename-value', value: string): void
  (e: 'submit-rename', id: number): void
  (e: 'delete-conversation', id: number): void
  (e: 'open-studio-menu', id: number): void
  (e: 'close-studio-menu'): void
  (e: 'start-rename-studio', item: MessageItem): void
  (e: 'cancel-rename-studio'): void
  (e: 'update-studio-rename-value', value: string): void
  (e: 'submit-rename-studio', id: number): void
  (e: 'delete-studio-item', id: number): void
  (
    e: 'send-message',
    payload: {
      conversation_id: number
      mode: 'CHAT' | 'FLASHCARD' | 'QUIZ' 
      message: string
    }
  ): void
}>()

const md = new MarkdownIt({
  breaks: true,
  linkify: true,
})

const fileInput = ref<HTMLInputElement | null>(null)
const messageInput = ref('')
const activeTool = ref<'CHAT' | 'FLASHCARD' | 'QUIZ' >('CHAT')
const selectedStudioMessageId = ref<number | null>(null)
const flashcardAnswersOpen = ref<Record<number, boolean>>({})
const flashcardIndexByMessage = ref<Record<number, number>>({})
const quizIndexByMessage = ref<Record<number, number>>({})
const quizAnswersByMessage = ref<Record<number, number>>({})
const messageListRef = ref<HTMLElement | null>(null)
const openFlashcardPopupId = ref<number | null>(null)
const openQuizPopupId = ref<number | null>(null)
const openFlashcardAnswerId = ref<number | null>(null)
const quizSubmittedByMessage = ref<Record<number, boolean>>({})
const LOADING_MIN_MS = 900
const pendingStartedAt = ref<number | null>(null)

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

const normalizeFiles = (files: File[]) => {
  const allowed = ['pdf', 'txt', 'md', 'docx']
  return files.filter((file) => {
    const ext = file.name.split('.').pop()?.toLowerCase() || ''
    return allowed.includes(ext)
  })
}

const pickMore = () => {
  fileInput.value?.click()
}

const onFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = normalizeFiles(Array.from(target.files || []))
  if (files.length) emit('upload-more', files)
  target.value = ''
}

const getMessageText = (content: any) => {
  if (typeof content === 'string') return normalizeMarkdown(content)

  let text = ''
  if (typeof content?.text === 'string') text = content.text
  else if (typeof content?.message === 'string') text = content.message
  else text = JSON.stringify(content, null, 2)

  return normalizeMarkdown(text)
}

const normalizeMarkdown = (rawText: string) => {
  return (rawText || '')
    .replace(/\\n/g, '\n')

    .replace(/\[Source\s*\d+\]/gi, '')
    .replace(/\(Source\s*\d+\)/gi, '')
    .replace(/chunk_id\s*=\s*\d+/gi, '')
    .replace(/order\s*=\s*\d+/gi, '')

    .replace(/^Answer:\s*$/gim, '## Answer:')
    .replace(/^Supporting points:\s*$/gim, '### Supporting points:')
    .replace(/^Summary:\s*$/gim, '## Summary:')
    .replace(/^Explanation:\s*$/gim, '## Explanation:')
    .replace(/^Key points:\s*$/gim, '## Key points:')
    .replace(/^Comparison:\s*$/gim, '## Comparison:')

    .replace(/^[•●▪◦]\s*/gim, '- ')

    .replace(/[•●▪◦]+\s*/g, '\n- ')

    .replace(/^\+\s*/gim, '- ')

    .replace(/\s*Purpose:\s*/gi, '\n- Purpose: ')

    .replace(/^(## .+:\s*)$/gim, '$1\n')
    .replace(/^(### .+:\s*)$/gim, '$1\n')

    .replace(/^\-\s*$/gim, '')

    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

const renderMessageHtml = (content: any) => {
  return md.render(getMessageText(content))
}

const sendCurrentMessage = () => {
  const text = messageInput.value.trim()
  if (!text || !props.selectedConversationId || props.isSending) return

  if (activeTool.value !== 'CHAT') {
    selectedStudioMessageId.value = null
  }

  emit('send-message', {
    conversation_id: props.selectedConversationId,
    mode: activeTool.value,
    message: text,
  })

  messageInput.value = ''
  if (activeTool.value !== 'CHAT') {
    activeTool.value = 'CHAT'
  }
}

const onInputKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendCurrentMessage()
  }
}

const pendingStudioMode = ref<'FLASHCARD' | 'QUIZ' | null>(null)
const previousStudioCount = ref(0)

const isStudioView = computed(() => {
  return !!selectedStudioMessage.value || !!pendingStudioMode.value
})

const showChatOnly = computed(() => {
  return !isStudioView.value
})

const pendingStudioTitle = computed(() => {
  if (pendingStudioMode.value === 'FLASHCARD') return 'Generating Flash Card'
  if (pendingStudioMode.value === 'QUIZ') return 'Generating Quiz'
  return ''
})

const scrollToBottom = async () => {
  await nextTick()
  const el = messageListRef.value
  if (!el) return
  el.scrollTop = el.scrollHeight
}

const toolLabelMap = {
  CHAT: 'Chat',
  FLASHCARD: 'Flash Card',
  QUIZ: 'Quiz',
} as const

const toolTemplateMap = {
  FLASHCARD: 'Create 4 flashcards from this source.',
  QUIZ: 'Create 3 quiz questions from this source.',
} as const

const activateTool = (mode: 'FLASHCARD' | 'QUIZ') => {
  if (!props.selectedConversationId || props.isSending) return

  pendingStudioMode.value = mode
  pendingStartedAt.value = Date.now()
  selectedStudioMessageId.value = null

  emit('send-message', {
    conversation_id: props.selectedConversationId,
    mode,
    message: toolTemplateMap[mode],
  })

  messageInput.value = ''
  activeTool.value = 'CHAT'
}

const studioItems = computed(() =>
  props.messages.filter(
    (item) =>
      item.role === 'assistant' &&
      (item.mode === 'FLASHCARD' || item.mode === 'QUIZ')
  )
)

const chatMessages = computed(() =>
  (props.messages || []).filter((msg) => msg.mode === 'CHAT')
)

const selectedStudioMessage = computed(() => {
  if (!selectedStudioMessageId.value) return null

  return (
    studioItems.value.find(
      (item) => item.id === selectedStudioMessageId.value
    ) || null
  )
})

const selectConversation = (id: number) => {
  selectedStudioMessageId.value = null
  pendingStudioMode.value = null
  emit('select-conversation', id)
}

watch(
  studioItems,
  async (items, oldItems) => {
    if (!items.length) {
      selectedStudioMessageId.value = null
      previousStudioCount.value = 0
      return
    }

    const latest = items[items.length - 1]
    const oldLength = oldItems?.length ?? 0

    if (items.length > oldLength && pendingStudioMode.value) {
      const startedAt = pendingStartedAt.value

      if (startedAt) {
        const elapsed = Date.now() - startedAt
        const remain = Math.max(0, LOADING_MIN_MS - elapsed)
        if (remain > 0) await sleep(remain)
      }

      pendingStudioMode.value = null
      pendingStartedAt.value = null
      selectedStudioMessageId.value = latest.id ?? null
    }

    previousStudioCount.value = items.length
  },
  { deep: true, immediate: true }
)

watch(
  () => props.isSending,
  (sending) => {
    if (!sending && !studioItems.value.length) {
      pendingStudioMode.value = null
    }
  }
)

watch(
  studioItems,
  (items) => {
    for (const item of items) {
      const id = item.id
      if (typeof id !== 'number') continue

      if (item.mode === 'FLASHCARD' && flashcardIndexByMessage.value[id] == null) {
        flashcardIndexByMessage.value[id] = 0
        flashcardAnswersOpen.value[id] = false
      }

      if (item.mode === 'QUIZ' && quizIndexByMessage.value[id] == null) {
        quizIndexByMessage.value[id] = 0
        quizAnswersByMessage.value[id] = -1
        quizSubmittedByMessage.value[id] = false

      }
    }
  },
  { deep: true, immediate: true }
)

const formatRelativeTime = (value?: string) => {
  if (!value) return 'Recently'

  const now = Date.now()
  const target = new Date(value).getTime()
  const diffMs = now - target
  const diffMin = Math.floor(diffMs / 60000)
  const diffHour = Math.floor(diffMs / 3600000)
  const diffDay = Math.floor(diffMs / 86400000)

  if (diffMin < 1) return 'Recently'
  if (diffMin < 60) return `${diffMin} min ago`
  if (diffHour < 24) return `${diffHour} hour${diffHour > 1 ? 's' : ''} ago`
  return `${diffDay} day${diffDay > 1 ? 's' : ''} ago`
}

const getStudioTitle = (message: MessageItem, index: number) => {
  if (message.title?.trim()) return message.title.trim()
  const label = toolLabelMap[message.mode as keyof typeof toolLabelMap] || 'Item'
  return `${label} ${index + 1}`
}

const getFlashcards = (content: any) => {
  const normalized = normalizeContent(content)

  if (Array.isArray(normalized?.items)) return normalized.items
  if (Array.isArray(normalized?.content?.items)) return normalized.content.items
  if (Array.isArray(normalized?.assistant_message?.content?.items)) {
    return normalized.assistant_message.content.items
  }

  return []
}

const normalizeContent = (content: any) => {
  if (!content) return {}

  if (typeof content === 'string') {
    try {
      return JSON.parse(content)
    } catch {
      return {}
    }
  }

  return content
}

const getQuizItems = (content: any) => {
  const normalized = normalizeContent(content)

  console.log('QUIZ CONTENT NORMALIZED:', normalized)

  if (Array.isArray(normalized?.items)) return normalized.items
  if (Array.isArray(normalized?.content?.items)) return normalized.content.items
  if (Array.isArray(normalized?.assistant_message?.content?.items)) {
    return normalized.assistant_message.content.items
  }

  return []
}

const pendingStudioCardClass = computed(() => {
  if (pendingStudioMode.value === 'QUIZ') {
    return 'border-[#00c16a] bg-[#00c16a1a]'
  }
  return 'border-[#5c01d5] bg-[#ffffff80]'
})

const pendingStudioIcon = computed(() => {
  return pendingStudioMode.value === 'QUIZ' ? QuizIcon : LoadingIcon
})

const nextFlashcard = (messageId: number, total: number) => {
  const current = flashcardIndexByMessage.value[messageId] ?? 0
  flashcardIndexByMessage.value[messageId] = Math.min(current + 1, total - 1)
  flashcardAnswersOpen.value[messageId] = false
}

const selectQuizAnswer = (messageId: number, choiceIndex: number) => {
  if (quizSubmittedByMessage.value[messageId]) return
  quizAnswersByMessage.value[messageId] = choiceIndex
}


const openFlashcardPopup = (messageId: number) => {
  openFlashcardPopupId.value = messageId
  openFlashcardAnswerId.value = null
}

const closeFlashcardPopup = () => {
  openFlashcardPopupId.value = null
  openFlashcardAnswerId.value = null
}

const showFlashcardAnswer = (messageId: number) => {
  openFlashcardAnswerId.value = messageId
}

const hideFlashcardAnswer = () => {
  openFlashcardAnswerId.value = null
}

const prevFlashcard = (messageId: number) => {
  const current = flashcardIndexByMessage.value[messageId] ?? 0
  flashcardIndexByMessage.value[messageId] = Math.max(current - 1, 0)
  openFlashcardAnswerId.value = null
}

const resetFlashcard = (messageId: number) => {
  flashcardIndexByMessage.value[messageId] = 0
  openFlashcardAnswerId.value = null
}

const openQuizPopup = (messageId: number) => {
  openQuizPopupId.value = messageId

  if (quizIndexByMessage.value[messageId] == null) {
    quizIndexByMessage.value[messageId] = 0
  }

  if (quizAnswersByMessage.value[messageId] == null) {
    quizAnswersByMessage.value[messageId] = -1
  }

  if (quizSubmittedByMessage.value[messageId] == null) {
    quizSubmittedByMessage.value[messageId] = false
  }
}

const closeQuizPopup = () => {
  openQuizPopupId.value = null
}


const submitQuizAnswer = (messageId: number) => {
  if ((quizAnswersByMessage.value[messageId] ?? -1) === -1) return
  quizSubmittedByMessage.value[messageId] = true
}

const goToPrevQuizQuestion = (messageId: number) => {
  const current = quizIndexByMessage.value[messageId] ?? 0
  quizIndexByMessage.value[messageId] = Math.max(current - 1, 0)
  quizAnswersByMessage.value[messageId] = -1
  quizSubmittedByMessage.value[messageId] = false
}

const goToNextQuizQuestion = (messageId: number, total: number) => {
  const current = quizIndexByMessage.value[messageId] ?? 0
  quizIndexByMessage.value[messageId] = Math.min(current + 1, total - 1)
  quizAnswersByMessage.value[messageId] = -1
  quizSubmittedByMessage.value[messageId] = false
}

const getQuizCorrectIndex = (question: any) => {
  if (typeof question?.answer_index === 'number') return question.answer_index
  return -1
}

const getQuizOptionClass = (messageId: number, question: any, optionIndex: number) => {
  const selected = quizAnswersByMessage.value[messageId] ?? -1
  const submitted = quizSubmittedByMessage.value[messageId] ?? false
  const correct = getQuizCorrectIndex(question)

  if (!submitted) {
    if (selected === optionIndex) {
      return 'bg-[#6460f41a] border-[#5c01d5] text-[#111827]'
    }
    return 'bg-[#f3f4f6] border-[#d1d5db] text-[#111827] hover:bg-[#f9fafb] cursor-pointer'
  }

  if (optionIndex === correct) {
    return 'bg-[#00c16a1a] border-[#00c16a] text-[#111827]'
  }

  if (optionIndex === selected && selected !== correct) {
    return 'bg-[#fb2c361a] border-[#fb2c36] text-[#111827]'
  }

  return 'bg-[#f3f4f6] border-[#d1d5db] text-[#111827]'
}

const getQuizDotClass = (messageId: number, question: any, optionIndex: number) => {
  const selected = quizAnswersByMessage.value[messageId] ?? -1
  const submitted = quizSubmittedByMessage.value[messageId] ?? false
  const correct = getQuizCorrectIndex(question)

  if (!submitted) {
    if (selected === optionIndex) {
      return 'bg-[#5c01d5] border-[#5c01d5]'
    }
    return 'bg-white border-[#d1d5db]'
  }

  if (optionIndex === correct) {
    return 'bg-[#00c16a] border-[#00c16a]'
  }

  if (optionIndex === selected && selected !== correct) {
    return 'bg-[#fb2c36] border-[#fb2c36]'
  }

  return 'bg-white border-[#d1d5db]'
}

const selectedStudioCardClass = computed(() => {
  if (selectedStudioMessage.value?.mode === 'QUIZ') {
    return 'bg-[#00c16a1a]'
  }
  return 'bg-[#6460f41a]'
})
watch(
  () => props.messages,
  async () => {
    await scrollToBottom()
  },
  { deep: true }
)

watch(
  () => props.selectedConversationId,
  async () => {
    await scrollToBottom()
  }
)

watch(
  [openFlashcardPopupId, openQuizPopupId,],
  ([flashcardVal, quizVal,]) => {
    if (flashcardVal || quizVal ) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
  }
)
</script>

<template>
  <div
    class="w-full h-full relative bg-[#f5f5f5] overflow-hidden flex flex-col items-start pt-8 pb-6 pl-8 pr-6 box-border text-left text-[18px] text-[#4b5563] font-inter"
  >
    <div class="self-stretch flex-1 rounded-3xl bg-white overflow-hidden flex flex-col items-start p-6 gap-6">
      <div class="w-full flex items-center gap-3">
        <div class="relative leading-7 font-semibold text-[#111827]">
          {{ currentTitle || 'AI Content Extractor' }}
        </div>
      </div>

      <div class="self-stretch flex-1 overflow-hidden flex items-start gap-6 text-[16px] text-[#374151]">
        <div
          class="self-stretch w-[253px] rounded-xl bg-[#f5f5f5] overflow-hidden shrink-0 flex flex-col items-start p-3 box-border relative gap-4"
        >
          <div class="self-stretch border-b border-[#d1d5db] flex items-center pb-3 gap-2.5">
            <div class="flex-1 relative leading-6">Source</div>
            <img :src="SidebarToggle" alt="SidebarToggle" class="w-6 h-6 object-contain" />
          </div>

          <button
            class="self-stretch rounded-md border border-[#8b5cf6] flex items-center justify-center py-2 px-3 gap-2 text-[#7c3aed] hover:bg-[#faf5ff] transition cursor-pointer"
            @click="pickMore"
          >
            <img :src="AddCircleIcon" alt="Add Source" class="w-6 h-6 object-contain" />
            <span class="leading-6">Add Source</span>
          </button>

          <div class="self-stretch flex-1 overflow-y-auto flex flex-col gap-4 pr-1">
            <div class="flex flex-col items-stretch gap-2">
              <div
                v-for="item in conversations"
                :key="item.id"
                class="relative"
                @mouseleave="$emit('close-menu')"
              >
                <div
                  class="w-full rounded-lg flex items-start p-3 gap-2 cursor-pointer transition"
                  :class="
                    item.id === selectedConversationId
                      ? 'bg-[#ede9fe]'
                      : 'bg-transparent hover:bg-[#f3f4f6]'
                  "
                  @click="selectConversation(item.id)"
                >
                  <div class="w-6 h-6 shrink-0 flex items-center justify-center">
                    <img :src="SourceItemChatIcon" alt="Source item" class="w-6 h-6 object-contain" />
                  </div>

                  <div class="flex-1 min-w-0">
                    <div
                      v-if="isRenamingId === item.id"
                      class="flex items-center gap-2"
                      @click.stop
                    >
                      <input
                        :value="renameValue"
                        class="w-full rounded-md border border-[#d1d5db] px-2 py-1 text-sm outline-none focus:border-[#8b5cf6]"
                        @input="$emit('update-rename-value', ($event.target as HTMLInputElement).value)"
                        @keyup.enter="$emit('submit-rename', item.id)"
                        @keyup.esc="$emit('cancel-rename')"
                      />
                    </div>

                    <div v-else class="line-clamp-2 leading-6 text-[#374151]">
                      {{ item.title }}
                    </div>
                  </div>

                  <button
                    class="w-6 h-6 shrink-0 flex items-center justify-center"
                    @click.stop="$emit('open-menu', item.id)"
                  >
                    <img
                      v-if="item.id === selectedConversationId"
                      :src="SourceItemCheckIcon"
                      alt="Selected"
                      class="w-6 h-6 object-contain"
                    />
                    <span v-else class="text-[#6b7280] text-lg leading-none">⋮</span>
                  </button>
                </div>

                <div
                  v-if="item.menuOpen"
                  class="absolute left-3 top-[56px] z-20 w-[184px] shadow-lg rounded-md bg-white border border-[#d1d5db] flex flex-col"
                >
                  <button
                    class="w-full flex items-center px-4 py-3 gap-2 text-left hover:bg-[#f9fafb] transition cursor-pointer"
                    @click.stop="$emit('start-rename', item)"
                  >
                    <img :src="EditIcon" alt="Rename" class="w-5 h-5 object-contain" />
                    <span>Rename Source</span>
                  </button>

                  <button
                    class="w-full flex items-center px-4 py-3 gap-2 text-left hover:bg-[#f9fafb] transition cursor-pointer"
                    @click.stop="$emit('delete-conversation', item.id)"
                  >
                    <img :src="DeleteIcon" alt="Delete" class="w-5 h-5 object-contain" />
                    <span>Delete Source</span>
                  </button>
                </div>
              </div>
            </div>

            <div class="self-stretch pt-2 border-t border-[#d1d5db] flex flex-col gap-2">
              <div class="text-[#4b5563] leading-6">Studio</div>
              <div
                v-if="pendingStudioMode"
                class="w-full rounded-[18px] border backdrop-blur-md flex items-center p-3 gap-3"
                :class="pendingStudioCardClass"
              >
                <div class="w-12 h-12 rounded-full bg-white flex items-center justify-center shrink-0">
                  <img
                    :src="LoadingIcon"
                    alt="Loading"
                    class="w-7 h-7 object-contain animate-spin"
                  />
                </div>

                <div class="min-w-0 flex-1">
                  <div class="leading-6 font-semibold text-[#111827]">
                    {{ pendingStudioTitle }}
                  </div>
                  <div class="text-sm leading-5 text-[#4b5563]">
                    Base on 1 source
                  </div>
                </div>
              </div>
              <div
                v-for="(item, index) in studioItems"
                :key="item.id ?? index"
                class="relative"
                @mouseleave="$emit('close-studio-menu')"
              >
                <div
                  class="w-full rounded-lg flex items-center p-2 gap-2 cursor-pointer transition group"
                  :class="
                    (item.id ?? index) === selectedStudioMessageId
                      ? 'bg-[#ede9fe]'
                      : 'hover:bg-[#f3f4f6]'
                  "
                  @click="
                    selectedStudioMessageId = item.id ?? null;
                  "
                >
                  <div class="rounded-full bg-[#f3f4f6] p-1 flex items-center justify-center">
                    <img
                      :src="item.mode === 'FLASHCARD' ? FlashcardIcon : QuizIcon"
                      class="w-6 h-6 object-contain"
                      alt=""
                    />
                  </div>

                  <div class="flex-1 min-w-0">
                    <div
                      v-if="isRenamingStudioId === item.id"
                      class="flex items-center gap-2"
                      @click.stop
                    >
                      <input
                        :value="studioRenameValue"
                        class="w-full rounded-md border border-[#d1d5db] px-2 py-1 text-sm outline-none focus:border-[#8b5cf6]"
                        @input="$emit('update-studio-rename-value', ($event.target as HTMLInputElement).value)"
                        @keyup.enter="$emit('submit-rename-studio', item.id!)"
                        @keyup.esc="$emit('cancel-rename-studio')"
                      />
                    </div>

                    <template v-else>
                      <div class="leading-5 font-medium line-clamp-2">
                        {{ getStudioTitle(item, index) }}
                      </div>
                      <div class="text-xs leading-4 text-[#6b7280] line-clamp-1">
                        1 source - {{ formatRelativeTime(item.created_at) }}
                      </div>
                    </template>
                  </div>

                  <button
                    v-if="item.id"
                    class="w-6 h-6 shrink-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition"
                    @click.stop="$emit('open-studio-menu', item.id)"
                  >
                    <span class="text-[#6b7280] text-lg leading-none">⋮</span>
                  </button>
                </div>

                <div
                  v-if="item.menuOpen"
                  class="absolute right-2 top-[44px] z-20 w-[160px] shadow-lg rounded-md bg-white border border-[#d1d5db] flex flex-col"
                >
                  <button
                    class="w-full flex items-center px-4 py-3 gap-2 text-left hover:bg-[#f9fafb] transition cursor-pointer "
                    @click.stop="$emit('start-rename-studio', item)"
                  >
                    <img :src="EditIcon" alt="Rename" class="w-5 h-5 object-contain" />
                    <span>Rename</span>
                  </button>

                  <button
                    class="w-full flex items-center px-4 py-3 gap-2 text-left hover:bg-[#f9fafb] transition cursor-pointer "
                    @click.stop="$emit('delete-studio-item', item.id!)"
                  >
                    <img :src="DeleteIcon" alt="Delete" class="w-5 h-5 object-contain" />
                    <span>Delete</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <input
            ref="fileInput"
            type="file"
            class="hidden"
            multiple
            accept=".pdf,.txt,.md,.docx"
            @change="onFileChange"
          />
        </div>

        <div class="self-stretch flex-1 overflow-hidden flex flex-col items-start p-2.5 gap-6">
          <div class="self-stretch border-b border-[#d1d5db] flex items-start pb-3">
            <div class="flex-1 relative leading-6">Chat</div>
          </div>

          <div class="self-stretch grid grid-cols-2 gap-2.5 text-[12px]">
            <div
              :class="
                activeTool === 'FLASHCARD'
                  ? 'rounded-lg bg-[#e9e7f9] ring-2 ring-[#8b5cf6] flex items-center p-2 gap-2 cursor-pointer'
                  : 'rounded-lg bg-[#e9e7f9] flex items-center p-2 gap-2 cursor-pointer'
              "
              @click="activateTool('FLASHCARD')"
            >
              <div class="flex-1 flex flex-col items-start gap-2">
                <img :src="FlashcardIcon" alt="Flash Card" class="w-6 h-6 object-contain" />
                <div class="self-stretch relative leading-4">Flash Card</div>
              </div>
              <img :src="AddCircleIcon" alt="Add" class="h-8 w-8 object-contain" />
            </div>

            <div
              :class="
                activeTool === 'QUIZ'
                  ? 'rounded-lg bg-[#dff1ea] ring-2 ring-[#10b981] flex items-center p-2 gap-2 cursor-pointer'
                  : 'rounded-lg bg-[#dff1ea] flex items-center p-2 gap-2 cursor-pointer'
              "
              @click="activateTool('QUIZ')"
            >
              <div class="flex-1 flex flex-col items-start gap-2">
                <img :src="QuizIcon" alt="Quiz" class="w-6 h-6 object-contain" />
                <div class="self-stretch relative leading-4">Quiz</div>
              </div>
              <img :src="AddQuizIcon" alt="Add" class="h-8 w-8 object-contain" />
            </div>
          </div>

          <div class="self-stretch flex-1 flex flex-col items-start justify-between gap-4 text-[14px] relative">
            <div
              ref="messageListRef"
              class="self-stretch flex-1 overflow-y-auto flex flex-col items-start pt-0 px-0 pb-5 gap-4"
            >
            <div
              v-if="selectedStudioMessage"
              class="self-stretch flex justify-start mb-4"
            >
              <div
                class="w-full max-w-[760px] rounded-[20px] px-5 py-4 flex items-center gap-4 cursor-pointer"
                :class="selectedStudioCardClass"
                @click="
                  selectedStudioMessage.mode === 'FLASHCARD' && selectedStudioMessage.id
                    ? openFlashcardPopup(selectedStudioMessage.id)
                    : selectedStudioMessage.mode === 'QUIZ' && selectedStudioMessage.id
                      ? openQuizPopup(selectedStudioMessage.id)
                      : null
                "
              >
                <div class="w-12 h-12 rounded-full bg-white/90 flex items-center justify-center shrink-0">
                  <img
                    :src="selectedStudioMessage.mode === 'FLASHCARD' ? FlashcardIcon : QuizIcon"
                    class="w-7 h-7 object-contain"
                    alt=""
                  />
                </div>

                <div class="min-w-0 flex-1">
                  <div class="text-[18px] leading-7 font-semibold text-[#1f2937] line-clamp-1">
                    {{
                      getStudioTitle(
                        selectedStudioMessage,
                        studioItems.findIndex((item) => item.id === selectedStudioMessage.id)
                      )
                    }}
                  </div>
                  <div class="text-[14px] leading-5 text-[#1f2937]">
                    1 source - {{ formatRelativeTime(selectedStudioMessage.created_at) }}
                  </div>
                </div>
              </div>
            </div>
              <template v-if="showChatOnly && chatMessages.length">
                <div
                  v-for="(message, index) in chatMessages"
                  :key="message.id ?? index"
                  class="self-stretch flex"
                  :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
                >
                  <div
                    class="max-w-[760px] rounded-xl px-4 py-3 leading-6 break-words"
                    :class="
                      message.role === 'user'
                        ? 'bg-[#e9e7f9] text-[#111827] rounded-br-none whitespace-pre-wrap'
                        : 'bg-transparent text-[#374151]'
                    "
                  >
                    <template v-if="message.role === 'assistant'">
                      <div
                        class="max-w-none whitespace-normal leading-6
                              [&_p]:my-1
                              [&_ul]:my-2
                              [&_ul]:list-disc
                              [&_ul]:pl-5
                              [&_ol]:my-2
                              [&_ol]:list-decimal
                              [&_ol]:pl-5
                              [&_li]:my-0.5
                              [&_h2]:text-[16px]
                              [&_h2]:font-semibold
                              [&_h2]:mb-2
                              [&_h3]:text-[14px]
                              [&_h3]:font-semibold
                              [&_h3]:mt-3
                              [&_h3]:mb-1"
                        v-html="renderMessageHtml(message.content)"
                      />
                    </template>

                    <template v-else>
                      {{ getMessageText(message.content) }}
                    </template>
                  </div>
                </div>
              </template>

              <div
                v-else-if="showChatOnly"
                class="w-full max-w-[760px] leading-6 text-[#374151]"
              >
                Upload the source code so the bot can generate the first response from the document. Then you can ask further questions directly in the box below.
              </div>
            </div>

            <div
              class="w-full rounded-xl border box-border flex items-center py-2 px-4 gap-2.5 min-h-[60px] text-[#9ca3af]"
              :class="isStudioView ? 'border-[#e5e7eb] bg-[#f9fafb] opacity-70' : 'border-[#d1d5db]'"
            >
              <textarea
                v-model="messageInput"
                rows="1"
                class="flex-1 resize-none border-none outline-none bg-transparent text-[14px] leading-5 text-[#111827] placeholder:text-[#9ca3af]"
                :placeholder="isStudioView ? 'Studio mode' : 'Start typing ...'"
                :disabled="isStudioView || isSending"
                @keydown="onInputKeydown"
              />

              <div class="relative text-[12px] leading-4 whitespace-nowrap">
                {{ selectedConversationId ? '1 Source selected' : 'No source selected' }}
              </div>

              <button
                type="button"
                class="h-8 w-8 rounded-full border border-[#d1d5db] flex items-center justify-center disabled:opacity-50"
                :disabled="isStudioView || !selectedConversationId || !messageInput.trim() || isSending"
                @click="sendCurrentMessage"
              >
                <img :src="AddSourceIcon" alt="Send" class="w-5 h-5 object-contain" />
              </button>
            </div>
          </div>
          <div
            v-if="
              selectedStudioMessage &&
              selectedStudioMessage.mode === 'FLASHCARD' &&
              openFlashcardPopupId === (selectedStudioMessage.id ?? 0)
            "
            class="fixed inset-0 z-[999] bg-black/35 backdrop-blur-[6px] flex items-center justify-center p-6 overflow-hidden"

          >
            <div class="relative w-full max-w-[600px] flex flex-col items-center gap-4">
              <button
                class="absolute right-[-10px] top-[-50px] z-50 bg-transparent p-2 cursor-pointer"
                @click.stop="closeFlashcardPopup"
              >
                <img :src="DeleteIcon" class="w-6 h-6 object-contain" alt="" />
              </button>

              <button
                class="absolute left-[-56px] top-1/2 -translate-y-1/2 rounded-full bg-[#d9d9d9] border border-white p-2 disabled:opacity-40 z-20 cursor-pointer"
                :disabled="(flashcardIndexByMessage[selectedStudioMessage.id ?? 0] ?? 0) <= 0"
                @click.stop="prevFlashcard(selectedStudioMessage.id ?? 0)"
              >
                <img :src="PrevIcon" class="w-6 h-6 object-contain" alt="" />
              </button>

              <button
                class="absolute right-[-56px] top-1/2 -translate-y-1/2 rounded-full bg-[#d9d9d9] border border-white p-2 disabled:opacity-40 z-20 cursor-pointer"
                :disabled="(flashcardIndexByMessage[selectedStudioMessage.id ?? 0] ?? 0) >= getFlashcards(selectedStudioMessage.content).length - 1"
                @click.stop="nextFlashcard(selectedStudioMessage.id ?? 0, getFlashcards(selectedStudioMessage.content).length)"
              >
                <img :src="NextIcon" class="w-6 h-6 object-contain" alt="" />
              </button>

              <div
                class="w-full h-[620px] relative rounded-[32px] bg-black border-[#d1d5db] border-[4px]
                      overflow-hidden text-center p-8 text-2xl text-white"
              >
                <div class="relative z-[2] pr-6 text-[24px] leading-[1.35] font-semibold">
                  {{
                    getFlashcards(selectedStudioMessage.content)[flashcardIndexByMessage[selectedStudioMessage.id ?? 0] ?? 0]?.front
                  }}
                </div>

                <button
                  v-if="openFlashcardAnswerId !== (selectedStudioMessage.id ?? 0)"
                  class="absolute bottom-[32px] left-1/2 -translate-x-1/2 text-lg leading-7 z-[3] cursor-pointer"
                  @click.stop="showFlashcardAnswer(selectedStudioMessage.id ?? 0)"
                >
                  See Answer
                </button>

                <div
                  class="absolute bottom-0 left-1/2 -translate-x-1/2 text-[220px] leading-[300px]
                        font-black text-[#374151] text-center blur-[12px] z-[0]"
                >
                  {{
                    String((flashcardIndexByMessage[selectedStudioMessage.id ?? 0] ?? 0) + 1).padStart(2, '0')
                  }}
                </div>

                <div
                  v-if="openFlashcardAnswerId === (selectedStudioMessage.id ?? 0)"
                  class="absolute inset-x-0 bottom-0 h-[360px]
                        shadow-[0px_4px_12px_rgba(255,_255,_255,_0.12)_inset]
                        [backdrop-filter:blur(48px)]
                        rounded-t-[28px]
                        bg-[#2a2a2a]/95 border-t border-white/20
                        overflow-hidden z-[4]
                        flex items-start justify-center
                        pt-12 px-8 pb-8 text-left text-lg text-white"
                >
                  <button
                    class="absolute top-[18px] right-[18px] p-2 z-[5] cursor-pointer"
                    @click.stop="hideFlashcardAnswer"
                  >
                    <img :src="DeleteIcon" class="w-6 h-6 object-contain" alt="" />
                  </button>

                  <div class="w-full max-w-[420px] leading-7 inline-block">
                    {{
                      getFlashcards(selectedStudioMessage.content)[flashcardIndexByMessage[selectedStudioMessage.id ?? 0] ?? 0]?.back
                    }}
                  </div>
                </div>
              </div>

              <div class="w-full flex items-center gap-4 mt-2">
                <button
                  class="rounded-[999px] bg-[#d9d9d9] border border-white p-2 shrink-0 cursor-pointer"
                  @click.stop="resetFlashcard(selectedStudioMessage.id ?? 0)"
                >
                  <img :src="RefreshIcon" class="w-6 h-6 object-contain" alt="" />
                </button>

                <div class="flex-1 h-3 rounded-full bg-[#e5e7eb] overflow-hidden">
                  <div
                    class="h-full bg-[#6d28d9]"
                    :style="{
                      width: `${(((flashcardIndexByMessage[selectedStudioMessage.id ?? 0] ?? 0) + 1) / getFlashcards(selectedStudioMessage.content).length) * 100}%`
                    }"
                  />
                </div>
                <div class="text-2xl font-semibold text-white min-w-[88px] text-right">
                  {{ String((flashcardIndexByMessage[selectedStudioMessage.id ?? 0] ?? 0) + 1).padStart(2, '0') }}/{{
                    String(getFlashcards(selectedStudioMessage.content).length).padStart(2, '0')
                  }}
                </div>
              </div>
            </div>
           </div>
           </div>
           <div
              v-if="
                selectedStudioMessage &&
                selectedStudioMessage.mode === 'QUIZ' &&
                openQuizPopupId === (selectedStudioMessage.id ?? 0)
              "
              class="fixed inset-0 z-[999] bg-black/35 backdrop-blur-[6px] flex items-center justify-center p-6 overflow-hidden"
            >
              <div class="relative w-full max-w-[930px]">
                <div
                  class="w-full rounded-[32px] bg-white border border-[#e5e7eb]
                        shadow-[0px_0px_0px_8px_rgba(255,255,255,0.12),0px_194px_54px_rgba(0,0,0,0),0px_124px_50px_rgba(0,0,0,0.01),0px_70px_42px_rgba(0,0,0,0.05),0px_31px_31px_rgba(0,0,0,0.09),0px_8px_17px_rgba(0,0,0,0.1)]
                        overflow-hidden flex flex-col items-center p-8 gap-8"
                >
                  <div class="self-stretch flex flex-col items-start gap-3">
                    <div class="self-stretch flex items-center gap-3">
                      <div class="flex-1 text-[16px] leading-6 text-[#111827]">
                        {{
                          `${(quizIndexByMessage[selectedStudioMessage.id ?? 0] ?? 0) + 1}/${getQuizItems(selectedStudioMessage.content).length}`
                        }}
                      </div>

                      <button @click.stop="closeQuizPopup">
                        <img :src="DeleteIcon" class="w-6 h-6 object-contain cursor-pointer" alt="" />
                      </button>
                    </div>

                    <div class="self-stretch text-[24px] leading-8 font-semibold text-[#374151]">
                      {{
                        getQuizItems(selectedStudioMessage.content)[quizIndexByMessage[selectedStudioMessage.id ?? 0] ?? 0]?.question
                      }}
                    </div>
                  </div>

                  <div class="self-stretch flex flex-col items-start gap-4 text-[18px]">
                    <button
                      v-for="(choice, optionIndex) in getQuizItems(selectedStudioMessage.content)[quizIndexByMessage[selectedStudioMessage.id ?? 0] ?? 0]?.choices || []"
                      :key="optionIndex"
                      class="self-stretch rounded-xl border flex items-start p-8 gap-4 text-left transition cursor-pointer hover:scale-[1.01]"
                      :class="getQuizOptionClass(selectedStudioMessage.id ?? 0, getQuizItems(selectedStudioMessage.content)[quizIndexByMessage[selectedStudioMessage.id ?? 0] ?? 0], optionIndex)"
                      @click.stop="selectQuizAnswer(selectedStudioMessage.id ?? 0, optionIndex)"
                    >
                      <div class="flex items-start pt-[2px]">
                        <div class="h-6 w-5 relative overflow-hidden shrink-0">
                          <div
                            class="absolute top-[2px] left-0 rounded-[999px] border box-border w-5 h-5 overflow-hidden"
                            :class="getQuizDotClass(selectedStudioMessage.id ?? 0, getQuizItems(selectedStudioMessage.content)[quizIndexByMessage[selectedStudioMessage.id ?? 0] ?? 0], optionIndex)"
                          />
                        </div>
                      </div>

                      <div class="flex-1 flex items-start gap-1">
                        <div class="w-5 leading-7 shrink-0">
                          {{ ['A.', 'B.', 'C.', 'D.'][optionIndex] }}
                        </div>
                        <div class="flex-1 leading-7">
                          {{ choice }}
                        </div>
                      </div>
                    </button>
                  </div>

                  <div class="self-stretch flex items-center justify-end gap-6 pt-6">
                    <button
                      class="h-10 w-[120px] rounded-md bg-white border border-[#d1d5db] flex items-center justify-center py-2 px-3 text-[#374151] disabled:opacity-40 cursor-pointer"
                      :disabled="(quizIndexByMessage[selectedStudioMessage.id ?? 0] ?? 0) <= 0"
                      @click.stop="goToPrevQuizQuestion(selectedStudioMessage.id ?? 0)"
                    >
                      <div class="leading-6 font-medium">Previous</div>
                    </button>

                    <button
                      v-if="!(quizSubmittedByMessage[selectedStudioMessage.id ?? 0] ?? false)"
                      class="w-[120px] rounded-md bg-[#5c01d5] flex items-center justify-center py-2 px-3 box-border text-white disabled:opacity-40 cursor-pointer"
                      :disabled="(quizAnswersByMessage[selectedStudioMessage.id ?? 0] ?? -1) === -1"
                      @click.stop="submitQuizAnswer(selectedStudioMessage.id ?? 0)"
                    >
                      <div class="leading-6 font-medium">Check</div>
                    </button>

                    <button
                      v-else
                      class="w-[120px] rounded-md bg-[#5c01d5] flex items-center justify-center py-2 px-3 box-border text-white disabled:opacity-40 cursor-pointer"
                      :disabled="(quizIndexByMessage[selectedStudioMessage.id ?? 0] ?? 0) >= getQuizItems(selectedStudioMessage.content).length - 1"
                      @click.stop="goToNextQuizQuestion(selectedStudioMessage.id ?? 0, getQuizItems(selectedStudioMessage.content).length)"
                    >
                      <div class="leading-6 font-medium">Next</div>
                    </button>
                  </div>
                </div>
              </div>
            </div>
           </div>
          </div>
        </div>
</template>

<style scoped>
.studio-spin {
  animation: studio-spin 0.9s linear infinite;
}
@keyframes studio-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>