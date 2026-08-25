"""The platform-agnostic interface every scraper backend implements.

This is the extension point the brief asks for. An X, LinkedIn, Threads, or
Reddit backend subclasses `SocialScraper`, implements the five things that are
genuinely platform-specific, and immediately gets the rest — deduplication
against the ledger, the daily monitoring loop, creator pacing, video downloads —
for free. The AI agent keeps calling the same six methods and never learns which
platform it is talking to.

The split is the whole point of the file:

  abstract — `login`, `get_profile`, `fetch_recent`, `get_post`, `download_media`,
             `close`. Every one of these is "how does *this* site work".
  concrete — `get_latest_posts`, `monitor`, `download_video`. Every one of these
             is "what does the agent need", and none of it changes per platform.

Note that `fetch_recent` is abstract while `get_latest_posts` is not. The
platform knows how to list a creator's recent posts; it has no business also
knowing about the seen-posts ledger, and if each backend implemented its own
skip-what-we-have logic they would drift apart within two backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar, Sequence

from .config import Settings
from .database import PostStore
from .exceptions import ScraperError
from .models import DownloadResult, MonitorResult, Platform, Post, Profile
from .utils import RateLimiter, get_logger


class SocialScraper(ABC):
    """One creator-monitoring backend for one platform."""

    platform: ClassVar[Platform]

    def __init__(self, settings: Settings, store: PostStore) -> None:
        self._settings = settings
        self._store = store
        self._limiter = RateLimiter(settings)
        self._log = get_logger(self.platform.value)

    @property
    def settings(self) -> Settings:
        return self._settings

    @property
    def store(self) -> PostStore:
        return self._store

    # -- platform-specific -------------------------------------------------- #
    @abstractmethod
    async def login(self, *, force: bool = False) -> None:
        """Establish or validate a session. Idempotent."""

    @abstractmethod
    async def get_profile(self, username: str) -> Profile:
        """One creator's profile."""

    @abstractmethod
    async def fetch_recent(self, username: str, limit: int) -> list[Post]:
        """The creator's `limit` most recent posts, newest first, no deduplication."""

    @abstractmethod
    async def get_post(self, url: str) -> Post:
        """One post or reel, by URL or shortcode."""

    @abstractmethod
    async def download_media(self, post: Post, *, dest=None) -> DownloadResult:
        """Save this post's primary media to disk and return where it landed."""

    @abstractmethod
    async def close(self) -> None:
        """Release the browser and any other resources. Safe to call twice."""

    # -- shared ------------------------------------------------------------- #
    async def get_latest_posts(
        self,
        username: str,
        limit: int = 5,
        *,
        only_new: bool = True,
        record: bool = True,
    ) -> list[Post]:
        """The newest posts, with everything already processed filtered out.

        `only_new=False` returns the raw newest posts without consulting the
        ledger — useful for refreshing engagement counts on posts the agent has
        already handled, which is a real need and shouldn't require a second API.
        `record=False` additionally leaves the ledger untouched, so a dry run
        does not mark posts as processed that the agent never actually saw.
        """
        posts = await self.fetch_recent(username, limit)
        if not posts:
            return []

        if not only_new:
            if record:
                await self._store.record(posts)
            return posts

        fresh, skipped = await self._store.filter_new(posts)
        if skipped:
            self._log.debug(f"@{username}: skipped {skipped} already-processed post(s)")
        if record and fresh:
            await self._store.record(fresh)
        return fresh

    async def monitor(
        self,
        usernames: Sequence[str],
        limit: int = 5,
        *,
        record: bool = True,
    ) -> list[MonitorResult]:
        """Check a list of creators for new posts. One bad creator cannot fail the run.

        Errors are captured into the result rather than raised: a monitoring pass
        over twenty creators that dies on creator three because someone went
        private has thrown away seventeen good answers for no reason. The agent
        reads `result.ok` and decides what to do about the failures.
        """
        results: list[MonitorResult] = []

        for index, raw_username in enumerate(usernames):
            if index:
                await self._limiter.between_creators()

            username = str(raw_username).lstrip("@").lower()
            try:
                posts = await self.fetch_recent(username, limit)
                fresh, skipped = await self._store.filter_new(posts)
                if record and fresh:
                    await self._store.record(fresh)
                results.append(
                    MonitorResult(
                        platform=self.platform,
                        creator=username,
                        new_posts=fresh,
                        skipped_count=skipped,
                    )
                )
                self._log.info(f"@{username}: {len(fresh)} new, {skipped} already seen")
            except ScraperError as exc:
                self._log.error(f"@{username}: {type(exc).__name__}: {exc}")
                results.append(
                    MonitorResult(platform=self.platform, creator=username, error=str(exc))
                )

        return results

    async def download_video(self, post: Post, *, dest=None) -> DownloadResult:
        """Save a post's video and return the path.

        Transcription is explicitly out of scope for this package — this hands
        back a file path and stops. Whatever generates transcripts consumes that
        path as its own input.
        """
        return await self.download_media(post, dest=dest)

    # -- context manager ---------------------------------------------------- #
    async def __aenter__(self) -> SocialScraper:
        await self.login()
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        await self.close()
