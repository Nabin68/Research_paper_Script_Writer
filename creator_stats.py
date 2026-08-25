#!/usr/bin/env python3
"""
creator_stats.py — Daily creator-performance tracker (X/Twitter first).

Pulls recent posts from the accounts listed in creators.json via an Apify actor,
then appends ONE ROW PER POST PER DAY to creator_posts.csv. Because each day gets
its own snapshot, the run can diff against yesterday and report what actually
moved today (views_gained) instead of just lifetime totals.

Also extracts any arXiv / HF-papers IDs mentioned in a post and matches them
against papers.csv, so the sheet tells you which paper a post covered — and,
read the other way, which papers are getting traction before you script them.

Pure Python standard library. No pip installs.

Requires an Apify API token. Either:
    set APIFY_TOKEN=...            (environment variable)
or put this line in a .env file next to this script:
    APIFY_TOKEN=apify_api_xxxxxxxx

Usage:
    python creator_stats.py                 # fetch + snapshot today
    python creator_stats.py --date 2026-07-17   # stamp under a specific day
    python creator_stats.py --resort         # re-sort existing CSV, no fetching
    python creator_stats.py --check          # verify token + config, fetch nothing

Config lives in creators.json (edit that, not this file, to add accounts).
"""

import sys
import os
import re
import csv
import json
import time
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

try:  # keep emoji/unicode prints from crashing the scheduled task on legacy consoles
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "creators.json")
CSV_PATH = os.path.join(HERE, "creator_posts.csv")
PAPERS_PATH = os.path.join(HERE, "papers.csv")
ENV_PATH = os.path.join(HERE, ".env")

APIFY_BASE = "https://api.apify.com/v2"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) creator-stats/1.0"

# Columns you own. The script NEVER overwrites these — and it carries the most
# recent non-empty value forward onto each new daily snapshot of the same post,
# so you only ever fill them in once per post.
USER_COLS = ["topic", "my_notes"]

FIELDNAMES = [
    "snapshot_date", "platform", "creator", "handle", "post_id", "post_url",
    "posted_iso", "days_old", "caption", "arxiv_ids", "papers_covered",
    "views", "likes", "comments", "reposts", "quotes", "bookmarks", "engagement",
    "views_gained", "likes_gained", "transcript",
] + USER_COLS

ARXIV_RE = re.compile(r"(?:arxiv\.org/(?:abs|pdf)/|huggingface\.co/papers/)(\d{4}\.\d{4,5})", re.I)


