import React, { useEffect, useState } from 'react'
import { systemApi } from '../services/api'
import type { ModelStatusResponse, AgentToolInfo } from '../types'
import { Spinner } from '../components/Spinner'
import { ErrorMessage } from '../components/ErrorMessage'

export const Settings: React.FC = () => {
  const [status, setStatus] = useState<ModelStatusResponse | null>(null)
  const [tools, setTools] = useState<AgentToolInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const [s, t] = await Promise.all([systemApi.modelStatus(), systemApi.agentTools()])
      setStatus(s)
      setTools(t)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  if (loading) return <Spinner message="Loading settings…" size="lg" />
  if (error) return <ErrorMessage message={error} onRetry={load} />

  return (
    <div className="page">
      <h1 className="page__title">Settings</h1>

      {status && (
        <>
          <div className="info-panel">
            <h2>Model Configuration</h2>
            <div className="info-grid">
              <span>LLM Provider</span>
              <span className="mono">{status.llm_provider}</span>

              <span>LLM Model</span>
              <span className="mono">{status.llm_model}</span>

              <span>LLM Type</span>
              <span>{status.llm_local ? 'Local (no API key needed)' : 'API-based'}</span>

              <span>LLM Ready</span>
              <span className={`badge badge--${status.llm_ready ? 'green' : 'red'}`}>
                {status.llm_ready ? 'Ready' : 'Not loaded'}
              </span>

              <span>Embedding Model</span>
              <span className="mono">{status.embedding_model}</span>

              <span>Embedding Ready</span>
              <span className={`badge badge--${status.embedding_ready ? 'green' : 'red'}`}>
                {status.embedding_ready ? 'Ready' : 'Not loaded'}
              </span>
            </div>
          </div>

          <div className="info-panel">
            <h2>Vector Database</h2>
            <div className="info-grid">
              <span>Status</span>
              <span>{status.vector_db_status}</span>
              <span>Documents</span>
              <span>{status.document_count}</span>
            </div>
          </div>
        </>
      )}

      <div className="info-panel">
        <h2>Agent Tools</h2>
        <div className="tools-list">
          {tools.map(tool => (
            <div key={tool.name} className="tool-item">
              <div className="tool-item__header">
                <strong>{tool.name}</strong>
                <span className={`badge badge--${tool.enabled ? 'green' : 'gray'}`}>
                  {tool.enabled ? 'Enabled' : 'Disabled'}
                </span>
              </div>
              <p className="tool-item__desc">{tool.description}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="info-panel info-panel--warn">
        <h2>⚠ Security Notice</h2>
        <p>
          API keys and secrets are configured via the <code>.env</code> file and are never
          displayed here. This application is intended for local use. Add authentication
          before exposing it to multiple users or the public internet.
        </p>
      </div>
    </div>
  )
}
