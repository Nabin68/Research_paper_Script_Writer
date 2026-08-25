#!/usr/bin/env python3
"""
research_filter.py — authenticity gate for finding_papers.py.

Runs right after merge() and before trending_score(): separates "confirmed,
authentic research" (real papers / technical reports / documented methods) from
items that merely "look AI-related" (product/pricing/hiring/partnership posts,
opinion threads, memes, AI-flavored repos with no paper behind them).

Applied ONLY to items newly added this run. It never touches rows already in the
ledger, and never touches any row carrying user-owned picked/my_notes/performance
data — so historical rows and your annotations are always preserved.

Two layers (mirrors the finding_papers.py field/name conventions):

  1. Structural filter (no LLM, instant, every candidate):
       * a valid arxiv_id                -> always authentic, KEEP
       * no arxiv_id (rss/scraped/github/
         reddit items) -> DROP on an EXCLUDE match; otherwise must match an
         INCLUDE term OR link to a real paper/PDF/arxiv URL, else DROP.
       * GitHub repos get a stricter gate: keep only if the description links to
         an arxiv URL or explicitly references implementing a named paper/method.

  2. LLM batch verification (ONE call per run) for structural survivors that
     still lack an arxiv_id: Claude marks each KEEP only if confident it is
     backed by actual research; ambiguous/unverifiable -> DROP.

Pure Python standard library (urllib for the API call) so finding_papers.py stays
zero-pip. If ANTHROPIC_API_KEY is unset or the call fails, layer 2 is skipped and
the structural survivors are kept (fail-open) with a logged note — a missing key
must never silently empty the digest.

Lightweight logging: a per-source drop tally (structural vs LLM) is appended to
filter_log.csv each run, so you can watch which sources are mostly noise over time.
"""

import os
import re
import csv
import json
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
FILTER_LOG = os.path.join(HERE, "filter_log.csv")
FILTER_LOG_FIELDS = ["date", "source", "candidates",
                     "dropped_structural", "dropped_llm", "kept"]

# No-API-key handoff: undecided items are staged here for Claude Code (Opus) to
# classify, and the keep-list is read back before pruning the ledger.
QUEUE_PATH = os.path.join(HERE, "agent1_verify_queue.json")
RESULT_PATH = os.path.join(HERE, "agent1_verify_result.json")

# User-owned columns — a candidate carrying any of these is never dropped.
USER_COLS = ["picked", "my_notes", "performance"]

# --- Anthropic Messages API (raw HTTP, stdlib only) ------------------------- #
API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-opus-4-8"   # override via settings.llm_filter_model
LLM_MAX_TOKENS = 1024

# --------------------------------------------------------------------------- #
# Structural patterns
# --------------------------------------------------------------------------- #
# A clean arxiv id like 2506.12345 — the mark of a real paper row.
ARXIV_ID_RE = re.compile(r"^\d{4}\.\d{4,5}$")

# An explicit paper / PDF / arxiv URL anywhere in the item body.
PAPER_LINK_RE = re.compile(
    r"(arxiv\.org/(?:abs|pdf|html)/"
    r"|/\d{4}\.\d{4,5}(?:v\d+)?(?:\.pdf)?\b"
    r"|\.pdf\b"
    r"|openreview\.net/"
    r"|doi\.org/"
    r"|aclanthology\.org|proceedings\.mlr\.press|papers\.nips\.cc"
    r"|semanticscholar\.org|dl\.acm\.org)",
    re.I,
)

# Non-research signals. An EXCLUDE match on a non-arxiv item is a hard DROP.
# Phrases are chosen to be distinctive so substring matching stays safe
# (e.g. no bare "job" — that would wrongly hit a "job exposure" paper).
EXCLUDE_TERMS = [
    "hiring", "we're hiring", "we are hiring", "join our team", "open roles",
    "job opening", "now hiring",
    "pricing", "new pricing", "price increase", "per seat", "per month",
    "subscription", "free tier", "paid plan",
    "waitlist", "wait list", "join the waitlist", "early access", "sign up now",
    "partnership", "partners with", "partnering with", "strategic partnership",
    "now available", "generally available", "available today", "available now",
    "coming soon", "we're excited to announce", "we are excited to announce",
    "case study", "customer story", "customer success", "success story",
    "funding round", "raises $", "raised $", "series a", "series b", "series c",
    "seed round", "valuation", "acquires", "acquisition of",
]

