import axios from 'axios'
import type {
  DocumentMeta,
  ChatResponse,
  SummaryResponse,
  CompareResponse,
  HealthResponse,
  ModelStatusResponse,
  AgentToolInfo,
} from '../types'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const message = err.response?.data?.error || err.response?.data?.detail || err.message || 'Request failed'
    return Promise.reject(new Error(message))
  }
)

export const documentsApi = {
  list: () => api.get<{ documents: DocumentMeta[]; total: number }>('/documents').then(r => r.data),
  upload: (file: File, onProgress?: (pct: number) => void) => {
    const form = new FormData()
    form.append('file', file)
    return api.post<{ document_id: string; filename: string; status: string; message: string }>(
      '/documents/upload',
      form,
      { onUploadProgress: e => onProgress?.(Math.round((e.loaded * 100) / (e.total || 1))) }
    ).then(r => r.data)
  },
  get: (id: string) => api.get<DocumentMeta>(`/documents/${id}`).then(r => r.data),
  delete: (id: string) => api.delete(`/documents/${id}`).then(r => r.data),
  summarize: (id: string) => api.post<SummaryResponse>(`/documents/${id}/summary`).then(r => r.data),
  compare: (document_ids: string[], question?: string) =>
    api.post<CompareResponse>('/documents/compare', { document_ids, question }).then(r => r.data),
}

export const chatApi = {
  send: (question: string, document_ids?: string[], conversation_id?: string) =>
    api.post<ChatResponse>('/chat', { question, document_ids, conversation_id, use_agent: true }).then(r => r.data),

  stream: (
    question: string,
    document_ids: string[] | undefined,
    conversation_id: string | undefined,
    onToken: (token: string) => void,
    onMeta: (meta: { conversation_id: string; sources: any[] }) => void,
    onDone: () => void,
    onError: (err: string) => void,
  ) => {
    const ctrl = new AbortController()
    fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, document_ids, conversation_id, use_agent: true }),
      signal: ctrl.signal,
    }).then(async res => {
      if (!res.ok) { onError('Stream request failed'); return }
      const reader = res.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = JSON.parse(line.slice(6))
          if (data.type === 'meta') onMeta({ conversation_id: data.conversation_id, sources: data.sources })
          else if (data.type === 'token') onToken(data.text)
          else if (data.type === 'done') onDone()
        }
      }
    }).catch(e => { if (e.name !== 'AbortError') onError(e.message) })
    return () => ctrl.abort()
  },
}

export const systemApi = {
  health: () => api.get<HealthResponse>('/health').then(r => r.data),
  modelStatus: () => api.get<ModelStatusResponse>('/models/status').then(r => r.data),
  agentTools: () => api.get<AgentToolInfo[]>('/agent/tools').then(r => r.data),
}
