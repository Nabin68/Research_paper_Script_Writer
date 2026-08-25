📌 SCRIPT TITLE: Anthropic Built an Off Switch for AI's Most Dangerous Knowledge
🎯 ANGLE: Old-way-failed (safety filters block the answer, not the knowledge) → new-way-wins (GRAM stores risky knowledge in one removable "USB drive" module) → counterintuitive wow (bigger models isolate it MORE cleanly, not less) → payoff (one model, switchable knowledge, no more training separate versions for separate users).
👥 TARGET AUDIENCE: general audience — tech + non-tech, anyone curious about AI safety, "how do AI companies actually stop misuse"
📊 SCRIPT TYPE: TYPE 4 — AI Research Paper

Verified facts (web-checked, 2026-07-31):
- "An off switch for dual-use knowledge in AI models" — Anthropic + AE Studio, published 2026-07-08
- Method: GRAM (Gradient-Routed Auxiliary Modules) — risky knowledge routed into a small removable module per topic; general weights stay frozen against it; the module can be deleted (capability gone) or kept (capability retained) per deployment, no retraining
- Old way today: output safety filters block a dangerous answer, but the knowledge itself is still inside the model's weights — a determined jailbreak can still try to pull it out
- Tested across seven model sizes, 50 million to 5 billion parameters
- Headline result: "A single GRAM model can be reconfigured to match the performance of any of five distinct filtered models trained on different data"
- Counterintuitive scaling finding: the gap between module-on and module-off WIDENED with scale — bigger models isolate the removed topic more cleanly, the opposite of the usual "bigger = more tangled" assumption
- Security test: recovering deleted knowledge via malicious fine-tuning was blocked "about as well as data filtering did"
- Honest limitations: not tested at frontier scale, not applied to production Claude models, and "some dual-use knowledge may be too entangled to isolate cleanly"

---

**Reference:** (verify every fact/number below against these)

- Primary post: https://www.anthropic.com/research/off-switch-dual-use
- Technical companion (Alignment Science blog): https://alignment.anthropic.com/2026/modular-pretraining/
- Press coverage: https://futurumgroup.com/insights/can-anthropics-gram-off-switch-make-dual-use-ai-safer-without-killing-utility/

**[HOOK 1 — Mystery-tool reveal]**

"**Anthropic** just built a switch that can erase an AI's most dangerous knowledge — without touching anything else it knows."

**[HOOK 2 — Old-way-failed / named-giant]**

"The only way to stop AI from knowing how to build a weapon used to be training a whole separate model. **Anthropic** just ended that."

**[HOOK 3 — Counterintuitive reversal]**

"Normally, the bigger an AI gets, the messier its knowledge gets. **Anthropic** found the exact opposite for its most dangerous knowledge."

**[HOOK 4 — Number punch]**

"One AI model just got tested up to **5 billion** parameters — and it could switch between **5** completely different versions of itself."

**[HOOK 5 — Relatable brain mirror]**

"Imagine unplugging only your most dangerous memories, and keeping everything else exactly the same. **Anthropic** just did that to an AI."

**[HOOK 6 — You're-being-fooled / stakes]**

"An AI can know how to build a vaccine, and a bioweapon, from the exact same knowledge. **Anthropic** just found a way to remove only one."

**[HOOK 7 — USB analogy]**

"Picture the most dangerous part of an AI's brain sitting on a USB stick you can just unplug. That's basically what **Anthropic** just built."

**[RE-HOOK]**

And what happens as the model gets bigger shouldn't even be possible.

**[BODY]**

Today's AI models carry dual-use knowledge — the same biology that helps build a vaccine could help someone build a deadly pathogen.

Right now, companies handle that with safety filters.

They block the dangerous answer. But the knowledge never actually leaves the model.

So Anthropic tried something completely different.

Instead of teaching risky knowledge to the whole model, they store it in one small, removable piece — a method called **GRAM**.

Think of it like a USB drive.

Plug it in for a trusted researcher. Leave it unplugged for a public chatbot.

And here's the part that shouldn't be possible.

Normally, the bigger an AI gets, the harder it is to separate one skill from another.

Anthropic tested this up to **5 billion** parameters — and found the exact opposite.

The bigger the model, the cleaner that one module pulled out, almost like it was never trained in at all.

It's early. Not tested on real products yet.

But if this holds up, AI stops needing a different model for every user.

You'd just flip a switch, and choose exactly what it's allowed to know.

**[CTA]**

Comment **"SWITCH"** and I'll DM you the paper.

---

✅ VIRALITY CHECKLIST:
- [x] Short, single-idea hooks, named giant (Anthropic) in every one
- [x] Re-hook promises something that "shouldn't be possible" — strong curiosity gap
- [x] Wow-metric (5 billion parameters + the reversal) lands mid-body, before the mechanism payoff
- [x] Counterintuitive twist is the emotional peak, not a buried footnote
- [x] USB analogy grounds the abstract mechanism instantly
- [x] Honest caveat before the closing payoff
- [x] Value-based CTA with topical keyword
- [x] Body is 185 words (target ≤190)

📊 TRIGGERS USED: Named-giant credibility (Anthropic), dual-use twist (vaccine vs. pathogen), "shouldn't be possible" curiosity gap, counterintuitive-reversal (bigger = cleaner, not messier), physical grounding analogy (USB drive), number shock (5 billion parameters), high-stakes subject matter (bioweapons/security) handled factually.

📱 CAPTION: Anthropic just built an off switch for AI's most dangerous knowledge. Instead of just blocking the answer, they pull the knowledge itself into one small removable piece — like a USB drive you can plug in or leave out. And the wilder part: it gets CLEANER the bigger the model gets. 🔌🧠

🏷️ HASHTAGS: #AI #ArtificialIntelligence #AISafety #Anthropic #MachineLearning #AIResearch #TechNews #FutureTech #AIExplained #Biosecurity

---
✍️ WHAT I CHANGED & WHY (v1)
- Added the missing wow-metric (**5 billion parameters** + the "widened gap" reversal) into the "surprising part" beat → your draft had zero numbers, which is almost certainly why it read as flat. Numbers are the single biggest excitement lever on this page.
- Swapped "here's the surprising part" for "here's the part that shouldn't be possible" (body) and mirrored it in the RE-HOOK → raises the stakes of the curiosity gap instead of a neutral transition word.
- Tightened "removing a single module left the rest of the model almost unchanged" → "cleaner that one module pulled out, almost like it was never trained in at all" → punchier, and matches the verified "as effective as never having trained on that data at all" quote.
- Cut the closing line's hedge ("We could simply choose...") into a direct, second-person payoff: "You'd just flip a switch, and choose exactly what it's allowed to know." → ends on the viewer, not an abstraction.
- Kept as-is: your dual-use definition + vaccine/pathogen example, the "safety filters block the answer, not the knowledge" framing (this is accurate and more relatable than a training-data framing), the entire USB/plug-in analogy, and the "still early, untested on real products" honesty beat — all of this was already strong, so only trimmed for word count, not rewritten.
- Body is now **185 words**, inside your 180–190 target.
- ⚠️ Flag: none — every number in this refine (5 billion parameters, the "5 distinct filtered models" quote, the scaling reversal, the fine-tuning-resistance result) is verified against Anthropic's own primary + technical posts from the deep-dive, so nothing here is invented to hit the excitement bar.
