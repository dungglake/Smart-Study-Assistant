import axios from 'axios'

const api = axios.create({
    baseURL: 'http://127.0.0.1:8000/api',
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

export default api