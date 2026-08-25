#!/usr/bin/env python3
"""
ScrapeX — trending AI research papers, ranked by what they're doing on X.

Reads the timelines of the paper-discovery accounts (alphaXiv, elvis/DAIR.AI, AK,
arXiv, ...) plus a set of full-site X searches, pulls every post that links a
paper, and scores each paper by the real reach of the posts carrying it — views,
likes, reposts, quotes, bookmarks — across every account that shared it.

Two ledgers, both deduped and both permanent:

  scrapex/posts.csv   one row per post, ever. Metrics are refreshed on each run
                      (a post keeps gaining views for days), never duplicated.
  scrapex/papers.csv  one row per paper, ever. Reach is re-aggregated from all
                      posts each run, so it only ever gets more accurate.

Each run writes scrapex/trending_<date>.md, and that report shows you a paper
ONCE. A paper appears in "new since last run" the first time it clears the reach
floor; after that it only comes back if it has grown enough to count as still
climbing. Nothing repeats run over run.

Scraping is done with twikit (https://github.com/d60/twikit), which talks to X's
internal API using a logged-in session. Unlike the rest of this project, this
script is NOT standard-library only:

    pip install twikit

It also needs an X account to log in as. Put these in the .env file next to this
script (already gitignored, same file that holds APIFY_TOKEN):

    X_USERNAME=your_handle
    X_EMAIL=you@example.com
    X_PASSWORD=your_password

The session cookie is cached in scrapex/cookies.json after the first run, so a
normal run does not log in again. Use a spare/burner account: X rate-limits and
occasionally challenges accounts that read a lot of timelines quickly.

Usage:
    python scrapex.py                  # fetch, score, write today's report
    python scrapex.py --check          # verify deps + creds + config, fetch nothing
    python scrapex.py --date 2026-07-20    # stamp the run under a specific day
    python scrapex.py --all            # report every paper over the floor, not just new
    python scrapex.py --rebuild        # re-score from stored posts, fetch nothing
    python scrapex.py --no-search      # accounts only, skip the full-site searches

Config lives in scrapex.json (edit that, not this file, to add accounts/queries).
"""

import sys
import os
import re
import csv
import json
import time
import asyncio
import argparse
import urllib.request
from datetime import datetime, timedelta, timezone

try:  # keep emoji/unicode prints from crashing on legacy Windows consoles
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "scrapex")
CONFIG_PATH = os.path.join(HERE, "scrapex.json")
POSTS_CSV = os.path.join(OUT_DIR, "posts.csv")
PAPERS_CSV = os.path.join(OUT_DIR, "papers.csv")
COOKIES_PATH = os.path.join(OUT_DIR, "cookies.json")
ENV_PATH = os.path.join(HERE, ".env")
MAIN_PAPERS_CSV = os.path.join(HERE, "papers.csv")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) scrapex/1.0 (research digest)"

# Columns you own on scrapex/papers.csv. The script NEVER overwrites these.
PAPER_USER_COLS = ["picked", "my_notes"]

POST_FIELDS = [
    "first_seen", "last_updated", "post_id", "post_url", "handle", "creator",
    "discovered_via", "found_by", "posted_iso", "text", "paper_keys",
    "views", "likes", "reposts", "replies", "quotes", "bookmarks",
    "engagement", "reach",
]

PAPER_FIELDS = [
    "first_seen", "last_updated", "paper_key", "kind", "paper_id", "title",
    "url", "reach_score", "trend_score", "post_count", "creator_count",
    "creators", "top_post_url", "top_post_views", "total_views", "total_likes",
    "total_reposts", "newest_post_iso", "in_main_ledger",
    "reported_on", "last_reported_reach",
] + PAPER_USER_COLS


# --------------------------------------------------------------------------- #
# Config / credentials
# --------------------------------------------------------------------------- #
def die(msg):
    print(f"ERROR: {msg}")
    sys.exit(1)


