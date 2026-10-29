import React, { useEffect, useState, useCallback } from 'react'
import { documentsApi } from '../services/api'
import type { DocumentMeta } from '../types'
import { DocumentCard } from '../components/DocumentCard'
import { FileUpload } from '../components/FileUpload'
import { Spinner } from '../components/Spinner'
import { ErrorMessage } from '../components/ErrorMessage'

export const Documents: React.FC = () => {
  const [docs, setDocs] = useState<DocumentMeta[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadMsg, setUploadMsg] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await documentsApi.list()
      setDocs(res.documents)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleUpload = async (file: File) => {
    setUploading(true)
    setUploadProgress(0)
    setUploadMsg('')
    try {
      const res = await documentsApi.upload(file, setUploadProgress)
      setUploadMsg(`✓ ${res.message}`)
      await load()
    } catch (e: any) {
      setUploadMsg(`✗ ${e.message}`)
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this document and its indexed data?')) return
    try {
      await documentsApi.delete(id)
      setDocs(prev => prev.filter(d => d.id !== id))
    } catch (e: any) {
      setError(e.message)
    }
  }

  return (
    <div className="page">
      <h1 className="page__title">Documents</h1>

      <FileUpload onUpload={handleUpload} uploading={uploading} progress={uploadProgress} />
      {uploadMsg && (
        <div className={`upload-msg ${uploadMsg.startsWith('✓') ? 'upload-msg--ok' : 'upload-msg--err'}`}>
          {uploadMsg}
        </div>
      )}

      <div className="section">
        <div className="section__header">
          <h2>Uploaded Documents ({docs.length})</h2>
          <button className="btn btn-sm" onClick={load}>Refresh</button>
        </div>

        {loading ? (
          <Spinner message="Loading documents..." />
        ) : error ? (
          <ErrorMessage message={error} onRetry={load} />
        ) : docs.length === 0 ? (
          <div className="empty-state">
            <p>No documents uploaded yet. Upload a PDF, DOCX, or TXT file above.</p>
          </div>
        ) : (
          <div className="doc-grid">
            {docs.map(doc => (
              <DocumentCard key={doc.id} doc={doc} onDelete={handleDelete} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
