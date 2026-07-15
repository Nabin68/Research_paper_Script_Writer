#!/usr/bin/env python3
"""
agent2_prep.py — Agent 2 (the "picker") data prep.

Runs AFTER finding_papers.py (Agent 1). It:
  1. Parses the historical reels in `all past scripts/` into a clean performance table.
  2. Pulls today's candidate papers from papers.csv.
  3. Applies a transparent first-pass heuristic score (the playbook rubric, sections 7)
     so ~100 candidates are pre-ranked down to a focused shortlist.
  4. Writes `agent2/brief_<date>.md` — the packet Claude reads to make the final
     wow-factor judgment and produce picks/top5_<date>.md.

The heuristic is deliberately a PRE-FILTER, not the final word. The real "will this go
viral" call is made by Claude on top of this, using agent2/playbook.md.

Pure standard library.

Usage:
    python agent2_prep.py                 # today
    python agent2_prep.py --date 2026-07-14
"""

import os
import re
import csv
import sys
import argparse
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(HERE, "all past scripts")
CSV_PATH = os.path.join(HERE, "papers.csv")
OUT_DIR = os.path.join(HERE, "agent2")

# ---- keyword banks for the heuristic (mirrors playbook rubric factors) ---------- #
KW = {
    "brain":   r"\b(brain|neuro\w*|mind[- ]?read\w*|cognit\w*|thought|conscious\w*|eeg|meg|"
               r"neural interface|bci|telepath\w*|memory|psycholog\w*)\b",
    "body":    r"\b(hand|body|muscle|wearable|prosthe\w*|motor|limb|implant)\b",
    "money":   r"(\$\s?\d|\bbillion|\bmillion|\btrillion|\bindustry\b|\bcost\w*|\bcheaper|"
               r"\brevenue|\bmarket\b|\bfunding|\braised\b|\bvaluation)",
    "company": r"\b(nvidia|google|deepmind|openai|anthropic|claude|gpt|gemini|meta\b|"
               r"microsoft|deepseek|mistral|alibaba|qwen|xai|apple|amazon|tesla|bytedance)\b",
    "relatable": r"\b(job|jobs|doctor|medical|health|patient|treatment|salary|worker|"
               r"student|your\b|everyday|daily)\b",
    "underdog": r"\b(\d{1,2}[- ]year[- ]old|solo|alone|dropout|student|from scratch|"
               r"single (developer|engineer|researcher)|open[- ]?source|reverse[- ]engineer\w*)\b",
    "reversal": r"\b(beats?|outperform\w*|smaller|cheaper|wrong|surpass\w*|faster than|"
               r"without|no longer|replaces?|kills?|obsolete|counterintuit\w*)\b",
    "wow_num": r"(\d+\s?[x×]\b|\d{2,}\s?%|\d+\s?→\s?\d+|from \d+\s?%? to \d+|"
               r"\$\s?\d+(\.\d+)?\s?(b|m|billion|million|trillion)?)",
    # penalties
    "history": r"\b(19\d\d|200\d|201[0-5]|turing|mcculloch|pitts|resnet|classic|seminal|"
               r"foundational|decades ago|revisit\w*)\b",
    "theory":  r"\b(theorem|lemma|proof|convergence|bound(s|ed)?|optimization|gradient|"
               r"regularization|kernel|manifold|complexity|provably)\b",
    "hardware": r"\b(robot\w*|actuator|lidar|sensor|chip(?!ay)|fpga|hardware|manipulat\w*|"
               r"locomo\w*|grasp\w*)\b",
}


def kw(text, key):
    return len(re.findall(KW[key], text, re.I))


