import React from 'react'
import { Provider } from 'react-redux'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { store } from './store'
import { Sidebar } from './components/Sidebar'
import { Dashboard } from './pages/Dashboard'
import { Documents } from './pages/Documents'
import { Chat } from './pages/Chat'
import { Summary } from './pages/Summary'
import { Settings } from './pages/Settings'
import { News } from './pages/News'
import './styles.css'

const App: React.FC = () => (
  <Provider store={store}>
    <BrowserRouter>
      <Routes>
        <Route path="/chat" element={<Chat />} />
        <Route path="/news" element={<News />} />
        <Route path="*" element={
          <div className="app-layout">
            <Sidebar />
            <main className="app-main">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/documents" element={<Documents />} />
                <Route path="/summary" element={<Summary />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </main>
          </div>
        } />
      </Routes>
    </BrowserRouter>
  </Provider>
)

export default App
