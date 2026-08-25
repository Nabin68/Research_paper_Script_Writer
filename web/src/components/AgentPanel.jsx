import React, { useEffect, useState } from 'react'
import RunView from './RunView.jsx'
import Markdown from './Markdown.jsx'
import Icon from './Icons.jsx'
import Workspace, { EmptyPreview } from './Workspace.jsx'
import { getFile, getRecent } from '../api.js'
import { AGENT_ICONS } from '../pages.js'

/** Merge in the variant matching the controlling field's current value. */
function resolve(field, values) {
  if (!field.variantOn || !field.variants) return field
  return { ...field, ...(field.variants[values[field.variantOn]] || {}) }
}

function Field({ field, value, onChange, today }) {
  const common = {
    id: field.name,
    value: value ?? '',
    onChange: (e) => onChange(field.name, e.target.value),
    placeholder: field.placeholder || '',
  }

  if (field.type === 'segmented') {
    return (
      <div className="field">
        <label>{field.label}</label>
        {field.help && <span className="help">{field.help}</span>}
        <div className="segmented full">
          {field.options.map((o) => (
            <button
              key={o.value}
              type="button"
              className={(value ?? field.default) === o.value ? 'on' : ''}
              onClick={() => onChange(field.name, o.value)}
            >
              {o.label}
            </button>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="field">
      <label htmlFor={field.name}>
        {field.label}
        {field.required && <span className="req">Required</span>}
      </label>
      {field.help && <span className="help">{field.help}</span>}
      {field.type === 'textarea' ? (
        <textarea {...common} rows={field.rows || 6} />
      ) : field.type === 'date' ? (
        <input type="date" {...common} value={value ?? today} />
      ) : (
        <input type="text" {...common} />
      )}
    </div>
  )
}

function Recent({ agentId }) {
  const [files, setFiles] = useState([])
  const [open, setOpen] = useState(null)

  useEffect(() => {
    setOpen(null)
    getRecent(agentId).then((r) => setFiles(r.files)).catch(() => setFiles([]))
  }, [agentId])

  if (!files.length) {
    return (
      <EmptyPreview
        icon={<Icon name="play" size={24} />}
        title="No output yet"
        body="Fill in the settings and run this agent — its progress and result will appear here."
      />
    )
  }

  const view = async (path) => {
    if (open?.path === path) return setOpen(null)
    setOpen(await getFile(path))
  }

  return (
    <div className="recent">
      <p className="section-label">Previous outputs</p>
      <div className="recent-list">
        {files.map((f) => (
          <button
            key={f.path}
            className={`chip ${open?.path === f.path ? 'active' : ''}`}
            onClick={() => view(f.path)}
          >
            {f.name.replace(/\.md$/, '')}
          </button>
        ))}
      </div>
      {open ? (
        <div className="file-card">
          <div className="file-head">
            <span className="file-path">{open.path}</span>
            <button className="mini" onClick={() => navigator.clipboard.writeText(open.content)}>Copy</button>
          </div>
          <div className="file-body"><Markdown>{open.content}</Markdown></div>
        </div>
      ) : (
        <p className="recent-hint">Pick one to read it, or run the agent to make a new one.</p>
      )}
    </div>
  )
}

export default function AgentPanel({ agent, run, today }) {
  // seed any field that declares a default (e.g. the Generate/Refine switch)
  const seed = () => {
    const s = {}
    for (const f of agent.inputs || []) if (f.default !== undefined) s[f.name] = f.default
    return s
  }

  const [values, setValues] = useState(seed)

  useEffect(() => {
    setValues(seed())
    run.reset()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agent.id])

  const set = (k, v) => setValues((s) => ({ ...s, [k]: v }))

  // a field gated behind showIf only exists when its gate is open
  const visible = (agent.inputs || [])
    .filter((f) => !f.showIf || String(values[f.showIf.field] ?? '') === f.showIf.equals)
    .map((f) => resolve(f, values))

  const missing = visible.filter((f) => f.required && !String(values[f.name] ?? '').trim())

  const go = () => {
    const inputs = {}
    for (const f of visible) inputs[f.name] = values[f.name]
    for (const f of agent.inputs || []) {
      if (f.type === 'segmented' && inputs[f.name] === undefined) inputs[f.name] = values[f.name] ?? f.default
      if (f.type === 'date' && !inputs[f.name]) inputs[f.name] = today
    }
    run.start({ agentId: agent.id, inputs })
  }

  const running = run.busy
  const showRun = run.agents.length > 0 || run.error || running

  return (
    <Workspace
      title={
        <span className="title-with-icon">
          <span className="title-icon">
            <Icon name={AGENT_ICONS[agent.num - 1] || 'search'} size={17} />
          </span>
          {agent.name}
          <span className="title-badge">Agent {agent.num}</span>
        </span>
      }
      subtitle={agent.blurb}
      form={
        <>
          <div className="fields">
            {visible.map((f) => (
              <Field key={f.name} field={f} value={values[f.name]} onChange={set} today={today} />
            ))}
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
              <button className="btn" onClick={go} disabled={missing.length > 0}>
                <Icon name="play" size={13} /> Run agent
              </button>
            )}
          </div>

          {missing.length > 0 && !running && (
            <div className="need">Fill in {missing.map((m) => `“${m.label}”`).join(', ')} to run.</div>
          )}
        </>
      }
      preview={showRun ? <RunView run={run} /> : <Recent agentId={agent.id} />}
    />
  )
}
