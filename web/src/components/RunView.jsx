import React, { useEffect, useRef, useState } from 'react'
import Markdown from './Markdown.jsx'

const fmtMs = (ms) => (ms == null ? null : ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`)

function StepRow({ step }) {
  const icon = {
    pending: <span className="s-pending" />,
    running: <span className="s-running" />,
    done: <span className="s-done">✓</span>,
    error: <span className="s-error">✕</span>,
    skipped: <span className="s-skipped">–</span>,
  }[step.status]

  return (
    <li className={`step ${step.status}`}>
      <span className="step-icon">{icon}</span>
      <span className="step-label">{step.label}</span>
      {step.status === 'skipped' && <span className="step-note">not needed</span>}
      {step.status === 'done' && step.ms != null && <span className="step-ms">{fmtMs(step.ms)}</span>}
    </li>
  )
}

function ToolTicker({ tools }) {
  const last = tools[tools.length - 1]
  if (!last) return null
  return (
    <div className="tool-ticker">
      <span className="tool-name">{last.tool}</span>
      {last.detail && <span className="tool-arrow">→</span>}
      {last.detail && <span className="tool-detail">{last.detail}</span>}
    </div>
  )
}

function FileCard({ file, primary }) {
  const [copied, setCopied] = useState(false)
  const [raw, setRaw] = useState(false)

  const copy = async () => {
    await navigator.clipboard.writeText(file.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 1600)
  }

  return (
    <div className={`file-card ${primary ? 'primary' : ''}`}>
      <div className="file-head">
        <span className="file-path">{file.path}</span>
        <span className="file-actions">
          <button className="mini" onClick={() => setRaw(!raw)}>{raw ? 'Rendered' : 'Raw'}</button>
          <button className={`mini ${copied ? 'done' : ''}`} onClick={copy}>
            {copied ? 'Copied ✓' : 'Copy'}
          </button>
        </span>
      </div>
      <div className="file-body">
        {raw ? <pre className="raw">{file.content}</pre> : <Markdown>{file.content}</Markdown>}
      </div>
    </div>
  )
}

function AgentCard({ agent, isLast, status }) {
  const live = isLast && !agent.done && status === 'running'
  const textRef = useRef(null)

  useEffect(() => {
    if (textRef.current) textRef.current.scrollTop = textRef.current.scrollHeight
  }, [agent.text])

  return (
    <section className={`agent-card ${agent.done ? 'done' : live ? 'live' : ''}`}>
      <header className="agent-card-head">
        <h3>{agent.name}</h3>
        {agent.done ? (
          <span className="pill ok">done</span>
        ) : live ? (
          <span className="pill run">working</span>
        ) : null}
      </header>

      <ul className="steps">
        {agent.steps.map((s) => <StepRow key={s.i} step={s} />)}
      </ul>

      {live && <ToolTicker tools={agent.tools} />}

      {agent.text && (
        <div className="claude-text" ref={textRef}>
          {agent.text}
          {live && <span className="caret-blink" />}
        </div>
      )}

      {agent.done && agent.files.length > 0 && (
        <div className="files">
          {agent.files.map((f) => (
            <FileCard key={f.path} file={f} primary={f.path === agent.primary} />
          ))}
        </div>
      )}

      {agent.done && agent.files.length === 0 && (
        <p className="empty-note">No output file was written. Check the activity log below.</p>
      )}
    </section>
  )
}

/**
 * Between agents the run pauses here. Anything the next agent still needs is
 * asked for right in this box — so you can pick the paper *after* reading the
 * deep-dive, rather than guessing it up front.
 */
function Approval({ awaiting, onApprove }) {
  const [vals, setVals] = useState(awaiting.values || {})
  useEffect(() => setVals(awaiting.values || {}), [awaiting.agentId])

  const ask = (awaiting.fields || []).filter((f) => f.type !== 'date')
  const missing = ask.filter((f) => f.required && !String(vals[f.name] ?? '').trim())

  return (
    <div className="approval">
      <div className="approval-text">
        <strong>Next up: {awaiting.agentName}</strong>
        <span>Review the output above — it feeds this agent. Edit anything it needs, then continue.</span>
      </div>

      {ask.length > 0 && (
        <div className="approval-fields">
          {ask.map((f) => (
            <div key={f.name} className={`field ${f.type === 'textarea' ? 'wide' : ''}`}>
              <label>
                {f.label}
                {f.required && <span className="req">required</span>}
              </label>
              {f.type === 'textarea' ? (
                <textarea
                  rows={f.rows || 4}
                  placeholder={f.placeholder || ''}
                  value={vals[f.name] ?? ''}
                  onChange={(e) => setVals((s) => ({ ...s, [f.name]: e.target.value }))}
                />
              ) : (
                <input
                  type="text"
                  placeholder={f.placeholder || ''}
                  value={vals[f.name] ?? ''}
                  onChange={(e) => setVals((s) => ({ ...s, [f.name]: e.target.value }))}
                />
              )}
            </div>
          ))}
        </div>
      )}

      <div className="approval-actions">
        <button className="btn ghost" onClick={() => onApprove(true)}>Stop here</button>
        <button className="btn" onClick={() => onApprove(false, vals)} disabled={missing.length > 0}>
          Approve &amp; continue
        </button>
      </div>
      {missing.length > 0 && (
        <div className="need">Fill in {missing.map((m) => `“${m.label}”`).join(', ')} to continue.</div>
      )}
    </div>
  )
}

export default function RunView({ run }) {
  const logRef = useRef(null)
  const [showLog, setShowLog] = useState(false)

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
  }, [run.log])

  if (run.status === 'idle' && run.agents.length === 0 && !run.error) return null

  return (
    <div className="runview">
      {run.error && (
        <div className="banner error">
          <span className="banner-icon">✕</span>
          <span><strong>Run failed.</strong> {run.error}</span>
        </div>
      )}

      {run.status === 'cancelled' && (
        <div className="banner warn">
          <span className="banner-icon">■</span>
          <span>Run stopped.</span>
        </div>
      )}

      {run.agents.map((a, i) => (
        <AgentCard key={`${a.id}-${i}`} agent={a} isLast={i === run.agents.length - 1} status={run.status} />
      ))}

      {run.awaiting && <Approval awaiting={run.awaiting} onApprove={run.approve} />}

      {run.status === 'done' && (
        <div className="banner ok">
          <span className="banner-icon">✓</span>
          <span>Pipeline complete.</span>
        </div>
      )}

      {run.log.length > 0 && (
        <div className="logbox">
          <button className="log-toggle" onClick={() => setShowLog(!showLog)}>
            <span className="log-caret">{showLog ? '▾' : '▸'}</span>
            Activity log
            <span className="log-count">{run.log.length}</span>
          </button>
          {showLog && (
            <pre className="log" ref={logRef}>
              {run.log.map((l, i) => (
                <span key={i} className={`log-${l.stream}`}>{l.text}</span>
              ))}
            </pre>
          )}
        </div>
      )}
    </div>
  )
}
