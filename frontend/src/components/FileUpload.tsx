import React, { useCallback, useState } from 'react'

interface Props {
  onUpload: (file: File) => void
  uploading: boolean
  progress: number
}

const ALLOWED = ['.pdf', '.docx', '.txt']
const MAX_MB = 50

export const FileUpload: React.FC<Props> = ({ onUpload, uploading, progress }) => {
  const [dragOver, setDragOver] = useState(false)
  const [error, setError] = useState('')

  const validate = (file: File): string => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!ALLOWED.includes(ext)) return `Unsupported type. Allowed: ${ALLOWED.join(', ')}`
    if (file.size > MAX_MB * 1024 * 1024) return `File too large. Max ${MAX_MB}MB.`
    return ''
  }

  const handle = useCallback((file: File) => {
    const err = validate(file)
    if (err) { setError(err); return }
    setError('')
    onUpload(file)
  }, [onUpload])

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handle(file)
  }

  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handle(file)
    e.target.value = ''
  }

  return (
    <div
      className={`upload-zone ${dragOver ? 'upload-zone--active' : ''}`}
      onDragOver={e => { e.preventDefault(); setDragOver(true) }}
      onDragLeave={() => setDragOver(false)}
      onDrop={onDrop}
    >
      <input type="file" id="file-input" accept=".pdf,.docx,.txt" onChange={onChange} hidden />
      <label htmlFor="file-input" className="upload-zone__label">
        <span className="upload-zone__icon">📄</span>
        <span>Drop a file here or <strong>click to browse</strong></span>
        <span className="upload-zone__hint">PDF, DOCX, TXT — max {MAX_MB}MB</span>
      </label>
      {error && <div className="upload-zone__error">{error}</div>}
      {uploading && (
        <div className="upload-progress">
          <div className="upload-progress__bar" style={{ width: `${progress}%` }} />
          <span>{progress}%</span>
        </div>
      )}
    </div>
  )
}
