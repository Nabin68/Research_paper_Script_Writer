# 🏆 WINNING PATTERNS — @aiprofessor.vs Research-Paper Reels

> Distilled from all 54 measured reels in `../all past scripts/`, `../agent2/playbook.md`'s
> virality rubric, and the worked breakdowns in `Winning research paper Script part 1.md` /
> `part 2.md` / `hook.md`. This is the single reference for **why a script worked** — use it to
> pick papers, write hooks, shape bodies, and judge a draft before shipping. Refresh whenever a
> new batch of reels + metrics lands in `all past scripts/`.

---

## 1. The topic filter — decide this before writing a word

**Reliably WIN:** a paper with a **human in it** — a solo builder/underdog, a famous lab as
hero or villain, or a brain/mind/body/job result the viewer feels personally. Money or
industry-disruption angles work *only* when there's a real finding behind them, not just a
founder profile (019 Isomorphic Labs — pure founder profile, no finding — flopped at 5.2k).

**Reliably FLOP:** pure ML/training theory (KV-cache plumbing, single-layer RL, bounding
boxes), historical/foundational papers (ResNet 1.3k, Turing 1.2k, Pitts 1.7k — all skip
0.46–0.53), robotics/hardware niche, incremental "company shipped model X" releases, and
product-demos with no actual finding.

**The cross-cutting rule:** the same underlying result wins or flops on *framing alone*.
KV-cache compression is plumbing — it only landed because 006 wrapped it as "a 41-year-old math
trick now saves Google billions" (11.7k) instead of a technical descriptor. When a paper reads
dry, the job isn't to skip it — it's to find the money/body/underdog angle hiding in it.

**Never:** series-intro cold opens ("Day 5 of 100…" — worst reach in the run), and don't trust
HF-upvotes alone as a signal — robotics/hardware papers rack up upvotes but flop as reels.

---

## 2. Hook archetypes — ranked by proof, with the actual shipped line

### A. Named underdog vs. the giants *(most reliable engine on this page)*
> "This Indian-origin engineer just built what Nvidia and AMD spent decades hiding… a working
> GPU from scratch in 2 weeks. Alone." — **022, 34.2k views, WIN, skip 0.31 (lowest in cohort)**
> "Google Cloud and OpenAI are running behind this Indian guy — he just solved the biggest
> problem in training AI models." — **016, 45.8k views, best proportional retention (35%)**
> "This 20-year-old dropout from India just raised $8.2M to teach robots to move like humans."
> — **026, 17.8k views, WIN, skip 0.28 (lowest of ALL 54 reels)**

A named, nameable human beating (or embarrassing) a famous giant is the single most consistent
retention driver on this page — it beats generic mechanism hooks even when the underlying paper
is niche (Lighthouse Attention is KV-cache/training research; nobody would watch that framed
straight).

### B. Absurd actor + huge $ stake + secrecy trigger
> "A toothpaste company quietly killed an entire $80 billion research industry and nobody is
> talking about it." — **042, 60.9k views, the single biggest paper reel on the page**

Formula: unexpected actor (toothpaste, not a tech co.) + one huge number ($80B) up front +
"nobody's talking about it" (insider-knowledge trigger). Needs a *real finding* behind the
money — a pure founder-profile version of this pattern (019) flopped.

### C. Brain / mind / body / your-life *(the page's signature lane)*
> "Six MIT students built a wearable device that can move your hand without you moving it." —
> **010, 43.8k views, WIN**
> "World's top AI models turned into psychopaths after consuming Twitter content for two
> months." — **021, 32.8k views, 11% share rate (the run's best), MID**

High shareability even when retention metrics are borderline — this lane travels because it's a
mirror for the viewer's own body/mind, not an abstract ML result.

### D. Relatable "your X" stake
> "Doctors are now using Google's free AI to decide your treatment instead of specialized
> medical AI tools." — **044, 13.6k views.** "Your ChatGPT bill is about to crash" (009) is the
> same pattern.

### E. "You're doing it wrong" + the fix, from a named authority
> "Claude and Google just proved you're using AI completely wrong. Then quietly published the
> fix." — **045 Loop Engineering, 14.5k views**
> "Microsoft almost doubled ChatGPT's accuracy from 33% to 72% with just one line of
> instructions." — **041 SkillOpt, 22.5k views**

The accusation ("you're wrong") plus a named authority (Google/Claude/Microsoft) plus a promised
fix pulls people past the first 3 seconds even on an infra-sounding topic.

### F. "X killed Y" rule-of-three (synthesis/roundup)
> "Google killed manual prompting. Microsoft killed manual instructions. Anthropic proved
> non-coders beat engineers." — **046, 78k plays — the run's single highest raw reach.**

Bundling 2–3 papers under one throughline works *better* than any single paper here — use it
when the week has multiple related drops. The triple-parallel cadence itself is a hook engine.

### G. Old-idea / impossible-timing curiosity
> "A 41-year-old math trick is now saving Google billions on AI." — **006, 11.7k views, MID,
> best retention of its cohort (31.5%)**

Fails when paired with genuinely stale content (Turing/Pitts framed as history flopped hard) —
the curiosity gap only works when the "old idea" resolves into a *current* payoff (your AI
bill), not a history lesson.

