import React, { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { chatApi, documentsApi } from '../services/api'
import type { ChatMessage, DocumentMeta } from '../types'
import { SourceCitations } from '../components/SourceCitations'
import { generateId } from '../utils/helpers'

const SUGGESTIONS = [
  'Summarize this document',
  'What are the key requirements?',
  'What is the main topic?',
  'List the important points',
]

const SendIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
)

const PlusIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
  </svg>
)

export const Chat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [docs, setDocs] = useState<DocumentMeta[]>([])
  const [selectedDocs, setSelectedDocs] = useState<string[]>([])
  const [conversationId, setConversationId] = useState<string | undefined>()
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const navigate = useNavigate()

  useEffect(() => {
    documentsApi.list().then(r => setDocs(r.documents.filter(d => d.status === 'indexed')))
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const autoResize = () => {
    const ta = textareaRef.current
    if (!ta) return
    ta.style.height = 'auto'
    ta.style.height = Math.min(ta.scrollHeight, 200) + 'px'
  }

  const send = (question?: string) => {
    const q = (question ?? input).trim()
    if (!q || loading) return
    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'

    const userMsg: ChatMessage = { id: generateId(), role: 'user', content: q, timestamp: new Date() }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    const assistantId = generateId()
    setMessages(prev => [...prev, { id: assistantId, role: 'assistant', content: '', timestamp: new Date() }])

    chatApi.stream(
      q,
      selectedDocs.length > 0 ? selectedDocs : undefined,
      conversationId,
      (token) => {
        setMessages(prev => prev.map(m =>
          m.id === assistantId ? { ...m, content: m.content + token } : m
        ))
      },
      (meta) => {
        setConversationId(meta.conversation_id)
        setMessages(prev => prev.map(m =>
          m.id === assistantId ? { ...m, sources: meta.sources } : m
        ))
      },
      () => setLoading(false),
      (err) => {
        setMessages(prev => prev.map(m =>
          m.id === assistantId ? { ...m, content: `Error: ${err}` } : m
        ))
        setLoading(false)
      },
    )
  }

  const toggleDoc = (id: string) =>
    setSelectedDocs(prev => prev.includes(id) ? prev.filter(d => d !== id) : [...prev, id])

  const clearChat = () => { setMessages([]); setConversationId(undefined) }

  return (
    <div className="chat-layout">
      {/* Sidebar */}
      <aside className="chat-sidebar">
        <div className="chat-sidebar__top">
          <button className="chat-sidebar__new" onClick={clearChat}>
            <PlusIcon /> New chat
          </button>
        </div>

        <div className="chat-sidebar__docs">
          <div className="chat-sidebar__section">Documents</div>
          {docs.length === 0 ? (
            <div className="chat-sidebar__empty">No indexed documents</div>
          ) : (
            docs.map(doc => (
              <label key={doc.id} className="doc-filter">
                <input type="checkbox" checked={selectedDocs.includes(doc.id)} onChange={() => toggleDoc(doc.id)} />
                <span title={doc.original_filename}>{doc.original_filename}</span>
              </label>
            ))
          )}
        </div>

        <div className="chat-sidebar__bottom">
          <button className="chat-sidebar__clear" onClick={() => navigate('/')}>
            ← Back to Dashboard
          </button>
          {messages.length > 0 && (
            <button className="chat-sidebar__clear" onClick={clearChat} style={{ marginTop: 4 }}>
              🗑 Clear chat
            </button>
          )}
        </div>
      </aside>

      {/* Main */}
      <div className="chat-main">
        <div className="chat-messages">
          {messages.length === 0 ? (
            <div className="chat-empty">
              <div className="chat-empty__logo">🧠</div>
              <div className="chat-empty__title">AI Knowledge Assistant</div>
              <div className="chat-empty__subtitle">
                {docs.length > 0
                  ? 'Ask anything about your uploaded documents'
                  : 'Upload documents first, then ask questions about them'}
              </div>
              {docs.length > 0 && (
                <div className="chat-empty__suggestions">
                  {SUGGESTIONS.map(s => (
                    <button key={s} className="chat-suggestion" onClick={() => send(s)}>{s}</button>
                  ))}
                </div>
              )}
            </div>
          ) : (
            messages.map(msg => (
              <div key={msg.id} className={`chat-row chat-row--${msg.role}`}>
                <div className="chat-row__inner">
                  <div className={`chat-avatar chat-avatar--${msg.role}`}>
                    {msg.role === 'user' ? 'U' : '✦'}
                  </div>
                  <div className={`chat-bubble chat-bubble--${msg.role}`}>
                    {msg.role === 'assistant' ? (
                      <>
                        {msg.no_answer && (
                          <div className="no-answer-badge">⚠ No sufficient information found</div>
                        )}
                        <div className="chat-bubble__content">
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                          {loading && msg.content === '' && (
                            <span className="chat-cursor" />
                          )}
                          {loading && msg.content !== '' && messages[messages.length - 1]?.id === msg.id && (
                            <span className="chat-cursor" />
                          )}
                        </div>
                        {msg.sources && msg.sources.length > 0 && (
                          <SourceCitations sources={msg.sources} steps={msg.agent_steps || []} />
                        )}
                      </>
                    ) : (
                      <div className="chat-bubble__content">{msg.content}</div>
                    )}
                    <div className="chat-bubble__time">{msg.timestamp.toLocaleTimeString()}</div>
                  </div>
                </div>
              </div>
            ))
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="chat-input-area">
          <div className="chat-input-wrap">
            <textarea
              ref={textareaRef}
              className="chat-input"
              value={input}
              onChange={e => { setInput(e.target.value); autoResize() }}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
              }}
              placeholder="Message AI Assistant..."
              rows={1}
              disabled={loading}
            />
            <button className="chat-send" onClick={() => send()} disabled={loading || !input.trim()}>
              <SendIcon />
            </button>
          </div>
          <div className="chat-input-hint">
            {selectedDocs.length > 0
              ? `Searching in ${selectedDocs.length} selected document${selectedDocs.length > 1 ? 's' : ''}`
              : 'Searching all documents · Enter to send · Shift+Enter for newline'}
          </div>
        </div>
      </div>
    </div>
  )
}
