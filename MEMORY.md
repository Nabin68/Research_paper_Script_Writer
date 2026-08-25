# 🧠 PROJECT MEMORY — Finding Papers content pipeline

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
> _Last updated: 2026-07-16_

---

## 👤 Who / context
- **User:** runs @aiprofessor.vs on Instagram — short reels that explain AI research papers
  simply. Also marketing at GrowthSchool. Not looking for heavy technical setup; wants
  practical, low-friction tools.
- **Goal of this project:** a pipeline that takes new AI papers, picks the best ones for the
  page, deep-researches them, and writes reel scripts — learning from what worked/didn't.

## 🧩 The system — independent "plugs" (run one alone, or all in a row)
| # | Agent | Run it | Output |
|---|-------|--------|--------|
| 2 | **Picker** | `python agent2_prep.py` → ask Claude | `picks/top5_<date>.md` — 5 papers + hooks |
| 3 | **Deep-dive** | `python agent3_prep.py` → ask Claude | `agent3/deepdive_<date>.md` — Wow /10 + verdicts |
| 4 | **Writer** (from scratch) | `python agent4_prep.py --paper "..." --notes "..."` → ask Claude | `scripts/<date>-<slug>.md` |
| 5 | **Refiner** (polish an existing draft) | paste draft in chat + say how to refine → Claude runs `agent5_prep.py` | `agent5/refined/<date>-v<N>-<slug>.md` (versioned) |

- `papers.csv` is the **upstream ledger** the pipeline reads (the candidate AI papers, ranked).
  User-owned columns `picked`, `my_notes`, `performance` are never overwritten.
- All agents run **strictly on-demand, one at a time** — only when the user explicitly names
  that specific agent/action. Claude must NOT chain to the next agent in the pipeline on its own
  (e.g. don't auto-run Agent 4 just because Agent 2's picks were discussed) — always wait to be
  told, even if the next step seems obvious.

## 🗂️ Folder map
- `papers.csv` — master running ledger the pipeline reads (user-owned columns: `picked`,
  `my_notes`, `performance` — never overwritten)
- `agent2_prep.py` · `agent2/playbook.md` (virality rubric from 54 past reels) · `agent2/brief_*`
- `agent3_prep.py` · `agent3/deepdive_*`
- `agent4_prep.py` · `agent4/brief_*` · `scripts/` (finished reel scripts)
- `agent5_prep.py` · `agent5/refine_playbook.md` (refine checklist + growing CONDITIONAL USER
  PREFERENCES — the "training" file) · `agent5/input.md` (paste-your-draft drop-file) ·
  `agent5/brief_refine_*` · `agent5/refined/` (versioned refined scripts: `<date>-v<N>-<slug>.md`)
- `all past scripts/` — the user's past reels + metrics (the performance truth; keep adding new ones here)
- `Scripting_reference_things/` — hook.md, the 2 winning-script files, script-type templates,
  `winning-patterns.md` (consolidated hook/body/CTA pattern analysis from all 54 reels),
  `sample-scripts.md` (12 best reels reformatted as HOOK/BODY/CTA, for rhythm/pacing reference)
- `README.md` — full how-to · `MEMORY.md` — this file

## ✅ Rules & preferences (DO)
- **Numbers/comparisons in hooks are the DEFAULT weapon** — proven winners ($80B, 21×, 33%→72%,
  1 trillion minutes). Lead hooks with one shocking number.
- **Easy 6th-grade English**, understandable by both tech and non-tech viewers. No jargon in hooks.
- **Body must be connected** — if you mention A then B, the viewer already knows what A is (cause → effect).
- **Stay channel-centric** — it's a research-paper breakdown, not generic storytelling/motivation.
- **🔒 UNIVERSAL SCRIPT FORMAT (both Agent 4 + Agent 5 output this):** metadata block keeps emoji
  headers (📌 TITLE, 🎯 ANGLE, 👥 AUDIENCE, 📊 TYPE, Verified facts) → then the SCRIPT BLOCK which
  is **zero emojis**: a **`Reference:`** links block on top (paper/X/article/demo, plain text, one
  per line, no bold — for fact-checking) → numbered `[HOOK 1 — tag]`, `[HOOK 2 — tag]`… (flexible
  count, small strategy tag) → `[RE-HOOK]` → `[BODY]` → `[CTA]` → then closing metadata (checklist,
  triggers, caption, hashtags — emojis OK). No timestamps. Full spec in
  `Scripting_reference_things/7 script type template.md` under TYPE 4.
- **🔒 BOLD IS SELECTIVE, NOT BLANKET (corrected 2026-07-16 — overrides the old "all bold" rule).**
  Bold ONLY: (1) the structural labels themselves — `**Reference:**`, `**[HOOK 1 — tag]**`,
  `**[RE-HOOK]**`, `**[BODY]**`, `**[CTA]**`; (2) eye-catching words inline in the hook/body/CTA
  prose — named labs/companies (**Meta**, **Google**, **Anthropic**) and specific wow-numbers
  (**1,000 hours**, **700 people**, **70x**); (3) the quoted keyword in the CTA (`Comment
  **"BRAIN"**...`). Everything else — the hook/rehook/body/CTA sentences themselves, and every
  `Reference:` link line — is plain, non-bold text. Also: **`[BODY]` breaks onto a new line after
  roughly every sentence** (one sentence per line) for teleprompter pacing/pauses, blank line
  between beats — additive to the "one continuous story" rule, not a contradiction of it.
