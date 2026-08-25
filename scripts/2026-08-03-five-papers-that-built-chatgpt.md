📌 SCRIPT TITLE: The 5 Papers That Quietly Built ChatGPT
🎯 ANGLE: Myth-correction + rule-of-five synthesis — Attention Is All You Need gets all the credit, but four other papers had to solve intelligence, speed, memory, latency, and throughput before ChatGPT could ever reach a user. Framed as "quietly built it," not "more important than Attention," per the user's own note to avoid unnecessary controversy.
👥 TARGET AUDIENCE: AI-curious general audience, tech + non-tech, global
📊 SCRIPT TYPE: Hybrid — TYPE 4 (AI research paper) + rule-of-three/five roundup (proven pattern F, see `Scripting_reference_things/winning-patterns.md` §2F — the 3-paper version of this exact structure hit 78k views, the highest raw reach in the tracked run)

Verified facts (web-checked, 2026-08-03):
- Attention Is All You Need (Vaswani et al., 2017) — introduced the Transformer / self-attention; arXiv:1706.03762.
- FlashAttention (Dao et al., 2022) — reorders attention compute to stay inside GPU SRAM, cutting memory movement; arXiv:2205.14135.
- PagedAttention / vLLM (Kwon, Li et al., 2023) — pages the KV cache like OS virtual memory; paper reports 2–4x higher throughput than FasterTransformer/Orca at the same latency; arXiv:2309.06180. The "10–12 concurrent requests" pre-vLLM figure is the source creator's own claim (from the Hinglish inspiration transcript), not a number stated in the paper itself — used here as illustrative framing, not a cited paper stat.
- Speculative Decoding (Leviathan, Kalman, Matias, 2023) — small model drafts, large model verifies in parallel; reports 2–3x speedup on T5-XXL; arXiv:2211.17192.
- Continuous / iteration batching, "Orca" (Yu et al., OSDI 2022) — slots new requests into an in-flight batch; reports up to 36.9x throughput over FasterTransformer at matched latency.

---

**Reference:** (verify every fact/number below against these)

- Attention Is All You Need: https://arxiv.org/abs/1706.03762
- FlashAttention: https://arxiv.org/abs/2205.14135
- PagedAttention / vLLM: https://arxiv.org/abs/2309.06180
- Speculative Decoding (Leviathan et al.): https://arxiv.org/abs/2211.17192
- Orca (continuous batching): https://www.usenix.org/system/files/osdi22-yu.pdf

**[HOOK 1 — Misconception-correction]**

"Everyone thinks one paper built **ChatGPT** — **Attention Is All You Need**. It only solved one of five problems."

**[HOOK 2 — Timeline/authority]**

"**Attention** gave AI a brain in 2017. It took four more papers to make that brain fast enough for a billion people to actually use."

**[HOOK 3 — Rule-of-five synthesis]**

"One paper gave AI a brain. Four more had to fix its memory, its speed, and its patience — before you ever typed a prompt."

*(word count below is built on Hook 1 — swap in Hook 2/3 for an A/B take, same length.)*

**[RE-HOOK]**

Here's the one everyone skips.

**[BODY]**

**#1 — Attention Is All You Need (2017)**

It gave AI a brain — letting every word see every other word at once.

**GPT**, **Claude**, **Gemini**, **Llama** — all of them run on it.

**#2 — FlashAttention (2022)**

A brain that's slow is useless.

So this kept computation inside the GPU's fastest memory instead of shuffling data — making it dramatically faster.

**#3 — PagedAttention, or vLLM (2023)**

This is the one people skip.

One GPU could barely serve a dozen users — memory sat wasted, like booking ten hotel rooms for one guest.

It borrowed paging from operating systems, and pushed throughput up to **4x** higher.

**#4 — Speculative Decoding**

Writing one word at a time is slow.

So now a small model drafts ahead, and the big model just checks the draft — up to **3x** faster.

**#5 — Continuous Batching (Orca)**

Requests never arrive together.

So instead of waiting for a full batch, new ones now slot straight into one already running — pushing throughput up nearly **37x**.

None of these replaced the **Transformer**.

Each one just removed the next bottleneck between a research idea and a product a billion people use today.

**[CTA]**

Comment **"STACK"** and I'll DM you all five papers.

---

✅ VIRALITY CHECKLIST:
- [x] Named giants in the hook/body (ChatGPT, GPT, Claude, Gemini, Llama)
- [x] Misconception-correction hook (proven pattern E: "you think X, it's actually Y")
- [x] Rule-of-N synthesis structure (proven pattern F — 78k-view precedent)
- [x] Re-hook within first 5 seconds, teasing the "skipped" paper
- [x] Numbers as the weapon (4x, 3x, 37x) placed inside each beat, not saved for one spot
- [x] Closing portable thesis line
- [x] Single-line, single-ask CTA
- [x] Body stays under the requested ~190–200 word total (196 words, hook→CTA)

📊 TRIGGERS USED: Misconception-correction, named-giant credibility, hidden/skipped-knowledge curiosity, rule-of-five escalation, numeric proof stacking

📱 CAPTION: The 5 papers that quietly built ChatGPT 🧵 Everyone credits one. It took five. Full list + links in comments.

🏷️ HASHTAGS: #ChatGPT #AI #LLM #Transformers #MachineLearning #ArtificialIntelligence #OpenAI #Anthropic #DeepLearning #TechExplained #AIResearch #vLLM
