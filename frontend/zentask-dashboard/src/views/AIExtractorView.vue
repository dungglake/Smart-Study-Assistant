<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AiContentLibrary from '@/components/ai-content/AiContentLibrary.vue'
import AiContentEmptyState from '@/components/ai-content/AiContentEmptyState.vue'
import {
  deleteMaterial,
  getConversationMessages,
  getConversations,
  getMaterialDetail,
  renameMaterial,
  streamChatMessage,
  uploadMaterial,
  sendChatMessage,
  renameStudioMessage,
  deleteStudioMessage,
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
  mode: 'CHAT' | 'FLASHCARD' | 'QUIZ' 
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
const route = useRoute()
const router = useRouter()
const processingMaterialIds = ref<number[]>([])
const pollingTimer = ref<number | null>(null)

const selectedConversation = computed(
  () => conversations.value.find((item) => item.id === selectedConversationId.value) || null
)

const currentTitle = computed(() => selectedConversation.value?.title || 'AI Content Extractor')
const currentSummary = computed(() => selectedConversation.value?.summary || '')

const loadConversations = async (preferLatest = false) => {
  try {
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

    const queryConversationId = Number(route.query.conversation_id)

    if (
      queryConversationId &&
      conversations.value.some((item) => item.id === queryConversationId)
    ) {
      selectedConversationId.value = queryConversationId
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
  } catch (error) {
    console.error('Load conversations failed:', error)
    conversations.value = []
    selectedConversationId.value = null
    messages.value = []
  }
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

  await router.replace({
    path: '/extractor',
    query: {
      conversation_id: String(id),
    },
  })

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
    const target = conversations.value.find((item) => item.id === id)
    if (!target) return

    const updated = await renameMaterial(target.material, title)

    conversations.value = conversations.value.map((item) =>
      item.material === target.material
        ? {
            ...item,
            title: updated.title,
            material_title: updated.title,
          }
        : item
    )

    handleCancelRename()
  } catch (error) {
    console.error('Rename failed:', error)
  }
}

const handleDeleteConversation = async (id: number) => {
  try {
    const target = conversations.value.find((item) => item.id === id)
    if (!target) return

    const materialId = target.material
    const deletedSelectedMaterial =
      selectedConversation.value?.material === materialId

    await deleteMaterial(materialId)

    conversations.value = conversations.value.filter(
      (item) => item.material !== materialId
    )

    if (!conversations.value.length) {
      selectedConversationId.value = null
      messages.value = []
      return
    }

    if (deletedSelectedMaterial) {
      selectedConversationId.value = conversations.value[0].id
    }
  } catch (error) {
    console.error('Delete failed:', error)
  }
}

watch(selectedConversationId, async (id) => {
  if (!id) return

  const currentQueryId = Number(route.query.conversation_id)
  if (currentQueryId === id) return

  await router.replace({
    path: '/extractor',
    query: {
      conversation_id: String(id),
    },
  })
})
const isRenamingStudioId = ref<number | null>(null)
const studioRenameValue = ref('')

const handleOpenStudioMenu = (id: number) => {
  messages.value = messages.value.map((item) => ({
    ...item,
    menuOpen: item.id === id ? !item.menuOpen : false,
  }))
}

const handleCloseStudioMenu = () => {
  messages.value = messages.value.map((item) => ({
    ...item,
    menuOpen: false,
  }))
}

const handleStartRenameStudio = (item: MessageItem) => {
  isRenamingStudioId.value = item.id ?? null
  studioRenameValue.value = item.title || ''
}

const handleCancelRenameStudio = () => {
  isRenamingStudioId.value = null
  studioRenameValue.value = ''
}

const handleSubmitRenameStudio = async (id: number) => {
  const title = studioRenameValue.value.trim()
  if (!title) return
  const updated = await renameStudioMessage(id, title)

  messages.value = messages.value.map((item) =>
    item.id === id ? { ...item, title: updated.title, menuOpen: false } : item
  )

  handleCancelRenameStudio()
}

const handleDeleteStudioItem = async (id: number) => {
  await deleteStudioMessage(id)
  messages.value = messages.value.filter((item) => item.id !== id)
}

const handleSendMessage = async (payload: {
  conversation_id: number
  mode: 'CHAT' | 'FLASHCARD' | 'QUIZ'
  message: string
}) => {
  const text = payload.message.trim()
  if (!text || isSending.value) return

  isSending.value = true

  try {
    if (payload.mode === 'CHAT') {
      const optimisticUserMessage: MessageItem = {
        role: 'user',
        mode: payload.mode,
        content: { text },
      }

      const assistantPlaceholder: MessageItem = {
        role: 'assistant',
        mode: payload.mode,
        content: { text: '' },
      }

      messages.value = [
        ...messages.value,
        optimisticUserMessage,
        assistantPlaceholder,
      ]

      await streamChatMessage(payload, {
        onStart(data) {
          console.log('stream started', data)
        },

        onToken(token) {
          const lastIndex = messages.value.length - 1
          const last = messages.value[lastIndex]

          if (!last || last.role !== 'assistant') return

          messages.value[lastIndex] = {
            ...last,
            content: {
              ...(last.content || {}),
              text: ((last.content && last.content.text) || '') + token,
            },
          }
        },

        onDone(data) {
          const assistantMessage = data?.assistant_message
          if (!assistantMessage) return

          const lastIndex = messages.value.length - 1
          messages.value[lastIndex] = assistantMessage
        },

        onError(error) {
          console.error('Stream error:', error)

          const lastIndex = messages.value.length - 1
          const last = messages.value[lastIndex]

          if (last?.role === 'assistant') {
            messages.value[lastIndex] = {
              ...last,
              content: {
                text: 'Cannot receive realtime feedback from server.',
              },
            }
          }
        },
      })
    } else {
      const data = await sendChatMessage(payload)
      const assistantMessage = data?.assistant_message

      console.log('STUDIO RESPONSE:', data)
      console.log('ASSISTANT MESSAGE:', assistantMessage)
      console.log('ASSISTANT CONTENT:', assistantMessage?.content)

      if (assistantMessage) {
        messages.value = [...messages.value, assistantMessage]
      } else {
        messages.value = [
          ...messages.value,
          {
            role: 'assistant',
            mode: payload.mode,
            content: {
              message: 'Generation failed.',
              items: [],
            },
          },
        ]
      }
    }
  } catch (error) {
    console.error('Send failed:', error)

    if (payload.mode === 'CHAT') {
      const lastIndex = messages.value.length - 1

      messages.value[lastIndex] = {
        role: 'assistant',
        mode: payload.mode,
        content: {
          message: 'Cannot connect to chat stream.',
        },
      }
    } else {
      messages.value = [
        ...messages.value,
        {
          role: 'assistant',
          mode: payload.mode,
          content: {
            message: 'Cannot generate this content right now.',
            items: [],
          },
        },
      ]
    }
  } finally {
    isSending.value = false
  }
}

watch(
  selectedConversationId,
  async (id) => {
    if (!id) {
      messages.value = []
      return
    }
    await loadMessages(id)
  },
  { immediate: true }
)

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
    :is-renaming-studio-id="isRenamingStudioId"
    :studio-rename-value="studioRenameValue"
    @open-studio-menu="handleOpenStudioMenu"
    @close-studio-menu="handleCloseStudioMenu"
    @start-rename-studio="handleStartRenameStudio"
    @cancel-rename-studio="handleCancelRenameStudio"
    @update-studio-rename-value="studioRenameValue = $event"
    @submit-rename-studio="handleSubmitRenameStudio"
    @delete-studio-item="handleDeleteStudioItem"
  />
</template>