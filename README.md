# Finding Papers — Daily AI Research Digest & Script-Writing Pipeline

A small, zero-dependency system that every day gathers new AI research papers from the
big labs + community trending signals, logs them into a running spreadsheet with metrics,
and writes a clean daily digest. On top of that sits a 5-agent pipeline that picks the best
papers, deep-dives them, and writes/refines Instagram Reel scripts for **@aiprofessor.vs**.
Built to help you spot papers worth acting on and learn, over time, **what worked and what
didn't**.

> **This repo is a private backup.** It's pushed manually every so often (not on a schedule)
> to keep the ledger, scripts, and the accumulated "taste" playbooks safe. Everything here is
> the working state of the project as of the last push — pull before you start a new local
> session if you've been running this from more than one machine.

## Folder map

| Path | What's in it |
|---|---|
| `finding_papers.py`, `sources.json` | Agent 1 (finder) + its editable source list |
| `scrapex.py`, `scrapex.json`, `scrapex/` | **ScrapeX** — trending papers ranked by real reach on X, + its two deduped ledgers and daily report |
| `papers.csv` | Master running ledger — every paper ever found, deduped, with your notes |
| `digests/` | Daily digest snapshots (`digest_YYYY-MM-DD.md`) |
| `agent2_prep.py`, `agent2/` | Agent 2 (picker) prep + `playbook.md` (virality rubric, built from 54+ past reels) + `brief_*` |
| `agent3_prep.py`, `agent3/` | Agent 3 (deep-dive) prep + `input_*` / `deepdive_*` |
| `agent4_prep.py`, `agent4/` | Agent 4 (writer) prep + `brief_*` |
| `agent5_prep.py`, `agent5/` | Agent 5 (refiner) prep + `refine_playbook.md` (the growing, context-aware taste file) + `refined/` (versioned outputs) |
| `scripts/` | Finished reel scripts, in the universal script format (see below) |
| `picks/` | Agent 2's `top5_<date>.md` outputs |
| `all past scripts/` | Past reels + their real performance metrics — the ground truth the playbooks are built from |
| `Scripting_reference_things/` | Hook bible, winning-script breakdowns, script-type templates |
| `MEMORY.md` | The project's own standing-rules file — read this first if you're picking this project back up |

## What it does

Each run pulls from these free sources (no API keys, no paid Twitter):

| Source | Signal |
|---|---|
| **Hugging Face Daily Papers** | Community upvotes — the main "what's trending" signal |
| **arXiv** (cs.AI / cs.LG / cs.CL) | New papers, filtered to **big-lab authors** |
| **OpenAI / Google DeepMind / Google Research** (RSS) | Official lab releases |
| **Meta AI / Anthropic** (page scrape) | Official lab releases |
| **Reddit r/MachineLearning** (etc.) | Community discussion + arXiv mentions |
| **Bluesky** (curated AI accounts) | Buzz signal — likes+reposts on posts that link an arXiv paper |
| **GitHub Trending** | AI repos catching on (implementations of hot papers) |

It then writes two things:

- **`papers.csv`** — the master **running ledger**. One row per paper/post/repo, deduped,
  appended to every day. This is your permanent record.
- **`digests/digest_YYYY-MM-DD.md`** — a readable daily digest with three sections:
  🔥 Trending today · 🏢 From the big labs · 💻 Trending AI repos.

## Run it

```
python finding_papers.py
```

or just double-click **`run_daily.bat`** (it logs to `run.log`).

Backfill a specific day: `python finding_papers.py --date 2026-07-13`

## The ledger (`papers.csv`)

Columns: `first_seen, last_updated, source, lab, title, authors, url, arxiv_id,
hf_upvotes, hf_comments, reddit_mentions, github_stars, bluesky_score, trending_score,
category, summary, published_iso, picked, my_notes, performance`

**Three columns are yours** — the script *never* overwrites them:

- **`picked`** — mark `YES` when you use a paper (newsletter, course, post…).
- **`my_notes`** — anything you want to remember.
- **`performance`** — how it did (views, engagement, "went viral", "flopped"…).

