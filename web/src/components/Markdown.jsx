import React, { useMemo } from 'react'

/**
 * Small, dependency-free markdown renderer — enough for the pipeline's outputs
 * (headings, bold, italics, links, lists, rules, code, tables-as-text).
 * Everything is escaped first, so file content can never inject markup.
 */
const esc = (s) =>
  s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')

function inline(s) {
  return esc(s)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>')
    .replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>')
}

function toHtml(md) {
  const lines = String(md || '').split('\n')
  const out = []
  let inList = false
  let inCode = false

  const closeList = () => { if (inList) { out.push('</ul>'); inList = false } }

  for (const raw of lines) {
    const line = raw.replace(/\s+$/, '')

    if (/^```/.test(line)) {
      closeList()
      out.push(inCode ? '</code></pre>' : '<pre><code>')
      inCode = !inCode
      continue
    }
    if (inCode) { out.push(esc(raw) + '\n'); continue }

    if (!line.trim()) { closeList(); continue }

    if (/^---+$/.test(line.trim())) { closeList(); out.push('<hr/>'); continue }

    const h = line.match(/^(#{1,6})\s+(.*)$/)
    if (h) {
      closeList()
      const n = h[1].length
      out.push(`<h${n}>${inline(h[2])}</h${n}>`)
      continue
    }

    const li = line.match(/^\s*[-*+]\s+(.*)$/)
    if (li) {
      if (!inList) { out.push('<ul>'); inList = true }
      out.push(`<li>${inline(li[1])}</li>`)
      continue
    }

    const oli = line.match(/^\s*\d+\.\s+(.*)$/)
    if (oli) {
      if (!inList) { out.push('<ul>'); inList = true }
      out.push(`<li>${inline(oli[1])}</li>`)
      continue
    }

    closeList()
    out.push(`<p>${inline(line)}</p>`)
  }
  closeList()
  if (inCode) out.push('</code></pre>')
  return out.join('\n')
}

export default function Markdown({ children }) {
  const html = useMemo(() => toHtml(children), [children])
  return <div className="md" dangerouslySetInnerHTML={{ __html: html }} />
}
