const REFRESH_URL = '/api/auth/refresh/'

function getStoredValue(keys: string[]) {
    for (const key of keys) {
        const value = localStorage.getItem(key)
        if (value) return value
    }
    return ''
}

function setStoredValue(keys: string[], value: string) {
    for (const key of keys) {
        if (localStorage.getItem(key) !== null) {
            localStorage.setItem(key, value)
            return
        }
    }

    if (keys.length > 0 && keys[0]) {
        localStorage.setItem(keys[0], value)
    }
}

export function getAccessToken() {
    return getStoredValue(['access', 'accessToken', 'access_token'])
}

export function getRefreshToken() {
    return getStoredValue(['refresh', 'refreshToken', 'refresh_token'])
}

export function setAccessToken(token: string) {
    setStoredValue(['access', 'accessToken', 'access_token'], token)
}

export function setRefreshToken(token: string) {
    setStoredValue(['refresh', 'refreshToken', 'refresh_token'], token)
}

export function clearAuthTokens() {
    for (const key of ['access', 'accessToken', 'access_token', 'refresh', 'refreshToken', 'refresh_token']) {
        localStorage.removeItem(key)
    }
}

async function refreshAccessToken() {
    const refresh = getRefreshToken()

    if (!refresh) {
        throw new Error('No refresh token found.')
    }

    const response = await fetch(REFRESH_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh }),
    })

    const data = await response.json().catch(() => ({}))

    if (!response.ok || !data?.access) {
        clearAuthTokens()
        throw new Error(data?.detail || 'Session expired. Please log in again.')
    }

    setAccessToken(data.access)

    // Quan trọng khi ROTATE_REFRESH_TOKENS = True
    if (data.refresh) {
        setRefreshToken(data.refresh)
    }

    return data.access as string
}

function buildHeaders(headers?: HeadersInit, access?: string) {
    const nextHeaders = new Headers(headers || {})

    if (access) {
        nextHeaders.set('Authorization', `Bearer ${access}`)
    }

    return nextHeaders
}

export async function authFetch(url: string, options: RequestInit = {}) {
    let access = getAccessToken()

    let response = await fetch(url, {
        ...options,
        headers: buildHeaders(options.headers, access),
    })

    if (response.status !== 401) {
        return response
    }

    access = await refreshAccessToken()

    response = await fetch(url, {
        ...options,
        headers: buildHeaders(options.headers, access),
    })

    if (response.status === 401) {
        clearAuthTokens()
    }

    return response
}

export async function authJson<T = any>(url: string, options: RequestInit = {}): Promise<T> {
    const response = await authFetch(url, options)
    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
        throw new Error(data?.detail || data?.hint || 'Request failed')
    }

    return data as T
}