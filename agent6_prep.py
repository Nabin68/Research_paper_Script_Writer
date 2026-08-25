#!/usr/bin/env python3
"""
agent6_prep.py — Agent 6 (CAPTION writer / refiner) data prep.

Standalone "plug," same spirit as Agent 5. You have a finished reel script; this agent turns
it into the Instagram caption — or refines a caption you already have.

Two modes:
  * generate — read the script, write a fresh caption in the page's proven caption shape
  * refine   — read the script AND your current caption, improve only what you asked for

What this prep step assembles into `agent6/brief_caption_<slug>.md`:
  * the reel script the caption is for (from --file, or the drop-file agent6/input_script.md)
  * your current caption, when refining (from --caption-file, or agent6/input_caption.md)
  * the CAPTION PLAYBOOK (agent6/caption_playbook.md) — the shape rules, the reference
    captions, and the growing "LEARNINGS & USER PREFERENCES" section (§5)
  * your instructions for THIS pass

The caption is written to a VERSIONED file so re-refining keeps a clean history:

    captions/<date>-v<N>-<slug>.md

LEARNING LOOP: every pass is logged to agent6/caption_playbook.md §5B WITH its subject, and
stated preferences become CONDITIONAL rules ("IF <context> THEN <direction>") in §5A — never
flat global rules, for the same reason Agent 5 works that way.

Each agent runs independently (run ONE at a time, only when you ask):
    python finding_papers.py                                # 1 finder
    python agent2_prep.py                                   # 2 picker
    python agent3_prep.py                                   # 3 deep-dive
    python agent4_prep.py --paper "SensorFM" --notes ".."   # 4 script writer
    python agent5_prep.py --file draft.md --notes ".."      # 5 script refiner
    python agent6_prep.py --file script.md                  # 6 caption writer

Usage:
    python agent6_prep.py                                   # caption agent6/input_script.md
    python agent6_prep.py --file scripts/2026-07-18-seal.md
    python agent6_prep.py --mode refine --notes "hook is flat, keep my ending"
"""

import os
import re
import glob
import argparse
from datetime import datetime

# Reuse the existing helpers so all the writers stay in lockstep.
try:
    from agent4_prep import slugify, read_file
except Exception:  # pragma: no cover - fallback if import path differs
    slugify = None
    read_file = None

try:
    from agent5_prep import title_from_draft
except Exception:  # pragma: no cover
    title_from_draft = None

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "agent6")
CAPTIONS_DIR = os.path.join(HERE, "captions")  # versioned captions land here

SCRIPT_DROPFILE = os.path.join(OUT_DIR, "input_script.md")
CAPTION_DROPFILE = os.path.join(OUT_DIR, "input_caption.md")
CAPTION_PLAYBOOK = os.path.join(OUT_DIR, "caption_playbook.md")


def _fallback_slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return (s[:50] or "caption")


def _fallback_read(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def _fallback_title(text, fallback):
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"^#{1,6}\s+(.+)$", line)
        if m:
            return m.group(1).strip()
    return fallback


def next_version(slug):
    """captions/<date>-v<N>-<slug>.md → the next N for this script."""
    highest = 0
    for p in glob.glob(os.path.join(CAPTIONS_DIR, f"*-v*-{slug}.md")):
        m = re.search(r"-v(\d+)-", os.path.basename(p))
        if m:
            highest = max(highest, int(m.group(1)))
    return highest + 1


