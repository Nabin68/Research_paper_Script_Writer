# 🧠 PROJECT MEMORY — Finding Papers multi-agent system

> **What this file is:** the local, always-on memory for this project. It holds who we are,
> how the system works, the user's rules/preferences, and every correction given — so the AI
> doesn't need re-explaining and gets better over time.
>
> **For the AI (Claude):** READ this file at the start of every session before doing work.
> UPDATE it at the end of any session where something new is decided, a preference is stated,
> or a mistake is corrected. Keep it tight and factual. Newest corrections go at the top of the
> "Corrections & learnings" log with a date. This local file is the source of truth the user
> can see and edit.
>
> _Last updated: 2026-07-14_

---

## 👤 Who / context
- **User:** runs @aiprofessor.vs on Instagram — short reels that explain AI research papers
  simply. Also marketing at GrowthSchool. Not looking for heavy technical setup; wants
  practical, low-friction tools.
- **Goal of this project:** a daily pipeline that finds new AI papers, picks the best ones for
  the page, deep-researches them, and writes reel scripts — learning from what worked/didn't.
- **Second email for delivery:** nabin.rouniyar@growthschool.io (email delivery deferred — see TODO).

## 🧩 The system — 5 independent "plugs" (run one alone, or all in a row)
| # | Agent | Run it | Output |
|---|-------|--------|--------|
| 1 | **Finder** | `python finding_papers.py` | `papers.csv` — every paper found, ranked |
| 2 | **Picker** | `python agent2_prep.py` → ask Claude | `picks/top5_<date>.md` — 5 papers + hooks |
| 3 | **Deep-dive** | `python agent3_prep.py` → ask Claude | `agent3/deepdive_<date>.md` — Wow /10 + verdicts |
| 4 | **Writer** (from scratch) | `python agent4_prep.py --paper "..." --notes "..."` → ask Claude | `scripts/<date>-<slug>.md` |
| 5 | **Refiner** (polish an existing draft) | paste draft in chat + say how to refine → Claude runs `agent5_prep.py` | `agent5/refined/<date>-v<N>-<slug>.md` (versioned) |

- All 4 agents run **strictly on-demand, one at a time** — only when the user explicitly names
  that specific agent/action. Claude must NOT chain to the next agent in the pipeline on its own
  (e.g. don't auto-run Agent 4 just because Agent 2's picks were discussed) — always wait to be
  told, even if the next step seems obvious.
- **Daily 9:00 AM Windows Task Scheduler automation is DISABLED as of 2026-07-15** (user wants
  zero automation, runs everything manually). The task definition still exists (`Disable-ScheduledTask`,
  not deleted) in case the user wants it re-enabled later — ask before re-enabling.

## 🗂️ Folder map
- `finding_papers.py`, `sources.json` — Agent 1 + its editable source list
- `papers.csv` — master running ledger (user-owned columns: `picked`, `my_notes`, `performance` — never overwritten)
- `digests/` — daily digest snapshots
- `agent2_prep.py` · `agent2/playbook.md` (virality rubric from 54 past reels) · `agent2/brief_*`
- `agent3_prep.py` · `agent3/deepdive_*`
- `agent4_prep.py` · `agent4/brief_*` · `scripts/` (finished reel scripts)
- `agent5_prep.py` · `agent5/refine_playbook.md` (refine checklist + growing CONDITIONAL USER
  PREFERENCES — the "training" file) · `agent5/input.md` (paste-your-draft drop-file) ·
  `agent5/brief_refine_*` · `agent5/refined/` (versioned refined scripts: `<date>-v<N>-<slug>.md`)
- `all past scripts/` — the user's past reels + metrics (the performance truth; keep adding new ones here)
- `Scripting_reference_things/` — hook.md, the 2 winning-script files, script-type templates
- `README.md` — full how-to · `MEMORY.md` — this file

## ✅ Rules & preferences (DO)
- **Numbers/comparisons in hooks are the DEFAULT weapon** — proven winners ($80B, 21×, 33%→72%,
  1 trillion minutes). Lead hooks with one shocking number.
- **Easy 6th-grade English**, understandable by both tech and non-tech viewers. No jargon in hooks.
- **Body must be connected** — if you mention A then B, the viewer already knows what A is (cause → effect).
- **Stay channel-centric** — it's a research-paper breakdown, not generic storytelling/motivation.
- **🔒 UNIVERSAL SCRIPT FORMAT (both Agent 4 + Agent 5 output this):** metadata block keeps emoji
  headers (📌 TITLE, 🎯 ANGLE, 👥 AUDIENCE, 📊 TYPE, Verified facts) → then the SCRIPT BLOCK which
  is **all bold, zero emojis**: a **`Reference:`** links block on top (paper/X/article/demo — for
  fact-checking) → numbered `[HOOK 1 — tag]`, `[HOOK 2 — tag]`… (flexible count, small strategy
  tag) → `[RE-HOOK]` → `[BODY]` with plain bold sub-labels (EVERYDAY STAKES: / WHY THE OLD WAY
  FAILED: / THE ONE CLEVER IDEA: / WHY IT MATTERS:) → `[CTA]` → then closing metadata (checklist,
  triggers, caption, hashtags — emojis OK). No timestamps. Full spec in
  `Scripting_reference_things/7 script type template.md` under TYPE 4.
