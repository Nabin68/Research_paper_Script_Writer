# Caption Playbook — @aiprofessor.vs

The caption is not the script. The script is what you *say* on camera; the caption is what
someone reads when the video is muted, or after it hooked them. It has to stand alone.

This file is the authority on caption shape. §1–§3 are the rules, §4 holds the reference
captions, §5 is the growing learnings log (same idea as `agent5/refine_playbook.md` — every
pass gets logged, and stated preferences become CONDITIONAL rules, never flat global ones).

---

## 1. THE SHAPE (in order)

**1. Hook line.** One sentence, on its own line. Names the lab(s) and states the surprising
finding. Present tense, "just" carries the recency. It is a claim, not a tease — a reader who
stops here should still have learned something.

> Google just discovered AI needs to sleep to actually remember anything.
> Two AI labs just quietly fixed the problem breaking every long-running AI agent.

**2. The problem.** Opens with `The problem:` or `The issue:`. Say what is broken in plain
words, from the reader's side ("every AI resets the moment you close the tab"). If the field
has a technical name for it, put it in quotes — `Researchers call it "behavioral state decay."`
Then land why it matters or why it was hard.

**3. The turn.** Who fixed it, and the pivot that makes it interesting. Often a short
negation before the reveal:

> Not by retraining.
> By giving AI something closer to a sleep cycle.

For multi-lab posts, frame the contrast instead: *"Meta and Alibaba solved it from opposite ends."*

**4. The mechanism.** `Here's how it works.` then plain English, carried by a human analogy —
sleep consolidating the day's events, dreaming up practice questions. No jargon that hasn't
been unpacked. This is the section that earns the save.

**5. The result, with hard numbers.** Labelled `The result:` or `Result:`. Give the number AND
its baseline — a number alone means nothing:

> tested past 10 million words of context, it stayed almost perfectly accurate.
> Rival memory methods started breaking down after just 1 million.

**6. The honest caveat.** Optional but strongly preferred when the paper is early. It builds
trust and costs nothing: *"Researchers are clear this is an early proof, not a finished system."*
Never oversell a result the paper didn't claim.

**7. The payoff line.** Echo the hook's own image so the caption closes a loop:

> because, like you, it learned to sleep on it.
> Combine both, and memory in AI agents is finally solved.

**8. CTA.** Exactly this shape, one line:

> Comment "SLEEP" and I'll send you the paper.

The keyword is ONE uppercase word pulled from the caption's central image (SLEEP, MEMORY).
Plural to `both papers` when the post covers more than one.

**9. P.S. block.** Fixed boilerplate, do not reword:

> P.S. I break down one AI paper like this every day inside my WhatsApp community.
> Link in bio.

**10. Spacer.** Four lines, each a single space followed by a period:

```
 .
 .
 .
 .
```

**11. Tag block.** One line, square brackets, comma-separated, Title Case, **no `#` symbols**.
About 15 tags, ordered specific → broad: the labs and the paper's own name first, then the
topic, then the wide reach tags.

> [Google Research, AI Memory, Long Term Memory, Sleep Consolidation, LLM, Machine Learning,
> AI Agents, Neural Networks, AI Research, Deep Learning, Tech News, AI Papers, Artificial
> Intelligence, Cognitive AI, Memory Consolidation]

---

## 2. VOICE

- Second person, direct. The reader is in the sentence: *"it stops forgetting you."*
- Short sentences. Line breaks do the pacing work — a sentence on its own line lands harder.
- Line density is flexible: reference A breaks nearly every sentence out; reference B runs
  fuller paragraphs. Both work. Break more when the idea is a chain of steps; run fuller when
  you are contrasting two things.
- Concrete and comparative always beats vague and superlative. `8.3 points higher`, `nearly
  half the searching`, `1 million vs 10 million` — never "dramatically better".
- No emojis anywhere in the caption body.
- No `#` hashtags — tags live in the bracket block only.
- Name the labs. Meta, Alibaba, Google Research are the credibility, use them early.

---

## 3. HARD RULES

