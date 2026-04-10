<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import MarkdownIt from 'markdown-it'
import {
  AddCircleIcon,
  AddSourceIcon,
  DeleteIcon,
  EditIcon,
  FlashcardIcon,
  MindmapIcon,
  QuizIcon,
  SidebarToggle,
  SourceItemChatIcon,
  SourceItemCheckIcon,
  AddMindmapIcon,
  AddQuizIcon,
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
  mode: 'CHAT' | 'FLASHCARD' | 'QUIZ' | 'MINDMAP'
  content: any
  created_at?: string
}

const props = defineProps<{
  conversations: ConversationItem[]
  selectedConversationId: number | null
  currentTitle: string
  currentSummary: string
  messages: MessageItem[]
  isRenamingId: number | null
  renameValue: string
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
  (e: 'send-message', payload: { conversation_id: number; mode: 'CHAT'; message: string }): void
}>()

const md = new MarkdownIt({
  breaks: true,
  linkify: true,
})

const fileInput = ref<HTMLInputElement | null>(null)
const messageInput = ref('')
const messageListRef = ref<HTMLElement | null>(null)

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
    .replace(/^\+\s*/gim, '- ')

    .replace(
      /^(Algorithmic bias|Data-driven bias|Selection bias|Confirmation bias|Implicit bias|Historical data bias|Selection rate bias|Accuracy by group bias|Case\s+\d+.*)$/gim,
      '- $1'
    )

    .replace(/^(## .+:\s*)$/gim, '$1\n')
    .replace(/^(### .+:\s*)$/gim, '$1\n')

    // Đảm bảo mỗi bullet đứng riêng dòng
    .replace(/(?<!\n)-\s+/g, '\n- ')

    // Gọn dòng trống
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

const renderMessageHtml = (content: any) => {
  return md.render(getMessageText(content))
}

const sendCurrentMessage = () => {
  const text = messageInput.value.trim()
  if (!text || !props.selectedConversationId || props.isSending) return

  emit('send-message', {
    conversation_id: props.selectedConversationId,
    mode: 'CHAT',
    message: text,
  })

  messageInput.value = ''
}

const onInputKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendCurrentMessage()
  }
}

const hasMessages = computed(() => props.messages && props.messages.length > 0)

const scrollToBottom = async () => {
  await nextTick()
  const el = messageListRef.value
  if (!el) return
  el.scrollTop = el.scrollHeight
}

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
            class="self-stretch rounded-md border border-[#8b5cf6] flex items-center justify-center py-2 px-3 gap-2 text-[#7c3aed] hover:bg-[#faf5ff] transition"
            @click="pickMore"
          >
            <img :src="AddCircleIcon" alt="Add Source" class="w-6 h-6 object-contain" />
            <span class="leading-6">Add Source</span>
          </button>

          <div class="self-stretch flex-1 overflow-y-auto flex flex-col items-stretch gap-2 pr-1">
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
                @click="$emit('select-conversation', item.id)"
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
                  class="w-full flex items-center px-4 py-3 gap-2 text-left hover:bg-[#f9fafb] transition"
                  @click.stop="$emit('start-rename', item)"
                >
                  <img :src="EditIcon" alt="Rename" class="w-5 h-5 object-contain" />
                  <span>Rename Source</span>
                </button>

                <button
                  class="w-full flex items-center px-4 py-3 gap-2 text-left hover:bg-[#f9fafb] transition"
                  @click.stop="$emit('delete-conversation', item.id)"
                >
                  <img :src="DeleteIcon" alt="Delete" class="w-5 h-5 object-contain" />
                  <span>Delete Source</span>
                </button>
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

          <div class="self-stretch grid grid-cols-3 gap-2.5 text-[12px]">
            <div class="rounded-lg bg-[#e9e7f9] flex items-center p-2 gap-2">
              <div class="flex-1 flex flex-col items-start gap-2">
                <img :src="FlashcardIcon" alt="Flash Card" class="w-6 h-6 object-contain" />
                <div class="self-stretch relative leading-4">Flash Card</div>
              </div>
              <img :src="AddCircleIcon" alt="Add" class="h-8 w-8 object-contain" />
            </div>

            <div class="rounded-lg bg-[#dff1ea] flex items-center p-2 gap-2">
              <div class="flex-1 flex flex-col items-start gap-2">
                <img :src="QuizIcon" alt="Quiz" class="w-6 h-6 object-contain" />
                <div class="self-stretch relative leading-4">Quiz</div>
              </div>
              <img :src="AddQuizIcon" alt="Add" class="h-8 w-8 object-contain" />
            </div>

            <div class="rounded-lg bg-[#efe7d1] flex items-center p-2 gap-2">
              <div class="flex-1 flex flex-col items-start gap-2">
                <img :src="MindmapIcon" alt="Mind Map" class="w-6 h-6 object-contain" />
                <div class="self-stretch relative leading-4">Mind Map</div>
              </div>
              <img :src="AddMindmapIcon" alt="Add" class="h-8 w-8 object-contain" />
            </div>
          </div>

          <div class="self-stretch flex-1 flex flex-col items-start justify-between gap-4 text-[14px]">
            <div
              ref="messageListRef"
              class="self-stretch flex-1 overflow-y-auto flex flex-col items-start pt-0 px-0 pb-5 gap-4"
            >
              <template v-if="hasMessages">
                <div
                  v-for="(message, index) in messages"
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
                    <div
                      v-if="message.role === 'assistant'"
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
                    <template v-else>
                      {{ getMessageText(message.content) }}
                    </template>
                  </div>
                </div>
              </template>

              <div v-else class="w-full max-w-[760px] leading-6 text-[#374151]">
                Upload source để bot tạo phản hồi đầu tiên từ tài liệu. Sau đó bạn có thể hỏi tiếp ngay trong ô bên dưới.
              </div>
            </div>

            <div
              class="w-full rounded-xl border border-[#d1d5db] box-border flex items-center py-2 px-4 gap-2.5 min-h-[60px] text-[#9ca3af]"
            >
              <textarea
                v-model="messageInput"
                rows="1"
                class="flex-1 resize-none border-none outline-none bg-transparent text-[14px] leading-5 text-[#111827] placeholder:text-[#9ca3af]"
                placeholder="Start typing ..."
                @keydown="onInputKeydown"
              />

              <div class="relative text-[12px] leading-4 whitespace-nowrap">
                {{ selectedConversationId ? '1 Source selected' : 'No source selected' }}
              </div>

              <button
                type="button"
                class="h-8 w-8 rounded-full border border-[#d1d5db] flex items-center justify-center disabled:opacity-50"
                :disabled="!selectedConversationId || !messageInput.trim() || isSending"
                @click="sendCurrentMessage"
              >
                <img :src="AddSourceIcon" alt="Send" class="w-5 h-5 object-contain" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>