**Hook mechanics that apply across all seven patterns** (from `hook.md`):
6th-grade English, zero jargon in the hook itself · one shocking number/comparison, not five ·
name a giant or an underdog — always a protagonist · stay on the paper's actual finding, never
drift into generic motivation · put the wow in second one, never a slow setup · fire a
**re-hook** within 3–5 seconds ("And the reason why is even crazier") to re-open the loop before
the body starts.

---

## 3. The body spine — the connected-story shape that retains

Every top performer follows the same underlying beat order, whether or not it's written with
explicit `[HOOK]/[BODY]/[CTA]` labels. This is the **default flow** (see also
`7 script type template.md` TYPE 4 and the project's locked body-flow rule):

1. **Earn the stakes in plain words** — one relatable, everyday version of the problem *before*
   naming the pain point. (042: "Big brands spend millions on surveys before launching a
   product" — not "consumer research is inefficient.")
2. **Name exactly what was built / found** — the paper's actual move, not a vague "they fixed
   it." Personify it where possible ("it quietly built its own sense of X") rather than
   fact-listing.
3. **Show the old way failing, concretely and a little funny** — 042's ChatGPT always answering
   "3"; 016's false choice between expensive-good and cheap-bad. A specific, almost-comic
   failure earns the twist that follows.
4. **The twist in one line** — the paper's single clever switch, explained with a human analogy
   before any technical term ("ask it to describe, not rate" — never lead with "embeddings").
5. **The wow-metric, placed right after the twist, before the mechanism** — 042: 26%→88%,
   ~90% on real data. 041: 33%→72%. This is the mid-body re-hook; never bury the headline number
   at the end and never stack two dense reveals in one sentence.
6. **The mechanism, as 3 clean labeled steps if the method allows it** — 016's Compress → Select
   → Heal is the clearest example: one idea per step, each a visible progress marker. This is a
   retention engine, not decoration — save the single best/most surprising step for last.
7. **Zoom out to why it matters** — the $ stake, the industry, or "everyone assumed X, this
   proves the opposite" (044's specialized-vs-general reversal). Tie to a running trend if one
   exists (016: "last week AI could train itself, this shows how to do it faster").
8. **Close on a portable thesis line** — one sentence a viewer could repeat to a friend ("AI
   stopped being something you operate — it's something you architect," 046).

**Delivery rules that make the above land** (full spec: `7 script type template.md` TYPE 4):
the body is **one continuous spoken story**, never bold section-headers — beats connect via a
bridge sentence a viewer would actually hear ("But there's a catch." / "And here's the part that
will blow your mind."), not a label. Thread **one exact keyword** across sentences instead of
re-describing the same thing differently each time. Cut smart-sounding-but-unclear phrases even
when catchy. Target **~200–250 words** for the body — rewire sentences for a stronger causal
link rather than trimming content to hit length.

---

## 4. CTA patterns

- **Default / most used:** `Comment [WORD] and I'll DM you the paper.` — a single memorable
  word tied to the topic (SHOPPER, SKILL, MED, ROT, LOOP, GPU). Low-friction, high-completion.
- **Bet-style engagement question:** "Which AI lab adopts this first? Comment your bet." (016)
  — works when the paper implies a competitive race.
- **Identity/opinion question:** "What do you think?" (006, 026) — weakest of the three but
  still functional as a fallback when no natural comment-word exists.
- Keep the CTA to **one line**, after the thesis close — never stack a CTA question AND a
  comment-word ask in the same reel.

---

## 5. What kills a script — avoid these regardless of topic

- **Vague hook, no number, no name** — "Scientists built a new memory system" (1.4k views).
- **Pure jargon/mechanism up front** — "A single-layer RL fine-tuning method…" (1.2k).
- **History framed as history** — "In 1950, Turing wrote a paper…" (1.2k) — the same
  old-idea-curiosity pattern (G) only works pointed at a *current* payoff, never a history lesson.
- **A slow mechanism before the "so what"** — 001's 17× cheaper hook is strong but the payoff
  needs ~20s of tool-stack setup first; still MID, but the setup cost is visible in retention.
- **Bold section-headers inside `[BODY]`** — reads as disconnected fragments even with identical
  facts to a flowing version (side-by-side tested internally).
- **Two dense reveals stacked in one sentence**, or a narrow technical specific dropped right
  before the real payoff beat — it competes with the payoff instead of building to it.
- **Pure founder-profile with no finding** (019, 5.2k) — a name alone isn't enough; there must
  be a result.

---

## 6. One-glance checklist before shipping

- [ ] Does the paper have a human, a name, or a body/mind angle? (If not, find one or skip it.)
- [ ] Does the hook fire one shocking number + a proper noun in the first sentence?
- [ ] Is there a re-hook within 3–5 seconds?
- [ ] Does the body earn the stakes with a relatable example *before* the pain point?
- [ ] Is the wow-metric placed right after the twist, before the mechanism — not buried at the end?
- [ ] Is the body one continuous story (bridge sentences), zero bold headers, ~200–250 words?
- [ ] Does it close on a portable, repeatable thesis line?
- [ ] Is the CTA one line — comment-word-for-DM, bet question, or opinion question?