# Research signals. A non-arxiv item needs at least one of these (or a paper
# link) to survive the structural stage and reach LLM verification.
INCLUDE_TERMS = [
    "paper", "arxiv", "preprint", "pre-print", "technical report",
    "research report", "report", "benchmark", "dataset", "we propose",
    "we introduce", "we present", "we train", "we fine-tune", "we release",
    "architecture", "evaluation", "ablation", "method", "approach",
    "model card", "state-of-the-art", "sota", "findings", "study", "experiments",
]

# GitHub repos: require an arxiv link or an explicit paper/method reference.
GH_PAPER_REF_RE = re.compile(
    r"(arxiv|preprint|official (?:code|implementation|repo|pytorch)"
    r"|implementation of|implements the|reproduc\w+|from the paper"
    r"|as described in|pytorch implementation|jax implementation"
    r"|paper|we (?:propose|introduce|present)|method from)",
    re.I,
)

def _alt_re(terms):
    """Alternation that only matches a term when it is NOT flanked by ASCII
    letters — so e.g. 'valuation' does not match inside 'evaluation', and
    'series a' does not match inside 'series analysis'."""
    return re.compile(r"(?<![a-z])(" + "|".join(re.escape(t) for t in terms)
                      + r")(?![a-z])", re.I)


EXCLUDE_RE = _alt_re(EXCLUDE_TERMS)
INCLUDE_RE = _alt_re(INCLUDE_TERMS)


# --------------------------------------------------------------------------- #
# Structural verdict
# --------------------------------------------------------------------------- #
def _text_blob(row):
    return " ".join(str(row.get(k) or "") for k in ("title", "summary")).strip()


def _link_blob(row):
    return " ".join(str(row.get(k) or "") for k in ("title", "summary", "url"))


def _has_paper_link(row):
    return bool(PAPER_LINK_RE.search(_link_blob(row)))


def _is_repo(row):
    srcs = set((row.get("source") or "").split("+"))
    return row.get("category") == "repo" or "github" in srcs


def _structural_verdict(row):
    """Return (decision, reason) where decision is 'keep' | 'drop' | 'llm'."""
    aid = str(row.get("arxiv_id") or "").strip()
    if ARXIV_ID_RE.match(aid):
        return "keep", "arxiv_id"

    text = _text_blob(row)

    # GitHub is the leakiest source: require a paper link or explicit reference.
    if _is_repo(row):
        if _has_paper_link(row) or GH_PAPER_REF_RE.search(text):
            return "llm", "github-paper-ref"
        return "drop", "github-no-paper"

    # Other non-arxiv items: EXCLUDE wins, then require INCLUDE or a paper link.
    m = EXCLUDE_RE.search(text)
    if m:
        return "drop", "exclude:" + m.group(1).lower()
    if INCLUDE_RE.search(text) or _has_paper_link(row):
        return "llm", "structural-pass"
    return "drop", "no-research-signal"


# --------------------------------------------------------------------------- #
# LLM batch verification (one call per run)
# --------------------------------------------------------------------------- #
_LLM_SYSTEM = (
    "You are a strict filter for a daily AI-research digest. You are given a "
    "numbered list of items (each a title plus a short snippet). For EACH item "
    "decide KEEP or DROP.\n\n"
    "KEEP only if you are confident the item is backed by actual research — a "
    "specific paper, a technical report, or a documented method, benchmark, or "
    "dataset with a real technical contribution.\n\n"
    "DROP if it is a product or feature announcement, pricing / hiring / "
    "partnership / funding news, an opinion or discussion thread, a demo or tool "
    "with no method behind it, or anything you cannot verify as genuine research "
    "from the text alone. When in doubt, DROP.\n\n"
    "Respond with ONLY the numbers to KEEP, comma-separated (e.g. \"1, 4, 7\"). "
    "If none qualify, respond with exactly \"NONE\". Do not explain."
)


def _numbered(rows):
    """Render rows as a numbered title+snippet list (shared by API + queue)."""
    lines = []
    for i, row in enumerate(rows, 1):
        title = (row.get("title") or "").strip()
        snippet = re.sub(r"\s+", " ", (row.get("summary") or "")).strip()[:240]
        src = row.get("source") or ""
        lines.append(f"{i}. [{src}] {title} — {snippet}")
    return "\n".join(lines)


def _parse_keep_numbers(text, n):
    """Parse the model's reply into a set of 0-based indices to KEEP.
    Returns None on an unparseable reply so the caller can fail open."""
    nums = {int(x) - 1 for x in re.findall(r"\d+", text) if 1 <= int(x) <= n}
    if nums:
        return nums
    if re.search(r"\bnone\b", text, re.I):
        return set()      # explicit: keep nothing
    return None           # unparseable -> fail open


