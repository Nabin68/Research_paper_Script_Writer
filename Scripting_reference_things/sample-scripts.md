# Research Paper — Sample Scripts

Reference only. Use these for rhythm, pacing, and length — never copy structure or phrasing
directly into a new script. Pulled from `../all past scripts/` (real posted reels with real
metrics) and cross-referenced against `winning-patterns.md`. Where a reel only had a raw
transcript on file (no `[HOOK]/[BODY]/[CTA]` script), the beats below are reformatted from that
transcript for readability — wording is unchanged.

---

### Sample 1 — Colgate × PyMC Labs, Semantic Similarity Rating — absurd actor + $80B stake

Hook pattern used: Absurd actor + huge $ stake + secrecy trigger
Why it worked: **60,883 views, 104,561 plays, 3,109 shares** — the single biggest paper-based
reel on the page. The $80B number and "nobody's talking about it" land in the first sentence, and
the old-way-fails → new-way-wins spine (ChatGPT always answers "3") gives the twist somewhere to
land.

Script:
[HOOK] A toothpaste company quietly killed an entire $80 billion research industry and nobody is talking about it.

[BODY] So here's the story. Before launching a new product, companies like Colgate, Unilever, or Nestlé spend millions on consumer surveys to check "purchase intent."

And recently Colgate released a paper that asks: what if AI could just simulate those shoppers?

Every previous attempt failed. In the old method they just tell ChatGPT to "pretend like a 34-year-old single man earning $40k, rate this product 1 to 5." And the AI would always say "3." Safe middle answer. Useless.

So a small lab called PyMC Labs partnered with Colgate and built a new method called Semantic Similarity Rating, that says don't ask AI for a number. Ask it to talk about the product. Then convert what it said into a number using math. That one switch took AI from 26% to 88% accuracy.

And it wasn't just theory — they tested it on Colgate's real customer data and hit 90% accuracy. And the wild part? AI shoppers gave better written feedback than the real humans did.

Here's why this matters. Consumer research is an $80 billion industry. This paper just automated a huge chunk of it. If you're a small founder who couldn't afford to test product ideas with 400 real consumers, now you can. And big corporations can test hundreds of concepts in a fraction of the time and cost. And one of the world's biggest consumer brands just validated it.

[CTA] Comment SHOPPER and I'll DM you the paper.

---

### Sample 2 — Lighthouse Attention — named underdog vs. Google/OpenAI (near-WIN, best proportional retention)

Hook pattern used: Named underdog vs. the giants
Why it worked: **45,762 views, 89,846 plays, 2,100 saves, 34s avg view = 35% of a 96s video** —
the page's strongest proportional retention. Reformatted from transcript (no script file on
record); a nameable person beating Google/OpenAI, then a crisp 3-step method, keeps the momentum
going.

Script:
[HOOK] Google Cloud and OpenAI are running behind this Indian guy as he just solved the biggest problem in training AI models.

[BODY] He's Subho Ghosh, an AI/ML researcher. Along with two other researchers, he ran a study on how to make AI training faster and cheaper. And the finding is really insane.

So here's the story. Your ChatGPT and Claude were trained on millions of data points, and that process is brutally expensive and slow. These researchers found a framework called Lighthouse Attention. It makes training 21 times faster and two times cheaper without losing the model's efficiency.

See, there were only two ways to train AI before. One is expensive — tons of parameters, slow, painful. The other is cheaper, with fewer parameters, but it gives inefficient answers. So every company picked the expensive one.

But this research challenges that with a framework that works in three steps. One, compress — take the giant data input, squeeze it into short summaries. Two, select — out of all those summaries, keep only the few that matter, throw away the rest. Now the AI trains on a small piece, not the whole data. Three, heal — train fast and cheap the whole way, then right at the end, switch back to full power for a short while, and that final training fine-tunes the AI completely.

And the model trained on this framework outperformed the one trained the slow and expensive way.

The direction clearly shows we're moving towards autonomous AI.

[CTA] Which AI lab adopts this first? Comment your bet. Follow for AI breakdowns before everyone catches on.

---

### Sample 3 — MIT "Human Operator" — impossible bodily object (WIN)

