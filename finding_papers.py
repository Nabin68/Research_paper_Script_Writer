#!/usr/bin/env python3
"""
finding_papers.py — Daily AI research paper digest.

Gathers new AI papers from big-lab blogs + arXiv, layers in community trending
signals (Hugging Face Daily Papers upvotes, Reddit r/ML, GitHub Trending), then:
  * updates papers.csv        -> the master running ledger (non-destructive)
  * writes digests/digest_<date>.md -> a human-readable daily digest

Pure Python standard library. No pip installs.

Usage:
    python finding_papers.py            # run once for today
    python finding_papers.py --once     # same (explicit)
    python finding_papers.py --date 2026-07-13   # backfill a specific day

Config lives in sources.json (edit that, not this file, to add sources).
"""

import sys
import os
import re
import csv
import json
import html
import time
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

try:  # keep emoji/unicode prints from crashing the scheduled task on legacy consoles
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES_PATH = os.path.join(HERE, "sources.json")
CSV_PATH = os.path.join(HERE, "papers.csv")
DIGEST_DIR = os.path.join(HERE, "digests")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) finding-papers/1.0 (research digest)"

# Columns the user owns. The script NEVER overwrites these on an existing row.
USER_COLS = ["picked", "my_notes", "performance"]

FIELDNAMES = [
    "first_seen", "last_updated", "source", "lab", "title", "authors", "url",
    "arxiv_id", "hf_upvotes", "hf_comments", "reddit_mentions", "github_stars",
    "trending_score", "category", "summary", "published_iso",
] + USER_COLS

# Labs that get a small "from a big lab" score bonus.
BIG_LAB_KEYWORDS = {
    "anthropic": "Anthropic", "openai": "OpenAI", "deepmind": "Google DeepMind",
    "google research": "Google Research", "google brain": "Google", "google": "Google",
    "meta ai": "Meta AI", "fair": "Meta AI", "facebook ai": "Meta AI", "meta": "Meta",
    "microsoft research": "Microsoft Research", "microsoft": "Microsoft",
    "nvidia": "NVIDIA", "mistral": "Mistral AI", "deepseek": "DeepSeek",
    "alibaba": "Alibaba", "qwen": "Qwen", "xai": "xAI", "cohere": "Cohere",
    "stability ai": "Stability AI", "allen institute": "AI2", "ai2": "AI2",
}


# --------------------------------------------------------------------------- #
# HTTP helper
# --------------------------------------------------------------------------- #
def http_get(url, as_json=False, timeout=25, retries=1):
    """Fetch a URL. Returns decoded text (or parsed json), or None on failure."""
    last_err = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
            if as_json:
                return json.loads(raw.decode("utf-8", "replace"))
            return raw.decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001 - one bad source must not kill the run
            last_err = e
            if attempt < retries:
                time.sleep(1.5)
    print(f"    ! fetch failed: {url}  ({last_err})")
    return None


