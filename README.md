# Finding Papers — Daily AI Research Digest & Script-Writing Pipeline

A small, zero-dependency system that every day gathers new AI research papers from the
big labs + community trending signals, logs them into a running spreadsheet with metrics,
and writes a clean daily digest. On top of that sits a 5-agent pipeline that picks the best
papers, deep-dives them, and writes/refines Instagram Reel scripts for **@aiprofessor.vs**.
Built to help you spot papers worth acting on and learn, over time, **what worked and what
didn't**.

> **This repo is a private backup.** It's pushed manually every so often (not on a schedule)
> to keep the ledger, scripts, and the accumulated "taste" playbooks safe. Everything here is
> the working state of the project as of the last push — pull before you start a new local
> session if you've been running this from more than one machine.

## Folder map

| Path | What's in it |
|---|---|
| `finding_papers.py`, `sources.json` | Agent 1 (finder) + its editable source list |
| `papers.csv` | Master running ledger — every paper ever found, deduped, with your notes |
| `digests/` | Daily digest snapshots (`digest_YYYY-MM-DD.md`) |
| `agent2_prep.py`, `agent2/` | Agent 2 (picker) prep + `playbook.md` (virality rubric, built from 54+ past reels) + `brief_*` |
| `agent3_prep.py`, `agent3/` | Agent 3 (deep-dive) prep + `input_*` / `deepdive_*` |
| `agent4_prep.py`, `agent4/` | Agent 4 (writer) prep + `brief_*` |
| `agent5_prep.py`, `agent5/` | Agent 5 (refiner) prep + `refine_playbook.md` (the growing, context-aware taste file) + `refined/` (versioned outputs) |
| `scripts/` | Finished reel scripts, in the universal script format (see below) |
| `picks/` | Agent 2's `top5_<date>.md` outputs |
| `all past scripts/` | Past reels + their real performance metrics — the ground truth the playbooks are built from |
| `Scripting_reference_things/` | Hook bible, winning-script breakdowns, script-type templates |
| `MEMORY.md` | The project's own standing-rules file — read this first if you're picking this project back up |

## What it does

Each run pulls from these free sources (no API keys, no paid Twitter):

| Source | Signal |
|---|---|
| **Hugging Face Daily Papers** | Community upvotes — the main "what's trending" signal |
| **arXiv** (cs.AI / cs.LG / cs.CL) | New papers, filtered to **big-lab authors** |
| **OpenAI / Google DeepMind / Google Research** (RSS) | Official lab releases |
| **Meta AI / Anthropic** (page scrape) | Official lab releases |
| **Reddit r/MachineLearning** (etc.) | Community discussion + arXiv mentions |
| **GitHub Trending** | AI repos catching on (implementations of hot papers) |

It then writes two things:

- **`papers.csv`** — the master **running ledger**. One row per paper/post/repo, deduped,
  appended to every day. This is your permanent record.
- **`digests/digest_YYYY-MM-DD.md`** — a readable daily digest with three sections:
  🔥 Trending today · 🏢 From the big labs · 💻 Trending AI repos.

## Run it

```
python finding_papers.py
```

or just double-click **`run_daily.bat`** (it logs to `run.log`).

Backfill a specific day: `python finding_papers.py --date 2026-07-13`

## The ledger (`papers.csv`)

Columns: `first_seen, last_updated, source, lab, title, authors, url, arxiv_id,
hf_upvotes, hf_comments, reddit_mentions, github_stars, trending_score, category,
summary, published_iso, picked, my_notes, performance`

**Three columns are yours** — the script *never* overwrites them:

- **`picked`** — mark `YES` when you use a paper (newsletter, course, post…).
- **`my_notes`** — anything you want to remember.
- **`performance`** — how it did (views, engagement, "went viral", "flopped"…).

Every run refreshes the objective metrics (upvotes/stars grow over days) and appends new
papers, but leaves your three columns untouched. That pairing — your outcome next to the
objective signals — is how you'll see what kind of paper actually worked.

> Tip: open `papers.csv` in Excel/Google Sheets, sort by `trending_score`, and fill in
> `picked` / `performance` as you go.

## How the `trending_score` works (0–100)

A transparent blend, computed in `trending_score()` in `finding_papers.py`:

```
raw   = hf_upvotes*3 + reddit_mentions*6 + github_stars*0.2 + (10 if big-lab)
score = min(100, raw * recency_multiplier)   # newer = higher
```