Every run refreshes the objective metrics (upvotes/stars grow over days) and appends new
papers, but leaves your three columns untouched. That pairing — your outcome next to the
objective signals — is how you'll see what kind of paper actually worked.

> Tip: open `papers.csv` in Excel/Google Sheets, sort by `trending_score`, and fill in
> `picked` / `performance` as you go.

## How the `trending_score` works (0–100)

A transparent blend, computed in `trending_score()` in `finding_papers.py`:

```
raw   = hf_upvotes*3 + reddit_mentions*6 + github_stars*0.2 + bluesky_score*0.5 + (10 if big-lab)
score = min(100, raw * recency_multiplier)   # newer = higher
```

(`bluesky_score` = summed likes+reposts from the curated Bluesky accounts that shared the paper.)

Edit those weights in that one function to retune what floats to the top.

## Adding sources

All sources live in **`sources.json`** — add one line to the relevant list and save; the
next run picks it up. No code changes.

- `rss_feeds` — a lab blog with an RSS feed: `{"lab": "Name", "url": "..."}`
- `scrape_pages` — a lab news page without RSS: `{"lab": "Name", "url": "..."}`
- `subreddits` — just the name, e.g. `"LocalLLaMA"`
- `bluesky_accounts` — a Bluesky handle, e.g. `"rasbt.bsky.social"`. We read its public feed
  (no login) and score papers by the likes+reposts on posts that link an arXiv paper. Add
  prolific paper-sharers. (Bluesky global search is auth-walled, so only listed accounts are
  read — like the RSS list. Category bots like `arxiv-cs-cl.bsky.social` give broad coverage but
  ~zero engagement; human curators are the real buzz signal.)
- `arxiv_categories` — e.g. `"cs.CV"`
- `creators` / `labs` — names to recognize as "big lab"
- `twitter_handles` — placeholder for if/when you add an X API key

Easiest path: **just tell Claude** "add <thing> as a source" and it edits the file for you.
(Claude will also check in each day about whether you want to add anything new.)

## ScrapeX — what's trending on X

Agent 1 tells you what got *published*. ScrapeX tells you what got **traction** — which
papers the AI-research side of X is actually amplifying right now, ranked by the real
reach of the posts carrying them.

```
pip install twikit          # one-time; the only non-stdlib dep in this project
python scrapex.py --check   # verify deps + login, fetch nothing
python scrapex.py           # the real run
```

It reads the timelines in `scrapex.json` (**alphaXiv/@askalphaxiv, elvis/@omarsar0,
DAIR.AI, AK, arXiv, Tanishq, Aran, Turing Post, Rohan Paul, Cameron Wolfe, Hugging
Face**) *plus* site-wide X searches like `arxiv.org/abs min_faves:200`, so papers still
reach you from accounts that aren't on the list. Add accounts or queries to
`scrapex.json` — no code changes.

> Two handles were wrong on the first pass and are worth knowing about if you add more:
> **`@alphaxiv` is not alphaXiv** — it's a dormant 158-follower account whose last tweet
> was in 2017. The real one is **`@askalphaxiv`**. And **`@arxiv_org` has been dead since
> February 2021**; the live account is **`@arxiv`**. Both looked fine in the run output
> (tweets were returned) and silently contributed nothing, because everything they
> returned fell outside the lookback window. If an account reports `0 with papers` run
> after run, check it's the handle you think it is.

**Login — use the cookie method.** X fronts its login endpoint with Cloudflare bot
management, which blocks automated username/password logins outright (confirmed on this
machine: the login POST comes back as a Cloudflare CAPTCHA page). The API endpoints
themselves accept a normal session cookie, so hand ScrapeX an existing session instead:

1. Open **x.com** in Chrome/Edge and log in as normal.
2. **F12** → *Application* → *Storage* → *Cookies* → `https://x.com`
3. Copy the **values** of the `auth_token` and `ct0` cookies.
4. Put them in `.env` (gitignored, same file as `APIFY_TOKEN`):

