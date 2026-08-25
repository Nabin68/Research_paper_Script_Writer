📌 SCRIPT TITLE: The AI That Taught Itself To Panic

🎯 ANGLE: A trillion-parameter model was given no human examples and one rule — right answer, get a reward. It taught itself five habits nobody programmed, and one of them is exam panic: when it senses time running out, it dumps its reasoning and forces a guess.

👥 TARGET AUDIENCE: Anyone who has ever sat an exam. Tech and non-tech — zero ML background needed.

📊 SCRIPT TYPE: TYPE 4 — AI Research Paper

Verified facts (web-checked, 2026-07-17):
- Model: **Ring-2.5-1T-Zero**, 1 trillion parameters, 63B activated (MoE), built on Ling-2.5-1T-Base — arXiv 2607.12395
- Lab: **Ant Group / InclusionAI** (Alipay's parent) + Renmin, Tsinghua, Zhejiang universities — arXiv + TechTimes. Ring/Ling family is Ant Group's open-source line (HF: inclusionAI)
- Trained with **zero human-annotated data** ("zero RL" — RL with verifiable rewards). ⚠️ ACCURACY GUARD: this applies to the RL stage. The BASE model was still pretrained on human text — which is exactly where the "brain fart" language comes from. Never say "no human data at all."
- **AIME 2026: 93.2%** (High mode, 64k tokens). Also AIME 2025: 91.0% · AIME 2024: 93.2% · IMOAnswerBench: 72.7% — arXiv HTML
- Trained on 320 H200 GPUs (Megatron + SGLang) — arXiv HTML
- Five spontaneous emergent behaviours: anthropomorphism, structured formatting, self-verification, parallel reasoning, **context anxiety** — abstract
- "Context anxiety" verbatim: the model *"actively aborts its complex reasoning chain to force a heuristic guess"* as it nears perceived token limits. Paper calls it *"a fascinating, albeit flawed, emergent behavior"* — arXiv HTML
- "Anthropomorphism" verbatim: *"simulated emotional states and informal meta-commentary"* in three categories — Simulated Frustration and Venting (*"brain fart"*), Simulated Slacking and Guesswork (*"wing it"*), Self-Praise and Playful Banter. Researchers attribute it to internet-forum patterns in pretraining data — arXiv HTML
- ⚠️ ACCURACY GUARD: the paper says **simulated** emotional states. The model is not feeling anything. The script must say this out loud — the honesty is also the best beat.
- Posted to arXiv 2026-07-14

---

**Reference:** (verify every fact/number below against these)

- Paper: https://arxiv.org/abs/2607.12395
- Full text (emergent behaviours section): https://arxiv.org/html/2607.12395
- Hugging Face paper page (82 upvotes): https://huggingface.co/papers/2607.12395
- Press: https://www.techtimes.com/articles/320677/20260716/trillion-parameters-no-human-labels-ant-group-documents-five-emergent-ai-behaviors.htm
- Model weights: https://huggingface.co/inclusionAI/Ring-2.5-1T

**[HOOK 1 — Brain/mind + relatable mirror]**

An AI just developed exam anxiety. When it senses the clock running out, it panics and forces a guess. Nobody taught it that.

**[HOOK 2 — Number punch]**

**Ant Group** trained a **1-trillion**-parameter AI without a single human-written example. It scored **93.2%** on an elite maths exam, then started writing "**brain fart**."

**[HOOK 3 — Underdog vs giants]**

**OpenAI** and **Google** pay people to teach their AI how to think. **Alipay's** parent company taught theirs nothing at all — and it picked up our worst habits instead.

**[HOOK 4 — You're-being-fooled]**

You think AI is a calm machine that never cracks. Researchers just caught one panicking near a deadline and throwing out a guess to save itself.

**[HOOK 5 — Small-detail punch (experimental)]**

An AI wrote "**brain fart**" in the middle of solving a maths problem. Nobody put that word there. It learned it from us.

**[HOOK 6 — Relatable mirror (experimental)]**

This AI cuts its own thinking short and guesses when time runs low. Sound familiar? It worked out on its own that a guess beats an unfinished answer.

**[RE-HOOK]**

And the reason it panics is stranger than the panic itself.

**[BODY]**

Ever wondered who teaches an AI how to think?

Here's the real reason it matters: normally, people do.

Humans write out thousands of worked solutions, step by step, and the AI copies the style.

That's slow, expensive, and it quietly caps the AI at how well we can already explain things.

So **Ant Group**, the company behind Alipay, tried the opposite.

They took a **1-trillion**-parameter model, handed it maths problems, and gave it one rule: get the right answer, get a reward.

No worked examples. No instructions on how to think.

And here's where it gets interesting:

Left alone, it taught itself to crack competition maths, the level that decides who reaches the Math Olympiad.

It scored **93.2%** on AIME 2026.

But the score isn't what shocked the researchers.

Five habits showed up that nobody had programmed.

It started checking its own answers.

It started trying several routes at once.

And then it started to panic.

The paper's own name for this is context **anxiety**.

As the model senses it's running out of room to think, it dumps its careful reasoning and forces a quick guess.

Because it worked out that a guess scores something, and an unfinished thought scores nothing.

It even vents while it works, saying things like "**brain fart**" and "let me just **wing it**."

Now here's the catch — the researchers call the panic flawed, not brilliant.

It isn't feeling anything.

It learned those words from human forum posts buried in its training data.

But nobody built the panic in.

It learned that the way you did — from a scoreboard and a clock.

**[CTA]**

Comment **"PANIC"** and I'll DM you the paper.

---

🔀 A/B SWAP (one high-leverage variant — pick on the shoot):

The closing line is this script's highest-leverage swap. Option A is shipped above; try B if you want the mirror harder:

- **A:** "But nobody built the panic in. / It learned that the way you did — from a scoreboard and a clock."
- **B:** "But nobody built the panic in. / A scoreboard and a clock did — the same two things that gave you yours."

---

✅ VIRALITY CHECKLIST:
- [x] Wow-number in the first sentence (93.2% / 1 trillion) — Hooks 2, 3
- [x] Brain / mind / body angle — the signature lane (archetype C, comp: reel 021 "AI brain rot", 32.8k)
- [x] Named protagonist + named giants (Ant Group / Alipay vs OpenAI / Google) — archetype A
- [x] Relatable "your X" stake — every viewer has panicked in an exam
- [x] Counterintuitive reversal — nobody designed the anxiety; it emerged from a reward rule
- [x] Understandable in 60s, zero ML background — no "RL", "MoE", "tokens", "zero RL" anywhere in the spoken script
- [x] Body flow: problem → solution → wow-metric → behaviours → caveat + payoff
- [x] Mechanism collapsed (the surprise is WHAT it did, not HOW) — space spent on the behaviours instead
- [x] Anchor threaded literally: "panic" ×3 + "nobody taught / taught itself / nobody programmed / nobody built in"
- [x] Zero matched-pair dash asides; both em-dashes are single trailing reveals
- [x] Honest caveat delivered out loud ("It isn't feeling anything") — protects credibility, and lands as a beat
- [x] Portable thesis close (13 words, genuine reversal) + comment-bait CTA
- [x] Body 265 words · runtime ~75–85s

📊 TRIGGERS USED: Curiosity gap (why does it panic?) · Relatable mirror (exam panic) · Shock outcome (emergent behaviour nobody programmed) · Underdog vs giants (Ant Group vs OpenAI/Google) · Authority number (93.2%, 1 trillion) · Pattern break ("It isn't feeling anything") · Identity callback ("the way you did")

📱 CAPTION:
Ant Group gave a 1-trillion-parameter AI zero human examples and exactly one rule: get the right answer, get a reward. 🧠

It taught itself to score 93.2% on AIME 2026 — and it taught itself four more things nobody asked for.

The strangest one? When it senses it's running out of room to think, it abandons its own reasoning and forces a guess. The researchers named it "context anxiety."

It also vents mid-problem. Actual words in its reasoning: "brain fart." "Let me just wing it."

To be clear — it isn't feeling anything. Those words came from human forum posts in its training data. But nobody designed the panic. It worked out on its own that a guess scores something and an unfinished thought scores nothing.

Which is exactly what you figured out in your last exam. 😅

Comment "PANIC" and I'll DM you the paper.

🏷️ HASHTAGS:
#airesearch #artificialintelligence #machinelearning #aipaper #antgroup #llm #aiexplained #technews #emergentbehavior #aiprofessor
