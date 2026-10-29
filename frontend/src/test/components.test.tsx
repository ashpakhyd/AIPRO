import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { Sidebar } from '../components/Sidebar'
import { ErrorMessage } from '../components/ErrorMessage'
import { Spinner } from '../components/Spinner'
import { DocumentCard } from '../components/DocumentCard'
import type { DocumentMeta } from '../types'

describe('Sidebar', () => {
  it('renders all nav links', () => {
    render(<MemoryRouter><Sidebar /></MemoryRouter>)
    expect(screen.getByText(/Dashboard/i)).toBeInTheDocument()
    expect(screen.getByText(/Documents/i)).toBeInTheDocument()
    expect(screen.getByText(/Chat/i)).toBeInTheDocument()
    expect(screen.getByText(/Summary/i)).toBeInTheDocument()
    expect(screen.getByText(/Settings/i)).toBeInTheDocument()
  })
})

describe('ErrorMessage', () => {
  it('renders error text', () => {
    render(<ErrorMessage message="Something went wrong" />)
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  })

  it('renders retry button when provided', () => {
    const retry = vi.fn()
    render(<ErrorMessage message="Error" onRetry={retry} />)
    expect(screen.getByText('Retry')).toBeInTheDocument()
  })
})

describe('Spinner', () => {
  it('renders message when provided', () => {
    render(<Spinner message="Loading..." />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })
})

describe('DocumentCard', () => {
  const doc: DocumentMeta = {
    id: 'doc1',
    filename: 'doc1.pdf',
    original_filename: 'My Document.pdf',
    file_size: 1024 * 50,
    file_type: 'pdf',
    status: 'indexed',
    chunk_count: 12,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }

  it('renders document name and status', () => {
    render(<DocumentCard doc={doc} onDelete={vi.fn()} />)
    expect(screen.getByText('My Document.pdf')).toBeInTheDocument()
    expect(screen.getByText('indexed')).toBeInTheDocument()
  })

  it('calls onDelete when delete button clicked', () => {
    const onDelete = vi.fn()
    render(<DocumentCard doc={doc} onDelete={onDelete} />)
    screen.getByText('Delete').click()
    expect(onDelete).toHaveBeenCalledWith('doc1')
  })

  it('shows error message when status is failed', () => {
    const failedDoc: DocumentMeta = { ...doc, status: 'failed', error_message: 'Extraction failed' }
    render(<DocumentCard doc={failedDoc} onDelete={vi.fn()} />)
    expect(screen.getByText('Extraction failed')).toBeInTheDocument()
  })
})
