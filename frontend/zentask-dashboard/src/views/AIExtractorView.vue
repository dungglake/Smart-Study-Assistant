<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import AiContentLibrary from '@/components/ai-content/AiContentLibrary.vue'
import AiContentEmptyState from '@/components/ai-content/AiContentEmptyState.vue'
import {
  deleteConversation,
  getConversationMessages,
  getConversations,
  getMaterialDetail,
  renameConversation,
  sendChatMessage,
  uploadMaterial,
} from '@/services/extractorApi'

type ConversationItem = {
  id: number
  material: number
  material_title: string
  title: string
  summary: string
  created_at: string
  menuOpen?: boolean
}

type MessageItem = {
  id?: number
  conversation?: number
  role: 'user' | 'assistant'
  mode: 'CHAT' | 'FLASHCARD' | 'QUIZ' | 'MINDMAP'
  content: any
  created_at?: string
}

const conversations = ref<ConversationItem[]>([])
const selectedConversationId = ref<number | null>(null)
const messages = ref<MessageItem[]>([])
const isRenamingId = ref<number | null>(null)
const renameValue = ref('')
const isSending = ref(false)
const isUploading = ref(false)
const loadingMessages = ref(false)

const processingMaterialIds = ref<number[]>([])
const pollingTimer = ref<number | null>(null)

const selectedConversation = computed(() =>
  conversations.value.find((item) => item.id === selectedConversationId.value) || null
)

const currentTitle = computed(() => selectedConversation.value?.title || 'AI Content Extractor')
const currentSummary = computed(() => selectedConversation.value?.summary || '')

const loadConversations = async (preferLatest = false) => {
  const data = await getConversations()
  conversations.value = (data || []).map((item: ConversationItem) => ({
    ...item,
    menuOpen: false,
  }))

  if (!conversations.value.length) {
    selectedConversationId.value = null
    messages.value = []
    return
  }

  if (preferLatest) {
    selectedConversationId.value = conversations.value[0].id
    return
  }

  if (
    selectedConversationId.value &&
    conversations.value.some((item) => item.id === selectedConversationId.value)
  ) {
    return
  }

  selectedConversationId.value = conversations.value[0].id
}

const loadMessages = async (conversationId: number) => {
  loadingMessages.value = true
  try {
    const data = await getConversationMessages(conversationId)
    messages.value = data || []
  } catch (error) {
    console.error('Load messages failed:', error)
    messages.value = []
  } finally {
    loadingMessages.value = false
  }
}

const stopPolling = () => {
  if (pollingTimer.value) {
    window.clearInterval(pollingTimer.value)
    pollingTimer.value = null
  }
}

const startPolling = () => {
  if (pollingTimer.value) return

  pollingTimer.value = window.setInterval(async () => {
    if (!processingMaterialIds.value.length) {
      stopPolling()
      return
    }

    const finishedIds: number[] = []

    for (const materialId of processingMaterialIds.value) {
      try {
        const detail = await getMaterialDetail(materialId)

        if (detail.status === 'DONE') {
          finishedIds.push(materialId)
          await loadConversations(true)
        } else if (detail.status === 'FAILED') {
          finishedIds.push(materialId)
        }
      } catch (error) {
        console.error('Polling material failed:', error)
      }
    }

    if (finishedIds.length) {
      processingMaterialIds.value = processingMaterialIds.value.filter(
        (id) => !finishedIds.includes(id)
      )
    }

    if (!processingMaterialIds.value.length) {
      stopPolling()
    }
  }, 1500)
}

const handleUploadMore = async (files: File[]) => {
  if (!files.length) return

  isUploading.value = true
  try {
    for (const file of files) {
      const result = await uploadMaterial(file, file.name)
      if (result?.material_id) {
        processingMaterialIds.value.push(result.material_id)
      }
    }
    startPolling()
  } catch (error) {
    console.error('Upload failed:', error)
  } finally {
    isUploading.value = false
  }
}

const handleSelectConversation = async (id: number) => {
  selectedConversationId.value = id
  conversations.value = conversations.value.map((item) => ({
    ...item,
    menuOpen: false,
  }))
}

const handleOpenMenu = (id: number) => {
  conversations.value = conversations.value.map((item) => ({
    ...item,
    menuOpen: item.id === id ? !item.menuOpen : false,
  }))
}

const handleCloseMenu = () => {
  conversations.value = conversations.value.map((item) => ({
    ...item,
    menuOpen: false,
  }))
}

const handleStartRename = (item: ConversationItem) => {
  isRenamingId.value = item.id
  renameValue.value = item.title
}

const handleCancelRename = () => {
  isRenamingId.value = null
  renameValue.value = ''
}

const handleSubmitRename = async (id: number) => {
  const title = renameValue.value.trim()
  if (!title) return

  try {
    const updated = await renameConversation(id, title)
    conversations.value = conversations.value.map((item) =>
      item.id === id ? { ...item, title: updated.title } : item
    )
    handleCancelRename()
  } catch (error) {
    console.error('Rename failed:', error)
  }
}

const handleDeleteConversation = async (id: number) => {
  try {
    await deleteConversation(id)
    const wasSelected = selectedConversationId.value === id

    conversations.value = conversations.value.filter((item) => item.id !== id)

    if (!conversations.value.length) {
      selectedConversationId.value = null
      messages.value = []
      return
    }

    if (wasSelected) {
      selectedConversationId.value = conversations.value[0].id
    }
  } catch (error) {
    console.error('Delete failed:', error)
  }
}

const handleSendMessage = async (payload: {
  conversation_id: number
  mode: 'CHAT'
  message: string
}) => {
  const text = payload.message.trim()
  if (!text) return

  const optimisticUserMessage: MessageItem = {
    role: 'user',
    mode: 'CHAT',
    content: { text },
  }

  messages.value = [...messages.value, optimisticUserMessage]
  isSending.value = true

  try {
    const res = await sendChatMessage(payload)

    const newMessages: MessageItem[] = []
    if (res?.user_message) newMessages.push(res.user_message)
    if (res?.assistant_message) newMessages.push(res.assistant_message)

    if (newMessages.length) {
      messages.value = [
        ...messages.value.slice(0, -1),
        ...newMessages,
      ]
    }
  } catch (error) {
    console.error('Send message failed:', error)
    messages.value = messages.value.slice(0, -1)
  } finally {
    isSending.value = false
  }
}

watch(selectedConversationId, async (id) => {
  if (!id) {
    messages.value = []
    return
  }
  await loadMessages(id)
}, { immediate: true })

onMounted(async () => {
  await loadConversations(false)
})

onBeforeUnmount(() => {
  stopPolling()
})
</script>

<template>
  <AiContentEmptyState
    v-if="!conversations.length && !isUploading"
    @upload-more="handleUploadMore"
  />

  <AiContentLibrary
    v-else
    :conversations="conversations"
    :selected-conversation-id="selectedConversationId"
    :current-title="currentTitle"
    :current-summary="currentSummary"
    :messages="messages"
    :is-renaming-id="isRenamingId"
    :rename-value="renameValue"
    :is-sending="isSending || loadingMessages"
    @select-conversation="handleSelectConversation"
    @upload-more="handleUploadMore"
    @open-menu="handleOpenMenu"
    @close-menu="handleCloseMenu"
    @start-rename="handleStartRename"
    @cancel-rename="handleCancelRename"
    @update-rename-value="renameValue = $event"
    @submit-rename="handleSubmitRename"
    @delete-conversation="handleDeleteConversation"
    @send-message="handleSendMessage"
  />
</template>