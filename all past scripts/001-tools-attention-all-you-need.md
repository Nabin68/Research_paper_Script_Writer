---
title: "Cheaper AI: Efficiency Over Size"
url: https://www.instagram.com/p/DXt37RgCKzS/
timestamp: 2026-04-29T13:12:00.000Z
videoDuration: 113.088
videoPlayCount: 19089
videoViewCount: 11043
Followers: 156.0
likesCount: 603.0
sharesCount: 257
Saves: 384.0
Skip Rate: 0.34
Average View Time: 38s
paperCovered: "Tools, Attention is All You Need"
paperUrl: unknown
paperSource: transcript-inferred
scriptStatus: transcript-only
verdict: MID
---

## Caption

Everyone’s chasing bigger AI models.

More tokens. More context.

But this paper just proved — we were solving the wrong problem.

AI agents were re-reading every tool… every single time.

Burning tokens = burning money.

Researchers fixed it.

Result? 17x cheaper AI.

95% fewer tokens.

86% lower cost.

94% success rate.

While OpenAI, Google, and Anthropic scale memory…

This shows efficiency > size.

Bigger ≠ better anymore.

What do you think?
.
.
.
.
[AI, AI Agents, OpenAI, Google, Anthropic, Machine Learning, Startups, Tech]

## Scripts

_No script file available. See Transcript below._

## Transcript

Google, Anthropic, and OpenAI are panicking right now. Some researchers just found a way to make AI agents 17 times cheaper. Here's what they found out. AI agents connect with your tools like Slack, Gmail, GitHub, your databases, and when you message the agent for fetching any data from these connected tools, it re-reads the full instruction manual of every single tool connected to it. Every single time. Even if you just typed, hi, think of it like a library. You walk in asking for one specific book on how LLMs work. But instead of going straight to that book, the librarian scans every shelf, every title, top to bottom, just to hand you that one book. Time and effort wasted. In an LLM, that waste means burning the tokens. Researchers are calling this the tool stacks. They propose a solution in a research paper titled, Tools, Attention is All You Need, a direct callback to the 2017 paper, Attention is All You Need, the paper that built modern AI. This paper talks about LLMs should focus only on the relevant tools. So the solution works in three layers. One, intent matching. The system reads your message first and picks only the tools that match what you're asking for. Two, state-aware gates. It removes the tools you don't have access to, like GitHub, when you're not logged in. Three, lazy loading. The full instructions of a tool only open the moment the AI is actually about to use it. And the effectiveness of this framework is insane. Tokens per message dropped 95%. Cost per task dropped 86%. Task success rate jumped from 72 to 94%. Everyone is racing to build bigger context windows. One million tokens, two million tokens. But this paper just proved we've been solving the wrong problem. The bottleneck was never how big the memory is. It was how effective the memory is. Follow for more insights like this.

## Notes

- Hook type: named entities (three frontier labs) + emotional stakes ("panicking") + specific number ("17 times cheaper") — a contrarian efficiency claim framed as a threat to the incumbents.
- Why it worked / didn't: MID. Skip rate 34%, 38s avg view. On a long 113s video, proportional retention is soft (~34%), but the absolute watch time (38s) is respectable — viewers gave it real time before dropping. The hook landed a concrete 17× number in the first 6 words, but the payoff (tool-stacks, intent matching, lazy loading) is an infrastructure mechanism that takes ~20s of setup before the "so what" (95% fewer tokens) arrives. Strong saves (384) suggest the value registered for those who finished.
- Paper → hook connection: the paper's novelty is a selective-tool-loading efficiency gain — inherently unsexy. The hook translated "fewer tokens per call" into "17× cheaper AI" and "big labs panicking," converting a plumbing optimization into a cost-war story with named villains.
