/**
 * runner.js — executes an agent's steps and emits a live event stream.
 *
 * Python steps shell out to the existing prep scripts. Claude steps shell out to
 * the Claude Code CLI in headless mode (`claude -p --output-format stream-json`),
 * which authenticates with the same subscription the terminal session uses — so
 * there is no API key anywhere in this app.
 */

import { spawn } from 'node:child_process'
import { EventEmitter } from 'node:events'
import fs from 'node:fs'
import path from 'node:path'
import { ROOT, byId } from './agents.js'

const CLAUDE_TOOLS = 'Read Write Edit Glob Grep WebSearch WebFetch TodoWrite'

function resolveClaude() {
  if (process.env.FP_CLAUDE_BIN) return process.env.FP_CLAUDE_BIN
  const candidates = [
    path.join(process.env.USERPROFILE || '', '.local', 'bin', 'claude.exe'),
    path.join(process.env.LOCALAPPDATA || '', 'Programs', 'claude', 'claude.exe'),
  ]
  for (const c of candidates) if (c && fs.existsSync(c)) return c
  return 'claude' // fall back to PATH
}

const PYTHON = process.env.FP_PYTHON || 'python'

/** One run = one agent, or a whole pipeline of agents. Never two at once. */
export class Run extends EventEmitter {
  constructor(id, plan, { mode = 'manual' } = {}) {
    super()
    this.id = id
    this.plan = plan // [{ agentId, inputs }]
    this.mode = mode // 'auto' | 'manual'
    this.status = 'idle' // idle | running | awaiting | done | error | cancelled
    this.history = [] // every event, so a late/reconnecting client sees the full run
    this.cancelled = false
    this.child = null
    this._approve = null
  }

  emitEvent(ev) {
    const e = { ...ev, t: Date.now() }
    this.history.push(e)
    this.emit('event', e)
  }

  cancel() {
    this.cancelled = true
    if (this.child) {
      try {
        // kill the whole tree — claude.exe spawns helpers
        spawn('taskkill', ['/pid', String(this.child.pid), '/T', '/F'], { stdio: 'ignore' })
      } catch {
        try { this.child.kill('SIGTERM') } catch {}
      }
    }
    if (this._approve) this._approve({ cancelled: true })
  }

  approve(decision) {
    if (this._approve) {
      const fn = this._approve
      this._approve = null
      fn(decision)
    }
  }

  waitForApproval(agent, values) {
    this.status = 'awaiting'
    this.emitEvent({
      type: 'awaiting',
      agentId: agent.id,
      agentName: `Agent ${agent.num} · ${agent.name}`,
      // let the UI ask for anything this agent still needs — e.g. which paper to
      // write about, once you've actually read the deep-dive
      fields: (agent.inputs || []).map(({ name, label, type, rows, required, placeholder, help }) => ({
        name, label, type, rows, required, placeholder, help,
      })),
      values: values || {},
    })
    return new Promise((resolve) => { this._approve = resolve })
  }

  // -------------------------------------------------------------------------

  async start() {
    this.status = 'running'
    this.emitEvent({ type: 'run_start', plan: this.plan.map((p) => p.agentId), mode: this.mode })

    try {
      for (let i = 0; i < this.plan.length; i++) {
        if (this.cancelled) break
        const { agentId, inputs } = this.plan[i]
        const agent = byId(agentId)
        if (!agent) throw new Error(`Unknown agent: ${agentId}`)

        // In manual mode, pause before every agent after the first so the user
        // can read the previous output and approve (or stop) before it feeds on.
        let stepInputs = inputs
        if (this.mode === 'manual' && i > 0) {
          const d = await this.waitForApproval(agent, inputs)
          if (d?.cancelled || d?.stop) {
            this.emitEvent({ type: 'run_stopped', reason: 'You stopped the pipeline.' })
            this.status = 'cancelled'
            this.emitEvent({ type: 'run_end', status: 'cancelled' })
            return
          }
          if (d?.inputs) stepInputs = { ...inputs, ...d.inputs }
          this.status = 'running'
        }

        await this.runAgent(agent, stepInputs)
      }

      if (this.cancelled) {
        this.status = 'cancelled'
        this.emitEvent({ type: 'run_end', status: 'cancelled' })
      } else {
        this.status = 'done'
        this.emitEvent({ type: 'run_end', status: 'done' })
      }
    } catch (err) {
      this.status = 'error'
      this.emitEvent({ type: 'error', message: err.message })
      this.emitEvent({ type: 'run_end', status: 'error' })
    }
  }

