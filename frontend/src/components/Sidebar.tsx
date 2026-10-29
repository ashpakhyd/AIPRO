import React from 'react'
import { NavLink } from 'react-router-dom'

const NAV_ITEMS = [
  { to: '/', label: '🏠 Dashboard', end: true },
  { to: '/documents', label: '📁 Documents' },
  { to: '/chat', label: '💬 Chat' },
  { to: '/news', label: '🌐 World News' },
  { to: '/summary', label: '📝 Summary' },
  { to: '/settings', label: '⚙️ Settings' },
]

export const Sidebar: React.FC = () => (
  <aside className="sidebar">
    <div className="sidebar__brand">
      <span className="sidebar__logo">🧠</span>
      <span className="sidebar__title">AI Assistant</span>
    </div>
    <nav className="sidebar__nav">
      {NAV_ITEMS.map(item => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          className={({ isActive }) => `sidebar__link ${isActive ? 'sidebar__link--active' : ''}`}
        >
          {item.label}
        </NavLink>
      ))}
    </nav>
  </aside>
)