- **🔒 [BODY] IS ONE CONTINUOUS STORY, NOT LABELED CHUNKS (corrected 2026-07-15).** Do NOT use bold
  headers like `EVERYDAY STAKES:` / `WHY THE OLD WAY FAILED:` / `THE ONE CLEVER IDEA:` /
  `WHY IT MATTERS:` inside the delivered body — a real side-by-side comparison showed this makes
  the script read disconnected even with identical facts. Instead: the same 4 beats still happen
  in order, but each one flows into the next via a spoken BRIDGE SENTENCE ("But there's a catch."
  / "And here's the part that will blow your mind." / "And here's why it matters.") that a viewer
  would actually hear — never a label. Also: earn the stakes with a concrete relatable example
  before stating the pain point; personify the finding ("it quietly built its own sense of X")
  over clinical fact-listing; cut smart-sounding-but-unclear jargon-adjacent phrases even if
  catchy; don't stack two dense reveals in one sentence; don't drop a narrow technical detail
  right before the real payoff. Full before/after example in the template file.
- **Keep the agents separate and modular** ("plugs"). Any one runnable alone.
- **Output stays local** (CSV + MD files in this folder).
- **Each script → a flexible number of hooks** (as many strong ones as the paper supports),
  numbered `[HOOK 1 — tag]`, `[HOOK 2 — tag]`… — lead with proven patterns, then experimental.
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
- Wow Score (Agent 3) = Internet virality /4 + Channel fit /6.

## ⏳ Deferred / TODO
- User may paste personal hook guidance into `Scripting_reference_things/hook.md`
  ("YOUR OWN HOOK GUIDANCE" section) — treat it as top priority once filled.
- Refresh `agent2/playbook.md` when new reels + metrics are added to `all past scripts/`.

## 📝 Corrections & learnings log (newest first)
- **2026-07-16** — **Bold formatting corrected (TRIBE v2 script).** The old "whole script block is
  ALL BOLD" rule (locked 2026-07-15) was wrong — user copy-pasted a delivered script and found it
  unreadable. New rule: bold ONLY the structural labels (`Reference:`, `[HOOK n]`, `[RE-HOOK]`,
  `[BODY]`, `[CTA]`) plus inline standout words (company/lab names, specific numbers/stats) and the
  CTA's quoted keyword — everything else, including every `Reference:` link line, is plain text.
  Also added: `[BODY]` now breaks onto a new line after ~each sentence (teleprompter pause pacing),
  blank line between beats — the "one continuous story, no labeled headers" rule still applies,
  this is just line-break rhythm, not new labels. Updated the template's format-rules section +
  worked layout example accordingly.
- **2026-07-16** — **Line breaks corrected (same TRIBE v2 script, round 2).** The label→content and
  sentence→sentence breaks weren't surviving copy-paste — root cause: a single `\n` collapses into
  a space in most renderers/paste targets, only a full BLANK LINE forces a real new line. Fixed:
  every `[HOOK n]` / `[RE-HOOK]` / `[BODY]` / `[CTA]` label now has a blank line before its content
  starts, and the body is one full sentence per blank-line-separated paragraph (not single-`\n`
  sentences). `Reference:` links stay as a `- ` bullet list (bullet lists don't need blank lines
  between items — they already render one-per-line). Updated the template's format rules + worked
  layout example to show blank lines explicitly.
- **2026-07-16** — Trimmed this file to the **content pipeline (agents 2–5)** at the user's
  request. `papers.csv` is now treated simply as the upstream input the pipeline reads. Agents
  2–5 and all script/content knowledge are unchanged.
- **2026-07-15** — **How I write TYPE-4 bodies, corrected (from the "Language Models Need Sleep"
  script).** User compared my Agent-4 draft to their finalized version: hooks were fine, but my BODY
  over-explained and read as disconnected info-blocks with no rising build. Encoded a **DEFAULT BODY
  FLOW** into `Scripting_reference_things/7 script type template.md` (TYPE 4) + `agent5/refine_playbook.md`:
  **problem → solution → wow-metric → how it works → opinion**, one connected story via spoken
  bridges (never labeled chunks). Key fixes: open the problem as a relatable **question**; name
  exactly **WHAT was built** (not vague "fixed it"; don't overstate a memory module as a whole new
  model — verify); put the headline **metric RIGHT AFTER the solution and BEFORE the mechanism** (the
  excitement pivot / mid-body re-hook, never buried at the end); best mechanism step last; close on
  caveat + payoff + a **callback to a known phrase** ("sleep on it"). Body **200–230 words**, global
  tech+non-tech 6th-grade, each beat must build to the next. (Extends the earlier "body is one story,
  not labeled chunks" fix with the specific ORDER + metric placement.)
- **2026-07-15** — Corrected the universal format's `[BODY]`: bold section headers
  (EVERYDAY STAKES: etc.) were making scripts read as disconnected, choppy chunks even with
  identical facts — user compared a labeled version vs. a flowing version side by side and the
  flowing one was clearly better. Fix: body is one continuous story using spoken bridge sentences
  instead of labels, stakes are earned with a relatable example before the pain point, findings
  are personified rather than fact-listed, jargon-adjacent "smart" phrases get cut even if catchy.
  This OVERRIDES the labeled-body format locked in earlier the same day — labels were a mistake.
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
- **2026-07-15** — User wants ZERO automation of my own initiative. Never chain-run an agent
  (e.g. running Agent 4's prep script right after being told "write the script") without the user
  naming that exact agent/action first — ask if ambiguous, run agents strictly one at a time, only
  when explicitly told.
- **2026-07-14** — User wants memory kept LOCALLY in this project folder (this file), readable,
  and updated over time so context isn't re-explained. (Created `MEMORY.md`.)
- **2026-07-14** — Numbers ARE good in hooks; "don't write numbers" was only an example of an
  optional per-script instruction, not a rule.
- **2026-07-14** — Keep all agents separate/independently runnable ("plugs").
