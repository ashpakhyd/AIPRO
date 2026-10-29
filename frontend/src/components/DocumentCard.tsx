import React from 'react'
import type { DocumentMeta } from '../types'
import { formatBytes, formatDate } from '../utils/helpers'

interface Props {
  doc: DocumentMeta
  onDelete: (id: string) => void
  onSelect?: (id: string) => void
  selected?: boolean
}

const STATUS_COLORS: Record<string, string> = {
  indexed: '#22c55e',
  processing: '#f59e0b',
  pending: '#94a3b8',
  failed: '#ef4444',
}

export const DocumentCard: React.FC<Props> = ({ doc, onDelete, onSelect, selected }) => (
  <div
    className={`doc-card ${selected ? 'doc-card--selected' : ''}`}
    onClick={() => onSelect?.(doc.id)}
    style={{ cursor: onSelect ? 'pointer' : 'default' }}
  >
    <div className="doc-card__header">
      <span className="doc-card__name" title={doc.original_filename}>{doc.original_filename}</span>
      <span className="doc-card__badge" style={{ background: STATUS_COLORS[doc.status] }}>
        {doc.status}
      </span>
    </div>
    <div className="doc-card__meta">
      <span>{doc.file_type.toUpperCase()}</span>
      <span>{formatBytes(doc.file_size)}</span>
      <span>{doc.chunk_count} chunks</span>
      <span>{formatDate(doc.created_at)}</span>
    </div>
    {doc.error_message && <div className="doc-card__error">{doc.error_message}</div>}
    <button
      className="btn btn-danger btn-sm doc-card__delete"
      onClick={e => { e.stopPropagation(); onDelete(doc.id) }}
    >
      Delete
    </button>
  </div>
)
