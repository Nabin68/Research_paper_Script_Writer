"""The Instagram backend, the six-function agent API, and the CLI.

Three layers, smallest surface outward:

  `InstagramScraper` — the `SocialScraper` implementation. Owns the browser, the
      session, and the three scraping modules, and wires them together.
  module functions — `login`, `get_profile`, `get_latest_posts`, `get_post`,
      `download_video`, `close`. Exactly the interface the brief specifies for
      the AI agent, backed by one lazily-created scraper so the agent never
      manages a lifecycle, never sees a browser, and never imports Playwright.
  `main()` — a CLI over the same functions, which is also how you smoke-test a
      selector change without writing a script.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Awaitable, Callable, Sequence, TypeVar

from .base import SocialScraper
from .browser import BrowserManager
from .config import Settings, get_settings, load_settings
from .database import PostStore, create_store
from .downloader import MediaDownloader
from .exceptions import LoginRequired, ScraperError
from .login import SessionManager
from .models import DownloadResult, MonitorResult, Platform, Post, Profile
from .profile import ProfileScraper
from .reel import PostScraper
from .utils import (
    classify_input,
    extract_shortcode,
    get_logger,
    normalize_username,
    setup_logging,
    with_retry,
)

T = TypeVar("T")


class InstagramScraper(SocialScraper):
    """Scrapes public Instagram profiles, posts, and reels through Playwright."""

    platform = Platform.INSTAGRAM

    def __init__(self, settings: Settings | None = None, store: PostStore | None = None) -> None:
        resolved = settings or get_settings()
        resolved.ensure_dirs()
        setup_logging(resolved)
        super().__init__(resolved, store or create_store(resolved))

        self._browser = BrowserManager(resolved)
        self._session = SessionManager(self._browser, resolved)
        self._profiles = ProfileScraper(self._browser, resolved)
        self._posts = PostScraper(self._browser, resolved)
        self._downloader = MediaDownloader(self._browser, resolved)
        self._log = get_logger("instagram")
        self._ready = False

    # -- lifecycle ---------------------------------------------------------- #
    async def login(self, *, force: bool = False) -> None:
        """Start the browser and guarantee a valid session, logging in if needed."""
        await self._browser.start()
        await self.store.connect()
        await self._session.ensure_session(force=force)
        # Cookies get refreshed by Instagram as you browse; writing them back
        # here is what makes a session survive weeks instead of expiring on the
        # original login's clock.
        await self._browser.save_state()
        self._ready = True

    async def close(self) -> None:
        """Close the browser and the ledger. Safe to call twice, and on a failed start."""
        if self._browser.started:
            try:
                await self._browser.save_state()
            except Exception as exc:  # noqa: BLE001 - never fail a run during teardown
                self._log.debug(f"could not save session on close: {exc}")
        await self._browser.stop()
        await self.store.close()
        self._ready = False
        self._log.debug("scraper closed")

    async def _ready_up(self) -> None:
        if not self._ready:
            await self.login()

    async def _run(self, operation: Callable[[], Awaitable[T]], *, scope: str) -> T:
        """Run one scraping operation with retries and mid-run session recovery.

        The session-expiry path is the interesting one. Instagram can invalidate a
        session at any moment, including between two posts of the same creator.
        Rather than making every caller handle that, one `LoginRequired` triggers
        a re-login and a single replay of the same operation. Retries proper are
        left to `with_retry`, which only backs off on genuinely transient errors.
        """
        await self._ready_up()

        async def attempt() -> T:
            try:
                return await operation()
            except LoginRequired:
                self._log.warning("session expired mid-run — re-establishing")
                self._session.invalidate()
                await self._session.ensure_session(force=True)
                await self._browser.save_state()
                return await operation()

        return await with_retry(attempt, self.settings, scope=scope)

    # -- scraping ----------------------------------------------------------- #
    async def get_profile(self, username: str) -> Profile:
        name = normalize_username(username)
        return await self._run(lambda: self._profiles.fetch(name), scope="profile")

    async def fetch_recent(self, username: str, limit: int = 5) -> list[Post]:
        name = normalize_username(username)
        return await self._run(lambda: self._profiles.latest_posts(name, limit), scope="timeline")

    async def get_post(self, url: str) -> Post:
        shortcode = extract_shortcode(url)
        return await self._run(lambda: self._posts.fetch(shortcode), scope="post")

    async def get(self, reference: str) -> Profile | Post:
        """Dispatch on what the input looks like: a profile handle/URL, or a post/reel URL.

        Convenience for callers holding a URL they have not classified — the
        brief lists all three input forms arriving through one door.
        """
        kind, value = classify_input(reference)
        return await (self.get_post(value) if kind == "post" else self.get_profile(value))

    async def download_media(self, post: Post, *, dest: Path | None = None) -> DownloadResult:
        await self._ready_up()
        return await self._downloader.download_media(post, dest=dest)

    async def download_video(self, post: Post, *, dest: Path | None = None) -> DownloadResult:
        await self._ready_up()
        return await self._downloader.download_video(post, dest=dest)


# --------------------------------------------------------------------------- #
# The agent-facing API
# --------------------------------------------------------------------------- #
# One scraper for the process, created on first use. This is what lets the agent
# call get_profile() and get_latest_posts() back to back without holding a handle
# to anything — and, more importantly, without a second Chromium launch.
_scraper: InstagramScraper | None = None


def get_scraper(**settings_overrides: object) -> InstagramScraper:
    """The process-wide scraper, created on first call.

    Overrides only apply when the scraper does not exist yet; pass them on the
    first call, or construct `InstagramScraper(Settings(...))` directly for full
    control.
    """
    global _scraper
    if _scraper is None:
        settings = load_settings(**settings_overrides) if settings_overrides else get_settings()
        _scraper = InstagramScraper(settings)
    return _scraper


async def login(*, force: bool = False, **overrides: object) -> None:
    """Establish a session, opening an interactive login window if required."""
    await get_scraper(**overrides).login(force=force)


async def get_profile(username: str) -> Profile:
    """Profile data for a username or profile URL."""
    return await get_scraper().get_profile(username)


async def get_latest_posts(username: str, limit: int = 5, *, only_new: bool = True) -> list[Post]:
    """The creator's newest posts, excluding anything already in the ledger."""
    return await get_scraper().get_latest_posts(username, limit, only_new=only_new)


