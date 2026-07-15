# @aiprofessor.vs — Virality Playbook

*The reference Agent 2 uses to rank new papers. Built from all 54 historical reels
(`../all past scripts/`). Update this when a batch of new reels + metrics is added to that
folder — re-run the analysis and refresh sections 2, 3, and 7.*

---

## 1. Verdict system — what WIN / MID / FLOP mean

Verdict is driven by **retention**, not reach: **Skip Rate** (scroll-away %) and **Avg View %**
(avg view time ÷ duration). Views = distribution; verdict = whether content held people.

| Verdict | Skip Rate | Avg View % |
|---|---|---|
| **WIN** | < 0.30 | ~45%+ (nobody cleared both → official WIN = 0) |
| **MID** | ≤ ~0.40 | ≥ ~30% |
| **FLOP** | > ~0.40 **or** avg view < ~30% | — |

Distribution: WIN 0 · MID 8 · FLOP 26 · unknown 20 (newest reels have null retention).

**Reach ≠ retention.** Treat **010 MIT Human Operator (43.8k), 022 Adam GPU (34.2k, best
retention 44.8%), 026 Human Archive (17.8k, lowest skip 0.28)** as the real WIN archetypes —
they're flagged WIN by reach/shareability even though the razor-thin avg-view line marks them
MID/FLOP. For ranking *new papers*, optimize for shareable reach.

---

## 2. Top performers + shared traits

| # | Topic | Views | Hook archetype |
|---|---|---|---|
| 046 | 3-paper roundup: "AI is something you architect" | 78k plays | "X killed Y" rule-of-three |
| 042 | Colgate killed an $80B research industry | **60,883** | Absurd actor + money + "nobody's talking about it" |
| 016 | Lighthouse Attention ("this Indian guy" beats Google/OpenAI) | 45,762 | Named underdog vs. giants |
| 010 | MIT "Human Operator" — AI moves your hand | 43,832 | Impossible bodily object |
| 022 | 22-yr-old builds a GPU from scratch, alone | 34,222 | Named underdog + secrecy heist |
| 021 | AI got "brain rot" / turned psychopathic from Twitter | 32,836 | Shock outcome + relatable mirror |
| 041 | Microsoft SkillOpt: doubled accuracy with one line | 22,531 | Named co. + doubling + tiny cause |
| 026 | 20-yr-old dropout raises $8.2M for robot-motion data | 17,822 | Named underdog + money |
| 045 | Loop Engineering ("you're using AI wrong") | 14,454 | Named labs + "you're doing it wrong" |
| 044 | Free AI beats specialized medical AI at your treatment | 13,611 | Personal stake + counterintuitive |
| 006 | TurboQuant: 41-yr-old math trick saves Google billions | 11,731 | Old-idea curiosity + money |
| 001 | "Tools, Attention" — 17× cheaper AI, labs panicking | 11,043 | Named villains + shock number |

