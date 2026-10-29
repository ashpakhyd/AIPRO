import React from 'react'

interface Props {
  message?: string
  size?: 'sm' | 'md' | 'lg'
}

export const Spinner: React.FC<Props> = ({ message, size = 'md' }) => {
  const sz = size === 'sm' ? 16 : size === 'lg' ? 40 : 24
  return (
    <div className="spinner-wrap">
      <div className="spinner" style={{ width: sz, height: sz }} />
      {message && <span className="spinner-msg">{message}</span>}
    </div>
  )
}