Edit those weights in that one function to retune what floats to the top.

## Adding sources

All sources live in **`sources.json`** — add one line to the relevant list and save; the
next run picks it up. No code changes.

- `rss_feeds` — a lab blog with an RSS feed: `{"lab": "Name", "url": "..."}`
- `scrape_pages` — a lab news page without RSS: `{"lab": "Name", "url": "..."}`
- `subreddits` — just the name, e.g. `"LocalLLaMA"`
- `arxiv_categories` — e.g. `"cs.CV"`
- `creators` / `labs` — names to recognize as "big lab"
- `twitter_handles` — placeholder for if/when you add an X API key

Easiest path: **just tell Claude** "add <thing> as a source" and it edits the file for you.
(Claude will also check in each day about whether you want to add anything new.)

## The agent pipeline (5 independent "plugs")

Run **one at a time, manually, only when you want it** — nothing auto-chains.

| # | Agent | Run it | Output |
|---|-------|--------|--------|
| 1 | **Finder** | `python finding_papers.py` | `papers.csv` + daily digest |
| 2 | **Picker** | `python agent2_prep.py` → ask Claude | `picks/top5_<date>.md` |
| 3 | **Deep-dive** | `python agent3_prep.py` → ask Claude | `agent3/deepdive_<date>.md` |
| 4 | **Writer** (from scratch) | `python agent4_prep.py --paper "..." --notes "..."` → ask Claude | `scripts/<date>-<slug>.md` |
| 5 | **Refiner** (polish an existing script) | paste your draft to Claude + say how to refine | `agent5/refined/<date>-v<N>-<slug>.md` (versioned) |

**Agent 5 (Refiner)** takes a script you *already have* — your own, an Agent 4 script, or one
from anywhere else — and polishes it against the page's proven levers **without rewriting it**.
Just paste your draft in chat and tell Claude how you want it refined; Claude drops it into
`agent5/input.md`, runs the prep, and writes the polished version to a **versioned** file in
`agent5/refined/` — `v1` the first time, `v2`/`v3` each time you refine that same script again,
so every pass is tracked and nothing is overwritten. Every refine ends with a short
"what I changed & why".

It **learns your taste — with context.** When you react with a preference, Claude doesn't save a
flat rule; it saves a *conditional* one. So "make the hook longer" on a compression paper and
"make the hook shorter" on a brain paper are stored as two situation-specific rules, not a
contradiction — the refiner analyzes each new draft's subject + structure and applies the rules
that fit. All of this lives in `agent5/refine_playbook.md`. Because Agents 4 and 5 share the same
reference set, sharper refines also make the from-scratch writer better over time.

## The universal script format

Every script (from Agent 4 or Agent 5) follows one locked format — full spec in
`Scripting_reference_things/7 script type template.md` under TYPE 4:

- **Metadata on top** (keeps emoji headers): 📌 title, 🎯 angle, 👥 audience, 📊 type, verified facts.
- **Then the script block — entirely bold, zero emojis:**
  - **`Reference:`** — real links (paper/arXiv/Reddit, X post, article, demo) so every claim is
    checkable.
  - **`[HOOK 1 — tag]`, `[HOOK 2 — tag]`…** — flexible count (as many strong hooks as the paper
    supports), each with a short strategy tag.
  - **`[RE-HOOK]`** → **`[BODY]`** (plain bold sub-labels: EVERYDAY STAKES / WHY THE OLD WAY
    FAILED / THE ONE CLEVER IDEA / WHY IT MATTERS) → **`[CTA]`**.
- **Closing metadata** (emojis OK): ✅ checklist, 📊 triggers used, 📱 caption, 🏷️ hashtags.

No timestamps in the script body. See any file in `scripts/` dated 2026-07-15 or later for a
worked example.

## Scheduling

- **Manual only (current):** the daily 9 AM Windows Task Scheduler auto-run was **disabled** —
  every agent is run by hand, on demand. The task definition still exists if you ever want it
  back (ask Claude to re-enable it).

## Notes / limits

- Reddit occasionally rate-limits (`429`) — that source is best-effort and skips silently.
- No live Twitter/X engagement data (paywalled). The HF + Reddit + GitHub signals are the
  free stand-in; wire in an X API key later via `twitter_handles` if you get one.
- Pure Python standard library — nothing to `pip install`.
