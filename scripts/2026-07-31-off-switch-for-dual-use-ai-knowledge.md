📌 SCRIPT TITLE: Anthropic Built an Off Switch for AI's Most Dangerous Knowledge
🎯 ANGLE: Frame Anthropic's GRAM method as literally what it is — an off switch for dual-use knowledge (virology, cybersecurity, nuclear physics) — built around the old-way-failed (train two whole separate models) → new-way-wins (one model, swappable modules) spine, with the counterintuitive "bigger models remove it cleaner" scaling result as the mid-body wow.
👥 TARGET AUDIENCE: general audience — tech + non-tech, anyone curious about AI safety, "how do AI companies actually stop misuse"
📊 SCRIPT TYPE: TYPE 4 — AI Research Paper

Verified facts (web-checked, 2026-07-31):
- "An off switch for dual-use knowledge in AI models" — Anthropic + AE Studio, published 2026-07-08
- Method name: GRAM (Gradient-Routed Auxiliary Modules) — adds small extra "module" neurons to every Transformer layer, one per dual-use topic; general weights stay frozen against risky text, only the matching module absorbs it; the module can be deleted (capability gone) or kept (capability retained) per deployment, no retraining needed
- Old way today: filter dangerous knowledge out of training entirely for every copy of the model — want a public-safe version AND a version unlocked for a vetted biosecurity lab? That requires training two separate models from scratch
- Tested dual-use domains: virology, cybersecurity, nuclear physics
- Tested across seven model sizes, 50 million to 5 billion parameters
- Headline result (direct quote): "A single GRAM model can be reconfigured to match the performance of any of five distinct filtered models trained on different data"
- At near-real scale (~800M params): capability removal was "about as effective as never having trained on that data at all," with no meaningful hit to general performance
- Counterintuitive scaling finding: the gap between module-on and module-off widened with scale — bigger models fall further behind the all-data baseline on the removed topic once it's off, i.e. the bigger the model, the cleaner the removal
- Security test: attempts to recover deleted knowledge via malicious fine-tuning were blocked "about as well as data filtering did"
- Honest limitations (stated by Anthropic): not tested at frontier scale, not applied to production Claude models, and "some dual-use knowledge may be too entangled to isolate cleanly"

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

And the strangest part is what happens as the AI gets bigger.

**[BODY]**

Ever wonder why an AI chatbot suddenly refuses to answer something, even when you have a legitimate reason to ask?

Here's the real problem behind that.

Some knowledge is dual-use — the same virology facts that help build a vaccine could help someone design a deadly pathogen.

So today, companies handle it one blunt way — filter it out of every copy of the model.

That locks out a vetted lab that genuinely needs it too — their only option was training a whole separate model from scratch.

That's the problem **Anthropic** just decided to fix.

They built something they're calling an off switch, using a method called **GRAM**.

Instead of baking risky knowledge into the model's core brain, each dangerous topic gets its own removable module.

And here's where it gets interesting.

Tested from **50 million** to **5 billion** parameters, one trained model could switch between **5** completely different versions — just by swapping modules.

Normally, the bigger an AI gets, the messier its knowledge gets tangled together.

Here, the opposite happened — the bigger the model, the cleaner the removal worked.

Here's how it actually works.

The model's general knowledge stays frozen during training.

Only the risky facts get routed into that one module, nowhere else.

Delete the module, and the knowledge is gone — like unplugging a USB stick.

Hackers trying to fine-tune it back in got blocked almost as hard as if it had never been trained in at all.

It's not perfect — untested on real production models, and some dangerous knowledge might be too tangled with intelligence itself to ever fully pull apart.

But if it holds up, AI might finally stop needing an all-or-nothing choice about what it's allowed to know.

**[CTA]**

Comment **"SWITCH"** and I'll DM you the paper.

---

✅ VIRALITY CHECKLIST:
- [x] Short, single-idea hooks (each under ~20 words, no buried payoff)
- [x] Named giant (Anthropic) in every hook
- [x] "Here's where it gets interesting" mid-body curiosity gap
- [x] Wow-metric (1 model = 5 versions) placed right after the solution, before the mechanism
- [x] Counterintuitive scaling twist as a genuine mid-body "wait, what?" beat
- [x] Direct retention-loop re-hook pulling the viewer into the scaling twist
- [x] Relatable human mirror (unplugging memories) threaded through the hook set
- [x] Physical analogy (USB stick) grounds an abstract ML mechanism
- [x] Honest caveat before the closing payoff
- [x] Value-based CTA with topical keyword
- [x] High-stakes, real subject matter (bioweapons/cyber/nuclear) handled factually, no fear-mongering

📊 TRIGGERS USED: Named-giant credibility (Anthropic), you're-being-fooled/dual-use twist (same knowledge builds a vaccine or a weapon), mystery-tool reveal (an "off switch" inside an AI), counterintuitive-reversal (bigger models are usually messier, here they're cleaner), self-recognition analogy (unplugging your own memories), physical grounding analogy (USB stick), number shock (50M→5B parameters, 1 model = 5 versions), high-stakes subject matter (bioweapons/cyber/nuclear).

📱 CAPTION: Anthropic just built something they're calling an off switch for AI's most dangerous knowledge — virology, cybersecurity, nuclear physics. Instead of training a whole new model to add or remove a risky skill, one model can now be reconfigured just by swapping small removable "modules." And the weirder part: it works BETTER the bigger the model gets. 🔌🧠

🏷️ HASHTAGS: #AI #ArtificialIntelligence #AISafety #Anthropic #MachineLearning #AIResearch #TechNews #FutureTech #AIExplained #Biosecurity