def strip_tags(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def now_utc():
    return datetime.now(timezone.utc)


def parse_date_any(value):
    """Best-effort parse of RFC822 or ISO8601 dates -> aware datetime (UTC)."""
    if not value:
        return None
    value = value.strip()
    try:
        dt = parsedate_to_datetime(value)
        if dt is not None:
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        pass
    try:
        iso = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# Item model
# --------------------------------------------------------------------------- #
def new_item(**kw):
    item = {
        "source": "", "lab": "community", "title": "", "authors": "", "url": "",
        "arxiv_id": "", "hf_upvotes": 0, "hf_comments": 0, "reddit_mentions": 0,
        "github_stars": 0, "category": "paper", "summary": "", "published": None,
    }
    item.update(kw)
    return item


ARXIV_RE = re.compile(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", re.I)


def detect_lab(*texts, default="community"):
    """Detect a big-lab affiliation from any of the given text blobs."""
    blob = " ".join(t for t in texts if t).lower()
    # Check longer/more-specific keys first so 'google research' wins over 'google'.
    for key in sorted(BIG_LAB_KEYWORDS, key=len, reverse=True):
        if re.search(r"\b" + re.escape(key) + r"\b", blob):
            return BIG_LAB_KEYWORDS[key]
    return default


def is_big_lab(lab):
    return bool(lab) and lab.lower() != "community"


# --------------------------------------------------------------------------- #
# Sources
# --------------------------------------------------------------------------- #
def fetch_hf_papers(cfg):
    """Hugging Face Daily Papers — the primary trending signal (upvotes)."""
    out = []
    lookback = int(cfg.get("settings", {}).get("hf_lookback_days", 3))
    for i in range(lookback):
        day = (now_utc() - timedelta(days=i)).strftime("%Y-%m-%d")
        data = http_get(f"https://huggingface.co/api/daily_papers?date={day}&limit=100",
                        as_json=True)
        if not data:
            continue
        for entry in data:
            p = entry.get("paper", entry) or {}
            aid = p.get("id", "")
            authors = ", ".join(a.get("name", "") for a in p.get("authors", []) if a.get("name"))
            org = (p.get("organization") or {}).get("fullname", "")
            lab = detect_lab(org, authors, p.get("title", ""), p.get("summary", ""))
            out.append(new_item(
                source="huggingface", lab=lab, title=p.get("title", "").strip(),
                authors=authors, url=f"https://huggingface.co/papers/{aid}" if aid else "",
                arxiv_id=aid, hf_upvotes=int(p.get("upvotes") or 0),
                hf_comments=int(entry.get("numComments") or p.get("numComments") or 0),
                category="paper", summary=strip_tags(p.get("summary", "")),
                published=parse_date_any(p.get("publishedAt")),
            ))
    print(f"  HuggingFace: {len(out)} paper-days")
    return out


def fetch_arxiv(cfg):
    """Recent arXiv papers in the configured categories."""
    out = []
    s = cfg.get("settings", {})
    cats = cfg.get("arxiv_categories", [])
    maxn = int(s.get("arxiv_max_per_category", 60))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for cat in cats:
        url = ("http://export.arxiv.org/api/query?search_query=cat:" + cat +
               "&sortBy=submittedDate&sortOrder=descending&max_results=" + str(maxn))
        xml = http_get(url)
        if not xml:
            continue
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            continue
        for e in root.findall("a:entry", ns):
            aid_url = (e.findtext("a:id", "", ns) or "")
            m = re.search(r"abs/(\d{4}\.\d{4,5})", aid_url)
            aid = m.group(1) if m else ""
            title = strip_tags(e.findtext("a:title", "", ns))
            summary = strip_tags(e.findtext("a:summary", "", ns))
            authors = ", ".join(strip_tags(a.findtext("a:name", "", ns))
                                for a in e.findall("a:author", ns))
            lab = detect_lab(authors, summary, title)
            # Keep only big-lab-authored papers here; community trending arrives
            # via Hugging Face / Reddit. This keeps the ledger focused, not flooded.
            if not is_big_lab(lab):
                continue
            out.append(new_item(
                source="arxiv", lab=lab, title=title, authors=authors,
                url=f"https://arxiv.org/abs/{aid}" if aid else aid_url,
                arxiv_id=aid, category="paper", summary=summary,
                published=parse_date_any(e.findtext("a:published", "", ns)),
            ))
        time.sleep(1)  # be polite to arXiv
    print(f"  arXiv (big-lab only): {len(out)} papers")
    return out


def _parse_feed(xml, lab, source):
    """Parse an RSS 2.0 or Atom feed into blog items."""
    out = []
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return out

    def tag(el):
        return el.tag.split("}")[-1]

    # RSS: channel/item ; Atom: feed/entry
    items = [el for el in root.iter() if tag(el) in ("item", "entry")]
    for it in items:
        title, link, summary, pub = "", "", "", None
        for child in it:
            t = tag(child)
            if t == "title":
                title = strip_tags(child.text or "")
            elif t == "link":
                href = child.get("href")
                link = href if href else (child.text or link)
            elif t in ("description", "summary", "content"):
                summary = summary or strip_tags(child.text or "")
            elif t in ("pubDate", "published", "updated"):
                pub = pub or parse_date_any(child.text or "")
        if title:
            out.append(new_item(
                source=source, lab=lab, title=title, url=link.strip(),
                category="blog", summary=summary[:600], published=pub,
            ))
    return out


def fetch_rss_feeds(cfg):
    """Lab blog RSS. Feeds carry their full archive, so keep only recent posts."""
    out = []
    lookback = int(cfg.get("settings", {}).get("blog_lookback_days", 21))
    cutoff = now_utc() - timedelta(days=lookback)
    for feed in cfg.get("rss_feeds", []):
        xml = http_get(feed["url"])
        if not xml:
            continue
        for item in _parse_feed(xml, feed.get("lab", "community"), "blog"):
            pub = item.get("published")
            if isinstance(pub, datetime) and pub >= cutoff:
                out.append(item)
    print(f"  Lab RSS feeds (last {lookback}d): {len(out)} posts")
    return out


_MONTHS = "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
_CATS = ("Announcements|Product|Case Study|Policy|Research|Company|Interpretability|"
         "Societal Impacts|Alignment|Event|Feature")


def strip_card_prefix(t):
    """Remove a leading 'Jul 9, 2026' date and/or 'Announcements' category label
    that some card-style news pages prepend to the linked headline."""
    for _ in range(2):  # date and category can appear in either order
        t = re.sub(rf"^(?:{_MONTHS})[a-z]*\s+\d{{1,2}},\s*\d{{4}}\s*", "", t, flags=re.I)
        t = re.sub(rf"^(?:{_CATS})\s+", "", t, flags=re.I)
    return t.strip()


def fetch_scrape_pages(cfg):
    """Scrape lab news pages that have no RSS (Anthropic, Meta AI)."""
    out = []
    for page in cfg.get("scrape_pages", []):
        base = page["url"].rstrip("/")
        html_text = http_get(page["url"])
        if not html_text:
            continue
        root_m = re.match(r"(https?://[^/]+)", base)
        root = root_m.group(1) if root_m else ""
        m = re.search(r"https?://[^/]+(/[^/]+)", base)
        prefix = m.group(1) if m else "/news"  # e.g. /news or /blog
        seen = set()
        # Match hrefs to <prefix>/<slug>, whether relative or absolute; grab inner text.
        pat = (r'<a[^>]+href="(?:' + re.escape(root) + r')?(' + re.escape(prefix) +
               r'/[a-z0-9\-]+)/?"[^>]*>(.*?)</a>')
        for am in re.finditer(pat, html_text, re.I | re.S):
            href, inner = am.group(1), strip_tags(am.group(2))
            slug = href.rstrip("/").split("/")[-1]
            if not slug or slug in seen or len(slug) < 4:
                continue
            seen.add(slug)
            # Anchor text is often junk on these pages (generic labels, or a whole
            # card with category+date concatenated). Fall back to the slug when so.
            inner = strip_card_prefix(inner)
            bad = re.fullmatch(r"(learn|read|watch|see) more|read the article",
                               inner.strip(), re.I) is not None
            title = inner if (11 <= len(inner) <= 110 and not bad) \
                else slug.replace("-", " ").title()
            out.append(new_item(
                source="blog", lab=page.get("lab", "community"),
                title=title, url=root + href, category="blog", published=now_utc(),
            ))
        if len(seen) == 0:
            print(f"    ! no article links parsed from {page['url']}")
    print(f"  Scraped lab pages: {len(out)} posts")
    return out


def fetch_reddit(cfg):
    """Reddit r/<sub> top-of-day via .rss (JSON endpoint is blocked).

    Returns (community_items, arxiv_mention_counts).
    Reddit posts that link to an arXiv paper bump that paper's reddit_mentions.
    """
    items, mentions = [], {}
    for idx, sub in enumerate(cfg.get("subreddits", [])):
        if idx:
            time.sleep(3)  # Reddit rate-limits rapid requests (429)
        xml = http_get(f"https://www.reddit.com/r/{sub}/top/.rss?t=day", retries=2)
        if not xml:
            continue
        posts = _parse_feed(xml, "community", "reddit")
        for p in posts:
            blob = p["title"] + " " + p["summary"] + " " + p["url"]
            found = set(ARXIV_RE.findall(blob))
            for aid in found:
                mentions[aid] = mentions.get(aid, 0) + 1
            p["category"] = "discussion"
            p["reddit_mentions"] = 1
            items.append(p)
    print(f"  Reddit: {len(items)} posts, {len(mentions)} arXiv mentions")
    return items, mentions


def fetch_github_trending(cfg):
    """GitHub Trending (daily), filtered to AI-relevant repos."""
    out = []
    ai_kw = re.compile(
        r"\b(ai|ml|llm|model|neural|transformer|diffusion|agent|gpt|"
        r"rag|deep learning|machine learning|inference|embedding|dataset)\b", re.I)
    html_text = http_get("https://github.com/trending?since=daily")
    if not html_text:
        print("  GitHub trending: 0 repos")
        return out
    rows = re.split(r'<article class="Box-row">', html_text)[1:]
    for row in rows:
        m = re.search(r'<h2[^>]*>\s*<a[^>]+href="/([^"/]+)/([^"/?]+)"', row)
        if not m:
            continue
        owner, repo = m.group(1), m.group(2)
        desc_m = re.search(r'<p class="col-9[^"]*">(.*?)</p>', row, re.S)
        desc = strip_tags(desc_m.group(1)) if desc_m else ""
        stars_m = re.search(r'([\d,]+)\s*stars today', row)
        stars_today = int(stars_m.group(1).replace(",", "")) if stars_m else 0
        blob = f"{owner} {repo} {desc}"
        if not ai_kw.search(blob):
            continue
        out.append(new_item(
            source="github", lab="community", title=f"{owner}/{repo}",
            url=f"https://github.com/{owner}/{repo}", github_stars=stars_today,
            category="repo", summary=desc,
        ))
    print(f"  GitHub trending: {len(out)} AI repos")
    return out


# --------------------------------------------------------------------------- #
# Merge / dedupe / score
# --------------------------------------------------------------------------- #
def norm_title(t):
    return re.sub(r"[^a-z0-9]+", "", (t or "").lower())


def dedupe_key(item):
    if item.get("arxiv_id"):
        return "arxiv:" + item["arxiv_id"]
    url = (item.get("url") or "").split("?")[0].rstrip("/").lower()
    if url:
        return "url:" + url
    return "title:" + norm_title(item.get("title", ""))


def trending_score(row):
    """Transparent 0-100 blend. Edit the weights here to retune."""
    up = int(row.get("hf_upvotes") or 0)
    red = int(row.get("reddit_mentions") or 0)
    stars = int(row.get("github_stars") or 0)
    lab_bonus = 10 if is_big_lab(row.get("lab")) else 0
    raw = up * 3 + red * 6 + stars * 0.2 + lab_bonus

    pub = parse_date_any(row.get("published_iso") or "")
    if pub:
        age = (now_utc() - pub).days
        recency = (1.0 if age <= 1 else 0.85 if age <= 3 else 0.6 if age <= 7
                   else 0.4 if age <= 14 else 0.25)
    else:
        recency = 0.6
    return int(min(100, round(raw * recency)))


def load_existing():
    """Return {key: row} from the current CSV ledger."""
    rows = {}
    if not os.path.exists(CSV_PATH):
        return rows
    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            rows[dedupe_key(r)] = r
    return rows


def merge(ledger, item, today, reddit_mentions):
    """Fold one fetched item into the ledger dict (non-destructive on user cols)."""
    key = dedupe_key(item)
    aid = item.get("arxiv_id", "")
    extra_red = reddit_mentions.get(aid, 0) if aid else 0
    red = max(int(item.get("reddit_mentions") or 0), extra_red)
    pub = item.get("published")
    pub_iso = pub.isoformat() if isinstance(pub, datetime) else ""

    if key in ledger:
        row = ledger[key]
        # refresh objective metrics (take the stronger signal)
        row["hf_upvotes"] = max(int(row.get("hf_upvotes") or 0), int(item.get("hf_upvotes") or 0))
        row["hf_comments"] = max(int(row.get("hf_comments") or 0), int(item.get("hf_comments") or 0))
        row["reddit_mentions"] = max(int(row.get("reddit_mentions") or 0), red)
        row["github_stars"] = max(int(row.get("github_stars") or 0), int(item.get("github_stars") or 0))
        # upgrade lab from 'community' if a better one appears
        if not is_big_lab(row.get("lab")) and is_big_lab(item.get("lab")):
            row["lab"] = item["lab"]
        # merge source tags
        srcs = set(filter(None, (row.get("source") or "").split("+"))) | {item["source"]}
        row["source"] = "+".join(sorted(srcs))
        if not row.get("summary") and item.get("summary"):
            row["summary"] = item["summary"]
        if not row.get("authors") and item.get("authors"):
            row["authors"] = item["authors"]
        row["last_updated"] = today
        row["published_iso"] = row.get("published_iso") or pub_iso
    else:
        ledger[key] = {
            "first_seen": today, "last_updated": today, "source": item["source"],
            "lab": item["lab"], "title": item["title"], "authors": item["authors"],
            "url": item["url"], "arxiv_id": aid, "hf_upvotes": int(item["hf_upvotes"]),
            "hf_comments": int(item["hf_comments"]), "reddit_mentions": red,
            "github_stars": int(item["github_stars"]), "category": item["category"],
            "summary": item["summary"], "picked": "", "my_notes": "", "performance": "",
            "published_iso": pub_iso,
        }


def write_ledger(ledger):
    rows = list(ledger.values())
    for r in rows:
        r["trending_score"] = trending_score(r)
    # Sort by fetch-date (newest day first), then popularity within that day —
    # so each day's most-trending paper sits at the top of its block.
    rows.sort(key=lambda r: (r.get("first_seen", ""), int(r.get("trending_score") or 0)),
              reverse=True)
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return rows


# --------------------------------------------------------------------------- #
# Digest
# --------------------------------------------------------------------------- #
def write_digest(rows, today, cfg):
    os.makedirs(DIGEST_DIR, exist_ok=True)
    top_n = int(cfg.get("settings", {}).get("digest_top_n", 25))
    # "Fresh" = discovered today. Items appear in the digest once (the day found);
    # their metrics keep updating in the ledger on later runs.
    fresh = [r for r in rows if r.get("first_seen") == today]

    def line(r):
        bits = []
        if int(r.get("hf_upvotes") or 0):
            bits.append(f"👍 {r['hf_upvotes']} HF")
        if int(r.get("reddit_mentions") or 0):
            bits.append(f"💬 {r['reddit_mentions']} Reddit")
        if int(r.get("github_stars") or 0):
            bits.append(f"⭐ {r['github_stars']}/day")
        metrics = " · ".join(bits)
        lab = r.get("lab", "community")
        summ = (r.get("summary") or "").strip()
        summ = (summ[:200] + "…") if len(summ) > 200 else summ
        head = f"- **[{r['title']}]({r['url']})** — *{lab}* · score **{r['trending_score']}**"
        if metrics:
            head += f" · {metrics}"
        return head + (f"\n  {summ}" if summ else "")

    trending = sorted([r for r in fresh if r.get("category") in ("paper", "discussion")],
                      key=lambda r: int(r.get("trending_score") or 0), reverse=True)[:top_n]
    labs = sorted([r for r in fresh if is_big_lab(r.get("lab")) and r.get("category") in ("blog", "paper")],
                  key=lambda r: int(r.get("trending_score") or 0), reverse=True)
    repos = sorted([r for r in fresh if r.get("category") == "repo"],
                   key=lambda r: int(r.get("github_stars") or 0), reverse=True)

    out = [f"# AI Research Digest — {today}", ""]
    out.append(f"_{len(fresh)} newly found today. Full running history in `papers.csv`._")
    out += ["", "## 🔥 Trending today", ""]
    out += [line(r) for r in trending] or ["_Nothing trending picked up today._"]
    out += ["", "## 🏢 From the big labs", ""]
    out += [line(r) for r in labs] or ["_No big-lab posts/papers detected today._"]
    out += ["", "## 💻 Trending AI repos", ""]
    out += [line(r) for r in repos] or ["_No trending AI repos today._"]
    out += ["", "---", "_Generated by finding_papers.py_"]

    path = os.path.join(DIGEST_DIR, f"digest_{today}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    return path


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="run one pull (default)")
    ap.add_argument("--date", help="YYYY-MM-DD label for this run (default: today)")
    args = ap.parse_args()

    if not os.path.exists(SOURCES_PATH):
        sys.exit(f"Missing config: {SOURCES_PATH}")
    with open(SOURCES_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    today = args.date or datetime.now().strftime("%Y-%m-%d")
    print(f"== Finding Papers — run for {today} ==")

    print("Fetching sources...")
    hf = fetch_hf_papers(cfg)
    arxiv = fetch_arxiv(cfg)
    rss = fetch_rss_feeds(cfg)
    scraped = fetch_scrape_pages(cfg)
    reddit_items, reddit_mentions = fetch_reddit(cfg)
    repos = fetch_github_trending(cfg)

    ledger = load_existing()
    before = len(ledger)

    # Order matters a little: papers first so blog/reddit merge onto them.
    for item in hf + arxiv + rss + scraped + reddit_items + repos:
        if not item.get("title"):
            continue
        merge(ledger, item, today, reddit_mentions)

    rows = write_ledger(ledger)
    added = len(ledger) - before
    digest_path = write_digest(rows, today, cfg)

    print(f"\nDone. Ledger: {len(rows)} total rows (+{added} new).")
    print(f"Digest: {digest_path}")
    print(f"Ledger: {CSV_PATH}")


if __name__ == "__main__":
    main()