async def get_post(url: str) -> Post:
    """One post or reel by URL (`/p/...`, `/reel/...`) or bare shortcode."""
    return await get_scraper().get_post(url)


async def download_video(post: Post, *, dest: Path | None = None) -> DownloadResult:
    """Save a post's video to disk and return the result, including its path."""
    return await get_scraper().download_video(post, dest=dest)


async def monitor(usernames: Sequence[str], limit: int = 5) -> list[MonitorResult]:
    """Check several creators for new posts in one pass, pacing between them."""
    return await get_scraper().monitor(usernames, limit)


async def close() -> None:
    """Shut the browser down. Call once, after all creators are processed."""
    global _scraper
    if _scraper is not None:
        await _scraper.close()
        _scraper = None


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _emit(payload: Any) -> None:
    """Print JSON to stdout. Logs go to stderr, so stdout stays pipeable."""
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def _dump(value: Any) -> Any:
    if isinstance(value, list):
        return [_dump(item) for item in value]
    return value.model_dump(mode="json") if hasattr(value, "model_dump") else value


async def _dispatch(args: argparse.Namespace) -> int:
    overrides: dict[str, object] = {"log_level": args.log_level}
    if args.headed:
        overrides["headless"] = False

    scraper = InstagramScraper(load_settings(**overrides))
    try:
        if args.command == "login":
            await scraper.login(force=args.force)
            _emit({"status": "ok", "session": str(scraper.settings.session_file)})

        elif args.command == "check":
            settings = scraper.settings
            await scraper.store.connect()
            _emit(
                {
                    "session_file": str(settings.session_file),
                    "session_present": settings.session_file.exists(),
                    "headless": settings.headless,
                    "download_media": settings.download_media,
                    "database": str(settings.db_path),
                    "ledger": await scraper.store.stats(),
                }
            )

        elif args.command == "profile":
            _emit(_dump(await scraper.get_profile(args.username)))

        elif args.command == "latest":
            posts = await scraper.get_latest_posts(
                args.username, args.limit, only_new=not args.all, record=not args.dry_run
            )
            _emit(_dump(posts))

        elif args.command == "post":
            _emit(_dump(await scraper.get_post(args.url)))

        elif args.command == "monitor":
            results = await scraper.monitor(args.usernames, args.limit)
            _emit(_dump(results))

        elif args.command == "download":
            post = await scraper.get_post(args.url)
            dest = Path(args.dest) if args.dest else None
            _emit(_dump(await scraper.download_video(post, dest=dest)))

        elif args.command == "stats":
            await scraper.store.connect()
            _emit(await scraper.store.stats())

        else:  # pragma: no cover - argparse rejects unknown commands first
            raise ScraperError(f"unknown command {args.command!r}")

    except ScraperError as exc:
        get_logger("cli").error(f"{type(exc).__name__}: {exc}")
        _emit({"error": type(exc).__name__, "message": str(exc)})
        return 1
    finally:
        await scraper.close()

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m instagram_scraper",
        description="Scrape public Instagram profiles and reels with Playwright.",
    )
    parser.add_argument("--headed", action="store_true", help="show the browser window")
    parser.add_argument("--log-level", default="INFO", help="TRACE/DEBUG/INFO/WARNING/ERROR")

    sub = parser.add_subparsers(dest="command", required=True)

    login_cmd = sub.add_parser("login", help="log in interactively and save the session")
    login_cmd.add_argument("--force", action="store_true", help="re-login even if the session works")

    sub.add_parser("check", help="print configuration and ledger status, scrape nothing")
    sub.add_parser("stats", help="print what the ledger holds")

    profile_cmd = sub.add_parser("profile", help="scrape one profile")
    profile_cmd.add_argument("username", help="handle, or a profile URL")

    latest_cmd = sub.add_parser("latest", help="newest posts for one creator")
    latest_cmd.add_argument("username")
    latest_cmd.add_argument("--limit", type=int, default=5)
    latest_cmd.add_argument("--all", action="store_true", help="include already-processed posts")
    latest_cmd.add_argument("--dry-run", action="store_true", help="do not write to the ledger")

    post_cmd = sub.add_parser("post", help="scrape one post or reel")
    post_cmd.add_argument("url", help="post/reel URL, or a bare shortcode")

    monitor_cmd = sub.add_parser("monitor", help="check several creators for new posts")
    monitor_cmd.add_argument("usernames", nargs="+")
    monitor_cmd.add_argument("--limit", type=int, default=5)

    download_cmd = sub.add_parser("download", help="scrape a reel and save its video")
    download_cmd.add_argument("url")
    download_cmd.add_argument("--dest", help="explicit output file path")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return asyncio.run(_dispatch(args))
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