# --------------------------------------------------------------------------- #
# 1. Historical performance
# --------------------------------------------------------------------------- #
def parse_frontmatter(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    fm = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                fm[k.strip()] = v.strip().strip('"')
    return fm


def num(v):
    try:
        return float(str(v).replace(",", ""))
    except (ValueError, TypeError):
        return None


def load_history():
    rows = []
    if not os.path.isdir(SCRIPTS_DIR):
        return rows
    for name in sorted(os.listdir(SCRIPTS_DIR)):
        if not re.match(r"\d{3}-.*\.md$", name):
            continue
        fm = parse_frontmatter(os.path.join(SCRIPTS_DIR, name))
        rows.append({
            "file": name,
            "title": fm.get("title", ""),
            "paper": fm.get("paperCovered", ""),
            "views": num(fm.get("videoViewCount")) or num(fm.get("videoPlayCount")),
            "likes": num(fm.get("likesCount")),
            "shares": num(fm.get("sharesCount")),
            "skip": num(fm.get("Skip Rate")),
            "verdict": fm.get("verdict", "unknown"),
        })
    return rows


def history_summary(hist):
    have_views = [r for r in hist if r["views"]]
    have_views.sort(key=lambda r: r["views"], reverse=True)
    top = have_views[:12]
    bottom = have_views[-10:]
    lines = ["## Historical performance (reference)\n",
             f"_{len(hist)} past reels · {len(have_views)} with view data._\n",
             "**Your biggest hits (learn from these):**\n"]
    for r in top:
        lines.append(f"- {int(r['views']):>6,} views · {r['verdict']:<7} · "
                     f"{(r['paper'] or r['title'])[:70]}")
    lines.append("\n**Your flops (avoid this shape):**\n")
    for r in reversed(bottom):
        lines.append(f"- {int(r['views']):>6,} views · {r['verdict']:<7} · "
                     f"{(r['paper'] or r['title'])[:70]}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# 2. Today's candidates + heuristic score
# --------------------------------------------------------------------------- #
def heuristic_score(title, summary, lab):
    """First-pass 0-100 fit score, mirroring playbook rubric section 7."""
    t = f"{title}. {summary}"
    s = 0
    hits = {}
    # A wow-number (20)
    a = min(20, kw(t, "wow_num") * 10); hits["wow#"] = a; s += a
    # B brain/body (18)
    b = 18 if kw(t, "brain") else (12 if kw(t, "body") else 0); hits["brain/body"] = b; s += b
    # C named company / underdog person (15)
    c = 15 if (kw(t, "company") or kw(t, "underdog")) else 0; hits["named"] = c; s += c
    # D money/disruption (12)
    d = 12 if kw(t, "money") >= 1 else 0; hits["money"] = d; s += d
    # E relatable (12)
    e = 12 if kw(t, "relatable") else 0; hits["relatable"] = e; s += e
    # F explainable — proxy: penalize heavy theory jargon (13 default, lose for theory)
    f = 13 - min(13, kw(t, "theory") * 5); hits["simple"] = f; s += f
    # G reversal/underdog (10)
    g = 10 if kw(t, "reversal") else 0; hits["reversal"] = g; s += g
    # penalties
    pen = 0
    if kw(t, "history"): pen += 25
    if kw(t, "theory") >= 2 and b == 0 and d == 0: pen += 20
    if kw(t, "hardware") and b == 0: pen += 15
    s = max(0, s - pen); hits["penalty"] = -pen
    return s, hits


def verdict_band(score):
    if score >= 80: return "WIN candidate (30k-60k+)"
    if score >= 60: return "MID / strong-share (10k-25k)"
    if score >= 40: return "risky, hook-dependent (3k-8k)"
    return "likely FLOP (<3k)"


def load_candidates(today):
    if not os.path.exists(CSV_PATH):
        sys.exit("papers.csv not found — run finding_papers.py (Agent 1) first.")
    cands = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("first_seen") != today:
                continue
            if r.get("category") == "repo":
                continue  # repos aren't reel topics
            score, hits = heuristic_score(r.get("title", ""), r.get("summary", ""),
                                          r.get("lab", ""))
            r["_fit"] = score
            r["_hits"] = hits
            cands.append(r)
    cands.sort(key=lambda r: (r["_fit"], int(r.get("trending_score") or 0)), reverse=True)
    return cands


# --------------------------------------------------------------------------- #
# Write brief
# --------------------------------------------------------------------------- #
def write_brief(today, hist, cands, shortlist_n=20):
    os.makedirs(OUT_DIR, exist_ok=True)
    out = [f"# Agent 2 brief — {today}", ""]
    out.append(f"_{len(cands)} candidate papers found today. Below: top {shortlist_n} by "
               f"first-pass fit score. Claude makes the final Top-5 call using "
               f"`agent2/playbook.md` + live web trends._")
    out.append("")
    out.append(history_summary(hist))
    out.append("\n---\n")
    out.append(f"## Today's candidates (pre-ranked, top {shortlist_n})\n")
    out.append("_Fit score = playbook rubric first pass. Not final._\n")
    for i, r in enumerate(cands[:shortlist_n], 1):
        h = r["_hits"]
        signal = " ".join(f"{k}:{v}" for k, v in h.items() if v)
        out.append(f"### {i}. [{r['title']}]({r['url']})")
        out.append(f"- **Fit {r['_fit']}/100** → {verdict_band(r['_fit'])}")
        out.append(f"- Lab: {r.get('lab')} · Source: {r.get('source')} · "
                   f"HF upvotes: {r.get('hf_upvotes')} · Trending: {r.get('trending_score')}")
        out.append(f"- Signals: {signal}")
        summ = (r.get("summary") or "")[:300]
        out.append(f"- {summ}")
        out.append("")
    # also a compact table
    out.append("## Quick table\n")
    out.append("| # | Fit | Lab | HF | Title |")
    out.append("|---|-----|-----|----|-------|")
    for i, r in enumerate(cands[:shortlist_n], 1):
        out.append(f"| {i} | {r['_fit']} | {r.get('lab')} | {r.get('hf_upvotes')} | "
                   f"{r['title'][:60]} |")

    path = os.path.join(OUT_DIR, f"brief_{today}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD (default: today)")
    args = ap.parse_args()
    today = args.date or datetime.now().strftime("%Y-%m-%d")

    hist = load_history()
    cands = load_candidates(today)
    path = write_brief(today, hist, cands)

    print(f"Agent 2 prep for {today}:")
    print(f"  historical reels parsed : {len(hist)}")
    print(f"  today's candidates      : {len(cands)}")
    print(f"  brief written           : {path}")
    if cands:
        print("  top pre-ranked pick     : "
              f"[{cands[0]['_fit']}] {cands[0]['title'][:60]}")


if __name__ == "__main__":
    main()
