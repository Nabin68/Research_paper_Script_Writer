---
title: "AI Agent Crashes GPU Kernel Writing"
url: https://www.instagram.com/p/DZP3kY1IM31/
timestamp: 2026-06-06T14:37:04.000Z
videoDuration: 105.579
videoPlayCount: 8215
videoViewCount: 3570
Followers: 120.0
likesCount: 426.0
sharesCount: 198
Saves: 277.0
Skip Rate: 0.49
Average View Time: 24s
paperCovered: "CUDA Agent — AI trained to write fast GPU kernels (ByteDance)"
paperUrl: https://arxiv.org/pdf/2602.24286
paperSource: script
scriptStatus: full
verdict: FLOP
---

## Caption

Every AI model on earth runs on GPUs.
And the real speed comes down to tiny programs called kernels that do the heavy lifting underneath.
Faster kernels mean faster, cheaper AI.
The catch is that writing a fast kernel needs deep knowledge of how a GPU works inside. Few people can do it, so it is slow and expensive. Even the strongest AI models could not beat a free tool called torch compile at it.
A new paper from ByteDance changed that with a system called CUDA Agent. An AI trained to become a genuine expert at writing GPU code.
The trick is that it works like an engineer, not a chatbot. It writes code, runs it on a real GPU, sees the result, fixes its mistakes, and repeats.
On the hardest tasks, it beat Claude Opus 4.5 and Gemini 3 Pro by around 40 percent.
One of the first real steps toward making AI cheaper for everyone.
Comment CUDA and I will share the paper. Day 2 of 100.
.
.
.
.
[AI, GPU, CUDA, Machine Learning, Deep Learning, AI Research, ByteDance, Reinforcement Learning, Artificial Intelligence, Tech, AI Agents, Research Paper, Tech Breakdown]

## Scripts

**[HOOK 01]**
ByteDance just released a paper that should make every NVIDIA investor sweat.
_(Vaibhav showing the paper and delivering the dialogue)_

**[HOOK 02]**
This research paper trained an AI agent that writes GPU code.
And it crushes Claude and Gemini by 40 percent.
_(Vaibhav showing paper, Dario hiding in area having table in the end, he stands up and takes the paper and sits down again hiding in the table space)_

**[HOOK 03]**
This research paper trained AI to code for GPU programs, and it beats the human experts now.
_(Vaibhav showing the paper and delivering the dialogue)_

**[BODY]**
Welcome to Day 2 of the 100 days of research papers series.

Every AI model on earth runs on GPUs.
And the real speed of any AI comes down to tiny GPU programs called kernels, that quietly do the real work underneath.
Faster running kernels means faster & cheaper AI.

But writing a fast kernel requires deep, specialized knowledge of how the GPU hardware works internally.

And there are few experts who can do it well.
That makes it expensive. And painfully slow.

Before this paper,
Experts tried using AI to write these kernels. But even the strongest AI models couldn't beat a basic, free tool called torch compile.

Then this paper changed everything.
It introduces a system called CUDA Agent.
An AI trained to become a genuine expert at writing fast GPU kernels

And it works remarkably well, beating both the torch compile and the best commercial AI models by large margins. (Highlight Claude & Gemini from paper here.)

And the way they trained it is the genius part.
First,
They used AI to turn simple GPU operations into 6000 hard practice problems.
Then filtered out anything broken or too easy for the final test.
So it learned real skill, not just memorized patterns.

Second, they gave it a real workspace.
Instead of writing code blindly in one shot, they trained AI to work like a real engineer, who writes code, runs it on actual GPUs, sees the results, fixes mistakes, and repeats.

Third, stable training.
First they added a gentle "warm-up" to make the model build foundations, then used intense reinforcement learning on top.

And the results are insane.
On a 250 task benchmark, it beat the standard optimizer on nearly every single problem.
And on the hardest tasks, It crushed Claude Opus 4.5 and Gemini 3 Pro by around 40 percent.

Honestly, this paper gave a new definition to GPU training.
And this is the first real step towards making AI cheaper for everyone.

**[CTA]**
Comment "CUDA" and I'll share the paper with you.

## Transcript

This research paper trained an AI agent that writes GPU code, and it crushes Claude and Gemini by 40%. Welcome to day two of the 100 days of research papers. Every AI model on earth runs on GPUs, and the real speed of any AI comes down to tiny GPU programs called kernels that quietly do the real work underneath. Faster running kernels means faster and cheaper AI. But writing a fast kernel requires specialized knowledge of how the GPU hardware works internally that makes it expensive and painfully slow. And till now, AI was not even close to write these kernels programmed by itself. But this paper changes everything. It introduces a system called CUDA Agent, an AI trained at writing fast GPU kernels, and it works remarkably well, beating the best commercial AI models by large margins. And the way they trained it is the genius part. First, they used AI to turn simple GPU operations into 6,000 hard practice problems, so it learns real skill, not just memorized patterns. Second, they gave it a real workspace. Instead of writing code blindly in one shot, they trained AI to work like a real engineer who writes code, runs it on actual GPUs, sees the results, fixes mistakes, and repeats. Third, stable training. First, they added a gentle warm-up to make the model build foundations, then used intense reinforcement learning on top of it. And the results are insane. On a 250-task benchmark, it beat the standard optimizer on nearly every single problem. And on the hardest task, it crushed clawed opus 4.5 and Gemini 3 Pro by around 40%. Honestly, this paper gave a new definition to GPU training, and this is the first real step towards making AI cheaper for everyone. Comment CUDA, and I'll share the paper with you. Follow for more content like this. And if you want to stay ahead with AI, join our free WhatsApp community. Link in bio.

## Notes

- Hook type: competitive-benchmark flex — the reel shipped HOOK 02 ("This research paper trained an AI agent that writes GPU code, and it crushes Claude and Gemini by 40%"). Concrete rivals (Claude, Gemini) + a hard number (40%). Strong specificity, though it opens on jargon ("writes GPU code") that may not grab a general viewer.
- Why it worked / didn't: FLOP. Skip 49% (near the 0.50 line), avg 24s = 23% of a 106s video — the longest reel in the run, which structurally hurts proportional retention. The 40%-beats-Claude hook is punchy for the technical crowd, but "GPU kernels" is a niche subject and the three-part training explanation is dense; saves (277) are strong from the audience that stayed.
- Paper → hook connection: the paper's wow factor is an AI out-coding Claude Opus 4.5 and Gemini 3 Pro at GPU kernels by ~40%. The hook cashed exactly that competitive number — the strongest possible frame for the paper — but the subject's inherent nicheness and the 106s length capped watch time. HOOK 01 ("make every NVIDIA investor sweat") might have widened the appeal.
