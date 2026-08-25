import React from 'react'
import Icon from './Icons.jsx'
import { PAGES, PLANNED_STAGES, AGENT_ICONS } from '../pages.js'

/**
 * Accordion nav: one section per Instagram page. Clicking a page header selects
 * it and expands it; clicking the header of the page you're already on collapses
 * it back down to a single row.
 */
export default function Sidebar({ agents, view, setView, busy, todayStatus, open, setOpen }) {
  const toggle = (page) => {
    const isCurrent =
      (view.kind === 'page' && view.pageId === page.id) ||
      (view.kind === 'agent' && view.pageId === page.id)

    if (isCurrent && open[page.id]) {
      setOpen((o) => ({ ...o, [page.id]: false }))
      return
    }
    setOpen((o) => ({ ...o, [page.id]: true }))
    setView({ kind: 'page', pageId: page.id })
  }

  return (
    <nav className="sidebar">
      <div className="sidebar-scroll">
        <p className="nav-eyebrow">Pages</p>

        {PAGES.map((page) => {
          const expanded = !!open[page.id]
          const pageActive = view.kind === 'page' && view.pageId === page.id
          const children = page.agentSource ? agents : null

          return (
            <div className={`nav-group ${expanded ? 'expanded' : ''}`} key={page.id}>
              <button
                className={`nav-head ${pageActive ? 'active' : ''}`}
                onClick={() => toggle(page)}
                aria-expanded={expanded}
              >
                <Icon name={page.icon} size={17} className="nav-head-icon" />
                <span className="nav-head-text">
                  <span className="nav-head-name">{page.name}</span>
                  <span className="nav-head-sub">{page.handle}</span>
                </span>
                {page.status === 'hold' && <span className="tag-hold">On hold</span>}
                <Icon name="chevron" size={15} className="nav-chevron" />
              </button>

              <div className="nav-panel" hidden={!expanded}>
                {children
                  ? children.map((a) => {
                      const active = view.kind === 'agent' && view.id === a.id
                      return (
                        <button
                          key={a.id}
                          className={`nav-item ${active ? 'active' : ''}`}
                          onClick={() => setView({ kind: 'agent', id: a.id, pageId: page.id })}
                        >
                          <Icon name={AGENT_ICONS[a.num - 1] || 'search'} size={16} className="nav-item-icon" />
                          <span className="nav-item-name">{a.name}</span>
                          {todayStatus?.[a.id] && <span className="has-output" title="Output exists for today" />}
                        </button>
                      )
                    })
                  : PLANNED_STAGES.map((s) => (
                      <button key={s} className="nav-item planned" disabled>
                        <Icon name="lock" size={15} className="nav-item-icon" />
                        <span className="nav-item-name">{s}</span>
                      </button>
                    ))}
              </div>
            </div>
          )
        })}
      </div>

      <div className="sidebar-foot">
        <span className={`dot ${busy ? 'busy' : ''}`} />
        {busy ? 'Agent running' : 'Idle'}
      </div>
    </nav>
  )
}
