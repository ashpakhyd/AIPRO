import React, { useEffect, useState } from 'react'
import { documentsApi } from '../services/api'
import type { DocumentMeta, SummaryResponse } from '../types'
import { Spinner } from '../components/Spinner'
import { ErrorMessage } from '../components/ErrorMessage'

export const Summary: React.FC = () => {
  const [docs, setDocs] = useState<DocumentMeta[]>([])
  const [selectedId, setSelectedId] = useState('')
  const [summary, setSummary] = useState<SummaryResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [docsLoading, setDocsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    documentsApi.list()
      .then(r => setDocs(r.documents.filter(d => d.status === 'indexed')))
      .finally(() => setDocsLoading(false))
  }, [])

  const generate = async () => {
    if (!selectedId) return
    setLoading(true)
    setError('')
    setSummary(null)
    try {
      const res = await documentsApi.summarize(selectedId)
      setSummary(res)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <h1 className="page__title">Document Summary</h1>

      {docsLoading ? (
        <Spinner message="Loading documents..." />
      ) : docs.length === 0 ? (
        <div className="empty-state">
          <p>No indexed documents available. Upload and index a document first.</p>
        </div>
      ) : (
        <div className="summary-controls">
          <select
            className="select"
            value={selectedId}
            onChange={e => { setSelectedId(e.target.value); setSummary(null); setError('') }}
          >
            <option value="">— Select a document —</option>
            {docs.map(d => (
              <option key={d.id} value={d.id}>{d.original_filename}</option>
            ))}
          </select>
          <button
            className="btn btn-primary"
            onClick={generate}
            disabled={!selectedId || loading}
          >
            {loading ? 'Generating…' : 'Generate Summary'}
          </button>
        </div>
      )}

      {loading && <Spinner message="Generating summary…" size="lg" />}
      {error && <ErrorMessage message={error} />}

      {summary && (
        <div className="summary-result">
          <h2>{summary.document_name}</h2>
          <div className="summary-result__overview">
            <h3>Overview</h3>
            <p>{summary.summary}</p>
          </div>
          {summary.key_points.length > 0 && (
            <div className="summary-result__points">
              <h3>Key Points</h3>
              <ul>
                {summary.key_points.map((pt, i) => <li key={i}>{pt}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
