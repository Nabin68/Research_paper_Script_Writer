# Agent Console — web interface for the Research Paper pipeline

A local web UI over the existing 5-agent pipeline. It does not reimplement anything:
it shells out to the same `*_prep.py` scripts and hands Claude the same briefs you
read in the terminal today.

## Start it

Double-click **`start.bat`** (installs on first run), or:

```
cd web
npm install     # first time only
npm run dev
```

Opens at **http://localhost:5180**. Close the window to stop it.

## How it runs the agents — no API key

Each agent is the same two beats as the terminal workflow:

1. **Prep** — runs the Python script (`agent2_prep.py`, etc.) and streams its output.
2. **Claude** — runs the Claude Code CLI headless (`claude -p --output-format stream-json`)
   from the project root, pointed at the brief the prep step just wrote.

Because it drives the CLI, it authenticates with your existing Claude Code
subscription. There is no API key in this app and no key to configure.

Claude runs with `--permission-mode acceptEdits` and an explicit tool allowlist
(Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, TodoWrite) so a headless run
never stalls on a permission prompt.

## Layout

- **Research Paper** (parent tab) — the pipeline runner.
  - Agent 1 · Finder — pulls today's papers into `papers.csv` + the digest
  - Agent 2 · Picker — the Top 5
  - Agent 3 · Deep-Dive — buzz research + Wow Score
  - Agent 4 · Writer — the reel script
  - Agent 5 · Refiner — paste a draft + what to fix
  - Agent 6 · Captions — paste a script, get the Instagram caption (or refine one)

Click an agent to run it alone. Click **Research Paper** to run the chain.

Open Source, Future Tech and Decoding are listed but on hold — they open a placeholder
that mirrors the real layout. Bringing one online is one entry in `src/pages.js` plus its
agents on the server.

### Manual vs Fully automated

- **Manual** (default) — stops after each agent so you can read the output and
  approve before it feeds the next one. The pause also collects anything the next
  agent needs, so you pick Agent 4's paper *after* reading the deep-dive.
- **Fully automated** — runs straight through. Agent 4's paper must be set up front,
  since nothing can ask you mid-run.

Agents 5 and 6 work off something you paste in, so they run from their own tabs, not in the chain.

## Notes

- Only one agent runs at a time, by design — this matches the project's standing rule.
- All reads and writes go to the real project folder. Outputs land exactly where the
  terminal workflow puts them (`picks/`, `agent3/`, `scripts/`, `agent5/refined/`).
- Localhost only; the server binds to `127.0.0.1`.

## Config (optional env vars)

| Var | Default | Use |
|---|---|---|
| `FP_PORT` | `8787` | API port |
| `FP_PYTHON` | `python` | Python executable |
| `FP_CLAUDE_BIN` | auto-detected | Path to `claude.exe` |
| `FP_ROOT` | the parent folder | Project root |
