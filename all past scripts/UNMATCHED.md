# Unmatched & Excluded

## Unmatched scripts

Scripts present in `raw-scripts/` that never matched any reel in `raw-metrics/` (no reel covers these papers). Listed with title, source file, and reference so they can be paired manually if a matching reel surfaces later.

- **"Lower Artificial Intelligence Literacy Predicts Greater AI Receptivity"** — `1.md` — Reference: https://osf.io/preprints/psyarxiv/t9u8g_v1
  Reason: no reel covers this psyarxiv AI-literacy study (27 countries, 7 experiments, insurance-exec prediction).
- **Sycophancy / "delusional spiraling"** — `1.md` — Reference: https://arxiv.org/pdf/2602.19141
  Reason: no reel covers this paper (AI validating false beliefs, ~300 cases / 14 deaths, "perfect reasoner" test).
- **Foundations 03 — Neocognitron (Kunihiko Fukushima, 1980)** — `1.md` — Reference: https://home.csulb.edu/~cwallis/382/readings/482/mccolloch.logical.calculus.ideas.1943.pdf (note: script Reference block was blank/missing for Foundations 03; the 1943 link belongs to Foundations 01)
  Reason: no reel covers the Fukushima/Neocognitron computer-vision-history paper.
- **"Job vs AI" (Ramp / Revelio economic study)** — `3.md` — Reference: https://x.com/arakharazian/status/2071942212925936053
  Reason: no reel covers this study (22,000 US companies, credit-card data, +10% headcount / +12% entry-level hiring, $34/employee/month). NOTE: reel `004 ai-freshers-job-market-fear` is a *different* jobs paper (Anthropic "observed exposure"), so it is not a match for this script.
- **SpikeBrain / SpikingBrain (Chinese Academy of Sciences)** — `3.md` — Reference: https://arxiv.org/pdf/2509.05276
  Reason: no reel covers this spiking-neuron paper (~100x faster on 4M-token input, 97% less energy, MetaX GPUs). NOTE: reel `050 chinese-labs-ai-breakthrough` is DSpark/DeepSeek (speculative decoding), a different Chinese-lab paper — not a match.

_(The empty "Blueprint" template block in `1.md` is intentionally ignored per instructions — not a script.)_

## Possible topic duplicates

Reels kept as SEPARATE `final/` files but flagged for manual review — each pair covers the same (or near-same) paper, usually posted twice with different titles/framing and near-identical transcripts. Cross-referenced in `merge-log.md` with tag `[possible-topic-duplicate]`.

- **015 `mit-artificial-muscle-fibers` ↔ 017 `mit-artificial-muscle-robotics`** — both MIT artificial-muscle reels (different URLs/timestamps).
  ⚠️ ADDITIONAL ISSUE on 015: its Transcript block contains *Microsoft synthetic-personas* content, not muscle content — a wrong-paste in the source (`[SCRIPT-ISSUE]`). Preserved as-is; paper set `unknown`.
- **036 `google-hope` ↔ 037 `google-nested-learning`** — same paper (Nested Learning / HOPE), same URL & timestamp.
- **038 `claude-code-expertise-domain` ↔ 039 `claude-code-expertise-understanding`** — same paper (Anthropic Claude Code expertise), same URL & timestamp.
- **040 `microsoft-skillopt` ↔ 041 `microsoft-skillopt-accuracy`** — same paper (SkillOpt), same URL & timestamp. (These are NOT `-2`-suffixed files, so per rules they were kept separate + flagged rather than merged.)
- **043 `medical-ai-doctors-prefer` ↔ 044 `medical-ai-general-outperform`** — same paper (NYU Langone / Nature Medicine), same URL & timestamp.

_(For reference, the 5 literal `-2`-suffixed duplicates WERE merged, not kept separate: game-animation→034, consumer-research→042, loop-engineering→045, architect→046, ais-impact→047. See `[dedup]`/`[dedup-conflict]` in `merge-log.md`.)_

## Excluded

Files deliberately not processed into `final/`.

- **`a-day-in-the-life-of-a-city-dog.md`** — off-topic (not an AI/research reel), and its `index.md` row contains literal placeholder values (`videoViewCount`, `sharesCount`) with an invalid `timestamp` ("timestamp"). Likely a test row. No merged file created.
