export interface DocumentMeta {
  id: string
  filename: string
  original_filename: string
  file_size: number
  file_type: string
  status: 'pending' | 'processing' | 'indexed' | 'failed'
  chunk_count: number
  error_message?: string
  created_at: string
  updated_at: string
}

export interface SourceChunk {
  document_id: string
  document_name: string
  chunk_index: number
  page_number?: number
  text: string
  score: number
}

export interface AgentStep {
  tool: string
  reason: string
  result_summary: string
  sources_count: number
  success: boolean
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: SourceChunk[]
  agent_steps?: AgentStep[]
  no_answer?: boolean
  timestamp: Date
}

export interface ChatResponse {
  answer: string
  sources: SourceChunk[]
  agent_steps: AgentStep[]
  conversation_id: string
  no_answer: boolean
}

export interface SummaryResponse {
  document_id: string
  document_name: string
  summary: string
  key_points: string[]
}

export interface CompareResponse {
  similarities: string[]
  differences: string[]
  summary: string
  sources: SourceChunk[]
}

export interface HealthResponse {
  status: string
  version: string
  llm_provider: string
  llm_model: string
  embedding_model: string
  vector_db: string
  document_count: number
}

export interface ModelStatusResponse {
  llm_provider: string
  llm_model: string
  llm_ready: boolean
  llm_local: boolean
  embedding_model: string
  embedding_ready: boolean
  vector_db_status: string
  document_count: number
}

export interface AgentToolInfo {
  name: string
  description: string
  enabled: boolean
}

export interface NewsArticle {
  id: string; title: string; url: string
  source_name: string; summary: string; category: string; published_at: string | null
}

export interface NewsEvent {
  id: string; title: string; summary: string; category: string
  importance_score: number; source_count: number; ai_analysis: string
  future_scenarios: string; articles: { title: string; url: string; source_name: string }[]
  latitude: number; longitude: number; country: string | null; updated_at: string
  prediction_confidence?: string
  score_breakdown?: { recency: number; sources: number; danger: number; cross_cat: number; cat_weight: number; final: number }
}