  async runAgent(agent, inputs) {
    const built = agent.build(inputs || {})
    const ctx = { ...inputs, view: built.view, produced: [] }

    this.emitEvent({
      type: 'agent_start',
      agentId: agent.id,
      agentName: `Agent ${agent.num} · ${agent.name}`,
      steps: built.steps.map((s, i) => ({ i, label: s.label, kind: s.kind })),
    })

    for (let i = 0; i < built.steps.length; i++) {
      if (this.cancelled) return
      const step = built.steps[i]

      if (step.when && !step.when(ctx)) {
        this.emitEvent({ type: 'step', agentId: agent.id, i, label: step.label, status: 'skipped' })
        continue
      }

      this.emitEvent({ type: 'step', agentId: agent.id, i, label: step.label, status: 'running' })
      const startedAt = Date.now()
      try {
        if (step.kind === 'writeFile') {
          const dest = path.join(ROOT, step.path)
          fs.mkdirSync(path.dirname(dest), { recursive: true })
          fs.writeFileSync(dest, step.content ?? '', 'utf8')
          this.emitEvent({ type: 'log', stream: 'sys', text: `wrote ${step.path}\n` })
        } else if (step.kind === 'python') {
          const out = await this.exec(PYTHON, step.args, agent.id)
          if (step.after) step.after(out, ctx)
        } else if (step.kind === 'claude') {
          const prompt = typeof step.prompt === 'function' ? step.prompt(ctx) : step.prompt
          await this.execClaude(prompt, agent.id)
        }
        this.emitEvent({
          type: 'step', agentId: agent.id, i, label: step.label,
          status: this.cancelled ? 'skipped' : 'done',
          ms: Date.now() - startedAt,
        })
        if (this.cancelled) return
      } catch (err) {
        this.emitEvent({
          type: 'step', agentId: agent.id, i, label: step.label,
          status: 'error', ms: Date.now() - startedAt,
        })
        throw new Error(`${agent.name} — "${step.label}" failed: ${err.message}`)
      }

      const produces = typeof step.produces === 'function' ? step.produces(ctx) : step.produces
      if (produces) ctx.produced.push(...produces.filter(Boolean))
    }

    // Collect whatever actually landed on disk, newest content first.
    const files = []
    const wanted = [ctx.view, ...ctx.produced].filter(Boolean)
    for (const rel of [...new Set(wanted)]) {
      const p = path.join(ROOT, rel)
      if (fs.existsSync(p) && fs.statSync(p).isFile()) {
        files.push({ path: rel, content: fs.readFileSync(p, 'utf8') })
      }
    }

    this.emitEvent({
      type: 'agent_done',
      agentId: agent.id,
      agentName: `Agent ${agent.num} · ${agent.name}`,
      primary: ctx.view || null,
      files,
    })
  }

  // -------------------------------------------------------------------------

  /** Run a child process, streaming stdout/stderr as log events. Resolves with stdout. */
  exec(cmd, args, agentId) {
    return new Promise((resolve, reject) => {
      this.emitEvent({ type: 'log', stream: 'sys', text: `$ ${path.basename(cmd)} ${args.join(' ')}\n` })
      const child = spawn(cmd, args, {
        cwd: ROOT,
        windowsHide: true,
        env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1' },
      })
      this.child = child
      let stdout = ''
      child.stdout.on('data', (b) => {
        const text = b.toString('utf8')
        stdout += text
        this.emitEvent({ type: 'log', stream: 'stdout', text, agentId })
      })
      child.stderr.on('data', (b) => {
        this.emitEvent({ type: 'log', stream: 'stderr', text: b.toString('utf8'), agentId })
      })
      child.on('error', (e) => { this.child = null; reject(e) })
      child.on('close', (code) => {
        this.child = null
        if (this.cancelled) return resolve(stdout)
        code === 0 ? resolve(stdout) : reject(new Error(`exited with code ${code}`))
      })
    })
  }

