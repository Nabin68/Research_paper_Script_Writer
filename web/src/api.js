const j = async (res) => {
  const body = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(body.error || `Request failed (${res.status})`)
  return body
}

export const getAgents = () => fetch('/api/agents').then(j)
export const getRecent = (agentId) => fetch(`/api/recent?agentId=${agentId}`).then(j)
export const getTodayStatus = (date) => fetch(`/api/today-status?date=${date}`).then(j)
export const getFile = (path) => fetch(`/api/file?path=${encodeURIComponent(path)}`).then(j)

export const startRun = (payload) =>
  fetch('/api/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }).then(j)

export const approveRun = (runId, stop = false, inputs = null) =>
  fetch(`/api/run/${runId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ stop, inputs }),
  }).then(j)

export const cancelRun = (runId) => fetch(`/api/run/${runId}/cancel`, { method: 'POST' }).then(j)
