import React, { useState } from 'react'
import type { SourceChunk, AgentStep } from '../types'

interface Props {
  sources: SourceChunk[]
  steps: AgentStep[]
}

export const SourceCitations: React.FC<Props> = ({ sources, steps }) => {
  const [showSources, setShowSources] = useState(false)
  const [showSteps, setShowSteps] = useState(false)
  const [expanded, setExpanded] = useState<number | null>(null)

  if (sources.length === 0 && steps.length === 0) return null

  return (
    <div className="citations">
      <div className="citations__toggles">
        {sources.length > 0 && (
          <button className="citations__pill" onClick={() => setShowSources(s => !s)}>
            📚 {sources.length} source{sources.length > 1 ? 's' : ''}
            <span className="citations__arrow">{showSources ? '▲' : '▼'}</span>
          </button>
        )}
        {steps.length > 0 && (
          <button className="citations__pill citations__pill--steps" onClick={() => setShowSteps(s => !s)}>
            🤖 Agent trace
            <span className="citations__arrow">{showSteps ? '▲' : '▼'}</span>
          </button>
        )}
      </div>

      {showSources && sources.length > 0 && (
        <div className="citations__sources">
          {sources.map((src, i) => (
            <div key={i} className="citation-item">
              <div className="citation-item__header" onClick={() => setExpanded(expanded === i ? null : i)}>
                <span className="citation-item__icon">📄</span>
                <span className="citation-item__name">{src.document_name}</span>
                {src.page_number && <span className="citation-item__page">p.{src.page_number}</span>}
                <span className="citation-item__score">{(src.score * 100).toFixed(0)}%</span>
                <span className="citation-item__chevron">{expanded === i ? '▲' : '▼'}</span>
              </div>
              {expanded === i && (
                <div className="citation-item__text">{src.text}</div>
              )}
            </div>
          ))}
        </div>
      )}

      {showSteps && steps.length > 0 && (
        <div className="citations__steps-list">
          {steps.map((s, i) => (
            <div key={i} className={`step-item ${s.success ? 'step-item--ok' : 'step-item--fail'}`}>
              <strong>{s.tool}</strong> — {s.reason}
              <div className="step-item__summary">{s.result_summary}</div>
              <span className="step-item__meta">{s.sources_count} sources · {s.success ? '✓' : '✗'}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
