#!/usr/bin/env python3
"""
agent4_prep.py — Agent 4 (script writer) data prep.

Standalone "plug." Given a chosen paper (name or URL) + optional extra instructions, it
assembles the full writing packet Claude needs to write the reel script:
  * the paper's details (from papers.csv / agent3 deep-dive if present)
  * the page's writing references (hook.md, the 2 winning-script files, script-type template,
    virality elements, and the agent2 playbook)
  * your extra instructions for this specific script
…and writes it to `agent4/brief_<slug>.md`.

Claude then writes the script (5 hooks: 3 proven + 2 experimental → connected easy-English
body → CTA → caption) to `scripts/<date>-<slug>.md`, cross-checking the paper on the web.

Each agent runs independently:
    python finding_papers.py     # 1 finder
    python agent2_prep.py        # 2 picker
    python agent3_prep.py        # 3 deep-dive
    python agent4_prep.py --paper "SensorFM" --notes "punchy, no jargon"   # 4 script writer

Usage:
    python agent4_prep.py --paper "<title or url>" [--notes "extra instructions"]
"""

import os
import re
import csv
import glob
import argparse
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "papers.csv")
REF_DIR = os.path.join(HERE, "Scripting_reference_things")
OUT_DIR = os.path.join(HERE, "agent4")

# Reference files to bundle into the brief (path, friendly label).
REFERENCES = [
    ("hook.md", "HOOK BIBLE (read first)"),
    ("Winning research paper Script part 1.md", "WINNING SCRIPT #1 (copy this shape)"),
    ("winning research paper script part 2.md", "WINNING SCRIPT #2"),
    ("7 script type template.md", "SCRIPT TYPE TEMPLATE (see TYPE 4)"),
    ("5 virality elements.md", "VIRALITY ELEMENTS"),
]
PLAYBOOK = os.path.join(HERE, "agent2", "playbook.md")


def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return (s[:50] or "paper")


STOPWORDS = {
    "a", "an", "the", "of", "for", "and", "or", "to", "in", "on", "with",
    "is", "are", "using", "via", "from", "at", "by", "as", "into",
}


def tokenize(text):
    """Meaningful words only: drop stopwords and very short tokens so a
    single common word (e.g. 'language') can't cause a false match."""
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return set(w for w in words if len(w) >= 3 and w not in STOPWORDS)


def find_paper(query):
    """Match a paper in papers.csv by URL substring or title keywords."""
    if not os.path.exists(CSV_PATH):
        return None
    q = query.strip().lower()
    rows = list(csv.DictReader(open(CSV_PATH, encoding="utf-8")))
    # 1) direct url match
    for r in rows:
        if q in (r.get("url", "").lower()):
            return r
    # 2) best keyword overlap on title (meaningful words only)
    q_words = tokenize(q)
    best, best_score = None, 0
    for r in rows:
        t_words = tokenize(r.get("title", ""))
        score = len(q_words & t_words)
        if score > best_score:
            best, best_score = r, score
    # Require 2+ overlapping meaningful words when the query has 2+ of its
    # own — a single shared word (often a generic one) isn't enough evidence.
    # A genuinely single-word query (e.g. "SensorFM") only needs 1 match.
    min_required = 2 if len(q_words) >= 2 else 1
    return best if best_score >= min_required else None


def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def latest_deepdive():
    files = sorted(glob.glob(os.path.join(HERE, "agent3", "deepdive_*.md")))
    return files[-1] if files else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", required=True, help="paper title keywords or URL")
    ap.add_argument("--notes", default="", help="extra instructions for THIS script")
    ap.add_argument("--date", default=None)
    args = ap.parse_args()
    today = args.date or datetime.now().strftime("%Y-%m-%d")

    row = find_paper(args.paper)
    title = (row or {}).get("title", args.paper)
    slug = slugify(title if row else args.paper)

    os.makedirs(OUT_DIR, exist_ok=True)
    out = [f"# Agent 4 — script-writing brief · {today}", ""]
    out.append(f"**Target paper:** {title}")
    if row:
        out.append(f"- URL: {row.get('url')}")
        out.append(f"- Lab: {row.get('lab')} · HF upvotes: {row.get('hf_upvotes')} · "
                   f"Trending: {row.get('trending_score')}")
        out.append(f"- Abstract/summary: {row.get('summary')}")
    else:
        out.append("- (not found in papers.csv — Claude should web-search this paper directly)")
    out.append("")
    if args.notes:
        out.append(f"## ⚙️ Extra instructions for THIS script (highest priority)\n\n{args.notes}\n")
    else:
        out.append("## ⚙️ Extra instructions\n\n(none given — use page defaults)\n")

    out.append("## 📋 What Claude does next")
    out.append("1. Web-search the paper to confirm facts + pull the best wow-numbers.")
    out.append("2. Write **5 hooks** (3 in proven patterns, 2 experimental) per `hook.md`.")
    out.append("3. Write a **connected, easy-English body** (TYPE 4 in the script-type template).")
    out.append("4. Add **CTA + caption + hashtags**. Save to `scripts/" + today + "-" + slug + ".md`.")
    out.append("\n---\n")

    # bundle references
    for fname, label in REFERENCES:
        content = read_file(os.path.join(REF_DIR, fname))
        if content:
            out.append(f"# ===== REFERENCE: {label} ({fname}) =====\n")
            out.append(content)
            out.append("\n")
    pb = read_file(PLAYBOOK)
    if pb:
        out.append("# ===== REFERENCE: VIRALITY PLAYBOOK (agent2/playbook.md) =====\n")
        out.append(pb)

    brief_path = os.path.join(OUT_DIR, f"brief_{slug}.md")
    with open(brief_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    print(f"Agent 4 prep:")
    print(f"  paper matched : {title[:60]}" + ("" if row else "  (NOT in csv — web-search)"))
    print(f"  extra notes   : {args.notes or '(none)'}")
    print(f"  brief written : {brief_path}")
    print(f"  -> next: ask Claude to write the script to scripts/{today}-{slug}.md")


if __name__ == "__main__":
    main()