def _api_headers():
    """Request headers for whichever credential is present, or None if neither
    ANTHROPIC_API_KEY nor ANTHROPIC_AUTH_TOKEN is set."""
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if key:
        return {"x-api-key": key,
                "anthropic-version": API_VERSION,
                "content-type": "application/json"}
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN", "").strip()
    if token:
        return {"authorization": "Bearer " + token,
                "anthropic-version": API_VERSION,
                "anthropic-beta": "oauth-2025-04-20",
                "content-type": "application/json"}
    return None


def _llm_keep_set(rows, headers, cfg, log):
    """Ask Claude (via the API) which rows are genuine research. Returns a set of
    0-based indices to KEEP, or None on any failure (network / refusal / parse)."""
    model = cfg.get("settings", {}).get("llm_filter_model", DEFAULT_MODEL)
    body = json.dumps({
        "model": model,
        "max_tokens": LLM_MAX_TOKENS,
        "system": _LLM_SYSTEM,
        "messages": [{"role": "user", "content": "Items:\n" + _numbered(rows)}],
    }).encode("utf-8")
    req = urllib.request.Request(API_URL, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
    except Exception as e:  # noqa: BLE001 - fail open, never kill the run
        log(f"    ! LLM verification failed ({e}) — keeping structural survivors")
        return None

    if data.get("stop_reason") == "refusal":
        log("    ! LLM verification refused — keeping structural survivors")
        return None
    text = "".join(b.get("text", "") for b in data.get("content", [])
                   if b.get("type") == "text")
    keep = _parse_keep_numbers(text, len(rows))
    if keep is None:
        log("    ! LLM reply unparseable — keeping structural survivors")
    return keep


def _write_verify_queue(today, pending, log):
    """No API credential: stage the undecided items for Claude Code to classify.
    `finding_papers.py --apply-verification` consumes the result afterward."""
    items = []
    for i, (key, row) in enumerate(pending, 1):
        items.append({
            "n": i, "key": key, "source": row.get("source") or "",
            "title": (row.get("title") or "").strip(),
            "snippet": re.sub(r"\s+", " ", (row.get("summary") or "")).strip()[:240],
        })
    try:
        with open(QUEUE_PATH, "w", encoding="utf-8") as f:
            json.dump({"date": today, "count": len(items), "items": items}, f,
                      ensure_ascii=False, indent=2)
    except Exception as e:  # noqa: BLE001
        log(f"    ! could not write {os.path.basename(QUEUE_PATH)} ({e})")
        return
    log(f"    No API key — wrote {len(items)} undecided items to "
        f"{os.path.basename(QUEUE_PATH)} (kept this pass).")
    log(f"    Have Claude classify them into {os.path.basename(RESULT_PATH)} "
        f'({{"keep": [<numbers>]}}), then run: '
        f"python finding_papers.py --apply-verification")


def apply_verification(ledger, log=print):
    """Apply a Claude-Code verification result to `ledger` in place: drop every
    queued item whose number is NOT in the result's keep-list. Never drops a
    user-annotated row. Consumes the queue + result files. Returns a stats dict."""
    if not os.path.exists(QUEUE_PATH):
        log("  No verification queue found — nothing to apply.")
        return {}
    try:
        with open(QUEUE_PATH, encoding="utf-8") as f:
            queue = json.load(f)
    except Exception as e:  # noqa: BLE001
        log(f"  ! could not read {os.path.basename(QUEUE_PATH)} ({e})")
        return {}
    if not os.path.exists(RESULT_PATH):
        log(f"  {os.path.basename(RESULT_PATH)} not found — keeping all "
            f"{queue.get('count', 0)} queued items until it is written.")
        return {}
    try:
        with open(RESULT_PATH, encoding="utf-8") as f:
            result = json.load(f)
    except Exception as e:  # noqa: BLE001
        log(f"  ! could not read {os.path.basename(RESULT_PATH)} ({e})")
        return {}

    keep = {int(x) for x in result.get("keep", [])}
    dropped = kept = 0
    for it in queue.get("items", []):
        row = ledger.get(it.get("key"))
        if row is None:
            continue
        if any((row.get(c) or "").strip() for c in USER_COLS):
            kept += 1
            continue
        if it.get("n") in keep:
            kept += 1
        else:
            ledger.pop(it["key"], None)
            dropped += 1

    log(f"  Applied verification: dropped {dropped}, kept {kept} of "
        f"{queue.get('count', 0)} queued items.")
    for path in (QUEUE_PATH, RESULT_PATH):
        try:
            os.remove(path)
        except OSError:
            pass
    return {"dropped": dropped, "kept": kept}


# --------------------------------------------------------------------------- #
# Filter log (per-source noise tracking over time)
# --------------------------------------------------------------------------- #
def _append_filter_log(today, per_source, log):
    try:
        exists = os.path.exists(FILTER_LOG)
        with open(FILTER_LOG, "a", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FILTER_LOG_FIELDS)
            if not exists:
                w.writeheader()
            for src in sorted(per_source):
                s = per_source[src]
                w.writerow({"date": today, "source": src, **s})
    except Exception as e:  # noqa: BLE001 - logging must not kill the run
        log(f"    ! could not write filter_log.csv ({e})")


# --------------------------------------------------------------------------- #
# Entry point — called by finding_papers.py between merge() and trending_score()
# --------------------------------------------------------------------------- #
def filter_authentic_research(ledger, new_keys, cfg, today, log=print):
    """Drop non-authentic items from `ledger` IN PLACE.

    Only items whose keys are in `new_keys` (added this run) are candidates;
    pre-existing rows and any row with user-owned data are always kept.
    Returns a stats dict.
    """
    if not cfg.get("settings", {}).get("research_filter_enabled", True):
        return {}

    pending = []                 # [(key, row)] structural survivors needing LLM
    drop_keys = []               # keys to remove from the ledger
    kept_arxiv = 0
    structural_dropped = 0
    per_source = {}              # source -> counts

    def tally(src, field, n=1):
        s = per_source.setdefault(src, {"candidates": 0, "dropped_structural": 0,
                                        "dropped_llm": 0, "kept": 0})
        s[field] += n

    for key in list(new_keys):
        row = ledger.get(key)
        if row is None:
            continue
        # Defensive: never drop a row the user has annotated.
        if any((row.get(c) or "").strip() for c in USER_COLS):
            continue
        src = row.get("source") or "?"
        tally(src, "candidates")
        decision, _reason = _structural_verdict(row)
        if decision == "keep":
            kept_arxiv += 1
            tally(src, "kept")
        elif decision == "drop":
            drop_keys.append(key)
            structural_dropped += 1
            tally(src, "dropped_structural")
        else:  # 'llm'
            pending.append((key, row))

    # Layer 2: LLM verification of structural survivors lacking an arxiv_id.
    llm_kept = llm_dropped = llm_skipped = llm_queued = 0
    if pending:
        headers = _api_headers()
        if headers is None:
            # No API credential — hand off to Claude Code (Opus) via a queue file.
            _write_verify_queue(today, pending, log)
            llm_queued = len(pending)
            for _, r in pending:
                tally(r.get("source") or "?", "kept")
        else:
            keep_idx = _llm_keep_set([r for _, r in pending], headers, cfg, log)
            if keep_idx is None:                  # transient failure — keep them all
                llm_skipped = len(pending)
                for _, r in pending:
                    tally(r.get("source") or "?", "kept")
            else:
                for i, (key, r) in enumerate(pending):
                    src = r.get("source") or "?"
                    if i in keep_idx:
                        llm_kept += 1
                        tally(src, "kept")
                    else:
                        drop_keys.append(key)
                        llm_dropped += 1
                        tally(src, "dropped_llm")

    for key in drop_keys:
        ledger.pop(key, None)

    total_dropped = structural_dropped + llm_dropped
    extra = []
    if llm_queued:
        extra.append(f"{llm_queued} queued for Claude verify")
    if llm_skipped:
        extra.append(f"{llm_skipped} kept (LLM unavailable)")
    tail = (" · " + ", ".join(extra)) if extra else ""
    log(f"  Authenticity filter: {len(new_keys)} new candidates -> "
        f"{total_dropped} dropped ({structural_dropped} structural, "
        f"{llm_dropped} LLM) · {kept_arxiv} auto-kept (arxiv), "
        f"{llm_kept} LLM-kept{tail}")

    _append_filter_log(today, per_source, log)
    return {
        "candidates": len(new_keys), "kept_arxiv": kept_arxiv,
        "pending_llm": len(pending), "dropped_structural": structural_dropped,
        "llm_kept": llm_kept, "llm_dropped": llm_dropped,
        "llm_skipped": llm_skipped, "llm_queued": llm_queued,
    }