# --------------------------------------------------------------------------- #
# Config / credentials
# --------------------------------------------------------------------------- #
def load_config():
    if not os.path.exists(CONFIG_PATH):
        die(f"missing config: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            die(f"creators.json is not valid JSON ({e}). Check commas and quotes.")


def load_token():
    """APIFY_TOKEN from the environment, falling back to a local .env file."""
    tok = os.environ.get("APIFY_TOKEN", "").strip()
    if tok:
        return tok
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                if key.strip() == "APIFY_TOKEN":
                    return val.strip().strip("'\"")
    return ""


def die(msg):
    print(f"ERROR: {msg}")
    sys.exit(1)


# --------------------------------------------------------------------------- #
# Apify
# --------------------------------------------------------------------------- #
def apify_post(path, token, payload, timeout=30):
    url = f"{APIFY_BASE}{path}?token={token}"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/json", "User-Agent": UA},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


def apify_get(path, token, timeout=60):
    url = f"{APIFY_BASE}{path}{'&' if '?' in path else '?'}token={token}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


def run_actor(actor_id, token, actor_input, poll_timeout):
    """Start an actor run, poll until it finishes, return its dataset items.

    Async rather than run-sync so a slow scrape doesn't drop the whole run on an
    HTTP timeout — X actors are routinely slow when an account has a long feed.
    """
    slug = actor_id.replace("/", "~")
    print(f"  starting actor {actor_id} ...")
    try:
        started = apify_post(f"/acts/{slug}/runs", token, actor_input)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        if e.code == 401:
            die("Apify rejected the token (401). Check APIFY_TOKEN.")
        if e.code == 404:
            die(f"Actor '{actor_id}' not found (404). Fix 'x_actor' in creators.json.")
        die(f"Apify returned HTTP {e.code}: {detail}")
    except Exception as e:  # noqa: BLE001
        die(f"could not reach Apify: {e}")

    run = started.get("data", {})
    run_id, dataset_id = run.get("id"), run.get("defaultDatasetId")
    if not run_id:
        die(f"Apify did not return a run id. Response: {str(started)[:300]}")

    deadline = time.time() + poll_timeout
    status = run.get("status", "READY")
    while status in ("READY", "RUNNING") and time.time() < deadline:
        time.sleep(5)
        try:
            info = apify_get(f"/actor-runs/{run_id}", token).get("data", {})
        except Exception as e:  # noqa: BLE001 - transient poll failure is not fatal
            print(f"    ! poll failed ({e}), retrying")
            continue
        status = info.get("status", status)
        dataset_id = info.get("defaultDatasetId", dataset_id)
        print(f"    status: {status}")

    if status != "SUCCEEDED":
        print(f"  ! run ended as {status} — falling back to whatever it did produce")

    try:
        items = apify_get(f"/datasets/{dataset_id}/items?format=json&clean=true", token)
    except Exception as e:  # noqa: BLE001
        print(f"  ! could not read dataset: {e}")
        return []
    return items if isinstance(items, list) else []


def build_x_input(handles, cfg):
    """Actor input for an X scraper.

    Field names differ between actors; these are the apidojo/tweet-scraper names,
    which most X actors mirror. If you swap actors and get zero results, this is
    the first place to look.
    """
    ap = cfg.get("apify", {})
    lookback = int(ap.get("lookback_days", 14))
    since = (datetime.now(timezone.utc) - timedelta(days=lookback)).strftime("%Y-%m-%d")
    return {
        "twitterHandles": handles,
        "maxItems": int(ap.get("max_items_per_run", 300)),
        "onlyVerifiedUsers": False,
        "sort": "Latest",
        "start": since,
    }


# --------------------------------------------------------------------------- #
# Normalising actor output
# --------------------------------------------------------------------------- #
def pick(d, *names, default=None):
    """First present, non-None value among several possible key spellings.

    Actors disagree on field names (likeCount vs favoriteCount vs favorite_count),
    and the same actor renames things between versions. Reading defensively costs
    nothing and stops a rename from silently zeroing a column.
    """
    for n in names:
        if isinstance(d, dict) and d.get(n) is not None:
            return d[n]
    return default


def to_int(v):
    if v is None:
        return 0
    if isinstance(v, (int, float)):
        return int(v)
    s = re.sub(r"[,\s]", "", str(v))
    m = re.match(r"^(\d+(?:\.\d+)?)([KMB])?$", s, re.I)
    if not m:
        return 0
    n = float(m.group(1))
    return int(n * {"k": 1e3, "m": 1e6, "b": 1e9}[m.group(2).lower()]) if m.group(2) else int(n)


def normalize_x_post(raw, name_by_handle):
    """Map one actor result onto our schema. Returns None if it isn't a usable post."""
    author = pick(raw, "author", "user", default={}) or {}
    handle = (pick(raw, "authorUsername", "username", "screen_name", default="")
              or pick(author, "userName", "username", "screen_name", default=""))
    handle = str(handle).lstrip("@")

    post_id = str(pick(raw, "id", "id_str", "tweetId", "conversationId", default="") or "")
    url = pick(raw, "url", "twitterUrl", "tweetUrl", default="") or ""
    if not post_id and url:
        m = re.search(r"/status/(\d+)", url)
        post_id = m.group(1) if m else ""
    if not post_id:
        return None
    if not url and handle:
        url = f"https://x.com/{handle}/status/{post_id}"

    text = str(pick(raw, "text", "full_text", "fullText", "content", default="") or "")
    posted = pick(raw, "createdAt", "created_at", "date", "timestamp", default="")
    posted_iso = parse_dt(posted)

    likes = to_int(pick(raw, "likeCount", "favoriteCount", "favorite_count", "likes"))
    reposts = to_int(pick(raw, "retweetCount", "retweet_count", "retweets"))
    replies = to_int(pick(raw, "replyCount", "reply_count", "replies"))
    quotes = to_int(pick(raw, "quoteCount", "quote_count", "quotes"))
    bookmarks = to_int(pick(raw, "bookmarkCount", "bookmark_count", "bookmarks"))
    views = to_int(pick(raw, "viewCount", "views", "view_count", "impressionCount"))

    return {
        "platform": "x",
        "creator": name_by_handle.get(handle.lower(), handle),
        "handle": handle,
        "post_id": post_id,
        "post_url": url,
        "posted_iso": posted_iso,
        "caption": re.sub(r"\s+", " ", text).strip(),
        "views": views,
        "likes": likes,
        "comments": replies,
        "reposts": reposts,
        "quotes": quotes,
        "bookmarks": bookmarks,
        "engagement": likes + reposts + replies + quotes + bookmarks,
        "transcript": "",  # text posts have no transcript; the caption IS the content
    }


def parse_dt(value):
    """Best-effort timestamp parse across the formats actors emit."""
    if not value:
        return ""
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), timezone.utc).isoformat()
        except Exception:  # noqa: BLE001
            return ""
    s = str(value).strip()
    try:  # ISO-8601, the common case
        return datetime.fromisoformat(s.replace("Z", "+00:00")).isoformat()
    except ValueError:
        pass
    for fmt in ("%a %b %d %H:%M:%S %z %Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.replace(tzinfo=dt.tzinfo or timezone.utc).isoformat()
        except ValueError:
            continue
    return ""


# --------------------------------------------------------------------------- #
# Paper matching
# --------------------------------------------------------------------------- #
def load_paper_titles():
    """{arxiv_id: title} from the existing papers.csv ledger."""
    titles = {}
    if not os.path.exists(PAPERS_PATH):
        return titles
    with open(PAPERS_PATH, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            aid = (row.get("arxiv_id") or "").strip()
            if aid:
                titles.setdefault(aid, (row.get("title") or "").strip())
    return titles


def attach_papers(post, titles):
    ids = sorted(set(ARXIV_RE.findall(post.get("caption", ""))))
    post["arxiv_ids"] = " ".join(ids)
    matched = [titles[i] for i in ids if titles.get(i)]
    post["papers_covered"] = " | ".join(matched)
    return post


# --------------------------------------------------------------------------- #
# Snapshot ledger
# --------------------------------------------------------------------------- #
def load_snapshots():
    if not os.path.exists(CSV_PATH):
        return []
    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def latest_prior(rows, today):
    """Most recent snapshot per post_id from BEFORE today — the delta baseline.

    Keyed on the newest prior date rather than literally yesterday so a skipped
    day produces a larger-but-correct delta instead of a bogus zero.
    """
    best = {}
    for r in rows:
        d = r.get("snapshot_date", "")
        if not d or d >= today:
            continue
        pid = r.get("post_id", "")
        if pid and (pid not in best or d > best[pid].get("snapshot_date", "")):
            best[pid] = r
    return best


def carried_user_cols(rows):
    """Newest non-empty value of each user column, per post_id."""
    out = {}
    for r in sorted(rows, key=lambda x: x.get("snapshot_date", "")):
        pid = r.get("post_id", "")
        if not pid:
            continue
        slot = out.setdefault(pid, {})
        for col in USER_COLS:
            if (r.get(col) or "").strip():
                slot[col] = r[col]
    return out


def days_since(posted_iso, today):
    if not posted_iso:
        return ""
    try:
        posted = datetime.fromisoformat(posted_iso).date()
        return max(0, (datetime.strptime(today, "%Y-%m-%d").date() - posted).days)
    except Exception:  # noqa: BLE001
        return ""


def write_ledger(rows):
    """Rewrite the whole CSV, newest day first and views-descending within each day."""
    rows.sort(
        key=lambda r: (r.get("snapshot_date", ""), to_int(r.get("views")), to_int(r.get("engagement"))),
        reverse=True,
    )
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return rows


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="Daily creator-performance snapshots (X).")
    ap.add_argument("--date", help="stamp the snapshot under this YYYY-MM-DD (default: today)")
    ap.add_argument("--resort", action="store_true", help="re-sort the existing CSV, fetch nothing")
    ap.add_argument("--check", action="store_true", help="verify token + config, fetch nothing")
    args = ap.parse_args()

    cfg = load_config()
    today = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if args.resort:
        existing = load_snapshots()
        if not existing:
            die(f"nothing to sort: {CSV_PATH} does not exist yet")
        write_ledger(existing)
        print(f"re-sorted {len(existing)} rows in creator_posts.csv")
        return

    accounts = cfg.get("x_accounts", [])
    handles = [a["handle"].lstrip("@") for a in accounts if a.get("handle")]
    name_by_handle = {a["handle"].lstrip("@").lower(): a.get("name") or a["handle"]
                      for a in accounts if a.get("handle")}
    if not handles:
        die("no x_accounts in creators.json")

    token = load_token()
    if args.check:
        print(f"config     : {len(handles)} X accounts -> {', '.join(handles)}")
        print(f"actor      : {cfg.get('apify', {}).get('x_actor')}")
        print(f"papers.csv : {len(load_paper_titles())} arXiv IDs available for matching")
        print(f"token      : {'found (' + token[:12] + '...)' if token else 'MISSING'}")
        if not token:
            print("\nSet it with:  set APIFY_TOKEN=apify_api_xxxx")
            print("or put APIFY_TOKEN=apify_api_xxxx in a .env file next to this script.")
        return

    if not token:
        die("no APIFY_TOKEN found. Run 'python creator_stats.py --check' for setup help.")

    print(f"creator_stats — {today}")
    print(f"  {len(handles)} X accounts: {', '.join(handles)}")

    apify_cfg = cfg.get("apify", {})
    items = run_actor(
        apify_cfg.get("x_actor", "apidojo/tweet-scraper"),
        token,
        build_x_input(handles, cfg),
        int(apify_cfg.get("poll_timeout_seconds", 420)),
    )
    print(f"  actor returned {len(items)} raw items")
    if not items:
        print("  nothing fetched — leaving creator_posts.csv untouched")
        return

    titles = load_paper_titles()
    tracked = {h.lower() for h in handles}
    posts, skipped = {}, 0
    for raw in items:
        p = normalize_x_post(raw, name_by_handle)
        if not p:
            skipped += 1
            continue
        if p["handle"].lower() not in tracked:  # actors often return replies/RTs from others
            skipped += 1
            continue
        posts[p["post_id"]] = attach_papers(p, titles)
    print(f"  {len(posts)} usable posts ({skipped} skipped: unparseable or off-list authors)")

    existing = load_snapshots()
    prior = latest_prior(existing, today)
    carried = carried_user_cols(existing)
    # Drop any rows already stamped today so a re-run replaces rather than duplicates.
    kept = [r for r in existing if r.get("snapshot_date") != today]

    fresh = []
    for pid, p in posts.items():
        row = dict(p)
        row["snapshot_date"] = today
        row["days_old"] = days_since(p["posted_iso"], today)
        base = prior.get(pid)
        row["views_gained"] = row["views"] - to_int(base.get("views")) if base else ""
        row["likes_gained"] = row["likes"] - to_int(base.get("likes")) if base else ""
        for col in USER_COLS:
            row[col] = carried.get(pid, {}).get(col, "")
        fresh.append(row)

    all_rows = write_ledger(kept + fresh)
    print(f"  wrote {len(fresh)} rows for {today} ({len(all_rows)} total in ledger)")
    if not prior:
        print("  note: first snapshot — views_gained fills in from tomorrow's run onward")

    top_n = int(cfg.get("settings", {}).get("console_top_n", 15))
    todays = [r for r in all_rows if r.get("snapshot_date") == today][:top_n]
    print(f"\n  Top {len(todays)} by views:")
    for i, r in enumerate(todays, 1):
        gained = r.get("views_gained")
        delta = f"  (+{gained} today)" if str(gained).strip() not in ("", "0") else ""
        paper = f"  [{r['papers_covered'][:45]}]" if r.get("papers_covered") else ""
        print(f"  {i:2}. {to_int(r['views']):>9,} views  @{r['handle']:<16}{delta}{paper}")
        print(f"      {r['caption'][:100]}")


if __name__ == "__main__":
    main()