def load_config():
    if not os.path.exists(CONFIG_PATH):
        die(f"missing config: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            die(f"scrapex.json is not valid JSON ({e}). Check commas and quotes.")


def load_env():
    """X credentials from the environment, falling back to the local .env file.

    Accepts KEY=value and KEY:value. The colon form is not real .env syntax, but
    it is the obvious thing to type and silently yielding "credentials MISSING"
    over a punctuation choice is a bad way to spend someone's afternoon. Only the
    three keys below are matched, and only on the first separator, so a value
    containing ':' or '=' still comes through intact.
    """
    keys = ("X_USERNAME", "X_EMAIL", "X_PASSWORD", "X_AUTH_TOKEN", "X_CT0")
    # The cookie step says "copy auth_token and ct0", so those are the names people
    # paste in. Accept them as-is rather than failing over a prefix.
    aliases = {"auth_token": "X_AUTH_TOKEN", "ct0": "X_CT0"}
    creds = {k: os.environ.get(k, "").strip() for k in keys}
    if os.path.exists(ENV_PATH):
        # utf-8-sig so a BOM from Notepad does not glue itself to the first key.
        names = "|".join(list(keys) + list(aliases))
        with open(ENV_PATH, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                m = re.match(rf"^({names})\s*[:=]\s*(.*)$", line)
                if not m:
                    continue
                key = aliases.get(m.group(1), m.group(1))
                if not creds[key]:
                    creds[key] = m.group(2).strip().strip("'\"")
    creds["X_USERNAME"] = creds["X_USERNAME"].lstrip("@")  # login wants the bare handle
    return creds


# --------------------------------------------------------------------------- #
# Paper extraction
# --------------------------------------------------------------------------- #
# A "paper key" is "<kind>:<id>" — the stable identity we dedupe on. arXiv IDs
# are canonical, so an alphaXiv link and an HF-papers link to 2501.12345 collapse
# to the same paper instead of counting as three trending papers.
PAPER_PATTERNS = [
    ("arxiv", re.compile(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", re.I)),
    ("arxiv", re.compile(r"huggingface\.co/papers/(\d{4}\.\d{4,5})", re.I)),
    ("arxiv", re.compile(r"alphaxiv\.org/(?:abs|overview|pdf)/(\d{4}\.\d{4,5})", re.I)),
    ("arxiv", re.compile(r"\barxiv[:\s]+(\d{4}\.\d{4,5})\b", re.I)),
    ("openreview", re.compile(r"openreview\.net/(?:forum|pdf)\?id=([A-Za-z0-9_-]+)", re.I)),
]

# Version suffixes (2501.12345v2) must not split one paper into two.
VERSION_RE = re.compile(r"v\d+$", re.I)


def extract_paper_keys(text, urls):
    """Every distinct paper referenced by a post, from its text and link entities.

    X wraps links as t.co, so the raw text alone finds almost nothing — the
    entity list is where the real URLs live. We read both anyway: some accounts
    paste a bare "arXiv:2501.12345" with no link at all.
    """
    haystack = " ".join([text or ""] + [u for u in urls if u])
    keys = []
    for kind, pattern in PAPER_PATTERNS:
        for raw_id in pattern.findall(haystack):
            paper_id = VERSION_RE.sub("", raw_id) if kind == "arxiv" else raw_id
            key = f"{kind}:{paper_id}"
            if key not in keys:
                keys.append(key)
    return keys


def paper_url(key):
    kind, _, paper_id = key.partition(":")
    if kind == "arxiv":
        return f"https://arxiv.org/abs/{paper_id}"
    if kind == "openreview":
        return f"https://openreview.net/forum?id={paper_id}"
    return ""


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #
def to_int(v):
    if v is None or v == "":
        return 0
    if isinstance(v, (int, float)):
        return int(v)
    s = re.sub(r"[,\s]", "", str(v))
    m = re.match(r"^(\d+(?:\.\d+)?)([KMB])?$", s, re.I)
    if not m:
        return 0
    n = float(m.group(1))
    return int(n * {"k": 1e3, "m": 1e6, "b": 1e9}[m.group(2).lower()]) if m.group(2) else int(n)


def post_reach(post, weights):
    """One post's reach: exposure (views) plus engagement scaled onto the same axis.

    Engagement runs ~1-2% of views on a typical post, so without the multiplier a
    post with a million passive impressions would always outrank a post people
    actually saved and shared. Reposts/quotes/bookmarks are weighted over likes
    because they cost the reader more than a tap.
    """
    engagement = (
        to_int(post.get("likes")) * weights.get("like", 1)
        + to_int(post.get("replies")) * weights.get("reply", 1)
        + to_int(post.get("reposts")) * weights.get("repost", 2)
        + to_int(post.get("quotes")) * weights.get("quote", 2)
        + to_int(post.get("bookmarks")) * weights.get("bookmark", 2)
    )
    reach = to_int(post.get("views")) + engagement * weights.get("engagement_multiplier", 50)
    return engagement, int(reach)


def recency_multiplier(newest_iso, today, halflife_days):
    """Exponential decay on the newest post about a paper.

    A paper that pulled 2M reach three weeks ago is not 'trending' today, but its
    cumulative reach never shrinks — so ranking on raw reach would pin old papers
    to the top of every report forever. reach_score stays raw and comparable;
    trend_score is what the report sorts by.
    """
    if not newest_iso or halflife_days <= 0:
        return 1.0
    try:
        newest = datetime.fromisoformat(newest_iso)
        ref = datetime.strptime(today, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return 1.0
    if newest.tzinfo is None:
        newest = newest.replace(tzinfo=timezone.utc)
    age_days = max(0.0, (ref - newest).total_seconds() / 86400.0)
    return 0.5 ** (age_days / halflife_days)


# --------------------------------------------------------------------------- #
# Fetching (twikit)
# --------------------------------------------------------------------------- #
def import_twikit():
    try:
        from twikit import Client  # noqa: PLC0415
        from twikit.errors import TooManyRequests  # noqa: PLC0415
    except ImportError:
        die("twikit is not installed. Run:  pip install twikit")
    patch_ondemand_lookup()
    patch_missing_legacy_fields()
    return Client, TooManyRequests


class LenientDict(dict):
    """A dict whose missing keys read as an empty (falsy) LenientDict, recursively.

    X's GraphQL responses now omit fields that used to always be present, and omit
    different ones per account. twikit reads ~40 of them as legacy['field'], so a
    single absent key raises KeyError and loses the whole timeline. Wrapping the
    legacy blob makes an absent field read as empty instead of exploding — which is
    what it means. Nested dicts are wrapped on access so legacy['entities']['url']
    stays safe all the way down.
    """

    def __missing__(self, key):
        return LenientDict()

    def __getitem__(self, key):
        value = super().__getitem__(key) if key in self else LenientDict()
        return LenientDict(value) if type(value) is dict else value


def patch_missing_legacy_fields():
    """Stop one omitted field from costing us an entire timeline.

    Patched at runtime for the same reason as patch_ondemand_lookup: it survives a
    twikit upgrade, and it is additive — if X starts sending these fields again,
    or twikit switches to .get(), this quietly does nothing.
    """
    from twikit import user as user_mod  # noqa: PLC0415
    from twikit import tweet as tweet_mod  # noqa: PLC0415

    def wrap(cls):
        if getattr(cls, "_scrapex_patched", False):
            return
        original = cls.__init__

        def __init__(self, client, data, *args, **kwargs):
            if isinstance(data, dict) and isinstance(data.get("legacy"), dict):
                data = {**data, "legacy": LenientDict(data["legacy"])}
            original(self, client, data, *args, **kwargs)

        cls.__init__ = __init__
        cls._scrapex_patched = True

    wrap(user_mod.User)
    wrap(tweet_mod.Tweet)


ONDEMAND_CHUNK_RE = re.compile(r'(\d+)\s*:\s*"ondemand\.s"')


def patch_ondemand_lookup():
    """Repair twikit's ondemand.s lookup, which X's current bundle layout broke.

    To sign requests, twikit derives a transaction key from a script X ships as
    ondemand.s.<hash>a.js, and it finds that hash by regexing `"ondemand.s":"<hash>"`
    out of the home page. X's webpack manifest now splits that into two maps — chunk
    id to name (`59924:"ondemand.s"`) and chunk id to hash (`59924:"7fac826"`) — so
    the old pattern matches nothing and login dies on "Couldn't get KEY_BYTE indices".
    Only the lookup is stale; every step after it still works, so that is all we
    replace.

    Patched on the class at runtime rather than edited into site-packages, so a
    `pip install -U twikit` cannot silently revert it. Upstream is tried first: the
    day twikit fixes this, its own code wins and this becomes dead weight.
    """
    from twikit.x_client_transaction import transaction as tx  # noqa: PLC0415

    if getattr(tx.ClientTransaction, "_scrapex_patched", False):
        return
    original = tx.ClientTransaction.get_indices

    async def get_indices(self, home_page_response, session, headers):
        try:
            return await original(self, home_page_response, session, headers)
        except Exception:  # noqa: BLE001 - upstream is stale; fall through to ours
            pass

        page = str(self.validate_response(home_page_response) or self.home_page_response)
        match = ONDEMAND_CHUNK_RE.search(page)
        if not match:
            raise RuntimeError(
                "ScrapeX: no 'ondemand.s' chunk in X's home page. X changed its bundle "
                "again — the lookup in patch_ondemand_lookup() needs updating."
            )
        chunk_id = match.group(1)
        # The id appears twice: once against the name, once against the hash.
        hashes = [h for h in re.findall(rf'{chunk_id}\s*:\s*"([\w-]+)"', page)
                  if h != "ondemand.s"]

        for file_hash in hashes:
            url = ("https://abs.twimg.com/responsive-web/client-web/"
                   f"ondemand.s.{file_hash}a.js")
            try:
                resp = await session.request(method="GET", url=url, headers=headers)
                indices = [int(m.group(2)) for m in tx.INDICES_REGEX.finditer(str(resp.text))]
            except Exception:  # noqa: BLE001 - try the next candidate hash
                continue
            if indices:
                return indices[0], indices[1:]

        raise RuntimeError(
            "ScrapeX: found the ondemand.s chunk but could not read KEY_BYTE indices "
            "from it. X changed the script's shape; twikit needs an upstream fix."
        )

    tx.ClientTransaction.get_indices = get_indices
    tx.ClientTransaction._scrapex_patched = True


def parse_dt(value):
    """Best-effort timestamp parse. X emits 'Wed Oct 10 20:19:24 +0000 2018'."""
    if not value:
        return ""
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    s = str(value).strip()
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
    except ValueError:
        pass
    for fmt in ("%a %b %d %H:%M:%S %z %Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
            dt = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except ValueError:
            continue
    return ""


def tweet_urls(tweet):
    """Expanded URLs out of a tweet's entities, tolerating twikit's shape changes."""
    out = []
    for item in (getattr(tweet, "urls", None) or []):
        if isinstance(item, dict):
            url = item.get("expanded_url") or item.get("url") or item.get("unwound_url")
        else:
            url = str(item)
        if url:
            out.append(url)
    return out


def tweet_to_post(tweet, found_by, name_by_handle, weights):
    """Map a twikit Tweet onto our post schema. Returns None if it carries no paper.

    A retweet is unwrapped to the original: the metrics that matter belong to the
    post everyone actually saw, and unwrapping means five accounts RTing the same
    paper post collapse into one row instead of five near-duplicates. Who
    surfaced it is kept in discovered_via.
    """
    inner = getattr(tweet, "retweeted_tweet", None)
    via = ""
    if inner is not None:
        via = str(getattr(getattr(tweet, "user", None), "screen_name", "") or "")
        tweet = inner

    post_id = str(getattr(tweet, "id", "") or "")
    if not post_id:
        return None

    user = getattr(tweet, "user", None)
    handle = str(getattr(user, "screen_name", "") or "")
    text = str(getattr(tweet, "full_text", None) or getattr(tweet, "text", "") or "")
    urls = tweet_urls(tweet)

    keys = extract_paper_keys(text, urls)
    if not keys:
        return None

    posted = getattr(tweet, "created_at_datetime", None) or getattr(tweet, "created_at", "")

    post = {
        "post_id": post_id,
        "post_url": f"https://x.com/{handle}/status/{post_id}" if handle else "",
        "handle": handle,
        "creator": name_by_handle.get(handle.lower(), handle),
        "discovered_via": via,
        "found_by": found_by,
        "posted_iso": parse_dt(posted),
        "text": re.sub(r"\s+", " ", text).strip()[:400],
        "paper_keys": " ".join(keys),
        "views": to_int(getattr(tweet, "view_count", 0)),
        "likes": to_int(getattr(tweet, "favorite_count", 0)),
        "reposts": to_int(getattr(tweet, "retweet_count", 0)),
        "replies": to_int(getattr(tweet, "reply_count", 0)),
        "quotes": to_int(getattr(tweet, "quote_count", 0)),
        "bookmarks": to_int(getattr(tweet, "bookmark_count", 0)),
    }
    post["engagement"], post["reach"] = post_reach(post, weights)
    return post


async def paged(first_result, wanted, delay):
    """Walk a twikit Result through .next() until we have `wanted` tweets."""
    tweets = list(first_result or [])
    result = first_result
    while len(tweets) < wanted:
        try:
            result = await result.next()
        except Exception:  # noqa: BLE001 - end of feed, or X declined; keep what we have
            break
        page = list(result or [])
        if not page:
            break
        tweets.extend(page)
        await asyncio.sleep(delay)
    return tweets[:wanted]


async def collect(client, cfg, args, name_by_handle, too_many):
    """Every paper-carrying post from the configured accounts and searches."""
    settings = cfg.get("settings", {})
    weights = cfg.get("weights", {})
    delay = float(settings.get("request_delay_seconds", 3))
    cutoff = datetime.now(timezone.utc) - timedelta(days=int(settings.get("lookback_days", 14)))

    posts = {}

    def absorb(tweets, found_by):
        kept = 0
        for tweet in tweets:
            post = tweet_to_post(tweet, found_by, name_by_handle, weights)
            if not post:
                continue
            if post["posted_iso"]:
                try:
                    if datetime.fromisoformat(post["posted_iso"]) < cutoff:
                        continue
                except ValueError:
                    pass
            # Same post can arrive from several accounts (RTs) and from search.
            # Keep the first sighting's attribution, it is the earliest signal.
            if post["post_id"] not in posts:
                posts[post["post_id"]] = post
                kept += 1
        return kept

    accounts = cfg.get("x_accounts", [])
    per_account = int(settings.get("tweets_per_account", 40))
    print(f"\n  reading {len(accounts)} account timelines ...")
    for account in accounts:
        handle = str(account.get("handle", "")).lstrip("@")
        if not handle:
            continue
        try:
            user = await client.get_user_by_screen_name(handle)
            result = await client.get_user_tweets(user.id, "Tweets", count=per_account)
            tweets = await paged(result, per_account, delay)
        except too_many:
            print("    ! X rate-limited us — stopping timeline reads, keeping what we have")
            break
        except Exception as e:  # noqa: BLE001 - one bad handle must not kill the run
            print(f"    ! @{handle}: {e}")
            await asyncio.sleep(delay)
            continue
        kept = absorb(tweets, f"@{handle}")
        print(f"    @{handle:<18} {len(tweets):>3} tweets -> {kept} with papers")
        await asyncio.sleep(delay)

    queries = [] if args.no_search else cfg.get("search_queries", [])
    per_query = int(settings.get("tweets_per_query", 40))
    product = settings.get("search_product", "Top")
    if queries:
        ok = await patch_search_endpoint()
        print(f"\n  running {len(queries)} site-wide searches "
              f"({'live query id' if ok else 'WARNING: could not resolve query id'}) ...")
    for query in queries:
        try:
            result = await client.search_tweet(query, product, count=per_query)
            tweets = await paged(result, per_query, delay)
        except too_many:
            print("    ! X rate-limited us — stopping searches, keeping what we have")
            break
        except Exception as e:  # noqa: BLE001
            print(f"    ! search failed ({query[:40]}...): {e}")
            await asyncio.sleep(delay)
            continue
        kept = absorb(tweets, "search")
        print(f"    {len(tweets):>3} tweets -> {kept} with papers   [{query[:52]}]")
        await asyncio.sleep(delay)

    return posts


# --------------------------------------------------------------------------- #
# Titles
# --------------------------------------------------------------------------- #
def load_main_ledger_titles():
    """{arxiv_id: title} from the project's papers.csv — free titles, no request."""
    titles = {}
    if not os.path.exists(MAIN_PAPERS_CSV):
        return titles
    with open(MAIN_PAPERS_CSV, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            aid = VERSION_RE.sub("", (row.get("arxiv_id") or "").strip())
            title = (row.get("title") or "").strip()
            if aid and title:
                titles.setdefault(aid, title)
    return titles


ENTRY_RE = re.compile(r"<entry>(.*?)</entry>", re.S)
ENTRY_ID_RE = re.compile(r"<id>\s*https?://arxiv\.org/abs/(\d{4}\.\d{4,5})", re.I)
ENTRY_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)


def fetch_arxiv_titles(arxiv_ids, batch_size=40):
    """{arxiv_id: title} for a batch of IDs.

    arXiv's id_list takes a comma-separated list, so one request covers dozens of
    papers. That matters for more than speed: firing one request per paper gets
    the run throttled (arXiv asks for ~3s between calls) and silently returns
    empty titles. Best-effort throughout — a missing title is not worth failing a
    run over, it just shows up as the bare ID in the report.
    """
    titles = {}
    ids = [i for i in arxiv_ids if i]
    for start in range(0, len(ids), batch_size):
        batch = ids[start:start + batch_size]
        url = ("http://export.arxiv.org/api/query"
               f"?id_list={','.join(batch)}&max_results={len(batch)}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as resp:
                xml = resp.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            print(f"    ! arXiv title lookup failed: {e}")
            continue
        for entry in ENTRY_RE.findall(xml):
            id_match = ENTRY_ID_RE.search(entry)
            title_match = ENTRY_TITLE_RE.search(entry)
            if id_match and title_match:
                title = re.sub(r"\s+", " ", title_match.group(1)).strip()
                if title and title.lower() != "error":
                    titles[id_match.group(1)] = title
        if start + batch_size < len(ids):
            time.sleep(3)  # arXiv's stated rate limit between calls
    return titles


# --------------------------------------------------------------------------- #
# Ledgers
# --------------------------------------------------------------------------- #
def load_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, fieldnames, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def merge_posts(existing, fresh, today):
    """Fold this run's posts into the stored ones, keyed on post_id.

    A post already in the ledger has its metrics refreshed rather than appended —
    a post keeps gaining views for days, and we want the current number, not one
    row per sighting. first_seen is never rewritten.
    """
    by_id = {r.get("post_id", ""): dict(r) for r in existing if r.get("post_id")}
    new_count = 0
    for post_id, post in fresh.items():
        if post_id in by_id:
            row = by_id[post_id]
            row.update(post)  # refresh metrics + text
            row["last_updated"] = today
        else:
            row = dict(post)
            row["first_seen"] = today
            row["last_updated"] = today
            by_id[post_id] = row
            new_count += 1
    rows = sorted(by_id.values(), key=lambda r: to_int(r.get("reach")), reverse=True)
    return rows, new_count


def aggregate_papers(post_rows, existing_papers, cfg, today):
    """Rebuild every paper's totals from the full post ledger.

    Recomputed from scratch each run rather than incremented, so it is idempotent:
    re-running, back-filling a date, or retuning the weights all produce the same
    correct numbers instead of double-counting. Only the columns that are memory
    rather than measurement — first_seen, reported_on, and yours — carry over.
    """
    weights = cfg.get("weights", {})
    halflife = float(weights.get("halflife_days", 10))
    creator_bonus = float(weights.get("extra_creator_bonus", 0.25))

    prior = {r.get("paper_key", ""): r for r in existing_papers if r.get("paper_key")}
    main_titles = load_main_ledger_titles()

    buckets = {}
    for post in post_rows:
        for key in (post.get("paper_keys") or "").split():
            buckets.setdefault(key, []).append(post)

    papers = []
    for key, posts in buckets.items():
        kind, _, paper_id = key.partition(":")
        old = prior.get(key, {})

        creators = []
        for p in posts:
            handle = p.get("handle", "")
            if handle and handle not in creators:
                creators.append(handle)

        total_reach = sum(to_int(p.get("reach")) for p in posts)
        # Breadth beats one viral post: five accounts sharing a paper is a
        # stronger signal than one account getting lucky with the algorithm.
        reach_score = int(total_reach * (1 + creator_bonus * max(0, len(creators) - 1)))
        newest = max((p.get("posted_iso") or "" for p in posts), default="")
        top = max(posts, key=lambda p: to_int(p.get("reach")))

        title = (old.get("title") or "").strip() or main_titles.get(paper_id, "")

        papers.append({
            "first_seen": old.get("first_seen") or today,
            "last_updated": today,
            "paper_key": key,
            "kind": kind,
            "paper_id": paper_id,
            "title": title,
            "url": paper_url(key),
            "reach_score": reach_score,
            "trend_score": int(reach_score * recency_multiplier(newest, today, halflife)),
            "post_count": len(posts),
            "creator_count": len(creators),
            "creators": " ".join(creators),
            "top_post_url": top.get("post_url", ""),
            "top_post_views": to_int(top.get("views")),
            "total_views": sum(to_int(p.get("views")) for p in posts),
            "total_likes": sum(to_int(p.get("likes")) for p in posts),
            "total_reposts": sum(to_int(p.get("reposts")) for p in posts),
            "newest_post_iso": newest,
            "in_main_ledger": "YES" if paper_id in main_titles else "",
            "reported_on": old.get("reported_on", ""),
            "last_reported_reach": old.get("last_reported_reach", ""),
            **{col: old.get(col, "") for col in PAPER_USER_COLS},
        })

    papers.sort(key=lambda r: to_int(r.get("trend_score")), reverse=True)
    return papers


def split_for_report(papers, cfg, show_all):
    """Which papers today's report is allowed to show.

    This is the whole no-repeats rule. A paper is NEW exactly once — the first
    run where it clears the reach floor. After that it is only allowed back if it
    has grown by climb_threshold since the run that last showed it, so a paper
    that is merely still popular stays quiet.
    """
    settings = cfg.get("settings", {})
    floor = to_int(settings.get("min_reach_to_report", 5000))
    climb = float(settings.get("climb_threshold", 0.5))

    fresh, climbing = [], []
    for paper in papers:
        reach = to_int(paper.get("reach_score"))
        if reach < floor:
            continue
        if not paper.get("reported_on"):
            fresh.append(paper)
        elif show_all:
            climbing.append(paper)
        else:
            last = to_int(paper.get("last_reported_reach"))
            if last and reach >= last * (1 + climb):
                climbing.append(paper)
    return fresh, climbing


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def human(n):
    n = to_int(n)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def write_report(path, today, fresh, climbing, cfg, stats):
    top_n = int(cfg.get("settings", {}).get("report_top_n", 25))
    lines = [
        f"# Trending on X — {today}",
        "",
        f"_{stats['posts_new']} new posts this run · {stats['posts_total']} in the post ledger · "
        f"{stats['papers_total']} papers tracked all-time._",
        "",
    ]

    def block(paper, index):
        title = paper.get("title") or f"({paper['kind']} {paper['paper_id']} — title not resolved)"
        out = [
            f"### {index}. {title}",
            "",
            f"- **Reach:** {human(paper['reach_score'])} "
            f"· {human(paper['total_views'])} views · {human(paper['total_likes'])} likes "
            f"· {human(paper['total_reposts'])} reposts",
            f"- **Shared by:** {paper['post_count']} post(s) from "
            f"{paper['creator_count']} account(s) — {paper['creators'] or 'n/a'}",
            f"- **Paper:** {paper['url']}",
            f"- **Biggest post:** {paper['top_post_url']} ({human(paper['top_post_views'])} views)",
        ]
        if paper.get("in_main_ledger"):
            out.append("- _Already in papers.csv (agent 1 found it too)._")
        out.append("")
        return out

    lines += ["## New since last run", ""]
    if fresh:
        for i, paper in enumerate(fresh[:top_n], 1):
            lines += block(paper, i)
    else:
        lines += ["_Nothing new cleared the reach floor this run._", ""]

    lines += ["## Still climbing", ""]
    if climbing:
        lines += [
            "_Reported before, but reach has grown enough to be worth another look._",
            "",
        ]
        for i, paper in enumerate(climbing[:top_n], 1):
            lines += block(paper, i)
    else:
        lines += ["_Nothing previously reported has moved much._", ""]

    lines += [
        "---",
        "",
        "Full history: `scrapex/papers.csv` (one row per paper) and `scrapex/posts.csv` "
        "(one row per post). Mark `picked` / `my_notes` in `scrapex/papers.csv` — ScrapeX "
        "never overwrites those two columns.",
        "",
    ]

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
COOKIE_HOWTO = """  Use the cookie method — X blocks automated password logins, but accepts a
  session cookie from a browser you are already logged into:

    1. Open x.com in Chrome/Edge and log in as normal.
    2. Press F12 -> Application tab -> Storage -> Cookies -> https://x.com
    3. Copy the VALUE of two cookies: auth_token  and  ct0
    4. Put them in .env next to this script:

         X_AUTH_TOKEN=<the auth_token value>
         X_CT0=<the ct0 value>

    5. python scrapex.py

  These two cookies ARE the login session — treat them like a password. They are
  written to scrapex/cookies.json, which is gitignored. Logging out of X in that
  browser invalidates them, and you will need to copy them again."""


QUERY_ID_RE = re.compile(r'queryId:"([\w-]{16,})",operationName:"(\w+)"')
MAIN_JS_RE = re.compile(
    r'src="(https://abs\.twimg\.com/responsive-web/client-web/main\.[0-9a-f]+\.js)"')


async def patch_search_endpoint():
    """Point SearchTimeline at the query ID X's own web app is currently using.

    Every GraphQL operation is addressed by a rotating opaque ID. twikit 2.3.3 has
    'flaR-PUMshxFWZWPNpq4zA' baked in for SearchTimeline; X has since rotated it, so
    every search comes back 404 and we lose the site-wide queries — the part that
    finds papers from accounts outside the configured list.

    Rather than hardcode today's ID and be stale again next month, read it out of
    main.<hash>.js, which is where the web app keeps the operation table. Only
    SearchTimeline is repointed: the timeline endpoints still work, and a query ID
    has to agree with the feature flags twikit sends alongside it, so swapping an
    ID that is not actually broken risks trading a working call for a 400.

    Best-effort — on any failure the searches just stay broken and the account
    timelines, which are the main source, carry the run.
    """
    import httpx  # noqa: PLC0415 - twikit's own dependency, not a new one
    from twikit.client.gql import Endpoint  # noqa: PLC0415
    from twikit.x_client_transaction.utils import handle_x_migration  # noqa: PLC0415

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "User-Agent": UA,
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as session:
            page = str(await handle_x_migration(session, headers))
            match = MAIN_JS_RE.search(page)
            if not match:
                return False
            js = (await session.get(match.group(1), headers=headers)).text
    except Exception:  # noqa: BLE001
        return False

    query_ids = {op: qid for qid, op in QUERY_ID_RE.findall(js)}
    search_id = query_ids.get("SearchTimeline")
    if not search_id:
        return False
    Endpoint.SEARCH_TIMELINE = Endpoint.url(f"{search_id}/SearchTimeline")
    return True


def login_help(err):
    return (
        f"X login failed: {err}\n\n"
        f"{COOKIE_HOWTO}\n\n"
        "  (If you want to keep trying the password flow: username = handle without @,\n"
        "   and 2FA accounts need the TOTP secret, not the 6-digit code.)"
    )


async def run(args, cfg, today):
    Client, too_many = import_twikit()
    creds = load_env()

    accounts = cfg.get("x_accounts", [])
    name_by_handle = {
        str(a["handle"]).lstrip("@").lower(): a.get("name") or a["handle"]
        for a in accounts if a.get("handle")
    }

    client = Client("en-US")
    have_cookies = os.path.exists(COOKIES_PATH)
    if have_cookies:
        try:
            client.load_cookies(COOKIES_PATH)
            print("  session: reusing scrapex/cookies.json")
        except Exception as e:  # noqa: BLE001
            print(f"  ! stored cookies unusable ({e}) — logging in fresh")
            have_cookies = False

    # Preferred path: cookies lifted from a browser where you are already logged in.
    # X fronts its login endpoint with Cloudflare bot management, which blocks the
    # automated password flow outright on most connections — but the API endpoints
    # accept a session cookie fine. Handing over an existing session sidesteps the
    # part that is actually defended, and never sends the password anywhere.
    if not have_cookies and creds["X_AUTH_TOKEN"] and creds["X_CT0"]:
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(COOKIES_PATH, "w", encoding="utf-8") as f:
            json.dump({"auth_token": creds["X_AUTH_TOKEN"], "ct0": creds["X_CT0"]}, f)
        client.load_cookies(COOKIES_PATH)
        have_cookies = True
        print("  session: built from X_AUTH_TOKEN / X_CT0 in .env")

    if not have_cookies:
        if not (creds["X_USERNAME"] and creds["X_PASSWORD"]):
            die("no X session. Run 'python scrapex.py --check' for setup help.")
        print("  note: password login is usually blocked by X's bot protection.")
        print("        If it fails, use the cookie method — 'python scrapex.py --check'.")
        print(f"  session: logging in as @{creds['X_USERNAME']} ...")
        os.makedirs(OUT_DIR, exist_ok=True)

        async def attempt(ui_metrics):
            await client.login(
                auth_info_1=creds["X_USERNAME"],
                auth_info_2=creds["X_EMAIL"] or None,
                password=creds["X_PASSWORD"],
                cookies_file=COOKIES_PATH,
                enable_ui_metrics=ui_metrics,
            )

        try:
            await attempt(True)
        except Exception as first:  # noqa: BLE001
            # ui_metrics is an anti-bot token twikit builds by running X's JS through
            # Js2Py, which is fragile on new Python versions. Login works without it,
            # so it is worth one retry before giving up — but report both failures,
            # since the second error alone can be misleading.
            print(f"    login with ui_metrics failed ({first}) — retrying without it")
            try:
                await attempt(False)
            except Exception as second:  # noqa: BLE001
                die(login_help(f"{second}   [first attempt: {first}]"))

    return await collect(client, cfg, args, name_by_handle, too_many)


def do_check(cfg):
    creds = load_env()
    accounts = cfg.get("x_accounts", [])
    print("ScrapeX — setup check\n")

    try:
        import twikit  # noqa: F401,PLC0415
        print("  twikit      : installed")
    except ImportError:
        print("  twikit      : MISSING  ->  pip install twikit")

    print(f"  accounts    : {len(accounts)} -> {', '.join('@' + a['handle'] for a in accounts)}")
    print(f"  searches    : {len(cfg.get('search_queries', []))}")
    have_cookie_creds = bool(creds["X_AUTH_TOKEN"] and creds["X_CT0"])
    if os.path.exists(COOKIES_PATH):
        session = "found (no login needed)"
    elif have_cookie_creds:
        session = "will be built from X_AUTH_TOKEN / X_CT0"
    else:
        session = "none yet"
    print(f"  session     : {session}")
    print(f"  cookie auth : {'X_AUTH_TOKEN + X_CT0 found  <- recommended' if have_cookie_creds else 'not set'}")
    have = creds["X_USERNAME"] and creds["X_PASSWORD"]
    print(f"  password    : {'found (@' + creds['X_USERNAME'] + ') — usually blocked by X' if have else 'not set'}")
    print(f"  post ledger : {len(load_csv(POSTS_CSV))} posts stored")
    print(f"  paper ledger: {len(load_csv(PAPERS_CSV))} papers stored")
    print(f"  main ledger : {len(load_main_ledger_titles())} arXiv titles available for matching")

    if not have_cookie_creds and not os.path.exists(COOKIES_PATH):
        print()
        print(COOKIE_HOWTO)


def main():
    ap = argparse.ArgumentParser(description="Trending AI papers, ranked by reach on X.")
    ap.add_argument("--date", help="stamp this run under this YYYY-MM-DD (default: today)")
    ap.add_argument("--check", action="store_true", help="verify deps + creds + config, fetch nothing")
    ap.add_argument("--rebuild", action="store_true", help="re-score from stored posts, fetch nothing")
    ap.add_argument("--all", action="store_true", help="report every paper over the floor, not just new ones")
    ap.add_argument("--no-search", action="store_true", help="accounts only, skip the site-wide searches")
    args = ap.parse_args()

    cfg = load_config()
    today = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if args.check:
        do_check(cfg)
        return

    print(f"ScrapeX — {today}")

    existing_posts = load_csv(POSTS_CSV)
    if args.rebuild:
        if not existing_posts:
            die(f"nothing to rebuild from: {POSTS_CSV} does not exist yet")
        # Recompute each post's reach from the stored raw metrics, so a rebuild
        # after retuning scrapex.json -> weights actually reflects the new weights.
        post_rows, new_posts = existing_posts, 0
        for row in post_rows:
            row["engagement"], row["reach"] = post_reach(row, cfg.get("weights", {}))
        write_csv(POSTS_CSV, POST_FIELDS, post_rows)
        print(f"  rebuild: re-scored {len(post_rows)} stored posts, fetched nothing")
    else:
        fresh_posts = asyncio.run(run(args, cfg, today))
        print(f"\n  {len(fresh_posts)} paper-carrying posts this run")
        if not fresh_posts and not existing_posts:
            print("  nothing fetched and nothing stored — leaving the ledgers alone")
            return
        post_rows, new_posts = merge_posts(existing_posts, fresh_posts, today)
        write_csv(POSTS_CSV, POST_FIELDS, post_rows)
        print(f"  posts.csv : {new_posts} new, {len(post_rows)} total")

    papers = aggregate_papers(post_rows, load_csv(PAPERS_CSV), cfg, today)

    if cfg.get("settings", {}).get("resolve_titles", True):
        missing = [p for p in papers if not p["title"] and p["kind"] == "arxiv"]
        if missing:
            print(f"  resolving {len(missing)} paper titles from arXiv ...")
            resolved = fetch_arxiv_titles([p["paper_id"] for p in missing])
            for paper in missing:
                paper["title"] = resolved.get(paper["paper_id"], "")
            print(f"    resolved {len(resolved)}/{len(missing)}")

    fresh, climbing = split_for_report(papers, cfg, args.all)

    report_path = os.path.join(OUT_DIR, f"trending_{today}.md")
    write_report(report_path, today, fresh, climbing, cfg, {
        "posts_new": new_posts,
        "posts_total": len(post_rows),
        "papers_total": len(papers),
    })

    # Stamp only what was actually shown, so a paper held back by the reach floor
    # still gets its turn in the "new" section on a later run.
    shown = {p["paper_key"] for p in fresh + climbing}
    for paper in papers:
        if paper["paper_key"] in shown:
            paper["reported_on"] = today
            paper["last_reported_reach"] = paper["reach_score"]
    write_csv(PAPERS_CSV, PAPER_FIELDS, papers)

    print(f"  papers.csv: {len(papers)} tracked")
    print(f"  report    : scrapex/trending_{today}.md "
          f"({len(fresh)} new, {len(climbing)} climbing)")

    if fresh:
        print("\n  New since last run:")
        for i, paper in enumerate(fresh[:10], 1):
            title = paper["title"] or f"{paper['kind']}:{paper['paper_id']}"
            print(f"  {i:2}. {human(paper['reach_score']):>7} reach  "
                  f"{paper['creator_count']}x shared  {title[:70]}")
    else:
        print("\n  No new papers cleared the reach floor "
              f"({to_int(cfg.get('settings', {}).get('min_reach_to_report'))}). "
              "Lower min_reach_to_report in scrapex.json to loosen it.")


if __name__ == "__main__":
    main()
