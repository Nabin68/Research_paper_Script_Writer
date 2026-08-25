import React, { useState } from 'react'
import RunView from './RunView.jsx'
import Icon from './Icons.jsx'
import Workspace, { EmptyPreview } from './Workspace.jsx'
import { AGENT_ICONS } from '../pages.js'

/** Agent 5 refines a draft you paste, so it is not part of the default chain. */
const DEFAULT_CHAIN = ['agent1', 'agent2', 'agent3', 'agent4']

export default function PipelinePanel({ agents, run, today, todayStatus }) {
  const [mode, setMode] = useState('manual')
  const [chain, setChain] = useState(DEFAULT_CHAIN)
  const [date, setDate] = useState(today)
  const [paper, setPaper] = useState('')
  const [notes, setNotes] = useState('')

  const toggle = (id) =>
    setChain((c) => (c.includes(id) ? c.filter((x) => x !== id) : [...c, id]))

  // 5 and 6 both work off something you paste in, so they aren't part of the chain
  const chainable = agents.filter((a) => a.id !== 'agent5' && a.id !== 'agent6')
  const ordered = chainable.filter((a) => chain.includes(a.id)).map((a) => a.id)
  const needsPaperNow = mode === 'auto' && ordered.includes('agent4') && !paper.trim()

  const go = () => {
    const inputs = {}
    for (const id of ordered) inputs[id] = { date }
    if (inputs.agent4) Object.assign(inputs.agent4, { paper, notes })
    if (inputs.agent3) Object.assign(inputs.agent3, { picks: '' })
    run.start({ agentIds: ordered, inputs, mode })
  }

  const running = run.busy
  const showRun = run.agents.length > 0 || run.error || running

  return (
    <Workspace
      title="Research Paper"
      subtitle="Run the agents end to end — find today’s papers, pick the top five, deep-dive them, then write the script."
      form={
        <>
          <p className="section-label">Mode</p>
          <div className="segmented full">
            <button className={mode === 'manual' ? 'on' : ''} onClick={() => setMode('manual')}>
              Manual
            </button>
            <button className={mode === 'auto' ? 'on' : ''} onClick={() => setMode('auto')}>
              Fully automated
            </button>
          </div>
          <p className="mode-help">
            {mode === 'manual'
              ? 'Stops after each agent so you can read the output and approve before it feeds the next one.'
              : 'Runs every selected agent back to back without stopping.'}
          </p>

          <p className="section-label">Agents in this run</p>
          <div className="chain">
            {chainable.map((a) => {
              const on = chain.includes(a.id)
              return (
                <button key={a.id} className={`chain-item ${on ? 'on' : ''}`} onClick={() => toggle(a.id)}>
                  <span className="chain-check">{on ? '✓' : ''}</span>
                  <Icon name={AGENT_ICONS[a.num - 1] || 'search'} size={16} className="chain-icon" />
                  <span className="chain-text">
                    <span className="chain-name">{a.name}</span>
                    <span className="chain-tag">{a.tagline}</span>
                  </span>
                  {todayStatus?.[a.id] && <span className="has-output" title="Output exists for today" />}
                </button>
              )
            })}
          </div>
          <p className="chain-note">
            Agents 5 and 6 work off a script you paste in, so they run from their own tabs rather
            than in the chain.
          </p>

          <div className="fields">
            <div className="field">
              <label>Date</label>
              <span className="help">Applies to every agent in the run.</span>
              <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            </div>

            {ordered.includes('agent4') && (
              <div className="field">
                <label>
                  Paper for Agent 4
                  {mode === 'auto' && <span className="req">Required</span>}
                </label>
                <span className="help">
                  {mode === 'manual'
                    ? 'Optional — Manual mode pauses before Agent 4 and asks, once you’ve read the deep-dive.'
                    : 'Automated runs cannot ask, so this is needed up front.'}
                </span>
                <input
                  type="text"
                  value={paper}
                  onChange={(e) => setPaper(e.target.value)}
                  placeholder="Title keywords or URL"
                />
              </div>
            )}

            {ordered.includes('agent4') && (
              <div className="field wide">
                <label>Extra instructions for the script</label>
                <textarea
                  rows={3}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Optional — e.g. lead with the cost number, keep it tight"
                />
              </div>
            )}
          </div>

          <div className="card-actions">
            {running ? (
              <>
                <span className="running-note">
                  <span className="spinner" /> {run.awaiting ? 'Waiting for you' : 'Running…'}
                </span>
                <button className="btn ghost" onClick={run.cancel}>Stop</button>
              </>
            ) : (
              <button className="btn" onClick={go} disabled={!ordered.length || needsPaperNow}>
                <Icon name="play" size={13} />
                Run pipeline ({ordered.length})
              </button>
            )}
          </div>

          {needsPaperNow && (
            <div className="need">Automated mode needs the paper for Agent 4 before it can start.</div>
          )}
        </>
      }
      preview={
        showRun ? (
          <RunView run={run} />
        ) : (
          <EmptyPreview
            icon={<Icon name="stack" size={26} />}
            title="Ready when you are"
            body="Each agent’s steps, live activity and finished files will stream into this panel as the pipeline runs."
          />
        )
      }
    />
  )
}
