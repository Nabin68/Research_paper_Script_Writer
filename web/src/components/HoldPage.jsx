import React from 'react'
import Icon from './Icons.jsx'
import { PLANNED_STAGES } from '../pages.js'
import Workspace, { EmptyPreview } from './Workspace.jsx'

/** Placeholder for pages whose pipeline doesn't exist yet. */
export default function HoldPage({ page }) {
  return (
    <Workspace
      title={page.name}
      subtitle="This page is on hold. Its pipeline will follow the same five stages as Research Paper."
      previewLabel="Preview"
      form={
        <>
          <div className="hold-banner">
            <Icon name="lock" size={16} />
            <span>
              Nothing is wired up here yet — no scripts, no prep steps, no output folders.
              The layout is in place so it only needs its agents.
            </span>
          </div>

          <p className="section-label">Planned stages</p>
          <ol className="planned-list">
            {PLANNED_STAGES.map((s, i) => (
              <li key={s}>
                <span className="planned-num">{i + 1}</span>
                <span className="planned-name">{s}</span>
                <span className="tag-hold">On hold</span>
              </li>
            ))}
          </ol>

          <div className="card-actions">
            <button className="btn" disabled>Run pipeline</button>
          </div>
        </>
      }
      preview={
        <EmptyPreview
          icon={<Icon name="stack" size={26} />}
          title="Nothing to preview"
          body={`Once ${page.name} has its agents, their output will stream here just like Research Paper.`}
        />
      }
    />
  )
}