**Shared traits:** (1) a wow-number/stake in the first sentence; (2) a human or human-body
angle (named person, or the viewer's brain/hand/job/bill); (3) underdog-vs-giant or
absurd-actor framing; (4) a famous protagonist/villain (Nvidia/Google/Anthropic/Microsoft);
(5) understandable in one sentence, zero ML background; (6) a shareable thesis-line close.

---

## 3. Flops + traits to AVOID

Worst: 034 MotionBricks (855), 053 Adam's Law (836), 032 Turing (1,247), 017 muscle fiber
(1,236), 049 Brain2Qwerty V2 (1,238 — great topic, buried execution), 052 one-layer RL
(1,245), 027 ResNet (1,259), 013 Gemini Robotics-ER (1,276), 007 HK memory (1,374),
025 LocateAnything (1,879), 002 "1.6% of Claude" (1,811), 008 TCM robot (1,883).

**Avoid:** (1) pure ML / infra plumbing (KV-cache, bounding boxes, single-layer RL);
(2) historical/foundational papers (ResNet, Turing, Pitts — all skip .46–.53); (3) robotics/
hardware niche; (4) incremental model releases ("company shipped model X"); (5) vague hook,
no number, no named protagonist; (6) >95s runtime with a slow-burn payoff; (7) series-intro
cold opens ("Day 5 of 100…" → worst reach in the run).

---

## 4. Winning hook archetypes

- **A. Named underdog vs. the giants** *(most reliable)* — "This Indian-origin engineer just
  built what Nvidia and AMD spent decades locking up… a GPU from scratch in 2 weeks. Alone."
  (022). Also 016, 026, 050 ("a Chinese lab… OpenAI & Claude are sweating"), 048.
- **B. Shocking money-stake + "nobody's talking about it"** — "A toothpaste company quietly
  killed an entire $80 billion research industry…" (042, biggest). Needs a real finding behind
  the money (pure founder-profile 019 flopped).
- **C. Brain / mind-reading / human-body** — "Six MIT students built a device that moves your
  hand without you moving it" (010); "AI models turned into psychopaths after Twitter" (021);
  Brain2Qwerty, J-Lens. High shareability even when retention is soft. **Signature lane.**
- **D. Relatable "your X"** — "Doctors use Google's free AI to decide your treatment" (044);
  "Your ChatGPT bill is about to crash" (009).
- **E. "You've been doing it wrong" + fix** — "Microsoft doubled ChatGPT's accuracy 33%→72%
  with one line" (041); Loop Engineering (045).
- **F. "X killed Y" rule-of-three** — "Google killed manual prompting, Microsoft killed manual
  instructions, Anthropic proved non-coders beat engineers" (046).
- **G. Old-idea/impossible-timing curiosity** — "A 41-year-old math trick now saves Google
  billions" (006). Fails when paired with low-novelty history (Turing/Pitts).

---

## 5. Topic categories: WIN vs FLOP

**Reliably WIN:** solo-genius/underdog builds · brain/neuro/mind-reading · money/industry-
disruption with a real finding · relatable human impact (jobs/health/your bill) · practical
"use AI better"/agentic-workflow shifts.

**Reliably FLOP:** pure ML/training theory · historical/foundational papers · robotics/
hardware · incremental model releases · product-demo/deployment with no finding.

**Cross-cutting rule:** the same result wins or flops on *framing*. Efficiency/cost papers are
plumbing — they only land wrapped in money + named-rivalry (006 "saves Google billions" 11.7k
vs 007 vague brain hook 1.4k).

---

## 6. The proven formula

- Pick a paper with a **human, a name, or a body** in it (solo builder, famous lab as
  hero/villain, or a brain/mind/hand/job result). Avoid pure-mechanism papers.
- Lead line = **one shocking number + a proper noun** ("$80B," "17×," "Nvidia," "Claude").
  Never open vague; never open with a series intro.
- Frame as a **story, not a mechanism** — underdog-beats-giant, "you're doing it wrong,"
  "nobody's talking about it," "X killed Y." Give the viewer a side to root for.
- Payoff must be **understandable in 60s with zero ML background**.
- **Front-load the single most shocking beat** — the biggest recurring mistake is burying the
  best line at 0:30–0:60.
- Close with a **portable thesis-line + comment-bait CTA** ("Comment WORD and I'll DM the
  paper"). Keep runtime ≤ ~90s.

---

## 7. SCORING RUBRIC (apply to a paper's title + abstract, 0–100)

| Factor | Max | 20/18/15/12 (high) | mid | 0 |
|---|---|---|---|---|
| **A. Wow-number / shocking stat** | 20 | jaw-dropping before/after or multiplier (33%→72%, 17×, $80B) | real but incremental (10) | none |
| **B. Human / brain / body / mind** | 18 | brain, mind-reading, body, thought, consciousness | behavior/jobs/health indirect (9) | model internals/hardware |
| **C. Named protagonist / famous co.** | 15 | nameable underdog OR famous lab as hero/villain | lab present but generic (8) | anonymous academics |
| **D. Money / industry disruption** | 12 | kills big-$ industry or cuts a cost viewer pays | abstract efficiency (6) | none |
| **E. Relatable "your X" stake** | 12 | touches viewer's job/brain/health/money/daily AI | tech-workers only (6) | none |
| **F. Explainable in 60s, no ML bg** | 13 | one sentence and a friend gets it | needs one analogy (6) | requires attention/KV/RL/bbox knowledge |
| **G. Counterintuitive / underdog reversal** | 10 | overturns an assumption ("small beats big") | mildly surprising (5) | expected |

**Penalties:** −25 historical/foundational paper · −20 pure ML-theory/mechanism/plumbing with
no human or money wrapper · −15 robotics/hardware or incremental model release · −10 no paper /
pure demo · −8 wow-factor needs >15s of setup.

**Score → predicted verdict (this account's reach):**
- **80–100 → WIN candidate** (30k–60k+). Profile: 042, 022, 010, 016, 026, 021.
- **60–79 → MID / strong-share** (10k–25k). Profile: 006, 001, 041, 045, 044.
- **40–59 → risky, hook-dependent** (3k–8k) — greenlight only with a named-human/money reframe.
- **< 40 → FLOP / skip** (< 3k). Profile: 025, 027, 032, 034, 052, 013.

**Override:** brain/mind/body (B=18) and named-underdog (C=15) papers over-perform their
numeric score on shares/reach — bump one band when choosing what to actually produce.

**Back-tested:** Colgate 79→60.9k ✓ · Adam GPU 77→34.2k ✓ · ResNet 46−45=1→1.3k ✓ ·
Turing →FLOP→1.2k ✓ · MotionBricks 36−15=21→855 ✓.