- **Keep the 4 agents separate and modular** ("plugs"). Any one runnable alone.
- **Output stays local** (CSV + MD files in this folder).
- **Each script → a flexible number of hooks** (as many strong ones as the paper supports),
  numbered `[HOOK 1 — tag]`, `[HOOK 2 — tag]`… — lead with proven patterns, then experimental.
- **Ask casually each session** whether to add new sources (creators/subreddits/feeds) to `sources.json`.
- Winning topic formula: brain/mind · money/industry-disruption · named-underdog-vs-giant ·
  your-body/your-job · one wow-number · understandable in 60s.

## 🚫 Don'ts
- **Don't trust HF upvotes alone** — robotics/hardware papers get upvotes but flop as reels.
- **Don't make reels on:** pure ML theory, historical/foundational papers, robotics/hardware,
  incremental "company shipped model X" releases (they consistently flop for this page).
- **Don't add numbers to a script only if a specific `--notes` instruction says so** — otherwise
  numbers stay in. (The earlier "don't write numbers" was a per-script example, not a global rule.)
- **Don't rely on live Instagram access** — there's no IG connector; performance data comes from
  files the user exports into `all past scripts/`.

## 🧾 Decisions made
- Output = local CSV + Markdown (not Google Sheet / Notion).
- Trending signal = free proxies (Hugging Face upvotes + Reddit) + GitHub trending. No paid Twitter/X.
- Scheduling = local Windows Task Scheduler (cloud can't write local files).
- Wow Score (Agent 3) = Internet virality /4 + Channel fit /6.

## ⏳ Deferred / TODO
- **Email delivery of the digest to nabin.rouniyar@growthschool.io** — blocked: connected Gmail
  can only *draft*, not send. Options: cloud `/schedule` daily draft (one-click send) · local SMTP
  auto-send via Gmail App Password (needs Workspace admin) · write to Google Drive. User said "later."
- User may paste personal hook guidance into `Scripting_reference_things/hook.md`
  ("YOUR OWN HOOK GUIDANCE" section) — treat it as top priority once filled.
- Refresh `agent2/playbook.md` when new reels + metrics are added to `all past scripts/`.

## 📝 Corrections & learnings log (newest first)
- **2026-07-15** — Locked the **🔒 UNIVERSAL SCRIPT FORMAT** for the hook/body part of every
  script (both Agent 4 and Agent 5): numbered `[HOOK n — tag]` (flexible count, keep a small
  strategy tag), `[RE-HOOK]` → `[BODY]` sub-labels → `[CTA]`, the whole script block **bold with
  no emojis**, and a **`Reference:`** links block on top for fact-checking. Metadata sections
  (title/angle/audience/type/checklist/caption/hashtags) keep their emojis. Dropped timestamps and
  the old "🎣 HOOK OPTIONS (5 variations)" / "📝 FULL SCRIPT" headings. Reformatted the Bonsai
  script to this. User decisions: **flexible hook count** (not fixed 5) + **keep small strategy tag**.
- **2026-07-15** — Added **Agent 5 (Refiner)**: polishes an existing/draft script (user's own,
  Agent 4's, or from anywhere) against the page's levers WITHOUT rewriting — preserves the user's
  voice. **Workflow:** user PASTES the draft in chat + says how to refine → I drop it into
  `agent5/input.md`, run `agent5_prep.py`, then refine. **Output is VERSIONED:**
  `agent5/refined/<date>-v<N>-<slug>.md` (v1 first pass, v2/v3 on re-refine — never overwrite, for
  tracking). Each refined file ends with "WHAT I CHANGED & WHY (vN)".
  **Preferences are CONDITIONAL, not global** (user's explicit ask): the same lever can go opposite
  ways by context — e.g. "longer hook for script A" vs "shorter hook for script B" are two IF-THEN
  rules, not a contradiction. Store them in `agent5/refine_playbook.md` §4A as
  "IF <subject/type + structural situation> THEN <direction>", backed by a §4B raw log that records
  each pass WITH its subject/context. Never write a flat rule like "hooks should be short".
- **2026-07-15** — User wants ZERO automation. Disabled the daily 9 AM Task Scheduler job.
  Also: never chain-run an agent (e.g. running Agent 4's prep script right after being told
  "write the script") without the user naming that exact agent/action first — ask if ambiguous,
  run agents strictly one at a time, only when explicitly told.
- **2026-07-14** — User wants memory kept LOCALLY in this project folder (this file), readable,
  and updated over time so context isn't re-explained. (Created `MEMORY.md`.)
- **2026-07-14** — Numbers ARE good in hooks; "don't write numbers" was only an example of an
  optional per-script instruction, not a rule.
- **2026-07-14** — Cloud email deferred after discovering Gmail connector is draft-only.
- **2026-07-14** — Keep all agents separate/independently runnable ("plugs").
