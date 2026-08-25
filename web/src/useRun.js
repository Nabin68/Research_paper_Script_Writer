import { useCallback, useEffect, useRef, useState } from 'react'
import { approveRun, cancelRun, startRun } from './api.js'

/**
 * Owns one live run: opens the SSE stream and folds its events into the
 * shape the UI renders (agent cards, step tracker, live text, outputs).
 */
const EMPTY = { runId: null, status: 'idle', agents: [], log: [], awaiting: null, error: null }

export function useRun() {
  const [state, setState] = useState(EMPTY)
  const esRef = useRef(null)

  useEffect(() => () => esRef.current?.close(), [])

  const apply = useCallback((ev) => {
    setState((s) => {
      const agents = s.agents.map((a) => ({ ...a, steps: [...a.steps] }))
      const cur = agents[agents.length - 1]

      switch (ev.type) {
        case 'run_start':
          return { ...s, status: 'running' }

        case 'agent_start':
          agents.push({
            id: ev.agentId,
            name: ev.agentName,
            steps: ev.steps.map((st) => ({ ...st, status: 'pending' })),
            text: '',
            tools: [],
            files: [],
            primary: null,
            done: false,
            model: null,
            cost: null,
            summary: '',
          })
          return { ...s, agents, awaiting: null }

        case 'step': {
          const a = agents.find((x) => x.id === ev.agentId) || cur
          if (a) {
            const st = a.steps[ev.i]
            if (st) {
              st.status = ev.status
              if (ev.ms != null) st.ms = ev.ms
            }
          }
          return { ...s, agents }
        }

        case 'claude_init':
          if (cur) cur.model = ev.model
          return { ...s, agents }

        case 'claude_text':
          if (cur) cur.text += ev.text
          return { ...s, agents }

        case 'claude_tool':
          if (cur) cur.tools = [...cur.tools.slice(-40), { tool: ev.tool, detail: ev.detail }]
          return { ...s, agents }

        case 'claude_result':
          if (cur) {
            cur.summary = ev.summary || ''
            cur.cost = ev.cost ?? null
          }
          return { ...s, agents }

        case 'agent_done': {
          const a = agents.find((x) => x.id === ev.agentId) || cur
          if (a) {
            a.files = ev.files || []
            a.primary = ev.primary
            a.done = true
          }
          return { ...s, agents }
        }

        case 'log':
          return { ...s, log: [...s.log.slice(-600), ev] }

        case 'awaiting':
          return {
            ...s,
            status: 'awaiting',
            awaiting: {
              agentId: ev.agentId,
              agentName: ev.agentName,
              fields: ev.fields || [],
              values: ev.values || {},
            },
          }

        case 'error':
          return { ...s, error: ev.message }

        case 'run_stopped':
          return { ...s, awaiting: null }

        case 'run_end':
          return { ...s, status: ev.status, awaiting: null }

        default:
          return s
      }
    })
  }, [])

  const start = useCallback(
    async (payload) => {
      esRef.current?.close()
      setState({ ...EMPTY, status: 'running' })
      try {
        const { runId } = await startRun(payload)
        setState((s) => ({ ...s, runId }))
        const es = new EventSource(`/api/run/${runId}/stream`)
        esRef.current = es
        es.onmessage = (m) => apply(JSON.parse(m.data))
        es.onerror = () => es.close()
      } catch (err) {
        setState((s) => ({ ...s, status: 'error', error: err.message }))
      }
    },
    [apply],
  )

  const approve = useCallback((stop = false, inputs = null) => {
    setState((s) => {
      if (s.runId) approveRun(s.runId, stop, inputs).catch(() => {})
      return { ...s, awaiting: null, status: stop ? s.status : 'running' }
    })
  }, [])

  const cancel = useCallback(() => {
    setState((s) => {
      if (s.runId) cancelRun(s.runId).catch(() => {})
      return s
    })
  }, [])

  const reset = useCallback(() => {
    esRef.current?.close()
    setState(EMPTY)
  }, [])

  const busy = state.status === 'running' || state.status === 'awaiting'
  return { ...state, busy, start, approve, cancel, reset }
}
