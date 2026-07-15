---
title: "22-year-old Engineer Cracks GPU Chip Design"
url: https://www.instagram.com/p/DY2J8FIIGbI/
timestamp: 2026-05-27T14:54:57.000Z
videoDuration: 64.683
videoPlayCount: 69191
videoViewCount: 34222
Followers: 1002.0
likesCount: 4006.0
sharesCount: 1592
Saves: 2100.0
Skip Rate: 0.31
Average View Time: 29s
paperCovered: not-a-paper
paperUrl: N/A
paperSource: unknown
scriptStatus: transcript-only
verdict: WIN
---

## Caption

𝗧𝗵𝗶𝘀 𝗜𝗻𝗱𝗶𝗮𝗻 𝗼𝗿𝗶𝗴𝗶𝗻 𝗲𝗻𝗴𝗶𝗻𝗲𝗲𝗿 𝗷𝘂𝘀𝘁 𝗯𝘂𝗶𝗹𝘁 𝘄𝗵𝗮𝘁 𝗡𝘃𝗶𝗱𝗶𝗮 𝘀𝗽𝗲𝗻𝘁 𝗱𝗲𝗰𝗮𝗱𝗲𝘀 𝗵𝗶𝗱𝗶𝗻𝗴.
His name is Adam Majmudar. He built a working GPU from scratch in just 2 weeks. Alone.
Every AI model you use, ChatGPT, Gemini, Claude, runs on GPUs. Only 2 companies on Earth make them. Nvidia and AMD. Neither has ever told the world how those chips actually work. The architecture is the most protected secret in tech. Trillion dollar moats are built on it.
Adam decided to reverse engineer it anyway.
He studied CUDA, Nvidia's own software, to read the architecture from the outside in. For everything that was not documented, he asked Claude to fill the gaps. Then he wrote the entire chip in Verilog, the language engineers use to describe circuits.
The design had 4 compute cores running in parallel and 11 core instructions, all built around the matrix math that powers every AI model in existence.
He verified it through OpenLane, submitted it to Tiny Tapeout for actual physical manufacturing, and dropped the whole thing on GitHub. For free. Open source. No paywall. No NDA.
A 22 year old just democratized the most guarded design in tech.
Comment GPU and I will share the complete breakdown of how he built it.
Follow for more future tech breakdowns like this one.

## Scripts

_No script file available. See Transcript below._

## Transcript

This Indian origin engineer just built what Nvidia and AMD have spent decades locking up. He's Adam Majmudar who built a working GPU from scratch within just two weeks. So here's the story. Your chat GPT, your Gemini, your Claude, every AI model you use runs on GPUs. But there are only two companies that make them, Nvidia and AMD. And neither has ever shared how those chips actually work. From outside, the design has been impossible to crack. So Adam reverse engineered it. He first studied CUDA, Nvidia's official software, to figure out the architecture of the hardware. And for everything he couldn't figure out, he asked Claude to fill in the gaps that no one documented. Two weeks later, he wrote the entire chip in Verilog. The language engineers used to describe chip circuits. The design had four compute cores running in parallel and 11 core instructions, all built around matrix math that powers every AI model you use. And then he got the design verified through OpenLane, submitted it to TinyTapeout for actual physical manufacturing, and open sourced the whole thing on GitHub for free. Comment GPU and I'll share the complete breakdown of how he built it.

## Notes

- Hook type: named individual + underdog + secrecy stakes — "This Indian-origin engineer just built what Nvidia and AMD have spent decades locking up... a working GPU from scratch in 2 weeks. Alone." Named person (Adam Majmudar) + specific timeline (2 weeks) + David-vs-Goliath framing.
- Why it worked / didn't: MID, and one of the run's top performers by reach (34.2k views, 2100 saves, 1592 shares, skip 0.31 — the lowest so far). Avg 29s = 44.8% of a tight 64.7s video, the best proportional retention yet; it narrowly misses WIN only because skip is 0.31 (needs <0.30) and avg view is <60%. The hook is the brand's formula executed cleanly (named underdog + timeline + secret), and the body delivers a concrete build (CUDA → Claude → Verilog → OpenLane → TinyTapeout → GitHub).
- Paper → hook connection: no paper — an open-source GitHub build. The hook reframed a solo engineering project as a heist against trillion-dollar secrecy ("what Nvidia spent decades hiding"), making a technical feat feel like defiance — exactly the specificity + stakes that drove the reach.
