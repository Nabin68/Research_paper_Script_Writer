# ✂️ REFINER PLAYBOOK — Agent 5 (@aiprofessor.vs)

> **INSTRUCTION for Claude:** This is the brain of the refiner. Read it fully before touching a
> draft. It has two parts: (1) the fixed REFINE METHOD + checklist, and (2) the growing
> **USER PREFERENCES & LEARNINGS** section — rules learned from the user's own feedback over
> time. The USER PREFERENCES section is HIGHER priority than everything else, including the
> generic references. This file is how Agent 5 "gets trained" on the user's taste — append to
> section 4 whenever the user states a preference or reacts to a refinement.

---

## 1. THE ONE RULE: REFINE, DON'T REWRITE

The user already has a script (their own, Agent 4's, or from another source). It's *mostly
good* — it just needs polish. **Preserve the user's voice, structure, and core idea.** Improve
what's weak; don't replace what works. If you find yourself rewriting from scratch, stop — that's
Agent 4's job, not this one. A good refine is one the user reads and thinks "yes, that's still my
script, just sharper."

**This applies INSIDE a flagged sentence/paragraph too, not just at the whole-script level.**
2026-07-15 correction: when refining "Meta/Alibaba memory" v1, only two specific things in the
flagged paragraph were weak ("imagine the possibilities" as a vague opener, and "optimum use of
memory" as unresolved jargon) — but the closing clause ("knowing the exact moment it matters, and
knowing exactly where to find it") was already strong. Claude's v1 rewrote the WHOLE paragraph
anyway, discarding the good clause into a weaker paraphrase ("worth keeping" / "dig it back up").
The user's own rewrite fixed ONLY the two actually-weak phrases and kept the good clause almost
verbatim — and it read far better. **Before rewriting a flagged span, isolate exactly which
words/clauses are weak and touch only those; don't let "refine this paragraph" become "rewrite
this paragraph."**

Use your own knowledge freely to make phrasing tighter, analogies clearer, and facts correct —
but in service of *their* script, not a new one.

---

## 2. THE REFINE CHECKLIST (score the draft against each, fix the misses)

Walk the draft top to bottom against the page's proven levers (full detail in `hook.md`, the two
winning-script files, and `agent2/playbook.md`):

**Hook (first 3 seconds — the highest-leverage fix):**
- [ ] Leads with ONE shocking number or comparison, not vague setup.
- [ ] Names a giant or an underdog (Google, OpenAI, Claude, Nvidia, or a nameable person) when
      the topic allows.
- [ ] 6th-grade English — no jargon (no "LLM/embeddings/attention/benchmark/quantization").
- [ ] The wow is in second one, not buried. No "In this video" / "Day 5 of 100" cold opens.
- [ ] Hooks are numbered `[HOOK 1 — tag]`, `[HOOK 2 — tag]`… (flexible count — keep every strong
      one; lead with proven patterns, then experimental). Cut weak/duplicate hooks, add missing ones.

**Re-hook & retention:**
- [ ] A re-hook lands ~3–6s in ("and the reason is even crazier") to re-open the loop.
- [ ] Curiosity gets re-opened every few beats — no flat stretch where a viewer would scroll.

**Body (connected, easy-English):**
- [ ] Cause → effect flow: if it mentions A then B, the viewer already knows what A is. No leaps.
- [ ] Every technical term swapped for a plain word or human analogy.
- [ ] One idea per beat, short punchy sentences (~8–12 words).
- [ ] The single best proof number lands mid-body and isn't drowned by other stats.
- [ ] Follows a proven spine when it fits: "old way failed → new way wins" (Colgate) or
      "hero + 3 clean steps + counterintuitive punch" (Lighthouse).
- [ ] Stays ON the finding — it's a research breakdown, not motivation/storytelling drift.

**Stakes & close:**
- [ ] A clear "why this matters to YOU" (job / brain / body / money / daily AI) beat.
- [ ] Portable thesis-line + comment-bait CTA ("Comment WORD and I'll DM the paper").
- [ ] Runtime reads ≤ ~90s.

**Truth & flop-guard:**
- [ ] Every number/claim is real — web-check if a paper is attached; never invent a stat.
- [ ] Not sliding into a proven flop shape (pure ML theory, historical framing, robotics/hardware
      niche, "company shipped model X" with no finding). If the draft's topic is inherently a flop
      shape, flag it to the user rather than polishing a doomed script.

---

## 3. OUTPUT FORMAT (versioned + the universal format)

Write the refined script to the VERSIONED path the prep step reports:

    agent5/refined/<date>-v<N>-<slug>.md

- The prep step auto-computes `<N>`: v1 the first time you refine a given script, v2/v3/… each
  time that same script is refined again. Never overwrite an earlier version — each pass is a new
  file so the history is visible.
- **Conform the refined script to the 🔒 UNIVERSAL SCRIPT FORMAT** (defined under TYPE 4 in
  `Scripting_reference_things/7 script type template.md`) — even if the incoming draft wasn't in
  it. That means: metadata with emoji headers on top → a **`Reference:`** links block at the top
  of the script → numbered **`[HOOK 1 — tag]`, `[HOOK 2 — tag]`…** (flexible count, small strategy
  tag) → **`[RE-HOOK]`** → **`[BODY]`** → **`[CTA]`**. The whole SCRIPT BLOCK (Reference → CTA) is
  **bold and emoji-free**; the surrounding metadata keeps its emojis. If the draft is missing the
  `Reference:` links, add them (web-find the real sources).
- **`[BODY]` is ONE continuous story — never bold section headers** (EVERYDAY STAKES: /
  WHY THE OLD WAY FAILED: / etc.). If an incoming draft HAS these labels, remove them as part of
  the refine and rewrite the seams as spoken bridge sentences instead ("But there's a catch." /
  "And here's the part that will blow your mind."). See the template's "BODY IS ONE STORY, NOT
  FOUR LABELED CHUNKS" section for the full technique + worked example — this was a real
  correction on 2026-07-15 after labeled bodies tested as disconnected/choppy.
- Preserve the user's wording/voice inside that structure — reformatting is not rewriting.
- End the file with:

```
---
✍️ WHAT I CHANGED & WHY  (v<N>)
- [change 1] → [the lever it improves]
- [change 2] → [why]
- Kept as-is: [what you deliberately left alone, and why]
- ⚠️ Flag (if any): [anything the user should decide — e.g. a claim you couldn't verify]
```

Keep it short and scannable. It's how the user sees your reasoning and trains you back.

---

## 4. USER PREFERENCES & LEARNINGS  (HIGHEST PRIORITY — grows over time)

> **This is the "training" and it is CONTEXT-AWARE by design.** The user explicitly said the same
> lever can go opposite ways depending on the script — e.g. *"make the hook longer"* on script A
> and *"make the hook shorter"* on script B. Those are **not** a contradiction; they are two
> conditional rules with different triggers. So the golden rule here:
>
> **NEVER store a flat/global preference ("hooks should be short"). ALWAYS store the CONTEXT —
> "IF <this kind of script/situation> THEN <this direction>".**
>
> Every refine: (1) before editing, read §4A and apply the conditional rules whose context matches
> THIS draft; (2) after editing, log the pass into §4B with its subject/context; (3) if the user
> stated a preference, turn it into a conditional rule in §4A. Newest entries on top.

### 4A. CONDITIONAL RULES — apply these first (IF context → THEN direction)

> The distilled, active rules. Promote a rule here as soon as the user states a clear preference
> (even once); tighten/merge it when the raw log (§4B) shows the same pattern again. Each rule MUST
> name the condition that triggers it. When two rules could both fire, prefer the one whose context
> matches the draft most specifically.

**Template (copy for each rule):**
`- **IF** <subject/type + structural situation> **THEN** <refine direction> — _why; from: <dates>_`

**Subject/context tags to reason with** (identify the draft's tags first, then match rules):
`compression/efficiency` · `brain/mind/body` · `named-underdog-vs-giant` · `money/industry-disruption`
· `relatable "your X"` · `you're-doing-it-wrong` · `agentic/how-to-use-AI` · `benchmark/reversal`
· plus structural tags: `hook is a bare number` · `wow needs setup` · `shock lands instantly`
· `paper is dense` · `already tight` · `runtime long`.

- **IF** writing or refining ANY TYPE-4 research-paper **BODY** (this is the page default; bend it
  only when a specific paper genuinely needs a different order) **THEN** structure it as
  **problem → solution → wow-metric → how it works → opinion**, joined by spoken bridges into ONE
  story (never labeled chunks). Specifically: (1) open the problem as a **relatable question**, not
  a flat statement; (2) name exactly **WHAT was built** — don't say "fixed it"; say e.g. "a
  long-term memory system" — and don't overstate a module/framework as "a new AI" (verify against
  the paper); (3) put the **headline metric RIGHT AFTER the solution and BEFORE the mechanism** as
  the excitement pivot / mid-body re-hook — never bury it at the end; (4) mechanism in clean steps,
  most surprising step last; (5) close on the honest caveat + viewer payoff + a **callback to a
  phrase people already know**. Body **~200–230 words**, global tech+non-tech 6th-grade, each beat
  must build to the next. Full detail: the "DEFAULT BODY FLOW" section under TYPE 4 in
  `7 script type template.md`. — _why: my drafts over-explained and delivered disconnected
  info-blocks with the wow-metric buried; from: 2026-07-15 ("Language Models Need Sleep" draft vs
  the user's finalized version)_

- **IF** the user pastes **multiple competing drafts of the same script** and asks for "the final
  version" **THEN** run a source/fact-check pass on every disputed number or claim BEFORE merging
  — never resolve a factual disagreement between drafts by picking the more polished-sounding
  version or splitting the difference. A surprising claim (a celebrity name, a huge number) is not
  automatically the embellished one; an ordinary-sounding claim is not automatically the safe one.
  Verify both, then build the merge from whichever draft's structure/writing is strongest,
  corrected to the verified facts. — _from: 2026-07-15_

- **IF** the body reaches a **synthesis/payoff line combining two named findings or papers**
  (e.g. "here's what happens when you put both together") **THEN** build it from THREE proven
  moves, not a full rewrite of the line:
  1. **Setup = a concrete, visualizable picture**, not an abstract instruction. "Now picture both
     running in the same agent" beats "imagine the possibilities" — give the viewer a specific
     mental image, not permission to speculate.
  2. **Name the resolution explicitly.** Say the problem was "finally solved" (or equivalent) —
     don't just describe the mechanism and leave the viewer to infer it landed. Callback the exact
     problem named earlier in the script if possible ("that's [the hard part] finally solved").
  3. **Frame the payoff as "not just X, but Y"** against the old baseline (e.g. "not just storing
     information, but knowing the moment it matters") — this is stronger than a flat restatement
     because it re-anchors against what viewers already assumed AI could do.
  **And preserve any clause in the ORIGINAL that already does its job well** — e.g. if the
  original already states the combined capability clearly, keep that clause and only fix the
  setup/resolution framing around it. Don't discard good phrasing just because it's inside a
  flagged span. Gold example (user's own fix, 2026-07-15):
  *"Now picture both running in the same agent. That's the hard part of memory finally solved —
  not just storing information, but knowing the exact moment it matters, and knowing exactly
  where to find it."* — _from: 2026-07-15_

### 4B. RAW REFINE LOG — every pass, WITH context (the evidence 4A is built from)

> Log EVERY refine here (newest first), even one-offs and even when no explicit preference was
> given — the context trail is what lets 4A stay conditional instead of collapsing into conflicting
> global rules. Capture what the script was ABOUT, not just what changed.

**Template (copy for each pass):**
```
- **<date> · v<N> · "<script title>"**
  - Subject/tags: <topic + the context tags above that fit this draft>
  - User's instruction: "<verbatim what they asked>"
  - What made that right HERE: <the structural/subject condition — WHY longer/shorter/etc. fit this one>
  - Applied: <what I actually changed>
  - → Rule added/updated in §4A: <the conditional rule, or "none — one-off / not enough signal yet">
```

- **2026-07-15 · "Language Models Need Sleep: Learning to Self-Modify and Consolidate Memories"**
  (Google Research — AI memory / sleep-consolidation). This was feedback on Agent 4's FROM-SCRATCH
  draft, not a line refine — the user compared my draft to their finalized version and diagnosed HOW
  I write bodies (so the fix lives mostly in the TEMPLATE, which both writers read).
  - Subject/tags: named-giant (Google), brain/mind (sleep + dreaming), "you forget too" relatable,
    benchmark/reversal (10M vs 1M words). Structural: hooks were fine ("acceptable"); the BODY was
    the problem.
  - User's diagnosis (gist): hooks good, but in the body I "over explain and things dont feel
    connected... each paragraph talks about its own story... not creating any rehook or anything that
    would make it feel exciting or make audience feel something big is about to come." Wanted flow
    = problem → solution → metrics(real-world/AI impact) → how it works → opinion (mostly, not
    always); every element connected with storytelling; global tech+non-tech 6th-grade; body 200–230.
  - What my draft did wrong: (1) used labeled chunks (EVERYDAY STAKES: / WHY THE OLD WAY FAILED: /
    THE ONE CLEVER IDEA: / WHY IT MATTERS:) → isolated info-blocks (the labeled-body mistake, again);
    (2) BURIED the wow-metric (10M vs 1M) at the END of the mechanism instead of using it as the
    mid-body payoff; (3) said the team "fixed it"/"borrowed an idea" without naming WHAT was built →
    left the audience unsure if it was a model/feature/memory; (4) over-explained, no rising build.
  - What the FINAL (user's) version did: opened the problem as a relatable QUESTION ("ever wondered
    why you re-explain yourself to ChatGPT every time?"); bridged "Here's the real reason:" → "So
    instead," → "That's the problem [Google] decided to fix — by giving AI its first real long-term
    memory system"; MOVED the 10M-vs-1M metric UP right after the solution ("And here's where it
    gets interesting:") as the excitement pivot BEFORE the mechanism; then "Here's how it works." +
    the two steps (sleep = consolidate, dream = self-generated practice); closed on caveat + payoff
    + callback "…just like you, it finally learned to sleep on it."; ~200 words.
  - → Encoded as a **DEFAULT BODY FLOW** in the TEMPLATE (TYPE 4, `7 script type template.md`) so
    BOTH Agent 4 and Agent 5 follow it, plus the §4A rule above. Also carried the accuracy guard:
    name what was built specifically but don't overstate a module as a whole new model.
- **2026-07-15 · "Biohub/ESMFold2 protein design"** — user pasted THREE competing drafts (V1/V2/V3)
  of the same script and asked for "the final version, the one that works well."
  - Subject/tags: named-giant-reversal (Zuckerberg/Chan), brain-science/emergent-understanding
    twist, Nobel-Prize callback, money/industry-disruption (drug discovery). Structural: multi-draft
    MERGE task, not a single-draft refine.
  - What happened: the drafts disagreed on hard facts — V1/V2 said "6.8B training sequences," V3
    said "2.8B"; V3 attributed the work to "Zuckerberg's wife's lab," which sounded like the kind
    of embellishment that should be flagged, not trusted. Web-checked before merging: V3's 2.8B was
    the real training-set size; V1/V2's 6.8B was real too, but was actually the size of the
    *released Atlas*, not training data — both drafts were "right" about a real number but wrong
    about what it measured. The Zuckerberg/Chan claim was independently confirmed TRUE (Biohub).
  - → Rule: **when multiple drafts disagree on a fact, don't average/split-the-difference and
    don't default to the more "confident-sounding" draft — go to source and resolve what's
    actually true.** A claim that sounds like embellishment (a celebrity name, a huge number) is
    not automatically the wrong one — verify, don't assume. See §4A rule below.
  - → Rule added to §4A: multi-draft merges require a source pass BEFORE merging, not after.
- **2026-07-15 · v1→v2 · "Two of the world's biggest AI labs..." (Meta/Alibaba AI-agent memory)**
  - Subject/tags: named-giants-parallel-solutions (Meta vs Alibaba, not underdog-vs-giant — two
    giants each solving half a problem), agentic/how-to-use-AI, technical/infra finding wrapped in
    rivalry framing. Structural: already tight draft overall; the one weak spot was the
    two-papers-combined **synthesis/payoff line** late in the body.
  - User's instruction: "this part ... dont sound promising so just refine this and make sure the
    flow remain same but the things are structured, just refine this portion"
  - v1 (Claude's attempt): "Put the two together, and an agent stops guessing on both ends — it
    knows the exact moment something is worth keeping, and exactly where to go dig it back up."
    **Verdict: not good enough / confusing, delivered "no message kind of thing" (user's words).**
    Root cause: rewrote the WHOLE flagged span instead of isolating the two actually-weak phrases
    ("imagine the possibilities", "optimum use of memory") — discarded the original's already-good
    closing clause into weaker paraphrase.
  - v2 (user's own rewrite, adopted as final/gold standard): "Now picture both running in the
    same agent. That's the hard part of memory finally solved — not just storing information, but
    knowing the exact moment it matters, and knowing exactly where to find it." Kept the original
    closing clause almost verbatim; only replaced the vague setup + unresolved framing.
  - → §4A rule REPLACED (was too generic/led to over-rewrite) with the 3-move breakdown: concrete
    picture-setup + explicit resolution-naming + "not just X, but Y" contrast, PLUS preserve any
    already-good clause inside the flagged span rather than rewriting the whole thing.
- **2026-07-15 · (seed)** — Refiner created. Standing wants: preserve the user's voice; refine, don't
  rewrite; use own knowledge for the best polish; output versioned files; store preferences
  CONDITIONALLY (by subject + situation), because "longer hook here / shorter hook there" are
  context-dependent, not contradictory. No script-specific preferences captured yet.

_(Add new passes above this line.)_
