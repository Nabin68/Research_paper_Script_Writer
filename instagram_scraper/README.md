# instagram_scraper

Scrapes public Instagram profiles, posts, and reels with Playwright (Chromium),
for an AI agent that checks creators daily and turns new content into topic ideas.

No unofficial API wrappers, no Selenium. One browser, one context, one manual
login that lasts for weeks.

---

## Setup

```bash
pip install playwright pydantic loguru tenacity python-dotenv
python -m playwright install chromium
```

Then log in once. A visible Chromium window opens — log in by hand, including
2FA or any checkpoint Instagram throws at you:

```bash
python -m instagram_scraper login
```

That writes `storage_state.json`. Every run after this is headless and silent.
**Your password is never stored, typed by the tool, or read from `.env`.**

Verify at any time:

```bash
python -m instagram_scraper check
```

---

## The agent interface

Six coroutines. The agent never touches Playwright and never manages a browser.

```python
import asyncio
from instagram_scraper import login, get_profile, get_latest_posts, get_post, download_video, close

async def main():
    await login()                                    # reuses the saved session

    profile = await get_profile("openai")
    print(profile.followers, profile.biography)

    posts = await get_latest_posts("openai", limit=5) # only posts never seen before
    for post in posts:
        print(post.to_json())
        if post.is_video:
            result = await download_video(post)       # only when you ask
            print(result.path)                        # another project transcribes it

    one = await get_post("https://www.instagram.com/reel/C8xYzAbCdEf/")

    await close()                                     # once, after all creators

asyncio.run(main())
```

Several creators in one pass, paced and fault-isolated:

```python
from instagram_scraper import monitor

for result in await monitor(["openai", "anthropicai", "deepmind"], limit=5):
    print(result.summary())   # {'creator': ..., 'new': 2, 'skipped': 3, 'error': None}
```

`monitor` never raises for one bad creator. A private or deleted account comes
back as `result.error` while every other creator still returns its posts.

Accepted inputs everywhere: `openai`, `@openai`,
`https://www.instagram.com/openai/`, `https://www.instagram.com/p/<code>/`,
`https://www.instagram.com/reel/<code>/`, or a bare shortcode.

---

## CLI

Every command prints JSON on stdout; logs go to stderr, so piping is safe.

```bash
python -m instagram_scraper login [--force]
python -m instagram_scraper check
python -m instagram_scraper profile openai
python -m instagram_scraper latest openai --limit 5 [--all] [--dry-run]
python -m instagram_scraper post https://www.instagram.com/reel/XXXX/
python -m instagram_scraper monitor openai anthropicai --limit 5
python -m instagram_scraper download https://www.instagram.com/reel/XXXX/
python -m instagram_scraper stats

python -m instagram_scraper --headed --log-level DEBUG profile openai   # debugging
```

`latest` returns only unprocessed posts and records them. `--all` includes ones
already seen; `--dry-run` leaves the ledger untouched.

---

## Output

```json
{
  "platform": "instagram",
  "creator": "openai",
  "post_id": "3245678901234567890",
  "shortcode": "C8xYzAbCdEf",
  "url": "https://www.instagram.com/reel/C8xYzAbCdEf/",
  "caption": "New model drop. #AI #GPT thanks @samaltman",
  "published_at": "2024-07-18T12:00:00+00:00",
  "likes": 15320,
  "comments": 342,
  "views": 324000,
  "hashtags": ["AI", "GPT"],
  "mentions": ["samaltman"],
  "tagged_users": ["samaltman"],
  "location": "San Francisco, California",
  "media_type": "reel",
  "thumbnail": "https://...",
  "video": "https://...",
  "images": []
}
```

`null` means Instagram did not report the field; `0` means it reported zero.
The distinction is preserved deliberately — do not collapse it when ranking.

Video URLs are signed and expire within hours. Download promptly or re-scrape.

---

## Configuration

All optional — the defaults are the intended production settings. Put any of
these in the project's `.env` (the same file the other scripts use).

| Variable | Default | Meaning |
|---|---|---|
| `HEADLESS` | `true` | `false` shows the browser window |
| `DOWNLOAD_MEDIA` | `false` | Media is never downloaded implicitly |
| `DATABASE` | `sqlite` | Backend for the seen-posts ledger |
| `SESSION_FILE` | `storage_state.json` | Where the session is saved |
| `DB_PATH` | `instagram_scraper/data/instagram.db` | Ledger location |
| `DOWNLOAD_DIR` | `downloads` | Where `download_video` writes |
| `POST_DELAY` | `2,6` | Random seconds between requests |
| `CREATOR_DELAY` | `5,15` | Random seconds between creators |
| `MAX_RETRIES` | `3` | Attempts for transient failures |
| `INTERACTIVE_LOGIN` | `true` | `false` = raise instead of opening a login window |
| `BLOCK_ASSETS` | `true` | Skip downloading images/video while scraping |
| `LOG_LEVEL` | `INFO` | `DEBUG` to see every request |
| `LOG_FILE` | unset | Also log to this file, rotated at 10 MB |

