/**
 * index.js — local API for the agent console.
 *
 * Localhost only, single-user, one run at a time (agents run strictly one at a
 * time, per the project's standing rules).
 */

import express from 'express'
import fs from 'node:fs'
import path from 'node:path'
import { AGENTS, ROOT, catalog, byId, today } from './agents.js'
import { Run } from './runner.js'

const app = express()
app.use(express.json({ limit: '8mb' }))

const PORT = Number(process.env.FP_PORT || 8787)

/** Only ever one live run — a second request is refused, not queued. */
let current = null
let counter = 0

const isBusy = () => !!current && (current.status === 'running' || current.status === 'awaiting')

// --- catalog ---------------------------------------------------------------

app.get('/api/agents', (_req, res) => {
  res.json({ root: ROOT, today: today(), agents: catalog() })
})

// --- start a run -----------------------------------------------------------

app.post('/api/run', (req, res) => {
  if (isBusy()) {
    return res.status(409).json({
      error: 'An agent is already running. Agents run one at a time — stop it or wait for it to finish.',
      runId: current.id,
    })
  }

  const { agentId, agentIds, inputs = {}, mode = 'manual' } = req.body || {}
  const ids = agentIds?.length ? agentIds : agentId ? [agentId] : null
  if (!ids) return res.status(400).json({ error: 'Nothing to run.' })

  for (let i = 0; i < ids.length; i++) {
    const agent = byId(ids[i])
    if (!agent) return res.status(400).json({ error: `Unknown agent: ${ids[i]}` })
    // In manual mode the run pauses before each later agent and collects what it
    // still needs, so only the first agent must be complete up front.
    if (mode !== 'auto' && i > 0) continue
    const given = inputs[ids[i]] ?? inputs
    for (const f of agent.inputs || []) {
      // a field gated behind showIf is only required when its gate is open
      if (f.showIf && String(given?.[f.showIf.field] ?? '') !== f.showIf.equals) continue
      if (f.required && !String(given?.[f.name] ?? '').trim()) {
        return res.status(400).json({ error: `Agent ${agent.num} (${agent.name}) needs "${f.label}".` })
      }
    }
  }

  const plan = ids.map((id) => ({ agentId: id, inputs: inputs[id] ?? inputs }))
  const run = new Run(`run_${++counter}_${Date.now()}`, plan, { mode })
  current = run
  run.start()
  res.json({ runId: run.id })
})

// --- live event stream -----------------------------------------------------

app.get('/api/run/:id/stream', (req, res) => {
  const run = current && current.id === req.params.id ? current : null
  if (!run) return res.status(404).end()

  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache, no-transform',
    Connection: 'keep-alive',
    'X-Accel-Buffering': 'no',
  })

  const send = (ev) => res.write(`data: ${JSON.stringify(ev)}\n\n`)
  // replay so a reconnect (or a slow browser) never misses the start of the run
  for (const ev of run.history) send(ev)
  if (run.status === 'done' || run.status === 'error' || run.status === 'cancelled') return res.end()

  const onEvent = (ev) => {
    send(ev)
    if (ev.type === 'run_end') res.end()
  }
  run.on('event', onEvent)

  const ping = setInterval(() => res.write(': ping\n\n'), 15000)
  req.on('close', () => {
    clearInterval(ping)
    run.off('event', onEvent)
  })
})

// --- control ---------------------------------------------------------------

app.post('/api/run/:id/approve', (req, res) => {
  if (!current || current.id !== req.params.id) return res.status(404).json({ error: 'No such run.' })
  current.approve({ stop: !!req.body?.stop, inputs: req.body?.inputs || null })
  res.json({ ok: true })
})

app.post('/api/run/:id/cancel', (req, res) => {
  if (!current || current.id !== req.params.id) return res.status(404).json({ error: 'No such run.' })
  current.cancel()
  res.json({ ok: true })
})

app.get('/api/status', (_req, res) => {
  res.json({ busy: isBusy(), runId: current?.id ?? null, status: current?.status ?? null })
})

// --- file access (read-only, sandboxed to the project root) ----------------

const safeJoin = (rel) => {
  const p = path.resolve(ROOT, rel)
  if (p !== ROOT && !p.startsWith(ROOT + path.sep)) return null
  return p
}

app.get('/api/file', (req, res) => {
  const p = safeJoin(String(req.query.path || ''))
  if (!p) return res.status(400).json({ error: 'Path outside the project folder.' })
  if (!fs.existsSync(p) || !fs.statSync(p).isFile()) return res.status(404).json({ error: 'Not found.' })
  res.json({ path: req.query.path, content: fs.readFileSync(p, 'utf8') })
})

/** Recent outputs per agent, so each tab opens showing your latest work. */
app.get('/api/recent', (req, res) => {
  const dirs = {
    agent1: 'digests',
    agent2: 'picks',
    agent3: 'agent3',
    agent4: 'scripts',
    agent5: 'agent5/refined',
    agent6: 'captions',
  }
  const dir = dirs[String(req.query.agentId)]
  if (!dir) return res.json({ files: [] })
  const abs = path.join(ROOT, dir)
  if (!fs.existsSync(abs)) return res.json({ files: [] })
  const files = fs
    .readdirSync(abs)
    .filter((f) => f.endsWith('.md'))
    .filter((f) => (dir === 'agent3' ? f.startsWith('deepdive_') : true))
    .map((f) => ({ path: `${dir}/${f}`, name: f, mtime: fs.statSync(path.join(abs, f)).mtimeMs }))
    .sort((a, b) => b.mtime - a.mtime)
    .slice(0, 25)
  res.json({ files })
})

/** Which agents already have output for a given date — drives the sidebar dots. */
app.get('/api/today-status', (req, res) => {
  const d = String(req.query.date || today())
  const has = (rel) => fs.existsSync(path.join(ROOT, rel))
  const globbed = (dir, prefix) => {
    const abs = path.join(ROOT, dir)
    if (!fs.existsSync(abs)) return false
    return fs.readdirSync(abs).some((f) => f.startsWith(prefix) && f.endsWith('.md'))
  }
  res.json({
    date: d,
    status: {
      agent1: has(`digests/digest_${d}.md`),
      agent2: has(`picks/top5_${d}.md`),
      agent3: has(`agent3/deepdive_${d}.md`),
      agent4: globbed('scripts', `${d}-`),
      agent5: globbed('agent5/refined', `${d}-`),
      agent6: globbed('captions', `${d}-`),
    },
  })
})

app.listen(PORT, '127.0.0.1', () => {
  console.log(`\n  Agent console API  →  http://127.0.0.1:${PORT}`)
  console.log(`  Project root       →  ${ROOT}`)
  console.log(`  Agents             →  ${AGENTS.map((a) => a.name).join(', ')}\n`)
})