```
X_AUTH_TOKEN=<auth_token value>
X_CT0=<ct0 value>
```

Those two cookies **are** the login session — treat them like a password. ScrapeX writes
them to `scrapex/cookies.json` (also gitignored) and reuses that on later runs. Logging
out of X in that browser invalidates them; copy them again if that happens.

`X_USERNAME`/`X_PASSWORD` still work as a fallback if X ever lets the password flow
through, but don't count on it. **Use a spare account** either way — this reads a lot of
timelines per run.

### Three twikit repairs ship inside `scrapex.py`

twikit 2.3.3 is behind X's current site in three separate ways, and each one is fatal on
its own. All three are patched **at runtime**, not in `site-packages`, so `pip install -U
twikit` can't silently revert them — and each tries upstream first, so it goes dormant the
day twikit catches up.

| Patch | What broke | Symptom |
|---|---|---|
| `patch_ondemand_lookup()` | twikit finds the script it derives X's request-signing key from by regexing `"ondemand.s":"<hash>"`. X's webpack manifest now splits that into two maps — `59924:"ondemand.s"` and `59924:"7fac826"`. | Login dies: *"Couldn't get KEY_BYTE indices"* |
| `patch_missing_legacy_fields()` | twikit hard-indexes ~40 `legacy['field']` values on users and tweets. X now omits fields it used to always send, and omits **different ones per account**. | `KeyError: 'urls'` / `'withheld_in_countries'` / `'pinned_tweet_ids_str'` — one missing field loses a whole timeline |
| `patch_search_endpoint()` | Every GraphQL operation has a rotating opaque ID. twikit has a stale one baked in for `SearchTimeline`. | Every site-wide search returns `404` |

The third reads the current ID out of `main.<hash>.js` rather than hardcoding today's
value, so it survives X's next rotation. It repoints **only** `SearchTimeline` — the
timeline endpoints still work, and a query ID has to agree with the feature flags sent
alongside it, so swapping an ID that isn't broken risks trading a working call for a 400.

### It never shows you the same paper twice

That's the whole point of the two ledgers, and it's why nothing repeats run over run:

| File | One row per | Behaviour |
|---|---|---|
| `scrapex/posts.csv` | **post, ever** | Metrics *refreshed* each run (a post keeps gaining views), never duplicated |
| `scrapex/papers.csv` | **paper, ever** | Reach re-aggregated from all posts each run, so it only gets more accurate |

A paper lands in **"New since last run"** exactly once — the first run it clears
`min_reach_to_report`. After that it's silent unless it grows by `climb_threshold`
(default +50%), which puts it in **"Still climbing"**. So a paper that's merely *still*
popular doesn't nag you every day, but one that's genuinely exploding comes back.

Because the paper key is the canonical arXiv ID, an arXiv link, an HF-papers link and an
alphaXiv link to the same paper collapse into **one** entry, not three. Retweets are
unwrapped to the original post, so five accounts RTing one paper is one row — with all
five credited.

### How reach is scored

```
engagement = likes + replies + reposts*2 + quotes*2 + bookmarks*2
post_reach = views + engagement*50
paper_reach = sum(post_reach) * (1 + 0.25*(distinct_creators - 1))
trend_score = paper_reach * 0.5^(days_since_newest_post / 10)
```

Views measure exposure, engagement measures whether anyone *cared* — engagement runs
~1–2% of views, so it's scaled up to sit on the same axis. Reposts/quotes/bookmarks
outweigh likes because they cost the reader more. Breadth gets a bonus: five accounts
sharing a paper beats one account getting lucky. `reach_score` stays raw and cumulative;
**`trend_score` decays with age** and is what the report ranks on, so month-old giants
don't pin themselves to the top forever. All of it is tunable in `scrapex.json` →
`weights`.

`picked` and `my_notes` in `scrapex/papers.csv` are yours — never overwritten, same deal
as `papers.csv`. Papers agent 1 already found are flagged `in_main_ledger`.

