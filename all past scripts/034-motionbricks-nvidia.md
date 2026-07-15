---
title: "AI Revolutionizes Game Animation"
url: https://www.instagram.com/p/DZrbUmEo4tB/
timestamp: 2026-06-17T07:27:37.000Z
videoDuration: 99.413
videoPlayCount: 2463
videoViewCount: 855
Followers: 12.0
likesCount: 108.0
sharesCount: 15
Saves: 59.0
Skip Rate: 0.56
Average View Time: 15s
paperCovered: "MotionBricks (NVIDIA) — generative motion model for game characters and humanoid robots"
paperUrl: https://research.nvidia.com/labs/gear/motionbricks/pdfs/motionbricks_siggraph_2026.pdf
paperSource: script
scriptStatus: full
verdict: FLOP
---

## Caption

NVIDIA just built the first AI that animates game characters on its own.
For decades, every move in a video game, every walk, jump, punch was hand-animated.
Pre-recorded clips stitched into giant animation graphs.
That's why GTA 6 took over a decade to ship.
NVIDIA's new paper "MotionBricks" rewrites the rules.

Three things stood out.
First, motion tokens.
They broke 350,000 clips into reusable building blocks and trained a model to generate new movement on demand.

Second, twin models.
One handles the character, the other its movement.
A single command, infinite styles.

Third, in-betweening.
Drop a start and end keyframe, and it fills the motion between them in 2 milliseconds with 99.6% accuracy.

The twist? They plugged the same model into a real humanoid robot.
It just worked.

Game development as we know it is about to collapse from years into hours.

Comment "MOTION" and I'll send the paper your way.
.
.
.
.
#researchpaper #research
[NVIDIA, MotionBricks, AI Animation, Game Development, Research Paper, Machine Learning, Motion Tokens, Generative AI, Humanoid Robotics, AI News, Tech Innovation, GTA 6, Animation Graphs, AI Research, 100DaysOfResearch]

## Scripts

_Parsing note: source script was table-embedded ([HOOK]/[INTRO]/[BODY]/[CTA] run together in one cell); blocks extracted below, verify against original._

**[HOOK]**
A new paper from NVIDIA introduces the first generative motion model that works on both game characters and real humanoid robots.

**[INTRO]**
Welcome to Day 05 of 100 days of research paper series.
Today is "MotionBricks" by NVIDIA and this one talks about the first AI model that builds game animations on its own.

**[BODY]**
So here's the story.
Every game character you ever played, was all hand animated.
Their walk, the jump, the punch, everything was animated using something called animation graphs — basically a giant collection of pre-recorded clips stitched together. But the biggest problem with this method is SCALING.
Every new movement means more clips and more transitions making even a small update takes months.
That's why modern games like GTA 6 took over a decade to build. Researchers previously tried fixing it with AI, but every model they built failed brutally.
Older ones could only handle a few movements. But recently NVIDIA launched a paper called "MotionBricks" that solves this exact problem and here are the 3 things they highlighted in the paper. **First — Motion Tokens.**
So they broke 350,000 motion clips into reusable "motion tokens" and trained the model on them, making it capable of generating new motions by itself. **Second — Twin Models.**
They used two different models, one for character animation and the other for its movement. So, a single command can generate different styles. **Third — In-Betweening.**
This is the crazy one.
So you just drop the start and end keyframe, and it fills the motion between them in 2 milliseconds with 99.6% accuracy. Also NVIDIA experimented by plugging the same model into a real humanoid robot — and surprisingly it just worked.

Insane Right!! Honestly, the way NVIDIA is dropping research papers like this openly, one after another, the entire AI industry is about to change.

**[CTA]**
Comment "MOTION" and I'll share the paper with you.

## Transcript

Welcome to day 5 of 100 days of research paper series. Today is Motion Bricks by NVIDIA and this one talks about the first AI model that builds game animations on its own. So here's the story. Every game character you ever played was all hand animated. The walk, the jump, the punch, everything was animated using something called animation graphs. Basically a giant collection of pre-recorded clips stitched together. But the biggest problem with this method is scaling. Every new movement means more clips and more transitions making even a small update takes months. That's why modern games like GTA 6 took over a decade to build. Researchers previously tried fixing it with AI but every model they built failed brutally. But recently NVIDIA launched a paper called Motion Bricks that solves this exact problem. And here are the three things they highlighted in the paper. First, motion tokens. So they broke 350,000 motion clips into reusable motion tokens and trained the model on them, making it capable of generating new motions by itself. Second, twin models. They used two different models, one for character animation and the other for its movement. So a single command can generate different styles. Third, in-betweening. And this is the crazy one. So you just drop the start and end keyframes and it fills the motion between them in two milliseconds with 99.6% accuracy. Also, NVIDIA experimented by plugging the same model into a real humanoid robot and surprisingly it just worked. Insane, right? Honestly, the way NVIDIA is dropping research papers like this openly one after another, comment motion and I'll share the paper with you. Follow for more content like this. And if you want to stay ahead with AI, join our free WhatsApp community. Link in bio.

## Notes

- Hook type: intro-led, low-tension — the reel opened with "Welcome to day 5 of 100 days of research paper series" before the concept, rather than leading with the script's HOOK ("first generative motion model for game characters AND humanoid robots"). Named entity present, but the series-intro opener buries the stakes.
- Why it worked / didn't: FLOP (worst-reach reel in the run: 855 views). Skip 56% (>0.50) and avg 15s = 15% of a 99s video. The "Welcome to day 5..." cold open is exactly the kind of generic intro the brand warns against — it hands the viewer a filing label, not a hook, so they scroll before the GTA-6 / 350k-clips payoff.
- Paper → hook connection: the paper's wow factor is 2ms in-betweening at 99.6% accuracy AND the same model driving a real robot. The scripted HOOK named the robot twist up front; the reel dropped it for a series intro, so the strongest angle (game-animation model that also runs a humanoid) never anchored the open. [Merged from `-2` duplicate; see dedup-conflict in log.]