**Set `INTERACTIVE_LOGIN=false` for scheduled/unattended runs.** Otherwise an
expired session opens a login window that nobody is there to complete, and the
run blocks until it times out.

---

## How it works, and why

**Data comes from Instagram's JSON API, not the DOM.** Instagram does not render
like counts, play counts, exact timestamps, tagged users, or direct video URLs
into the page in any reliable way, and what it does render is wrapped in class
names regenerated on every deploy (`x1i10hfl`, `_aacl`). So the scraper holds a
real logged-in session and calls the same internal endpoints Instagram's own web
app calls, issuing them with `fetch()` from inside a page on the instagram.com
origin so they carry the session cookies and origin headers exactly as the real
client sends them.

**Single posts skip the rotating query token.** An Instagram shortcode *is* the
media id, encoded in a known base64 alphabet — so `utils.shortcode_to_media_id`
decodes it locally and goes straight to `/api/v1/media/{id}/info/`. No GraphQL
`doc_id` to keep chasing.

**Everything Instagram-specific lives in `selectors.py`** — endpoints, JSON field
paths, and the few DOM selectors used for login detection and the fallback path.
Field paths are lists of candidates tried in order, so a rename like
`edge_liked_by` → `edge_media_preview_like` does not empty a column.

**Fallbacks degrade rather than fail.** If the direct API call is refused, the
scraper loads the page and reads whichever JSON payload Instagram itself fetches;
if that fails too, it reads the DOM. The DOM path returns `null` engagement
counts rather than zeros, so a degraded scrape is never mistaken for an unpopular
post.

**Pinned posts are handled.** Instagram returns pinned posts first regardless of
age, so results are re-sorted by publish time — a monitoring loop that trusted
feed order would treat a pinned two-year-old post as today's newest.

---

## Layout

```
browser.py     Playwright lifecycle + the JSON API call. Only file importing Playwright.
login.py       Session validation, interactive login, storage_state persistence.
profile.py     Profiles and creator timelines (with pagination).
reel.py        Single posts/reels + the two JSON parsers.
downloader.py  Optional media downloads. Returns a path; never transcribes.
database.py    PostStore interface + SQLite ledger (the skip-what-we-have logic).
models.py      Pydantic models: Profile, Post, MonitorResult, DownloadResult.
selectors.py   Every endpoint, JSON path, and DOM selector.
config.py      Settings from .env, frozen and injected.
utils.py       Parsing, digging, delays, retries, logging.
base.py        SocialScraper ABC — the multi-platform extension point.
main.py        InstagramScraper, the six agent functions, and the CLI.
```

---

## Adding another platform

`base.py` splits what is platform-specific from what is not. A new backend
implements six methods and inherits the rest:

```python
from instagram_scraper.base import SocialScraper
from instagram_scraper.models import Platform

class TwitterScraper(SocialScraper):
    platform = Platform.X

    async def login(self, *, force=False): ...
    async def get_profile(self, username): ...
    async def fetch_recent(self, username, limit): ...   # newest posts, no dedup
    async def get_post(self, url): ...
    async def download_media(self, post, *, dest=None): ...
    async def close(self): ...
```

`get_latest_posts`, `monitor`, `download_video`, and the async-context-manager
support come from the base class. Deduplication, pacing, and per-creator error
isolation are written once and shared, so backends cannot drift apart on them.
The agent's own code does not change.

---

## Error handling

Nothing crashes the process. Every failure is a typed exception:

| Exception | Meaning |
|---|---|
| `LoginRequired` / `ChallengeRequired` | Session expired or held behind a checkpoint |
| `ProfileNotFound` / `PostNotFound` | No such account; deleted post |
| `PrivateProfile` | Private, and the logged-in account does not follow it |
| `RateLimited` | Instagram is throttling us — retried with backoff |
| `NetworkError` / `ScrapeTimeout` | Transient — retried with backoff |
| `SelectorChanged` | A required field moved; names the field |
| `DownloadError`, `UnsupportedInput`, `ConfigError`, `BrowserError` | As named |

`RateLimited`, `NetworkError`, and `ScrapeTimeout` subclass `RetryableError` and
are retried with exponential backoff. Everything else fails immediately —
retrying a deleted post three times just adds a minute to a settled answer.

A session that expires mid-run is re-established and the operation replayed once,
so a long monitoring pass survives Instagram invalidating a session halfway.

---

## Tests

```bash
python tests/test_instagram_scraper.py
```

146 assertions over parsing, shortcode maths, config validation, the
deduplication ledger, and retry policy — no network, no browser. Runs under
pytest too if you have it.

---

## Notes

- Scrapes **public** profiles only, at human-paced request rates.
- Automating an Instagram account carries a real risk of restriction. Use an
  account you can afford to lose, not your main one.
- Transcription is deliberately out of scope: `download_video` returns a file
  path and stops there.
