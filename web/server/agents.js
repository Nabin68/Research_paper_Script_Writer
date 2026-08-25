/**
 * agents.js — declarative spec of the Research Paper pipeline.
 *
 * Each agent is (prep step in Python) -> (Claude step) exactly like the terminal
 * workflow. Nothing here reimplements pipeline logic; it only shells out to the
 * same scripts and hands Claude the same briefs it reads today.
 *
 * A step is one of:
 *   { kind: 'python', label, args:[...], after?(stdout, ctx) }
 *   { kind: 'claude', label, prompt, produces:[relPaths] }
 *   { kind: 'writeFile', label, path, content }
 * Any step may carry `when(ctx)` to be skipped conditionally.
 */

import fs from 'node:fs'
import path from 'node:path'

export const ROOT = path.resolve(process.env.FP_ROOT || path.join(import.meta.dirname, '..', '..'))

export const today = () => new Date().toLocaleDateString('en-CA') // YYYY-MM-DD, local time

const abs = (rel) => path.join(ROOT, rel)
const exists = (rel) => fs.existsSync(abs(rel))

/** Mirrors slugify() in agent4_prep.py exactly. */
export function slugify(text) {
  const s = String(text || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')
  return s.slice(0, 50) || 'paper'
}

/** Shared preamble so every Claude step behaves like the terminal session does. */
const HOUSE_RULES = `You are running one agent of the Finding_Papers pipeline for the Instagram page @aiprofessor.vs.

Standing rules:
- Read MEMORY.md first — it holds the project's standing rules and corrections log; they override your defaults.
- Do exactly this one agent's job. Do not run any other agent, and do not run any other prep script.
- This is a non-interactive run: you cannot ask follow-up questions. Where something is ambiguous, make the call a careful editor would make and note it in your final summary.
- You must actually WRITE the output file(s) named below to disk. Finishing without writing them is a failure.
- When done, reply with a short plain-text summary (a few lines) of what you produced and any judgement calls or warnings. Do not paste the whole file back.`

// ---------------------------------------------------------------------------
// Agent definitions
// ---------------------------------------------------------------------------

export const AGENTS = [
  {
    id: 'agent1',
    num: 1,
    name: 'Finder',
    tagline: 'Pulls today’s new papers into the ledger',
    blurb:
      'Fetches Hugging Face, arXiv, the big-lab feeds, Reddit, Bluesky and GitHub Trending, dedupes into papers.csv and writes the daily digest. If the research filter cannot auto-decide some items, Claude classifies them and the ledger is re-applied.',
    inputs: [{ name: 'date', label: 'Date', type: 'date', help: 'Run label. Defaults to today.' }],
    build({ date }) {
      const d = date || today()
      const steps = [
        {
          kind: 'python',
          label: 'Fetch sources & write ledger',
          args: ['finding_papers.py', '--date', d],
          produces: [`digests/digest_${d}.md`],
        },
        {
          kind: 'claude',
          label: 'Classify undecided items',
          when: () => exists('agent1_verify_queue.json'),
          produces: ['agent1_verify_result.json'],
          prompt: `${HOUSE_RULES}

AGENT 1 (finder) — verification pass for ${d}.

The research filter could not auto-decide some items, so it staged them in \`agent1_verify_queue.json\`.

Do this:
1. Read \`agent1_verify_queue.json\`.
2. For each numbered item decide: is this a genuine AI/ML research paper or lab release worth keeping in the ledger? Drop newsletters, job posts, listicles, marketing pages, duplicates and non-research chatter.
3. Write \`agent1_verify_result.json\` containing exactly {"keep": [<the n values you are keeping>]} and nothing else.

Then stop — the pipeline re-applies the ledger itself.`,
        },
        {
          kind: 'python',
          label: 'Apply verification to ledger',
          when: () => exists('agent1_verify_result.json'),
          args: ['finding_papers.py', '--apply-verification'],
          produces: [`digests/digest_${d}.md`],
        },
      ]
      return { steps, view: `digests/digest_${d}.md` }
    },
  },

  {
    id: 'agent2',
    num: 2,
    name: 'Picker',
    tagline: 'Chooses the Top 5 papers worth a reel',
    blurb:
      'Pre-ranks today’s candidates with the playbook heuristic, then Claude makes the real wow-factor call against agent2/playbook.md and live web trends.',
    inputs: [{ name: 'date', label: 'Date', type: 'date', help: 'Which day’s candidates to pick from.' }],
    build({ date }) {
      const d = date || today()
      return {
        view: `picks/top5_${d}.md`,
        steps: [
          {
            kind: 'python',
            label: 'Build candidate brief',
            args: ['agent2_prep.py', '--date', d],
            produces: [`agent2/brief_${d}.md`],
          },
          {
            kind: 'claude',
            label: 'Pick the Top 5',
            produces: [`picks/top5_${d}.md`],
            prompt: `${HOUSE_RULES}

AGENT 2 (picker) — Top 5 for ${d}.

Read:
- \`agent2/brief_${d}.md\` — today's pre-ranked candidates.
- \`agent2/playbook.md\` — the virality rubric built from 54+ past reels. Sections: verdict system, top performers, flops, hook archetypes, topic categories, proven formula, scoring rubric 0-100.

The heuristic score in the brief is a PRE-FILTER, not the verdict. You make the final call. Web-search the shortlisted papers to check what is actually getting traction right now.

Write \`picks/top5_${d}.md\` in the established format:

# 🎯 Top 5 Reel Picks — ${d} · @aiprofessor.vs

then a one-line italic preamble, then for each pick:

## <n>. <headline>
**Post:** <what it is> · [<paper title>](<url>)
- **Why it'll work:** ...
- **Wow-number to lead with:** ...
- **Hook options:** ...
- **CTA:** ...

Two hard requirements, because Agent 3 parses this file:
- each pick's heading is exactly \`## <n>. \`
- the paper URL is the FIRST markdown link inside that pick's section.

Use the filename \`top5_${d}.md\` even if you end up recommending fewer than five.`,
          },
        ],
      }
    },
  },

  {
    id: 'agent3',
    num: 3,
    name: 'Deep-Dive',
    tagline: 'Researches each pick and scores the wow factor',
    blurb:
      'Builds a scaffold from the Top 5, then Claude web-researches each paper: internet buzz, the real wow factors, Wow Score /10 (internet /4 + channel fit /6) and a MAKE / MAYBE / SKIP verdict.',
    inputs: [
      { name: 'date', label: 'Date', type: 'date', help: 'Which day to deep-dive.' },
      {
        name: 'picks',
        label: 'Picks file (optional)',
        type: 'text',
        placeholder: 'picks/top5_2026-07-18.md',
        help: 'Leave blank to use that date’s Top 5. Set this to deep-dive an older picks file.',
      },
    ],
    build({ date, picks }) {
      const d = date || today()
      const picksRel = (picks || '').trim() || `picks/top5_${d}.md`
      return {
        view: `agent3/deepdive_${d}.md`,
        steps: [
          {
            kind: 'python',
            label: 'Build deep-dive scaffold',
            // always pass --picks explicitly: the script's own fallback can silently
            // pick up a stale top5 file.
            args: ['agent3_prep.py', '--date', d, '--picks', picksRel],
            produces: [`agent3/input_${d}.md`],
          },
          {
            kind: 'claude',
            label: 'Research & score each paper',
            produces: [`agent3/deepdive_${d}.md`],
            prompt: `${HOUSE_RULES}

AGENT 3 (deep-dive) — ${d}.

Read \`agent3/input_${d}.md\`. It lists the picked papers with their live ledger metrics and a per-paper research TODO.

For EACH paper:
1. Web-search it. Find real coverage and buzz — who is posting about it, how much reach, is it actually spreading or is it quiet.
2. Confirm the wow factor(s) — the specific, checkable, surprising thing a viewer would react to. Kill any number you cannot verify, and say so.
3. Score it: Internet virality /4 + Channel fit /6 = Wow Score /10. Show both components, not just the total.
4. Give a verdict: MAKE / MAYBE / SKIP, with one line of reasoning.

Write the result to \`agent3/deepdive_${d}.md\`, keeping the same paper order as the input, and end with a one-line recommendation of which paper to script first.`,
          },
        ],
      }
    },
  },

  {
    id: 'agent4',
    num: 4,
    name: 'Writer',
    tagline: 'Writes the reel script for one paper',
    blurb:
      'Bundles the paper facts plus the hook bible, winning scripts, type templates and virality elements into one brief, then Claude writes the full script in the universal TYPE-4 format.',
    inputs: [
      {
        name: 'paper',
        label: 'Paper',
        type: 'text',
        required: true,
        placeholder: 'Paper title keywords, or its URL',
        help: 'Matched against papers.csv. If it is not in the ledger, Claude web-searches it directly.',
      },
      {
        name: 'notes',
        label: 'Extra instructions for this script',
        type: 'textarea',
        rows: 4,
        placeholder: 'e.g. lead with the cost number, keep it under 45 seconds, no analogies',
        help: 'Optional. These take highest priority over the page defaults.',
      },
      { name: 'date', label: 'Date', type: 'date' },
    ],
    build({ paper, notes, date }) {
      const d = date || today()
      const args = ['agent4_prep.py', '--paper', paper, '--date', d]
      if (notes && notes.trim()) args.push('--notes', notes.trim())
      return {
        // real path is resolved from prep stdout in `after`
        view: null,
        steps: [
          {
            kind: 'python',
            label: 'Build writing brief',
            args,
            after(stdout, ctx) {
              // agent4_prep prints: "  -> next: ask Claude to write the script to scripts/<date>-<slug>.md"
              const m = stdout.match(/write the script to\s+(\S+\.md)/i)
              ctx.scriptPath = m ? m[1].replace(/\\/g, '/') : `scripts/${d}-${slugify(paper)}.md`
              ctx.slug = path.basename(ctx.scriptPath, '.md').replace(/^\d{4}-\d{2}-\d{2}-/, '')
              const t = stdout.match(/paper matched\s*:\s*(.+)/i)
              ctx.matchedTitle = t ? t[1].trim() : paper
              ctx.view = ctx.scriptPath
              ctx.produced = [`agent4/brief_${ctx.slug}.md`]
            },
          },
          {
            kind: 'claude',
            label: 'Write the script',
            produces: (ctx) => [ctx.scriptPath],
            prompt: (ctx) => `${HOUSE_RULES}

AGENT 4 (writer) — script for: ${ctx.matchedTitle}

Read \`agent4/brief_${ctx.slug}.md\`. It is self-contained: the paper facts, then the hook bible, two winning scripts, the script-type template, the virality elements and the picker playbook, all inline. Read the whole brief before writing — the reference docs in it are the format spec.

Do this:
1. Web-search the paper to confirm the facts and pull the strongest verifiable wow-numbers. Do not ship a number you could not verify; if one is shaky, drop it or flag it.
2. Write the hooks per the hook bible — mostly proven patterns, one or two experimental. Use as many as genuinely earn their place; there is no fixed count.
3. Write a connected, easy-English body in TYPE 4 from the script-type template: problem → solution → wow-metric → how → opinion. It must read as one story, not labelled chunks, and the metric lands before the mechanism. Thread one exact keyword through it, use causal step links rather than hype labels, and active payoff verbs. Bodies run around 250 words.
4. Add the CTA, caption and hashtags.

Formatting is locked (see MEMORY.md and the template): bold is selective — labels, inline company names and numbers, and the CTA keyword only, never whole sentences. Blank line after every label, and one sentence per line in the body so the pacing carries the pauses. No timestamps.

Write it to \`${ctx.scriptPath}\`.`,
          },
        ],
      }
    },
  },

  {
    id: 'agent5',
    num: 5,
    name: 'Refiner',
    tagline: 'Polishes a draft without rewriting it',
    blurb:
      'Paste a draft and say what to fix. Claude refines surgically against agent5/refine_playbook.md, keeping your voice, and saves a new version. It also logs the pass back into the playbook so the taste file keeps growing.',
    inputs: [
      {
        name: 'script',
        label: 'Current script',
        type: 'textarea',
        required: true,
        rows: 16,
        placeholder: 'Paste the draft script here…',
        help: 'Saved to agent5/input.md, exactly as if you had pasted it there yourself.',
      },
      {
        name: 'notes',
        label: 'What to refine',
        type: 'textarea',
        rows: 6,
        placeholder: 'e.g. hook feels flat, tighten the middle, keep my ending exactly as it is',
        help: 'Optional but strongly recommended — this is the highest-priority instruction for the pass.',
      },
      {
        name: 'paper',
        label: 'Paper (optional)',
        type: 'text',
        placeholder: 'Title or URL, to fact-check against papers.csv',
      },
      { name: 'date', label: 'Date', type: 'date' },
    ],
    build({ script, notes, paper, date }) {
      const d = date || today()
      const args = ['agent5_prep.py', '--date', d]
      if (notes && notes.trim()) args.push('--notes', notes.trim())
      if (paper && paper.trim()) args.push('--paper', paper.trim())
      return {
        view: null,
        steps: [
          {
            kind: 'writeFile',
            label: 'Save draft to agent5/input.md',
            path: 'agent5/input.md',
            content: script,
          },
          {
            kind: 'python',
            label: 'Build refine brief',
            args,
            after(stdout, ctx) {
              // agent5_prep prints: "  -> next: ask Claude to refine into agent5\refined\<date>-v<N>-<slug>.md"
              const m = stdout.match(/refine into\s+(\S+\.md)/i)
              ctx.refinedPath = m ? m[1].replace(/\\/g, '/') : null
              const b = stdout.match(/brief written\s*:\s*(\S+\.md)/i)
              ctx.briefPath = b ? b[1].replace(/\\/g, '/') : null
              const v = stdout.match(/version\s*:\s*v(\d+)/i)
              ctx.version = v ? v[1] : '1'
              ctx.view = ctx.refinedPath
            },
          },
          {
            kind: 'claude',
            label: 'Refine the script',
            produces: (ctx) => [ctx.refinedPath, 'agent5/refine_playbook.md'].filter(Boolean),
            prompt: (ctx) => `${HOUSE_RULES}

AGENT 5 (refiner) — refine pass v${ctx.version}.

Read the brief at \`${ctx.briefPath || 'agent5/brief_refine_*.md'}\`. It contains the draft, the refiner playbook, the script references and the picker playbook.

REFINE — do not rewrite. That is the whole job:
1. Read the draft and the REFINER PLAYBOOK, especially §4 USER PREFERENCES. Match this draft's subject and context against the conditional rules there before you touch anything.
2. Honour the refine instructions in the brief above everything else — including what the user asked you to leave alone.
3. Fix only what is actually weak. When an excerpt is flagged, isolate the specific weak words and touch only those, even inside the flagged span — do not restage the sentence around them.
4. If a paper is attached or referenced, web-check the facts and numbers.
5. Conform the output to the universal script format even if the incoming draft was not in it.

Write the polished script to \`${ctx.refinedPath}\` and end it with:

---
✍️ WHAT I CHANGED & WHY  (v${ctx.version})
- [change] → [the lever it improves]
- Kept as-is: [what you deliberately left alone, and why]
- ⚠️ Flag (if any): [anything the user should decide]

Then log this pass into \`agent5/refine_playbook.md\` §4B (the raw log, with the context/subject). If the user stated a preference in the refine instructions, capture it in §4A as a CONDITIONAL rule — "IF <context> THEN <direction>" — never as a flat global rule.`,
          },
        ],
      }
    },
  },
]

AGENTS.push({
  id: 'agent6',
  num: 6,
  name: 'Captions',
  tagline: 'Turns a script into the Instagram caption',
  blurb:
    'Paste a finished reel script and get the caption in the page’s proven shape — hook, problem, mechanism, hard numbers, CTA, P.S. and the bracket tag block. Refine mode polishes a caption you already have instead of writing a new one.',
  inputs: [
    {
      name: 'mode',
      label: 'What do you want to do?',
      type: 'segmented',
      default: 'generate',
      options: [
        { value: 'generate', label: 'Generate' },
        { value: 'refine', label: 'Refine' },
      ],
    },
    {
      name: 'script',
      label: 'Reel script',
      type: 'textarea',
      required: true,
      rows: 14,
      placeholder: 'Paste the finished script here…',
      help: 'The caption’s only source of facts — numbers are pulled from here, never invented.',
    },
    {
      name: 'caption',
      label: 'Current caption',
      type: 'textarea',
      rows: 12,
      required: true,
      showIf: { field: 'mode', equals: 'refine' },
      placeholder: 'Paste the caption you want refined…',
      help: 'Refined surgically — only what you flag below gets touched.',
    },
    {
      name: 'notes',
      type: 'textarea',
      rows: 5,
      // the same field reads differently depending on the mode above
      variantOn: 'mode',
      variants: {
        generate: {
          label: 'Extra instructions',
          placeholder: 'Optional — e.g. lead with the cost number, use the two-lab contrast shape',
          help: 'Optional. Takes priority over the page defaults.',
        },
        refine: {
          label: 'What to refine',
          placeholder: 'e.g. hook is flat, tighten the middle, keep the ending exactly as it is',
          help: 'Highest-priority instruction for this pass — including what to leave alone.',
        },
      },
    },
    { name: 'date', label: 'Date', type: 'date' },
  ],
  build({ mode, script, caption, notes, date }) {
    const d = date || today()
    const refining = mode === 'refine'
    const args = ['agent6_prep.py', '--mode', refining ? 'refine' : 'generate', '--date', d]
    if (notes && notes.trim()) args.push('--notes', notes.trim())

    const steps = [
      {
        kind: 'writeFile',
        label: 'Save script to agent6/input_script.md',
        path: 'agent6/input_script.md',
        content: script,
      },
    ]

    if (refining) {
      steps.push({
        kind: 'writeFile',
        label: 'Save caption to agent6/input_caption.md',
        path: 'agent6/input_caption.md',
        content: caption,
      })
    }

    steps.push({
      kind: 'python',
      label: refining ? 'Build refine brief' : 'Build caption brief',
      args,
      after(stdout, ctx) {
        // agent6_prep prints: "  -> next: ask Claude to write the caption to captions\<file>.md"
        const m = stdout.match(/write the caption to\s+(\S+\.md)/i)
        ctx.captionPath = m ? m[1].replace(/\\/g, '/') : null
        const b = stdout.match(/brief written\s*:\s*(\S+\.md)/i)
        ctx.briefPath = b ? b[1].replace(/\\/g, '/') : null
        const v = stdout.match(/version\s*:\s*v(\d+)/i)
        ctx.version = v ? v[1] : '1'
        ctx.view = ctx.captionPath
      },
    })

    steps.push({
      kind: 'claude',
      label: refining ? 'Refine the caption' : 'Write the caption',
      produces: (ctx) => [ctx.captionPath, 'agent6/caption_playbook.md'].filter(Boolean),
      prompt: (ctx) => `${HOUSE_RULES}

AGENT 6 (captions) — ${refining ? 'refine' : 'write'} pass v${ctx.version}.

Read the brief at \`${ctx.briefPath || 'agent6/brief_caption_*.md'}\`. It contains ${
        refining ? 'the current caption, ' : ''
      }the reel script, and the CAPTION PLAYBOOK.

${
  refining
    ? `REFINE — do not rewrite. That is the whole job:
1. Read the current caption and the CAPTION PLAYBOOK, especially §5 LEARNINGS & USER PREFERENCES. Match this caption's subject and context against the conditional rules there before you touch anything.
2. Honour the refine instructions in the brief above everything else — including what the user asked you to leave alone.
3. Fix only what is actually weak. Isolate the specific weak words and touch only those, even inside a flagged span — do not restage the sentence around them.
4. Check every number against the script. Never introduce or sharpen a figure the script does not support.
5. Keep the structural tail intact: the CTA line, the P.S. block, the four spacer dots and the bracket tag block.`
    : `WRITE the caption:
1. Read the script and the CAPTION PLAYBOOK — §1 shape, §2 voice, §3 hard rules, §4 reference captions, §5 learned preferences.
2. Pick the matching shape: reference A when it is one paper explained as a chain of steps, reference B when two labs attack one problem from different ends.
3. Pull the wow-numbers from the script and give each one its baseline — a number with nothing to compare against is dead weight. Never invent or sharpen a figure the script does not contain.
4. Follow the shape in order: hook line, the problem, the turn, the mechanism with a human analogy, the result with hard numbers, the honest caveat if the paper is early, the payoff line that echoes the hook, the CTA with a single uppercase keyword, the P.S. block, four spacer dots, then the bracket tag block of about 15 Title Case tags ordered specific to broad.
5. No emojis, no # symbols, no markdown formatting inside the caption itself — it must be paste-ready plain text.`
}

Write it to \`${ctx.captionPath}\`. Put the caption first and completely unadorned so it can be copied straight into Instagram, then a \`---\` separator, then a short **WHAT I ${
        refining ? 'CHANGED' : 'WROTE'
      } & WHY (v${ctx.version})** section.

Then log this pass into \`agent6/caption_playbook.md\` §5B (the raw log, with the subject). If the user stated a preference, capture it in §5A as a CONDITIONAL rule — "IF <context> THEN <direction>" — never as a flat global rule.`,
    })

    return { steps, view: null }
  },
})

export const byId = (id) => AGENTS.find((a) => a.id === id)

/** Shape sent to the browser (functions stripped). */
export const catalog = () =>
  AGENTS.map(({ id, num, name, tagline, blurb, inputs }) => ({ id, num, name, tagline, blurb, inputs }))
