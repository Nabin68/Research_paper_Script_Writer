#!/usr/bin/env python3
"""
agent3_prep.py — Agent 3 (deep-dive & decide) data prep.

Standalone "plug." Reads the latest Top-5 (from Agent 2), matches each pick back to
papers.csv for its live metrics, computes a first-pass CHANNEL-FIT reference score from
your playbook rubric (reusing Agent 2's heuristic), and writes a research scaffold to
`agent3/input_<date>.md`.

Claude then does the internet research per paper, assesses wow factors, and finalizes the
Wow Score /10 (Internet virality /4 + Channel fit /6) in `agent3/deepdive_<date>.md`.

Each agent runs independently:
    python finding_papers.py     # Agent 1  -> papers.csv
    python agent2_prep.py        # Agent 2  -> agent2/brief, then ask Claude for top5
    python agent3_prep.py        # Agent 3  -> agent3/input, then ask Claude for deepdive

Usage:
    python agent3_prep.py                 # use latest picks/top5_*.md
    python agent3_prep.py --date 2026-07-14
    python agent3_prep.py --picks path/to/top5.md
"""

import os
import re
import csv
import glob
import argparse
from datetime import datetime

try:
    from agent2_prep import heuristic_score, verdict_band
except Exception:  # allow running even if import path differs
    heuristic_score = None
    def verdict_band(s):  # noqa: E704
        return ""

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "papers.csv")
PICKS_DIR = os.path.join(HERE, "picks")
OUT_DIR = os.path.join(HERE, "agent3")

LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")


def find_latest_picks():
    files = sorted(glob.glob(os.path.join(PICKS_DIR, "top5_*.md")))
    return files[-1] if files else None


def parse_picks(path):
    """Extract the 5 papers (title, url) from a top5 markdown file.

    Picks are the FIRST markdown link under each numbered '## <n>.' section — that's the
    paper link on the '**Paper:** ...[link](url)' or heading line.
    """
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    blocks = re.split(r"\n##\s+\d+\.\s", text)[1:]  # each numbered section
    picks = []
    for b in blocks:
        heading = b.splitlines()[0].strip()
        m = LINK_RE.search(b)
        if m:
            title, url = m.group(1), m.group(2)
            # prefer heading text as the human title if the link text is just "link"
            title = heading if title.lower() in ("link", "paper", "source") else title
        else:
            title, url = heading, ""
        picks.append({"headline": heading, "title": title, "url": url})
    return picks


def load_csv_index():
    idx = {}
    if not os.path.exists(CSV_PATH):
        return idx
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            key = (r.get("url") or "").split("?")[0].rstrip("/").lower()
            if key:
                idx[key] = r
    return idx


def match_metrics(url, idx):
    return idx.get((url or "").split("?")[0].rstrip("/").lower(), {})


def channel_fit_5(title, summary, lab):
    """Playbook heuristic mapped onto a /6 channel-fit reference (Claude finalizes)."""
    if heuristic_score is None:
        return None, {}
    score, hits = heuristic_score(title, summary, lab)
    fit6 = round(score / 100 * 6, 1)
    return fit6, {"rubric_100": score, "band": verdict_band(score)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--picks", help="explicit path to a top5 md file")
    args = ap.parse_args()
    today = args.date or datetime.now().strftime("%Y-%m-%d")

    picks_path = args.picks or (
        os.path.join(PICKS_DIR, f"top5_{today}.md")
        if os.path.exists(os.path.join(PICKS_DIR, f"top5_{today}.md"))
        else find_latest_picks()
    )
    if not picks_path or not os.path.exists(picks_path):
        raise SystemExit("No Top-5 file found. Run Agent 2 first (picks/top5_<date>.md).")

    picks = parse_picks(picks_path)
    idx = load_csv_index()

    os.makedirs(OUT_DIR, exist_ok=True)
    out = [f"# Agent 3 input — {today}",
           f"_Deep-dive scaffold for the {len(picks)} picks in `{os.path.relpath(picks_path, HERE)}`._",
           "",
           "For each paper, Claude fills: internet buzz/reach (web search), the wow "
           "factor(s), the Wow Score /10 (Internet /4 + Channel /6), and a MAKE/MAYBE/SKIP "
           "verdict — written to `agent3/deepdive_" + today + ".md`.", ""]

    for i, p in enumerate(picks, 1):
        row = match_metrics(p["url"], idx)
        summary = row.get("summary", "")
        lab = row.get("lab", "")
        fit6, meta = channel_fit_5(p["title"], summary, lab)
        out.append(f"## {i}. {p['headline']}")
        out.append(f"- URL: {p['url'] or '(none)'}")
        if row:
            out.append(f"- Live metrics: lab={row.get('lab')} · HF upvotes={row.get('hf_upvotes')}"
                       f" · reddit={row.get('reddit_mentions')} · trending={row.get('trending_score')}")
        else:
            out.append("- Live metrics: (not matched in papers.csv — likely a Reddit/thread pick)")
        if fit6 is not None:
            out.append(f"- Channel-fit reference: **{fit6}/6** (rubric {meta['rubric_100']}/100 → {meta['band']})")
        out.append(f"- Research TODO: search buzz/coverage → Internet virality /4 · confirm wow factors · final Wow /10")
        out.append("")

    path = os.path.join(OUT_DIR, f"input_{today}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    print(f"Agent 3 prep for {today}:")
    print(f"  picks source : {os.path.relpath(picks_path, HERE)}")
    print(f"  papers loaded: {len(picks)}")
    print(f"  scaffold     : {path}")
    for i, p in enumerate(picks, 1):
        print(f"    {i}. {p['title'][:60]}")


if __name__ == "__main__":
    main()
