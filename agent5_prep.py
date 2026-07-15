#!/usr/bin/env python3
"""
agent5_prep.py — Agent 5 (script REFINER) data prep.

Standalone "plug." You already have a script — written by you, by Agent 4, or pulled from
somewhere else — that's *mostly there* but needs polishing. This agent does NOT write from
scratch. It reads your draft, measures it against the page's proven levers + your accumulated
preferences, and hands Claude everything needed to refine it while keeping YOUR voice/intent.

What this prep step assembles into `agent5/brief_refine_<slug>.md`:
  * your draft script (from --file, or the drop-file agent5/input.md)
  * the page's writing references (hook.md, the 2 winning-script files, script-type template,
    virality elements, and the agent2 playbook)
  * the REFINER PLAYBOOK (agent5/refine_playbook.md) — the refine checklist PLUS the growing
    "USER PREFERENCES & LEARNINGS" section that makes Agent 5 better every time (the "training")
  * optional paper facts from papers.csv (--paper) so the refiner can fact-check numbers
  * your extra instructions for THIS refine pass

Typical use: paste your draft to Claude in chat and say how to refine it; Claude drops it into
agent5/input.md, runs this prep, then refines. The polished version is written to a VERSIONED file:

    agent5/refined/<date>-v<N>-<slug>.md

The same script keeps a clean v1 → v2 → v3 history as you re-refine it (this prep auto-computes
the next version). Each refined file ends with a short "WHAT I CHANGED & WHY" section.

LEARNING LOOP (context-aware): every refine is logged to agent5/refine_playbook.md §4 WITH its
subject/context, and stated preferences become CONDITIONAL rules ("IF <this kind of script/situation>
THEN <this direction>") — never flat global rules. This is deliberate: the same lever can go
opposite ways by context (e.g. "longer hook" on one script, "shorter hook" on another), so the
refiner stores WHEN each direction applies and gets more precise over time.

Each agent runs independently (run ONE at a time, only when you ask):
    python finding_papers.py                              # 1 finder
    python agent2_prep.py                                 # 2 picker
    python agent3_prep.py                                 # 3 deep-dive
    python agent4_prep.py --paper "SensorFM" --notes ".." # 4 script writer (from scratch)
    python agent5_prep.py --file draft.md --notes ".."    # 5 refiner (polish an existing script)

Usage:
    python agent5_prep.py                        # refine agent5/input.md (paste your draft there)
    python agent5_prep.py --file path/to/draft.md
    python agent5_prep.py --file draft.md --paper "Bonsai 27B" --notes "tighten the hook, keep my ending"
"""

import os
import re
import glob
import argparse
from datetime import datetime

# Reuse Agent 4's helpers/reference list so the two writers stay in lockstep.
try:
    from agent4_prep import slugify, read_file, find_paper, REFERENCES, REF_DIR, PLAYBOOK
except Exception:  # pragma: no cover - fallback if import path differs
    slugify = None

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "agent5")
REFINED_DIR = os.path.join(OUT_DIR, "refined")  # versioned refined scripts land here
INPUT_DROPFILE = os.path.join(OUT_DIR, "input.md")
REFINE_PLAYBOOK = os.path.join(OUT_DIR, "refine_playbook.md")


def next_version(slug):
    """Next v<N> for this slug in agent5/refined/ (v1 if none exist yet).
    Filenames look like <date>-v<N>-<slug>.md, so the same script keeps a clean
    v1 → v2 → v3 history as it's re-refined."""
    os.makedirs(REFINED_DIR, exist_ok=True)
    max_v = 0
    pat = re.compile(r"-v(\d+)-" + re.escape(slug) + r"\.md$")
    for p in glob.glob(os.path.join(REFINED_DIR, f"*-v*-{slug}.md")):
        m = pat.search(os.path.basename(p))
        if m:
            max_v = max(max_v, int(m.group(1)))
    return max_v + 1


def _fallback_slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return (s[:50] or "script")