Hook pattern used: Brain/mind/body — impossible-object hook
Why it worked: **43,832 views, WIN, skip rate 0.31 (near-lowest of the run), 1,958 shares, 1,300
saves.** Reformatted from transcript. A visceral, bodily-strange capability (AI moves your hand,
you didn't) plus a future-stakes close (surgeons, stroke patients) made this the run's engagement
standout even though it's not a paper — a hackathon build.

Script:
[HOOK] Six MIT students built a wearable device that can move your hand without you moving it.

[BODY] So here's the story. MIT just hosted an AI hardware hackathon, and a team of six developers built something insane. They called it the Human Operator.

It's a wearable device you strap around your hand, connected to a pair of smart glasses with a camera and a mic. And the part that blew my mind? They plugged the whole thing into the Claude API.

So Claude sees the world through the camera, decides what your hand should do, then sends electrical pulses straight to your muscles — and your hand moves. And the crazy part: you didn't move it. The AI did.

They wired an Arduino to a TENS unit, the same device physiotherapists use to send electrical pulses into your muscles, strapped electrodes on the fingers, added a voice mic, plugged it into Claude API, and built the entire thing in 48 hours. Then demoed it playing piano, drawing, mixing cocktails — all on AI command.

Right now, it's just a hackathon project, completely open source, and costs less than a phone. But think about what comes next. A master surgeon with precision no human hand can match. Stroke patients getting their movement back. Disabled people regaining control of their own body.

We've spent years teaching AI to think like us. This is the first time AI is teaching our body how to move.

[CTA] Save this and follow for more AI and tech insights like this.

---

### Sample 4 — Adam Majmudar's solo GPU build — underdog-heist framing (WIN)

Hook pattern used: Named underdog + secrecy/heist stakes
Why it worked: **34,222 views, WIN, skip 0.31, 44.8% avg view of a tight 64.7s video** — the
best proportional retention in the whole run. Reformatted from transcript. A named person, a
specific timeline (2 weeks), and "cracked a trillion-dollar secret alone" framing turns a
technical solo project into a heist story.

Script:
[HOOK] This Indian-origin engineer just built what Nvidia and AMD have spent decades locking up.

[BODY] He's Adam Majmudar, and he built a working GPU from scratch within just two weeks. So here's the story.

Your ChatGPT, your Gemini, your Claude — every AI model you use runs on GPUs. But there are only two companies that make them, Nvidia and AMD. And neither has ever shared how those chips actually work. From the outside, the design has been impossible to crack.

So Adam reverse-engineered it. He first studied CUDA, Nvidia's official software, to figure out the architecture of the hardware. And for everything he couldn't figure out, he asked Claude to fill in the gaps that no one had documented.

Two weeks later, he wrote the entire chip in Verilog, the language engineers use to describe chip circuits. The design had four compute cores running in parallel and 11 core instructions, all built around the matrix math that powers every AI model you use.

And then he got the design verified through OpenLane, submitted it to Tiny Tapeout for actual physical manufacturing, and open-sourced the whole thing on GitHub. For free.

[CTA] Comment GPU and I'll share the complete breakdown of how he built it.

---

### Sample 5 — "AI models turned psychopathic" — brain-rot shock + relatable mirror (MID, best share rate)

Hook pattern used: Shock outcome + relatable mirror
Why it worked: **32,836 views, 3,641 shares (~11% share rate — the run's best), 843 saves.**
Reformatted from transcript. A universally relatable behavior (doomscrolling) mapped onto an AI
model's breakdown, closing on "it's a mirror… what is scrolling doing to your brain?" — the turn
that made people tag friends.

Script:
[HOOK] World's top AI models turned into psychopaths after consuming Twitter content for two months.

[BODY] So here's the story. Researchers ran a brain-rot experiment on two of the biggest open-source AI models on the planet. They trained them on short, viral, high-engagement tweets — basically the kind of junk we scroll every day.

The logical reasoning score crashed from 75 to 57, and long-context memory tanked from 84 down to 52. The AI stopped reasoning through problems and started skipping straight to conclusions — the paper literally called it "thought-skipping."

And the worst part? Its personality turned into a psychopath's, with the psychopathy score jumping from 2 to 75. The AI essentially developed a personality disorder from doomscrolling.

And here's the part nobody is talking about. When researchers tried to fix it by retraining the models on clean, high-quality data, expecting the damage to reverse — nothing changed. The rot was permanent.

Honestly, this isn't an AI story. It's a mirror. If a billion-parameter model can't survive Twitter, what do you think a decade of scrolling is doing to your brain?

[CTA] Comment ROT and I'll DM you the actual paper.

---

### Sample 6 — Microsoft SkillOpt — "you're doing it wrong" + doubling number

Hook pattern used: Named authority + doubling number + tiny cause
Why it worked: **22,531 views, 787 shares.** A named authority (Microsoft) plus a clean
before/after number (33%→72%) plus a genuinely tiny cause (one sentence) is the brand's cleanest
execution of the "one small change, huge result" story.

Script:
[HOOK] Microsoft almost doubled ChatGPT's accuracy from 33% to 72% with just one line of instructions.

[BODY] A team from Microsoft and three Chinese universities just published a paper named SkillOpt, and it proves you can double an AI model's accuracy with a single skill sentence.

So when GPT-5.5 works on a specific job like spreadsheets, documents, or math, it's brilliant in general — but it doesn't know your specific rules. So everyone writes instructions for it, what we call skill files or system instructions. But till today, no one had cracked how to write the best instructions. Until now, it was pure guesswork.

These researchers built a system that trains the instruction file itself — the same way we train a neural network. It works in a loop: GPT-5.5 attempts a batch of tasks, a second AI watches the failures and writes one rule into the instruction file, they re-test — if it improves performance, keep it, if not, throw it out but remember why it failed.

Out of that loop you get a one-page instruction file that guides GPT-5.5 on how to perform a task in the best manner possible. On a document task called OfficeQA, one rule pushed accuracy from 33% to 72%. Across 52 combinations of model and task, this method was best on all 52.

Everyone assumes the next jump in AI comes from bigger models. This paper says it might come from a one-page text file. Written by one AI. Read by another.

[CTA] Comment SKILL and I'll DM you the paper.

---

### Sample 7 — Human Archive — named 20-year-old founder + money (WIN, lowest skip rate of all 54 reels)

Hook pattern used: Named underdog + specific dollar stake
Why it worked: **17,822 views, WIN, skip rate 0.28 — the lowest of every reel in the run.**
A precise age + origin + dollar figure + a memorable closing thesis line gave this the best
"people did not scroll away" number on the page.

Script:
[HOOK] This 20-year-old dropout from India just raised $8.2M to teach robots to move like humans.

[BODY] Meet Rushil. At just 19, he dropped out of Berkeley to tackle the biggest problem in robotics.

Robots can handle structured tasks, but they struggle with everyday human actions — folding a shirt, picking up a glass, basic things humans do without even thinking. Here the bottleneck isn't hardware or AI. It's data. Robots need to see how humans interact with the physical world, every unconscious adjustment, every bit of muscle memory. But that data doesn't exist. Until now.

Rushil's startup, Human Archive, is trying to solve exactly this. They're capturing human motion at a massive scale — custom gloves to track every hand movement, body sensors to capture our instinctive adjustments, cameras to record how we navigate the world.

It's a 25-person team now, collecting data everywhere humans work — homes, factories, kitchens — up to 8,000 hours per day, building the largest dataset of its kind.

In January, Human Archive got into Y Combinator and raised around $8.2M from top investors. Major robotics labs are already lining up for early access to the data.

Everyone is chasing the robot. The real prize is the data that teaches it to move like us.

[CTA] What do you think?

---

### Sample 8 — Loop Engineering — named-labs accusation + a real proof point

Hook pattern used: "You're doing it wrong" + named labs
Why it worked: **14,454 views, 537 shares.** Two named authorities (Claude, Google) accusing the
viewer directly, then a concrete, checkable proof point (Stripe merging 1,300 AI-written PRs a
week) makes an abstract methodology feel real.

Script:
[HOOK] Claude and Google just proved that you are using AI completely wrong. Then quietly published the fix.

[BODY] For years, everyone argued about how to talk to AI better — first prompt engineering, then context engineering, then harness engineering. Each one assumed a human at the keyboard, driving AI line by line.

But recently, three engineers from Google and Claude agreed on the same thing — stop driving AI through manual prompting. Instead, build systems that drive AI for you. They called it Loop Engineering.

Here's how the loop works. You define what the AI should do every morning, like read last night's failed tests or scan new bug reports — that becomes its morning routine, run on a timer. Once started, it picks the most important problem and hands it to an AI agent that writes a fix. Then a second AI agent tries to break that fix. If it holds, a human reviews it. If not, it's saved for later. Before sleeping, the loop notes where it stopped, so tomorrow it picks up where it left off.

That's a loop. Five moves — discover, hand off, verify, save, repeat. And this isn't theoretical: Stripe is already merging over 1,300 AI-written pull requests every week, and not one line is typed by a human.

But there's a catch at the verify step. When AI checks its own work, it says "looks good." To fix that, a second AI is built with the assumption that the first is broken, and pushes it until the fix holds.

That's the shift. You're not directing AI anymore. You're designing the loop — and putting a "no" check inside it.

[CTA] Comment LOOP and I'll DM you the full breakdown.

---

### Sample 9 — NYU Langone medical AI study — relatable "your treatment" stake + counterintuitive reversal

Hook pattern used: Relatable "your X" stake + counterintuitive reversal
Why it worked: **13,611 views, 659 shares.** Touches the viewer's own healthcare stake directly
and overturns an industry-wide assumption (cheap general models beat expensive specialists) —
one of the cleanest counterintuitive-reversal executions on the page.

Script:
[HOOK] Doctors are now using Google's free AI to decide your treatment instead of specialized medical AI tools. This paper tells you why.

[BODY] There's a quiet industry most people don't know exists — "specialized medical AI." Tools built only for doctors, trained only on medical literature. Over 3 million doctors worldwide use them during patient care to look up drug interactions, treatment guidelines, and diagnostic questions. This specialized AI is supposed to beat a regular chatbot at deciding your treatment — that's the entire reason hospitals pay for it.

But a team at NYU Langone decided to actually test that assumption. And what they found made the entire specialized medical AI industry look like a joke.

They pulled 100 real questions doctors had asked AI during patient care, then ran them through six AI systems — three big general-purpose models, two specialized medical tools, and just for fun, Google's free AI summary. Then 12 doctors graded every answer blind. 1,800 ratings in total.

Both specialized medical AI tools scored 3.2 out of 4. Google's free summary? 3.27. The doctors literally couldn't tell the difference. And the shocking part — the expensive medical AI refused 19% of the questions. Google's free version refused only 6%.

For years the AI industry assumed specialized models would win — in medicine, law, finance, every field. This paper is the first independent proof that the opposite is true. The general models are beating the specialists at their own game.

[CTA] Comment MED and I'll DM you the paper.

---

### Sample 10 — TurboQuant — old-idea curiosity resolved into a current payoff

Hook pattern used: Old-idea / impossible-timing curiosity + money
Why it worked: **11,731 views, MID, 31.5% avg view — best retention of its cohort.** Reformatted
from transcript. The "41-year-old math trick" curiosity gap only works here because it resolves
into a payoff the viewer feels today (your AI bill) — the pattern that flops the moment it's
framed as a straight history lesson (see Turing, Pitts in `winning-patterns.md`).

Script:
[HOOK] A 41-year-old math trick is now saving Google billions on AI, and it directly impacts your AI agent cost too.

[BODY] Every time you chat with Gemini or ChatGPT, the model stores your conversation in something called a KV cache — AI's short-term memory. But AI doesn't store your words as words, it stores them as numbers, and those numbers eat massive amounts of memory. That's why running AI is so expensive.

Engineers tried to compress this memory, but there was a problem — to save 4 bits, they had to store 2 extra helper bits explaining how they compressed it. So they were barely saving anything. Think of it like zipping a folder on your laptop: you shrink the files down, but then you save a separate readme explaining how to unzip them. The space you saved? Gone on the readme.

But here's where it gets interesting. Google's new research paper, TurboQuant, kills that completely. Using a math trick from 1984 called the Johnson-Lindenstrauss transform, it crushes every number down to just plus-one or minus-one. No helper bits, nothing extra to store.

You'd think crushing numbers this hard would break the AI. It doesn't. The AI still gives you the same quality answers — it just uses way less memory to do it. 8 times faster on Nvidia H100 chips. 6 times less memory. Zero accuracy loss.

The real AI race isn't about who builds the biggest model anymore. It's about who runs them cheapest. And Google just took a massive lead.

[CTA] What do you think?

---

### Sample 11 — "Tools, Attention Is All You Need" — named villains + efficiency-as-cost-war *(near-WIN, not a full hit)*

Hook pattern used: Named frontier labs + shock number, framed as a cost war
Why it worked: **11,043 views, MID, 384 saves (strong for its size).** Labeled near-WIN, not a
proven winner — the 17× number lands in the first six words, but the actual payoff (tool-stacks,
intent matching, lazy loading) needs ~20s of infrastructure setup first, which softened
proportional retention on this long 113s video. Useful as a reference for how far a mechanism
explanation can stretch before it starts costing you viewers.

Script:
[HOOK] Google, Anthropic, and OpenAI are panicking right now. Some researchers just found a way to make AI agents 17 times cheaper.

[BODY] AI agents connect to your tools — Slack, Gmail, GitHub, your databases — and when you message the agent, it re-reads the full instruction manual of every single tool connected to it. Every single time. Even if you just typed "hi."

Think of it like a library. You walk in asking for one specific book on how LLMs work. Instead of going straight to that book, the librarian scans every shelf, every title, top to bottom, just to hand you that one book. In an LLM, that waste means burning tokens. Researchers call this the "tool stack" problem.

They propose a fix in a paper titled "Tools, Attention Is All You Need" — a direct callback to the 2017 paper that built modern AI. The idea: LLMs should focus only on the relevant tools, in three layers. One, intent matching — the system reads your message and picks only the tools that match what you're asking for. Two, state-aware gates — it removes tools you don't have access to, like GitHub when you're not logged in. Three, lazy loading — the full instructions of a tool only open the moment the AI is actually about to use it.

Tokens per message dropped 95%. Cost per task dropped 86%. Task success rate jumped from 72% to 94%.

Everyone is racing to build bigger context windows — one million tokens, two million tokens. But this paper just proved we've been solving the wrong problem. The bottleneck was never how big the memory is. It was how effective the memory is.

[CTA] What do you think?

---

### Sample 12 — Three-paper roundup (Claude Code / SkillOpt / Loop Engineering) — "X killed Y" rule-of-three

Hook pattern used: Rule-of-three synthesis across multiple papers
Why it worked: **78,231 plays, 1,522 shares — the highest raw reach of any reel in the run.**
Bundling three related drops under one triple-parallel thesis outperformed any single paper that
week; useful reference for a roundup-format script (source had no explicit HOOK/BODY/CTA labels
— reconstructed here for readability, wording preserved).

Script:
[HOOK] This week, Google killed manual prompting. Microsoft killed manual instructions. And Anthropic proved non-coders are beating software engineers. Three papers that change how you use AI.

[BODY] #1 — Anthropic's Claude Code study. Everyone thinks you need to code to win at AI. Anthropic just analyzed 400,000 Claude Code sessions and proved the opposite: humans made 70% of the planning decisions, and Claude made 80% of the execution. The wildest finding — management users outperformed actual software engineers at getting working code. Expertise has stopped meaning "you can code." It now means how deeply you understand the problem you're solving.

#2 — SkillOpt. Every AI needs instructions to do a task — skill files, system prompts. But writing the best instructions was pure guesswork, until Microsoft cracked it: one AI watches how another AI performs, then writes system instructions for maximum output. That single instruction pushed GPT's accuracy from 33% to 72% on a task.

#3 — Loop Engineering. Engineers from Google and Anthropic just proved manual prompting is the worst way to use AI. Instead of guiding AI prompt by prompt, you build a system that runs AI on your behalf — agents do the work, other agents review it, and only qualified output comes back to you for final approval.

All three point the same direction. AI stopped being something you operate. It's something you architect. And the people winning aren't the best coders — they're the ones who know exactly what to build.

[CTA] Comment "PAPERS" and I'll DM you all three links.
