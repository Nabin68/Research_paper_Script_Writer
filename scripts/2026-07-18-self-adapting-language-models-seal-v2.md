📌 SCRIPT TITLE: The AI That Failed a Test, Then Beat GPT-4.1

🎯 ANGLE: Alternate-flow version of the same paper. The first SEAL script (scripts/2026-07-18-self-adapting-language-models-seal.md) runs problem → solution → wow-number → mechanism → caveat — the same spine as the Sleep script. This version drops the "study notes" framing and rebuilds the body as a climbing-scoreboard / retake narrative: score, then score, then score, with the mechanism folded inside each round instead of explained separately. Same verified facts, two of them (the 20% middle round, and the full 33.5/39.7/46.3/47.0 SQuAD progression) newly surfaced — the first script only said "beat GPT-4.1," this one shows the exact margin.

👥 TARGET AUDIENCE: Anyone who has ever failed a test and studied harder for the retake. Tech and non-tech — zero ML background needed.

📊 SCRIPT TYPE: TYPE 4 — AI Research Paper (deliberately reordered flow, see angle note)

Verified facts (same paper, same web-check pass as the first script, 2026-07-18):
- Paper: **Self-Adapting Language Models** (SEAL) — arXiv 2506.10943. v1 2025-06-12, v2 2025-09-18. **NeurIPS 2025**.
- Lab: **MIT** — Adam Zweiger, Jyothish Pari, Han Guo, Ekin Akyürek, Yoon Kim, Pulkit Agrawal.
- **ARC few-shot (Llama-3.2-1B-Instruct, curated/simplified subset): in-context 0% → self-edit without RL 20% → full SEAL 72.5% → oracle upper bound 100%.**
- **SQuAD no-passage QA (Qwen2.5-7B): passage only 33.5% → passage + self-generated notes 39.7% → passage + GPT-4.1-written notes 46.3% → SEAL after 2 RL rounds 47.0%.**
- ⚠️ ACCURACY GUARD: ARC (0/20/72.5) is **Llama-3.2-1B**. The GPT-4.1 comparison (46.3 vs 47.0) is a **different model, Qwen2.5-7B**. Kept as two separate "tests" in the body — never merge them into one claim.
- ⚠️ ACCURACY GUARD: 47.0% vs 46.3% is a **narrow** win. Say "narrow win," not "crushed" or "destroyed."
- ⚠️ ACCURACY GUARD: ARC subset is curated/simplified — never say "solved ARC."
- ⚠️ Limitation (verbatim from paper): catastrophic forgetting — *"performance on earlier tasks gradually declines as the number of edits increases."*
- ⚠️ Limitation (verbatim): cost — *"each self-edit evaluation takes approximately 30–45 seconds,"* called *"substantial overhead."*
- 📅 Same note as first script: paper is June 2025, not in papers.csv, shot on request.

---

**Reference:** (verify every fact/number below against these)
- Paper: https://arxiv.org/abs/2506.10943
- Full text (results + limitations): https://arxiv.org/html/2506.10943v2
- Project page: https://jyopari.github.io/posts/seal
- NeurIPS 2025 poster: https://neurips.cc/virtual/2025/poster/118690
- Code: https://github.com/Continual-Intelligence/SEAL

**[HOOK 1 — Score-climb / number punch]**

An AI took the same test three times. **Zero.** Then **20%.** Then **72.5%.** Nobody graded it in between.

**[HOOK 2 — Small beats big]**

A model small enough to run on a laptop rewrote its own notes for a test — and narrowly beat **GPT-4.1**'s.

**[HOOK 3 — Relatable mirror]**

You know the feeling of failing a test, rewriting your notes, and acing the retake? **MIT** just taught an AI to do that to itself.