- Never invent or round a number the script did not contain. If the script's figure is vague,
  keep it vague or drop it — do not manufacture precision.
- The caption must stand alone. Someone who never watched the video should follow it.
- Keep the reader's own claims and framing when refining. Polish, do not replace.
- The CTA, the P.S., the four spacer dots and the bracket tag block are structural. They appear
  every time, in that order, at the end.
- Output the caption as plain text ready to paste into Instagram — no markdown headings, no
  bullet characters, no code fences around the caption body itself.

---

## 4. REFERENCE CAPTIONS (the ground truth — match this feel)

### Reference A — Google, sleep/memory (single-paper, step-chain shape)

```
Google just discovered AI needs to sleep to actually remember anything.
The problem: every AI resets the moment you close the tab.
The only way to make it remember permanently is to retrain the whole model from scratch, millions of dollars, months of work.
So instead, most systems just stay frozen, knowing only what they were trained on.
A Google Research team decided to fix that.
Not by retraining.
By giving AI something closer to a sleep cycle.
Here's how it works.
While the AI "sleeps," it takes everything from the conversation and files it into permanent memory, the same way your brain consolidates the day's events overnight.
Then it starts "dreaming." It writes its own practice questions on what it just learned and rehearses them, with no human involved.
The result: tested past 10 million words of context, it stayed almost perfectly accurate.
Rival memory methods started breaking down after just 1 million.
Researchers are clear this is an early proof, not a finished system.
But if it holds at scale, it means AI stops forgetting you the moment the conversation ends , because, like you, it learned to sleep on it.
Comment "SLEEP" and I'll send you the paper.
P.S. I break down one AI paper like this every day inside my WhatsApp community.
Link in bio.
 .
 .
 .
 .
 [Google Research, AI Memory, Long Term Memory, Sleep Consolidation, LLM, Machine Learning, AI Agents, Neural Networks, AI Research, Deep Learning, Tech News, AI Papers, Artificial Intelligence, Cognitive AI, Memory Consolidation]
```

### Reference B — Meta + Alibaba, agent memory (two-lab contrast shape)

```
Two AI labs just quietly fixed the problem breaking every long-running AI agent.
The issue: AI agents build a huge trail of memory during long tasks — facts, mistakes, subgoals. But past a point, they stop acting on it. Researchers call it "behavioral state decay." The knowledge is there. It just stops mattering.
Meta and Alibaba solved it from opposite ends.
Meta built a second AI that watches the agent work and decides the exact moment to say "remember this." Result: up to 8.3 points higher success on coding benchmarks.
Alibaba built NapMem. Instead of handing the agent memories, it gives the agent tools to dig — raw conversations, summaries, full profiles — and decide how deep to search. Result: nearly half the searching, more correct answers.
Meta taught an agent when to remember. Alibaba taught it where to look.
Combine both, and memory in AI agents is finally solved.
Comment "MEMORY" and I'll send you both papers.
P.S. I break down one AI paper like this every day inside my WhatsApp community. Link in bio.
 .
 .
 .
 .
 [AI Agents, Meta AI, Alibaba, NapMem, AI Memory, Long Horizon Agents, LLM Agents, AI Research, Machine Learning, Behavioral State Decay, Agentic AI, Deep Learning, Tech News, AI Papers, Artificial Intelligence]
```

**What to take from each:** A is the shape for one paper explained as a chain of steps — problem,
pivot, mechanism, number, caveat, loop-close. B is the shape for two labs attacking one problem —
state the shared problem once, give each lab its own short block ending in its own `Result:`,
then a one-line contrast and a synthesis. Pick the shape that matches the script.

---

## 5. LEARNINGS & USER PREFERENCES

Same discipline as the refiner playbook: preferences are recorded as CONDITIONAL rules
("IF <context> THEN <direction>"), never as flat global rules — the same lever often goes
opposite ways depending on the subject.

### 5A. Conditional rules

_(none yet — added as the user states preferences)_

### 5B. Raw log

_(one line per caption pass: date · subject · what was asked for · what changed)_
