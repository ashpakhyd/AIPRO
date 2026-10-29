import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { WorldMap } from '../components/WorldMap'
import { useGetTop5EventsQuery, useGetArticlesQuery, useRefreshNewsMutation } from '../store/newsApi'
import type { NewsEvent } from '../types'

const CATEGORY_COLORS: Record<string, string> = {
  world: '#3b82f6', geopolitics: '#ef4444', conflict: '#f97316',
  politics: '#ec4899', economy: '#f59e0b', technology: '#8b5cf6', general: '#6b7280',
}
const CATEGORY_ICONS: Record<string, string> = {
  world: '🌍', geopolitics: '⚔️', conflict: '🔥',
  politics: '🏛️', economy: '📉', technology: '💻', general: '📰',
}

export const News: React.FC = () => {
  const [sliderOpen, setSliderOpen] = useState(false)
  const [selectedEvent, setSelectedEvent] = useState<NewsEvent | null>(null)
  const navigate = useNavigate()

  const { data: evData, isLoading: evLoading, isError: evError } = useGetTop5EventsQuery()
  const { data: arData, isLoading: arLoading } = useGetArticlesQuery(50)
  const [refreshNews, { isLoading: refreshing }] = useRefreshNewsMutation()

  const events = evData?.events ?? []
  const articles = arData?.articles ?? []
  const loading = evLoading || arLoading

  const handleRefresh = async () => {
    await refreshNews()
  }

  const handleSelect = (event: NewsEvent | null) => {
    setSelectedEvent(event)
    if (event) setSliderOpen(false)
  }

  const color = selectedEvent ? (CATEGORY_COLORS[selectedEvent.category] || '#6b7280') : '#6b7280'

  return (
    <div className="news-fullscreen">

      {/* Top Bar */}
      <div className="news-topbar">
        <div className="news-topbar__left">
          <button className="news-back-btn" onClick={() => navigate('/')}>← Back</button>
          <span className="news-topbar__title">🌐 World Intelligence</span>
        </div>
        <div className="news-topbar__right">
          {evError && <span className="news-topbar__error">⚠ Failed to load news</span>}
          <button className="btn btn-primary btn-sm" onClick={handleRefresh} disabled={refreshing}>
            {refreshing ? '⏳ Refreshing...' : '🔄 Refresh'}
          </button>
          <button
            className={`news-slider-toggle ${sliderOpen ? 'news-slider-toggle--open' : ''}`}
            onClick={() => { setSliderOpen(o => !o); setSelectedEvent(null) }}
          >
            📋 {sliderOpen ? '✕ Close' : 'News Feed'}
          </button>
        </div>
      </div>

      {/* Body */}
      <div className="news-body">

        {/* Map */}
        <div className="news-map-full">
          {loading ? (
            <div className="news-map-loading">
              <div className="news-map-loading__spinner" />
              <span>Fetching global news...</span>
            </div>
          ) : events.length === 0 ? (
            <div className="news-map-loading">
              <span>📡 No events yet. Click Refresh.</span>
            </div>
          ) : (
            <WorldMap events={events} selectedId={selectedEvent?.id} onSelect={handleSelect} />
          )}

          {!loading && events.length > 0 && (
            <div className="news-overlay-cards">
              {events.map((e, i) => (
                <div
                  key={e.id}
                  className={`news-overlay-card ${selectedEvent?.id === e.id ? 'news-overlay-card--active' : ''}`}
                  style={{ borderColor: selectedEvent?.id === e.id ? CATEGORY_COLORS[e.category] : CATEGORY_COLORS[e.category] + '44' }}
                  onClick={() => handleSelect(selectedEvent?.id === e.id ? null : e)}
                >
                  <div className="news-overlay-card__rank" style={{ color: CATEGORY_COLORS[e.category] }}>#{i + 1}</div>
                  <div className="news-overlay-card__content">
                    <div className="news-overlay-card__cat">{CATEGORY_ICONS[e.category]} {e.category}</div>
                    <div className="news-overlay-card__title">{e.title}</div>
                  </div>
                  <div className="news-overlay-card__score">⚡{e.importance_score.toFixed(0)}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Event Detail Panel */}
        {selectedEvent && (
          <div className="news-detail-panel" style={{ borderLeftColor: color + '44' }}>
            <div className="news-detail-panel__header" style={{ borderBottomColor: color + '33' }}>
              <div>
                <span className="news-detail-panel__cat" style={{ color, background: color + '18', border: `1px solid ${color}33` }}>
                  {CATEGORY_ICONS[selectedEvent.category]} {selectedEvent.category}
                </span>
              </div>
              <button className="news-detail-panel__close" onClick={() => setSelectedEvent(null)}>✕</button>
            </div>

            <div className="news-detail-panel__body">
              <h2 className="news-detail-panel__title">{selectedEvent.title}</h2>

              <div className="news-detail-panel__stats">
                <span>📰 {selectedEvent.source_count} sources</span>
                <span style={{ color: '#f59e0b' }}>⚡ {selectedEvent.importance_score.toFixed(0)}/100</span>
                {selectedEvent.country && (
                  <span style={{ color: '#94a3b8' }}>📍 {selectedEvent.country}</span>
                )}
                {selectedEvent.prediction_confidence && (
                  <span className={`news-confidence news-confidence--${selectedEvent.prediction_confidence.toLowerCase()}`}>
                    {selectedEvent.prediction_confidence === 'HIGH' ? '🔴' : selectedEvent.prediction_confidence === 'MEDIUM' ? '🟡' : '🟢'} {selectedEvent.prediction_confidence}
                  </span>
                )}
              </div>

              {selectedEvent.score_breakdown && (
                <div className="news-score-breakdown">
                  <div className="news-score-breakdown__label">📊 Score Breakdown</div>
                  <div className="news-score-breakdown__bars">
                    {[
                      { label: '⏱ Recency', val: selectedEvent.score_breakdown.recency, max: 100, color: '#3b82f6' },
                      { label: '📰 Sources', val: selectedEvent.score_breakdown.sources, max: 45, color: '#10b981' },
                      { label: '⚠ Danger', val: selectedEvent.score_breakdown.danger, max: 40, color: '#ef4444' },
                      { label: '🔗 Cross-Cat', val: selectedEvent.score_breakdown.cross_cat, max: 20, color: '#8b5cf6' },
                    ].map(({ label, val, max, color }) => (
                      <div key={label} className="news-score-bar">
                        <span className="news-score-bar__label">{label}</span>
                        <div className="news-score-bar__track">
                          <div className="news-score-bar__fill" style={{ width: `${Math.min((val / max) * 100, 100)}%`, background: color }} />
                        </div>
                        <span className="news-score-bar__val">{val.toFixed(0)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedEvent.summary && (
                <p className="news-detail-panel__summary">{selectedEvent.summary}</p>
              )}

              {selectedEvent.ai_analysis && (
                <div className="news-detail-panel__section">
                  <div className="news-detail-panel__section-label">🤖 AI Analysis</div>
                  <p>{selectedEvent.ai_analysis}</p>
                </div>
              )}

              {selectedEvent.future_scenarios && (
                <div className="news-detail-panel__section">
                  <div className="news-detail-panel__section-label">🔮 Future Scenarios</div>
                  <p style={{ whiteSpace: 'pre-line' }}>{selectedEvent.future_scenarios}</p>
                </div>
              )}

              {selectedEvent.articles.length > 0 && (
                <div className="news-detail-panel__section">
                  <div className="news-detail-panel__section-label">📚 Sources</div>
                  {selectedEvent.articles.map((a, i) => (
                    <a key={i} href={a.url} target="_blank" rel="noopener noreferrer" className="news-detail-panel__source">
                      <span className="news-detail-panel__source-name">{a.source_name}</span>
                      <span className="news-detail-panel__source-title">{a.title}</span>
                      <span>↗</span>
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* News Feed Slider */}
        <div className={`news-slider ${sliderOpen ? 'news-slider--open' : ''}`}>
          <div className="news-slider__header">
            <span>📋 Latest News Feed</span>
            <span className="news-slider__count">{articles.length} articles</span>
          </div>
          <div className="news-slider__list">
            {articles.length === 0 ? (
              <div className="news-slider__empty">No articles yet. Click Refresh.</div>
            ) : (
              articles.map((a, i) => (
                <a key={a.id} href={a.url} target="_blank" rel="noopener noreferrer" className="news-slider__item">
                  <div className="news-slider__item-num">{i + 1}</div>
                  <div className="news-slider__item-body">
                    <div className="news-slider__item-source" style={{ color: CATEGORY_COLORS[a.category] || '#6b7280' }}>
                      {CATEGORY_ICONS[a.category] || '📰'} {a.source_name}
                    </div>
                    <div className="news-slider__item-title">{a.title}</div>
                    {a.summary && <div className="news-slider__item-summary">{a.summary.slice(0, 100)}...</div>}
                  </div>
                  <span className="news-slider__item-arrow">↗</span>
                </a>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