**[HOOK 4 — You're-being-fooled]**

Every AI you talk to gets one shot at everything. **MIT** built one that keeps retaking the exam until it wins.

**[HOOK 5 — Counterintuitive]**

The best tutor for this AI wasn't a bigger AI. It was itself, failing the same test three times in a row.

**[RE-HOOK]**

And the third time it took that test, the score almost didn't make sense.

**[BODY]**

Ever fail a test, rewrite your notes, and ace the retake?

An **MIT** team just taught an AI to do exactly that, to itself.

They gave a small model, just **1 billion** settings, a simplified batch of visual puzzles.

First attempt: no notes, just the raw puzzle in front of it.

Score: **zero**.

Second attempt: the model writes its own notes first, then takes the test.

Score: **20%**.

For the third attempt they changed the rule: write several different versions of the notes, keep whichever version raised the score, throw out the rest, repeat.

Score: **72.5%**.

Zero, to twenty, to seventy-two point five, and nobody graded it in between.

A hand-built, perfectly tuned version tops out at **100**, so there's still room to climb.

Here's test two, and this one's a real contest.

A bigger model reads a passage with no notes at all: **33.5%**.

Same model, its own handwritten notes: **39.7%**.

Same model, notes written *for* it by **GPT-4.1**: **46.3%**.

Then the model retrains itself on its own notes for one more round.

New score: **47.0%**, a narrow win over **GPT-4.1**.

Now the honest part.

Every time this model rewrites itself, it forgets a little of what it learned the round before.

Researchers call it catastrophic forgetting.

You'd call it cramming.

Each retake also burns up to **45 seconds** of compute, so this is a proof of concept, not a finished tutor.

But the pattern holds.

An AI that grades its own retake keeps getting smarter, retake after retake.

Every AI you use today gets one attempt, and that's it.

This one keeps retaking the test until it wins.

**[CTA]**

Comment **"RETAKE"** and I'll DM you the paper.

---

✅ VIRALITY CHECKLIST:
- [x] Flow deliberately reordered vs. the first SEAL script and the Sleep script: scoreboard/retake climb (0→20→72.5, then 33.5→39.7→46.3→47.0) instead of problem→mechanism→single-number reveal
- [x] Mechanism folded inside each round instead of explained as a separate "how it works" block
- [x] Wow-numbers now appear three times as escalating beats, not once mid-body
- [x] Named giant beaten (GPT-4.1) + named lab (MIT), kept as a strictly separate second test per accuracy guard
- [x] New granular data surfaced vs. script 1: the 20% middle round, and the full 33.5/39.7/46.3/47.0 chain
- [x] Relatable "your X" stake — failing a test and acing the retake
- [x] Zero jargon spoken ("RL", "self-edit", "SFT", "fine-tune" never said aloud)
- [x] Anchor threaded literally: "score" / "retake" / "test" running through every beat
- [x] Honest caveat delivered out loud (catastrophic forgetting = cramming; proof of concept, not finished)
- [x] Portable thesis close + comment-bait CTA
- [x] Body ~250 words · runtime ~75–85s

📊 TRIGGERS USED: Curiosity gap (why does the score keep climbing with no one grading it?) · Relatable mirror (failing a test, rewriting notes, acing the retake) · Shock number ×2 (0→72.5, narrow GPT-4.1 win) · Small beats big (1B model outscoring itself; separately, its retrained notes edging out GPT-4.1's) · You're-being-fooled (your AI only gets one attempt) · Identity callback ("You'd call it cramming")

📱 CAPTION:
An AI took the same test three times. Zero. Then 20%. Then 72.5%. Nobody graded it in between. 📈

MIT built a model that retakes its own exams — it writes a batch of different notes, keeps whichever version raises its score, and tries again.

On a second test, its retrained notes narrowly beat notes written for it by GPT-4.1: 47.0% vs. 46.3%. 🤏

The honest part: every retake makes it forget a little of what it learned before. Researchers call it catastrophic forgetting.

You'd call it cramming. 😅

Comment "RETAKE" and I'll DM you the paper.

🏷️ HASHTAGS:
#airesearch #artificialintelligence #machinelearning #aipaper #mit #llm #aiexplained #technews #selflearningai #gpt4