def main():
    _slug = slugify or _fallback_slugify
    _read = read_file or _fallback_read
    _title = title_from_draft or _fallback_title

    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["generate", "refine"], default="generate",
                    help="write a new caption, or refine an existing one")
    ap.add_argument("--file", help="path to the reel script (default: agent6/input_script.md)")
    ap.add_argument("--caption-file", dest="caption_file",
                    help="path to the caption being refined (default: agent6/input_caption.md)")
    ap.add_argument("--notes", default="", help="instructions for THIS pass")
    ap.add_argument("--date", default=None)
    args = ap.parse_args()
    today = args.date or datetime.now().strftime("%Y-%m-%d")

    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(CAPTIONS_DIR, exist_ok=True)

    script_path = args.file or SCRIPT_DROPFILE
    script = _read(script_path)
    if not script or not script.strip():
        raise SystemExit(
            "No script found.\n"
            f"  Either: paste the reel script into  {SCRIPT_DROPFILE}\n"
            f"  or run: python agent6_prep.py --file path\\to\\script.md"
        )

    caption = None
    if args.mode == "refine":
        caption_path = args.caption_file or CAPTION_DROPFILE
        caption = _read(caption_path)
        if not caption or not caption.strip():
            raise SystemExit(
                "Refine mode needs the caption you want refined.\n"
                f"  Either: paste it into  {CAPTION_DROPFILE}\n"
                f"  or run: python agent6_prep.py --mode refine --caption-file path\\to\\caption.md"
            )

    title = _title(script, os.path.splitext(os.path.basename(script_path))[0])
    slug = _slug(title)
    ver = next_version(slug)
    out_rel = os.path.join("captions", f"{today}-v{ver}-{slug}.md")

    verb = "REFINING" if args.mode == "refine" else "WRITING"
    out = [f"# Agent 6 — caption {verb} brief · {today}", ""]
    out.append(f"**Script this caption is for:** {title}")
    out.append(f"- Source file: `{os.path.relpath(script_path, HERE)}`")
    out.append(f"- Mode: **{args.mode}**")
    out.append(f"- Version: **v{ver}** for this script")
    out.append("")

    if args.notes:
        out.append(f"## ⚙️ Instructions for THIS pass (highest priority)\n\n{args.notes}\n")
    elif args.mode == "refine":
        out.append("## ⚙️ Instructions\n\n(none given — use the playbook + §5 preferences; "
                   "polish don't rewrite, and preserve the user's voice)\n")
    else:
        out.append("## ⚙️ Instructions\n\n(none given — use the playbook shape and page defaults)\n")

    out.append("## 📋 What Claude does next")
    if args.mode == "refine":
        out.append("1. Read the CURRENT CAPTION and the CAPTION PLAYBOOK — especially §5 "
                   "LEARNINGS & USER PREFERENCES — and match this caption's SUBJECT/CONTEXT "
                   "against the conditional rules there before refining.")
        out.append("2. Honour the instructions above over everything else, including what the "
                   "user asked you to leave alone.")
        out.append("3. Refine only what is actually weak. Isolate the specific weak words and "
                   "touch only those — do not restage the sentences around them.")
        out.append("4. Check every number against the script. Never introduce a figure the "
                   "script does not support.")
    else:
        out.append("1. Read the SCRIPT below and the CAPTION PLAYBOOK (§1 shape, §2 voice, "
                   "§3 hard rules, §4 reference captions, §5 learned preferences).")
        out.append("2. Pick the shape that matches: reference A for one paper explained as a "
                   "chain of steps, reference B for two labs attacking one problem.")
        out.append("3. Pull the wow-numbers from the script. Never invent or sharpen a figure "
                   "the script does not contain.")
        out.append("4. Write the caption as plain text, ready to paste into Instagram.")
    out.append(f"5. Write it to **`{out_rel}`** (versioned — this is **v{ver}**), ending with a "
               "short **WHAT I WROTE & WHY** section (or **WHAT I CHANGED & WHY** when refining) "
               "*after* the caption, separated by a `---` so the caption above stays paste-ready.")
    out.append("6. Log this pass into `agent6/caption_playbook.md` §5B (raw log, WITH subject), "
               "and if the user stated a preference, capture it in §5A as a CONDITIONAL rule "
               "(\"IF <context> THEN <direction>\") — never a flat global rule.")
    out.append("\n---\n")

    if caption:
        out.append("# ===== CURRENT CAPTION (refine THIS — preserve its voice/intent) =====\n")
        out.append(caption)
        out.append("\n")

    out.append("# ===== THE REEL SCRIPT (the caption's source of facts) =====\n")
    out.append(script)
    out.append("\n")

    pb = _read(CAPTION_PLAYBOOK)
    if pb:
        out.append("# ===== CAPTION PLAYBOOK (agent6/caption_playbook.md) — read carefully =====\n")
        out.append(pb)

    brief_path = os.path.join(OUT_DIR, f"brief_caption_{slug}.md")
    with open(brief_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    print("Agent 6 prep (captions):")
    print(f"  mode         : {args.mode}")
    print(f"  script title : {title[:60]}")
    print(f"  script source: {os.path.relpath(script_path, HERE)}")
    print(f"  notes        : {args.notes or '(none)'}")
    print(f"  version      : v{ver} (for this script)")
    print(f"  brief written: {brief_path}")
    print(f"  -> next: ask Claude to write the caption to {out_rel}")


if __name__ == "__main__":
    main()
