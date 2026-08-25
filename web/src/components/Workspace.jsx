import React from 'react'

/**
 * The two-column workspace: settings on the left, live preview on the right.
 * Collapses to one column on narrow screens.
 */
export default function Workspace({ title, subtitle, form, preview, previewLabel = 'Live preview' }) {
  return (
    <div className="workspace">
      <section className="col-form">
        <div className="surface">
          <header className="surface-head">
            <h2>{title}</h2>
            {subtitle && <p className="subtitle">{subtitle}</p>}
          </header>
          {form}
        </div>
      </section>

      <aside className="col-preview">
        <div className="preview-label">{previewLabel}</div>
        {preview}
      </aside>
    </div>
  )
}

export function EmptyPreview({ icon, title, body }) {
  return (
    <div className="empty-preview">
      {icon}
      <p className="empty-title">{title}</p>
      <p className="empty-body">{body}</p>
    </div>
  )
}