  /** Run Claude Code headless, translating its stream-json into UI events. */
  execClaude(prompt, agentId) {
    return new Promise((resolve, reject) => {
      const bin = resolveClaude()
      const args = [
        '-p',
        '--output-format', 'stream-json',
        '--include-partial-messages',
        '--verbose',
        '--permission-mode', 'acceptEdits',
        '--allowedTools', CLAUDE_TOOLS,
      ]
      this.emitEvent({ type: 'log', stream: 'sys', text: `$ claude -p  (headless, ${prompt.length} char prompt)\n` })

      const child = spawn(bin, args, { cwd: ROOT, windowsHide: true })
      this.child = child
      child.stdin.write(prompt)
      child.stdin.end()

      let buf = ''
      let sawPartial = false
      let finalText = ''
      let errText = ''

      const handle = (msg) => {
        switch (msg.type) {
          case 'system':
            if (msg.subtype === 'init') {
              this.emitEvent({ type: 'claude_init', model: msg.model, agentId })
            }
            break

          case 'stream_event': {
            const ev = msg.event
            if (ev?.type === 'content_block_delta') {
              if (ev.delta?.type === 'text_delta' && ev.delta.text) {
                sawPartial = true
                this.emitEvent({ type: 'claude_text', text: ev.delta.text, agentId })
              } else if (ev.delta?.type === 'thinking_delta') {
                this.emitEvent({ type: 'claude_thinking', agentId })
              }
            }
            break
          }

          case 'assistant': {
            for (const block of msg.message?.content || []) {
              if (block.type === 'tool_use') {
                this.emitEvent({
                  type: 'claude_tool',
                  tool: block.name,
                  detail: describeTool(block),
                  agentId,
                })
              } else if (block.type === 'text' && !sawPartial && block.text) {
                this.emitEvent({ type: 'claude_text', text: block.text, agentId })
              }
            }
            break
          }

          case 'result':
            finalText = msg.result || ''
            if (msg.is_error) errText = msg.result || 'Claude reported an error'
            this.emitEvent({
              type: 'claude_result',
              summary: finalText,
              cost: msg.total_cost_usd,
              durationMs: msg.duration_ms,
              agentId,
            })
            break
        }
      }

      child.stdout.on('data', (b) => {
        buf += b.toString('utf8')
        let nl
        while ((nl = buf.indexOf('\n')) >= 0) {
          const line = buf.slice(0, nl).trim()
          buf = buf.slice(nl + 1)
          if (!line) continue
          try { handle(JSON.parse(line)) } catch { /* non-JSON noise */ }
        }
      })
      child.stderr.on('data', (b) => {
        this.emitEvent({ type: 'log', stream: 'stderr', text: b.toString('utf8'), agentId })
      })
      child.on('error', (e) => {
        this.child = null
        reject(new Error(`could not start Claude Code (${bin}): ${e.message}`))
      })
      child.on('close', (code) => {
        this.child = null
        if (this.cancelled) return resolve(finalText)
        if (code !== 0) return reject(new Error(errText || `claude exited with code ${code}`))
        if (errText) return reject(new Error(errText))
        resolve(finalText)
      })
    })
  }
}

function describeTool(block) {
  const i = block.input || {}
  switch (block.name) {
    case 'Read': return shortPath(i.file_path)
    case 'Write': return shortPath(i.file_path)
    case 'Edit': return shortPath(i.file_path)
    case 'WebSearch': return i.query || ''
    case 'WebFetch': return i.url || ''
    case 'Grep': return i.pattern || ''
    case 'Glob': return i.pattern || ''
    default: return ''
  }
}

const shortPath = (p) => (p ? String(p).replace(/\\/g, '/').split('/').slice(-2).join('/') : '')
