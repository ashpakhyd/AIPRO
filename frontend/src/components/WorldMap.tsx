import React, { useState } from 'react'
import { ComposableMap, Geographies, Geography, Marker, ZoomableGroup } from 'react-simple-maps'
import type { NewsEvent } from '../types'

const GEO_URL = 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json'

const CATEGORY_COLORS: Record<string, string> = {
  world: '#3b82f6', geopolitics: '#ef4444', conflict: '#f97316',
  politics: '#ec4899', economy: '#f59e0b', technology: '#8b5cf6', general: '#6b7280',
}

// Fallback spread positions for events with no geo (0,0)
const FALLBACK_COORDS: [number, number][] = [
  [-30, 20], [60, 30], [-80, 10], [20, -20], [100, 20], [-50, 50],
]

interface Props {
  events: NewsEvent[]
  selectedId?: string | null
  onSelect: (event: NewsEvent | null) => void
}

export const WorldMap: React.FC<Props> = ({ events, selectedId, onSelect }) => {
  const [zoom, setZoom] = useState(1)
  const [center, setCenter] = useState<[number, number]>([10, 15])

  let fallbackIdx = 0
  const mappable = events.map(e => {
    const hasGeo = e.latitude !== 0 || e.longitude !== 0
    const coords: [number, number] = hasGeo
      ? [e.longitude, e.latitude]
      : FALLBACK_COORDS[fallbackIdx++ % FALLBACK_COORDS.length]
    return { event: e, coords }
  })

  const getColor = (cat: string) => CATEGORY_COLORS[cat] || '#6b7280'
  const getRadius = (score: number) => Math.max(6, (score / 100) * 16)
  // Higher score = faster pulse
  const getPulseDur = (score: number) => `${Math.max(1.2, 3 - (score / 100) * 1.8).toFixed(1)}s`

  return (
    <div className="world-map-wrap" onClick={() => onSelect(null)}>
      <div className="map-controls">
        <button className="map-ctrl-btn" onClick={e => { e.stopPropagation(); setZoom(z => Math.min(z * 1.5, 8)) }}>+</button>
        <button className="map-ctrl-btn" onClick={e => { e.stopPropagation(); setZoom(z => Math.max(z / 1.5, 1)) }}>−</button>
        <button className="map-ctrl-btn map-ctrl-btn--reset" onClick={e => { e.stopPropagation(); setZoom(1); setCenter([10, 15]) }}>⊙</button>
      </div>

      <ComposableMap
        projection="geoNaturalEarth1"
        style={{ width: '100%', height: '100%' }}
        projectionConfig={{ scale: 155 }}
      >
        <ZoomableGroup center={center} zoom={zoom} onMoveEnd={({ coordinates, zoom: z }) => { setCenter(coordinates); setZoom(z) }}>
          <Geographies geography={GEO_URL}>
            {({ geographies }) =>
              geographies.map(geo => (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  fill="#1a1f35"
                  stroke="#2a3050"
                  strokeWidth={0.5}
                  style={{
                    default: { outline: 'none' },
                    hover: { fill: '#22263a', outline: 'none' },
                    pressed: { outline: 'none' },
                  }}
                />
              ))
            }
          </Geographies>

          {mappable.map(({ event, coords }, idx) => {
            const color = getColor(event.category)
            const r = getRadius(event.importance_score)
            const isSelected = selectedId === event.id
            const dur = getPulseDur(event.importance_score)

            return (
              <Marker
                key={event.id}
                coordinates={coords}
                onClick={e => { (e as unknown as React.MouseEvent).stopPropagation(); onSelect(isSelected ? null : event) }}
              >
                {/* Outer glow rings */}
                <circle r={r * 2.8} fill={color} opacity={0.06} style={{ cursor: 'pointer' }} />
                <circle r={r * 1.8} fill={color} opacity={0.13} style={{ cursor: 'pointer' }} />

                {/* Pulse animation — ALL markers */}
                <circle r={r} fill={color} opacity={0}>
                  <animate attributeName="r" values={`${r};${r * 3.2};${r}`} dur={dur} repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.5;0;0.5" dur={dur} repeatCount="indefinite" />
                </circle>

                {/* Core dot */}
                <circle
                  r={r}
                  fill={color}
                  stroke={isSelected ? '#fff' : 'rgba(255,255,255,0.3)'}
                  strokeWidth={isSelected ? 2.5 : 0.5}
                  opacity={0.95}
                  style={{ cursor: 'pointer', filter: `drop-shadow(0 0 ${r * 0.8}px ${color})` }}
                />

                {/* Rank label */}
                <text textAnchor="middle" y={-r - 5}
                  style={{ fontSize: 7, fill: '#fff', fontWeight: 700, pointerEvents: 'none' }}>
                  #{idx + 1}
                </text>

                {/* Country name */}
                {event.country && (
                  <text textAnchor="middle" y={r + 11}
                    style={{ fontSize: 6, fill: color, fontWeight: 600, pointerEvents: 'none', opacity: 0.9 }}>
                    {event.country}
                  </text>
                )}
              </Marker>
            )
          })}
        </ZoomableGroup>
      </ComposableMap>
    </div>
  )
}
