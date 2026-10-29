import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { documentsApi, systemApi } from '../services/api'
import type { DocumentMeta, HealthResponse } from '../types'
import { Spinner } from '../components/Spinner'
import { ErrorMessage } from '../components/ErrorMessage'
import { formatBytes, formatDate } from '../utils/helpers'

export const Dashboard: React.FC = () => {
  const [docs, setDocs] = useState<DocumentMeta[]>([])
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const [docsRes, healthRes] = await Promise.all([
        documentsApi.list(),
        systemApi.health(),
      ])
      setDocs(docsRes.documents)
      setHealth(healthRes)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  if (loading) return <Spinner message="Loading dashboard..." size="lg" />
  if (error) return <ErrorMessage message={error} onRetry={load} />

  const indexed = docs.filter(d => d.status === 'indexed').length
  const failed = docs.filter(d => d.status === 'failed').length

  return (
    <div className="page">
      <h1 className="page__title">Dashboard</h1>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-card__value">{docs.length}</div>
          <div className="stat-card__label">Total Documents</div>
        </div>
        <div className="stat-card stat-card--green">
          <div className="stat-card__value">{indexed}</div>
          <div className="stat-card__label">Indexed</div>
        </div>
        <div className="stat-card stat-card--red">
          <div className="stat-card__value">{failed}</div>
          <div className="stat-card__label">Failed</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__value">{health?.document_count ?? 0}</div>
          <div className="stat-card__label">Vector Chunks</div>
        </div>
      </div>

      {health && (
        <div className="info-panel">
          <h2>System Status</h2>
          <div className="info-grid">
            <span>Status</span><span className="badge badge--green">{health.status}</span>
            <span>LLM Provider</span><span>{health.llm_provider}</span>
            <span>LLM Model</span><span className="mono">{health.llm_model}</span>
            <span>Embedding</span><span className="mono">{health.embedding_model}</span>
            <span>Vector DB</span><span>{health.vector_db}</span>
          </div>
        </div>
      )}

      <div className="section">
        <div className="section__header">
          <h2>Recent Documents</h2>
          <Link to="/documents" className="btn btn-sm">View All</Link>
        </div>
        {docs.length === 0 ? (
          <div className="empty-state">
            <p>No documents uploaded yet.</p>
            <Link to="/documents" className="btn">Upload Documents</Link>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr><th>Name</th><th>Type</th><th>Size</th><th>Status</th><th>Date</th></tr>
            </thead>
            <tbody>
              {docs.slice(0, 5).map(doc => (
                <tr key={doc.id}>
                  <td>{doc.original_filename}</td>
                  <td>{doc.file_type.toUpperCase()}</td>
                  <td>{formatBytes(doc.file_size)}</td>
                  <td><span className={`badge badge--${doc.status}`}>{doc.status}</span></td>
                  <td>{formatDate(doc.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="quick-actions">
        <Link to="/documents" className="btn">📤 Upload Document</Link>
        <Link to="/chat" className="btn btn-primary">💬 Start Chat</Link>
      </div>
    </div>
  )
}
