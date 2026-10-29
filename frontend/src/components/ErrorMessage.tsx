import React from 'react'

interface Props {
  message: string
  onRetry?: () => void
}

export const ErrorMessage: React.FC<Props> = ({ message, onRetry }) => (
  <div className="error-box">
    <span className="error-icon">⚠</span>
    <span>{message}</span>
    {onRetry && <button className="btn btn-sm" onClick={onRetry}>Retry</button>}
  </div>
)
