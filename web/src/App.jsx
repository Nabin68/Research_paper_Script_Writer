import React, { useCallback, useEffect, useState } from 'react'
import Sidebar from './components/Sidebar.jsx'
import AgentPanel from './components/AgentPanel.jsx'
import PipelinePanel from './components/PipelinePanel.jsx'
import HoldPage from './components/HoldPage.jsx'
import Icon from './components/Icons.jsx'
import { getAgents, getTodayStatus } from './api.js'
import { useRun } from './useRun.js'
import { useTheme } from './useTheme.js'
import { PAGES } from './pages.js'

const prettyDate = (iso) => {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString(undefined, {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
  })
}

export default function App() {
  const [catalog, setCatalog] = useState(null)
  const [loadError, setLoadError] = useState(null)
  const [view, setView] = useState({ kind: 'page', pageId: 'research-paper' })
  const [open, setOpen] = useState({ 'research-paper': true })
  const [todayStatus, setTodayStatus] = useState(null)
  const run = useRun()
  const { isDark, toggle } = useTheme()

  useEffect(() => {
    getAgents().then(setCatalog).catch((e) => setLoadError(e.message))
  }, [])

  const refreshStatus = useCallback((date) => {
    if (!date) return
    getTodayStatus(date).then((r) => setTodayStatus(r.status)).catch(() => {})
  }, [])

  useEffect(() => { if (catalog) refreshStatus(catalog.today) }, [catalog, refreshStatus])

  // a finished run may have produced today's output — repaint the sidebar dots
  useEffect(() => {
    if (catalog && (run.status === 'done' || run.status === 'error')) refreshStatus(catalog.today)
  }, [run.status, catalog, refreshStatus])

  const switchTo = (next) => {
    if (run.busy) return // don't lose a live run behind a nav change
    run.reset()
    setView(next)
  }

  if (loadError) {
    return (
      <div className="boot-error">
        <h1>Can’t reach the local server</h1>
        <p>{loadError}</p>
        <p>Start it with <code>npm run dev</code> in the <code>web</code> folder.</p>
      </div>
    )
  }

  if (!catalog) return <div className="boot">Loading…</div>

  const agent = view.kind === 'agent' ? catalog.agents.find((a) => a.id === view.id) : null
  const page = PAGES.find((p) => p.id === view.pageId)

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">GS</span>
          Growth School
        </div>

        <div className="topbar-right">
          <span className="date-pill">
            <Icon name="calendar" size={14} />
            {prettyDate(catalog.today)}
          </span>
          <button
            className="theme-btn"
            onClick={toggle}
            title={isDark ? 'Switch to light' : 'Switch to dark'}
            aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
          >
            <Icon name={isDark ? 'sun' : 'moon'} size={16} />
          </button>
          <span className="owner">Nabin</span>
        </div>
      </header>

      <div className="body">
        <Sidebar
          agents={catalog.agents}
          view={view}
          setView={switchTo}
          busy={run.busy}
          todayStatus={todayStatus}
          open={open}
          setOpen={setOpen}
        />

        <main className="main">
          {run.busy && (
            <div className="lock-note">
              <span className="spinner" />
              An agent is running — navigation is paused so you don’t lose the output.
            </div>
          )}

          {view.kind === 'agent' && agent ? (
            <AgentPanel agent={agent} run={run} today={catalog.today} />
          ) : page?.status === 'hold' ? (
            <HoldPage page={page} />
          ) : (
            <PipelinePanel
              agents={catalog.agents}
              run={run}
              today={catalog.today}
              todayStatus={todayStatus}
            />
          )}
        </main>
      </div>
    </div>
  )
}