def _fallback_read(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def title_from_draft(text, fallback):
    """Best-effort human title for the draft: a 'TITLE:' line (even behind an
    emoji), or the first real markdown heading. Ignores hashtag/caption lines
    like '#AI #ML' (a real heading needs a space after the #'s). If neither is
    present (e.g. a bare pasted draft with no title), fall back to the first
    HOOK line's text so the slug/version-tracking is still meaningful instead
    of collapsing to the generic input filename."""
    hook_fallback = None
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        # strip a leading emoji/symbol run so '📌 SCRIPT TITLE:' still matches
        stripped = re.sub(r"^[^\w#]+", "", line).strip()
        m = re.match(r"(?i)^(?:script\s+)?title\s*[:\-]\s*(.+)$", stripped)
        if m:
            return m.group(1).strip()
        m = re.match(r"^#{1,6}\s+(.+)$", line)  # space required → excludes '#AI' tags
        if m:
            return m.group(1).strip()
        if hook_fallback is None:
            m = re.match(r"(?i)^\**\[\s*hook\s*\d*[^\]]*\]\**\s*(.*)$", line)
            if m and m.group(1).strip(' "\'*'):
                hook_fallback = m.group(1).strip(' "\'*')
            elif re.match(r"(?i)^\**\[\s*hook\s*\d*[^\]]*\]\**$", line):
                hook_fallback = "__NEXT_LINE__"  # hook text is on the following line
                continue
        elif hook_fallback == "__NEXT_LINE__":
            hook_fallback = line.strip(' "\'*')
    if hook_fallback and hook_fallback != "__NEXT_LINE__":
        return hook_fallback
    return fallback


def main():
    _slug = slugify or _fallback_slugify
    _read = read_file or _fallback_read

    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="path to your draft script (default: agent5/input.md)")
    ap.add_argument("--paper", default="", help="optional: paper title/URL to pull facts from papers.csv")
    ap.add_argument("--notes", default="", help="what to refine / what to keep in THIS pass")
    ap.add_argument("--date", default=None)
    args = ap.parse_args()
    today = args.date or datetime.now().strftime("%Y-%m-%d")

    os.makedirs(OUT_DIR, exist_ok=True)

    draft_path = args.file or INPUT_DROPFILE
    draft = _read(draft_path)
    if not draft or not draft.strip():
        raise SystemExit(
            "No draft script found.\n"
            f"  Either: paste your script into  {INPUT_DROPFILE}\n"
            f"  or run: python agent5_prep.py --file path\\to\\your_draft.md"
        )

    title = title_from_draft(draft, os.path.splitext(os.path.basename(draft_path))[0])
    slug = _slug(title)
    ver = next_version(slug)
    out_rel = os.path.join("agent5", "refined", f"{today}-v{ver}-{slug}.md")

    # optional paper facts for fact-checking numbers in the draft
    row = None
    if args.paper and find_paper:
        row = find_paper(args.paper)

    out = [f"# Agent 5 — script REFINING brief · {today}", ""]
    out.append(f"**Draft to refine:** {title}")
    out.append(f"- Source file: `{os.path.relpath(draft_path, HERE)}`")
    if row:
        out.append(f"- Matched paper: {row.get('title')}")
        out.append(f"  - URL: {row.get('url')}")
        out.append(f"  - Lab: {row.get('lab')} · HF upvotes: {row.get('hf_upvotes')} · "
                   f"Trending: {row.get('trending_score')}")
        out.append(f"  - Abstract/summary: {row.get('summary')}")
    elif args.paper:
        out.append(f"- Paper '{args.paper}' not found in papers.csv — Claude should web-check facts directly.")
    out.append("")

    if args.notes:
        out.append(f"## ⚙️ Refine instructions for THIS pass (highest priority)\n\n{args.notes}\n")
    else:
        out.append("## ⚙️ Refine instructions\n\n(none given — use the refine playbook + page defaults; "
                   "preserve the user's voice and intent, polish don't rewrite)\n")

    out.append("## 📋 What Claude does next (REFINE, don't rewrite)")
    out.append("1. Read the draft below + the REFINER PLAYBOOK — especially §4 USER PREFERENCES, and "
               "match this draft's SUBJECT/CONTEXT against the conditional rules there before refining.")
    out.append("2. If a paper is attached / referenced, web-check the facts & numbers are true.")
    out.append("3. Refine against the page's proven levers **while keeping the user's voice and core "
               "idea** — improve, don't replace. Use your own knowledge for stronger phrasing/analogies.")
    out.append(f"4. Write the polished script to **`{out_rel}`** (versioned — this is **v{ver}** for "
               "this script), ending with a short **WHAT I CHANGED & WHY** section.")
    out.append("5. Log this refine into `agent5/refine_playbook.md` §4B (raw log, WITH context/subject), "
               "and if the user states a preference, capture it as a CONDITIONAL rule (\"IF <context> "
               "THEN <direction>\") in §4A — never a flat global rule. See the playbook's §4 header.")
    out.append("\n---\n")

    # ---- the user's draft (front and center) ----
    out.append("# ===== YOUR DRAFT SCRIPT (refine THIS — preserve its voice/intent) =====\n")
    out.append(draft)
    out.append("\n")

    # ---- refiner playbook (checklist + learned preferences) ----
    rp = _read(REFINE_PLAYBOOK)
    if rp:
        out.append("# ===== REFINER PLAYBOOK (agent5/refine_playbook.md) — read carefully =====\n")
        out.append(rp)
        out.append("\n")

    # ---- shared writing references (same set Agent 4 uses) ----
    if REFERENCES and REF_DIR:
        for fname, label in REFERENCES:
            content = _read(os.path.join(REF_DIR, fname))
            if content:
                out.append(f"# ===== REFERENCE: {label} ({fname}) =====\n")
                out.append(content)
                out.append("\n")
    if PLAYBOOK:
        pb = _read(PLAYBOOK)
        if pb:
            out.append("# ===== REFERENCE: VIRALITY PLAYBOOK (agent2/playbook.md) =====\n")
            out.append(pb)

    brief_path = os.path.join(OUT_DIR, f"brief_refine_{slug}.md")
    with open(brief_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    print("Agent 5 prep (refiner):")
    print(f"  draft title  : {title[:60]}")
    print(f"  draft source : {os.path.relpath(draft_path, HERE)}")
    print(f"  paper facts  : {row.get('title')[:50] if row else ('(none / web-check)' )}")
    print(f"  refine notes : {args.notes or '(none)'}")
    print(f"  version      : v{ver} (for this script)")
    print(f"  brief written: {brief_path}")
    print(f"  -> next: ask Claude to refine into {out_rel}")


if __name__ == "__main__":
    main()
