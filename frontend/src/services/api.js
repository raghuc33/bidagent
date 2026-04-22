const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function getToken() {
    return localStorage.getItem('token')
}

function authHeaders(extra = {}) {
    const token = getToken()
    const headers = { ...extra }
    if (token) headers['Authorization'] = `Bearer ${token}`
    return headers
}

async function request(path, options = {}) {
    const response = await fetch(`${API_BASE}${path}`, options)

    if (!response.ok) {
        if (response.status === 401) {
            localStorage.removeItem('token')
            localStorage.removeItem('user')
            window.location.href = '/login'
            throw new Error('Session expired')
        }
        const errorData = await response.json().catch(() => ({ detail: response.statusText }))
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`)
    }

    return response.json()
}

// Auth
export async function signup(email, password, name) {
    const data = await request('/api/v1/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, name }),
    })
    localStorage.setItem('token', data.token)
    localStorage.setItem('user', JSON.stringify(data.user))
    return data
}

export async function login(email, password) {
    const data = await request('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
    })
    localStorage.setItem('token', data.token)
    localStorage.setItem('user', JSON.stringify(data.user))
    return data
}

export function logout() {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
}

export function getStoredUser() {
    const raw = localStorage.getItem('user')
    return raw ? JSON.parse(raw) : null
}

export function isAuthenticated() {
    return !!getToken()
}

// Health
export async function checkHealth() {
    return request('/health')
}

// Go/No-Go
export async function analyzeGoNoGo(file) {
    const formData = new FormData()
    formData.append('file', file)
    return request('/api/v1/go-no-go', { method: 'POST', headers: authHeaders(), body: formData })
}

// LLM
export async function generate(prompt, systemPrompt = '') {
    return request('/api/v1/generate', {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ prompt, system_prompt: systemPrompt }),
    })
}

// Knowledge Base
export async function uploadToKnowledgeBase(file) {
    const formData = new FormData()
    formData.append('file', file)
    return request('/api/v1/knowledge/upload', { method: 'POST', headers: authHeaders(), body: formData })
}

export async function listKnowledgeBase() {
    return request('/api/v1/knowledge', { headers: authHeaders() })
}

// Bid Builder
export async function extractSections(tenderName = '', docId = null) {
    return request('/api/v1/bid/extract-sections', {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ tender_name: tenderName, doc_id: docId }),
    })
}

export async function generateBidResponse(sectionTitle, sectionDescription = '', docId = null) {
    return request('/api/v1/bid/generate-response', {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ section_title: sectionTitle, section_description: sectionDescription, doc_id: docId }),
    })
}

// Sessions
export async function createSession(tenderName, tenderDocId, sections, drafts) {
    return request('/api/v1/sessions', {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ tender_name: tenderName, tender_doc_id: tenderDocId, sections, drafts }),
    })
}

export async function listSessions() {
    return request('/api/v1/sessions', { headers: authHeaders() })
}

export async function getSession(sessionId) {
    return request(`/api/v1/sessions/${sessionId}`, { headers: authHeaders() })
}

export async function updateSessionDrafts(sessionId, drafts, status) {
    return request(`/api/v1/sessions/${sessionId}`, {
        method: 'PUT',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ drafts, status }),
    })
}

export async function deleteSession(sessionId) {
    return request(`/api/v1/sessions/${sessionId}`, { method: 'DELETE', headers: authHeaders() })
}

// Compliance
export async function runComplianceCheck(drafts) {
    return request('/api/v1/bid/compliance', {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ drafts }),
    })
}

// Pipeline (SSE)
export function connectPipeline(sectionTitle, sectionDescription, docId, sessionId, sectionId, onEvent) {
    const body = JSON.stringify({
        section_title: sectionTitle,
        section_description: sectionDescription,
        doc_id: docId,
        session_id: sessionId,
        section_id: sectionId,
    })

    fetch(`${API_BASE}/api/v1/bid/generate-pipeline`, {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body,
    }).then(async (response) => {
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
            const { done, value } = await reader.read()
            if (done) break

            buffer += decoder.decode(value, { stream: true })
            const lines = buffer.split('\n')
            buffer = lines.pop() || ''

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6))
                        onEvent(data)
                    } catch {}
                }
            }
        }
    })
}

// Chat
export async function sendChatMessage(sessionId, sectionId, message, currentDraft, sectionTitle, sectionDescription, docId) {
    return request('/api/v1/chat/message', {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({
            session_id: sessionId,
            section_id: sectionId,
            message,
            current_draft: currentDraft,
            section_title: sectionTitle,
            section_description: sectionDescription,
            doc_id: docId,
        }),
    })
}

export async function getChatHistory(sessionId, sectionId) {
    return request(`/api/v1/chat/history/${sessionId}/${sectionId}`, { headers: authHeaders() })
}
