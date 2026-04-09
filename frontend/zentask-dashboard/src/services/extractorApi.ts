import axios from 'axios'

const API_BASE_URL = 'http://127.0.0.1:8000/api'

const api = axios.create({
    baseURL: API_BASE_URL,
})

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

export type ChatMode = 'CHAT' | 'FLASHCARD' | 'QUIZ' | 'MINDMAP'

export const getMaterialDetail = async (id: number) => {
    const res = await api.get(`/materials/${id}/`)
    return res.data
}

export const uploadMaterial = async (file: File, title?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    if (title) formData.append('title', title)

    const res = await api.post('/materials/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data
}

export const getConversations = async (materialId?: number) => {
    const params = materialId ? { material_id: materialId } : {}
    const res = await api.get('/conversations/', { params })
    return res.data
}

export const getConversationMessages = async (conversationId: number) => {
    const res = await api.get(`/conversations/${conversationId}/messages/`)
    return res.data
}

export const renameConversation = async (id: number, title: string) => {
    const res = await api.patch(`/conversations/${id}/`, { title })
    return res.data
}

export const deleteConversation = async (id: number) => {
    const res = await api.delete(`/conversations/${id}/`)
    return res.data
}

export const sendChatMessage = async (payload: {
    conversation_id: number
    mode: ChatMode
    message: string
}) => {
    const res = await api.post('/chat/', payload)
    return res.data
}

type StreamPayload = {
    conversation_id: number
    mode: ChatMode
    message: string
}

type StreamHandlers = {
    onStart?: (data: any) => void
    onToken?: (token: string) => void
    onDone?: (data: any) => void
    onError?: (error: Error | string) => void
}

export const streamChatMessage = async (
    payload: StreamPayload,
    handlers: StreamHandlers = {}
) => {
    const token = localStorage.getItem('access_token')

    const response = await fetch(`${API_BASE_URL}/chat/stream/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(payload),
    })

    if (!response.ok || !response.body) {
        const text = await response.text()
        throw new Error(text || 'Unable to start stream')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        const events = buffer.split('\n\n')
        buffer = events.pop() || ''

        for (const event of events) {
            const line = event
                .split('\n')
                .find((l) => l.startsWith('data: '))

            if (!line) continue

            const raw = line.replace(/^data:\s*/, '')

            try {
                const data = JSON.parse(raw)

                if (data.type === 'start') {
                    handlers.onStart?.(data)
                } else if (data.type === 'token') {
                    handlers.onToken?.(data.token || '')
                } else if (data.type === 'done') {
                    handlers.onDone?.(data)
                } else if (data.type === 'error') {
                    handlers.onError?.(data.detail || 'Streaming error')
                }
            } catch (error) {
                handlers.onError?.(error instanceof Error ? error : 'Invalid stream event')
            }
        }
    }
}

export default api