Other flags: `--all` (show everything over the floor, not just new), `--rebuild`
(re-score stored posts, fetch nothing — use after retuning weights), `--no-search`
(accounts only), `--date YYYY-MM-DD`.

## The agent pipeline (5 independent "plugs")

Run **one at a time, manually, only when you want it** — nothing auto-chains.

| # | Agent | Run it | Output |
|---|-------|--------|--------|
| 1 | **Finder** | `python finding_papers.py` | `papers.csv` + daily digest |
| 1b | **ScrapeX** (X trending) | `python scrapex.py` | `scrapex/trending_<date>.md` + 2 ledgers |
| 2 | **Picker** | `python agent2_prep.py` → ask Claude | `picks/top5_<date>.md` |
| 3 | **Deep-dive** | `python agent3_prep.py` → ask Claude | `agent3/deepdive_<date>.md` |
| 4 | **Writer** (from scratch) | `python agent4_prep.py --paper "..." --notes "..."` → ask Claude | `scripts/<date>-<slug>.md` |
| 5 | **Refiner** (polish an existing script) | paste your draft to Claude + say how to refine | `agent5/refined/<date>-v<N>-<slug>.md` (versioned) |

**Agent 5 (Refiner)** takes a script you *already have* — your own, an Agent 4 script, or one
from anywhere else — and polishes it against the page's proven levers **without rewriting it**.
Just paste your draft in chat and tell Claude how you want it refined; Claude drops it into
`agent5/input.md`, runs the prep, and writes the polished version to a **versioned** file in
`agent5/refined/` — `v1` the first time, `v2`/`v3` each time you refine that same script again,
so every pass is tracked and nothing is overwritten. Every refine ends with a short
"what I changed & why".

It **learns your taste — with context.** When you react with a preference, Claude doesn't save a
flat rule; it saves a *conditional* one. So "make the hook longer" on a compression paper and
"make the hook shorter" on a brain paper are stored as two situation-specific rules, not a
contradiction — the refiner analyzes each new draft's subject + structure and applies the rules
that fit. All of this lives in `agent5/refine_playbook.md`. Because Agents 4 and 5 share the same
reference set, sharper refines also make the from-scratch writer better over time.

## The universal script format

Every script (from Agent 4 or Agent 5) follows one locked format — full spec in
`Scripting_reference_things/7 script type template.md` under TYPE 4:

- **Metadata on top** (keeps emoji headers): 📌 title, 🎯 angle, 👥 audience, 📊 type, verified facts.
- **Then the script block — entirely bold, zero emojis:**
  - **`Reference:`** — real links (paper/arXiv/Reddit, X post, article, demo) so every claim is
    checkable.
  - **`[HOOK 1 — tag]`, `[HOOK 2 — tag]`…** — flexible count (as many strong hooks as the paper
    supports), each with a short strategy tag.
  - **`[RE-HOOK]`** → **`[BODY]`** (plain bold sub-labels: EVERYDAY STAKES / WHY THE OLD WAY
    FAILED / THE ONE CLEVER IDEA / WHY IT MATTERS) → **`[CTA]`**.
- **Closing metadata** (emojis OK): ✅ checklist, 📊 triggers used, 📱 caption, 🏷️ hashtags.

No timestamps in the script body. See any file in `scripts/` dated 2026-07-15 or later for a
worked example.

## Scheduling

- **Manual only (current):** the daily 9 AM Windows Task Scheduler auto-run was **disabled** —
  every agent is run by hand, on demand. The task definition still exists if you ever want it
  back (ask Claude to re-enable it).

## Notes / limits

- Reddit occasionally rate-limits (`429`) — that source is best-effort and skips silently.
- Agent 1 itself still has no X data (`twitter_handles` in `sources.json` is an unused
  placeholder). **ScrapeX** covers X separately — see above.
- Pure Python standard library — nothing to `pip install`. **Except ScrapeX**, which needs
  `pip install twikit` and an X login.
