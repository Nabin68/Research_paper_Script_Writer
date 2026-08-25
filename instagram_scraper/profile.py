"""Profiles and creator timelines.

`web_profile_info` is the workhorse: one call returns the whole profile header
*and* the first twelve posts, which is why `get_latest_posts(limit=5)` normally
costs exactly one request. Past twelve, pagination switches to
`/api/v1/feed/user/{id}/`, which is addressed by user id and takes a `max_id`
cursor — deliberately chosen over paginating the GraphQL edges, which would need
a `query_hash` that Instagram rotates every few weeks.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .browser import BrowserManager
from .config import Settings
from .exceptions import NotFound, PrivateProfile, ProfileNotFound, SelectorChanged
from .models import Platform, Post, Profile
from .reel import parse_api_item, parse_graphql_node
from .selectors import Endpoints, Paths
from .utils import RateLimiter, dig_any, get_logger, normalize_username, to_int

# `/api/v1/feed/user/` refuses counts above this and silently returns fewer.
_MAX_PAGE_SIZE = 33
# A guard against an infinite pagination loop if Instagram keeps handing back a
# cursor that yields nothing new.
_MAX_PAGES = 20
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


class ProfileScraper:
    """Fetches profile headers and creator timelines."""

    def __init__(self, browser: BrowserManager, settings: Settings) -> None:
        self._browser = browser
        self._settings = settings
        self._limiter = RateLimiter(settings)
        self._log = get_logger("profile")
        # username -> (user_id, is_private, followed_by_viewer). Saves a request
        # per creator on repeat calls within one run, which is most of them in a
        # monitoring pass that fetches a profile then its posts.
        self._cache: dict[str, tuple[str, bool, bool]] = {}

    # -- profile ------------------------------------------------------------ #
    async def fetch(self, username: str) -> Profile:
        """One creator's profile. Raises `ProfileNotFound` for a missing account."""
        username = normalize_username(username)
        user = await self._fetch_user_blob(username)
        profile = self._parse(user, username)
        self._log.info(
            f"profile @{profile.username}: {profile.followers or 0:,} followers, "
            f"{profile.posts_count or 0:,} posts"
            f"{' (private)' if profile.is_private else ''}"
        )
        return profile

    async def _fetch_user_blob(self, username: str) -> dict[str, Any]:
        try:
            data = await self._browser.fetch_json(
                Endpoints.WEB_PROFILE_INFO.format(username=username)
            )
        except NotFound as exc:
            raise ProfileNotFound(f"no Instagram account @{username}") from exc

        user = dig_any(data, Paths.PROFILE_ROOT)
        if not user:
            # A 200 with an empty user is how Instagram answers for accounts that
            # exist but are unavailable in this region, and for banned handles.
            raise ProfileNotFound(f"@{username} returned no profile data")

        self._cache[username] = (
            str(dig_any(user, Paths.USER_ID) or ""),
            bool(dig_any(user, Paths.IS_PRIVATE)),
            bool(dig_any(user, Paths.FOLLOWED_BY_VIEWER)),
        )
        return user

    def _parse(self, user: dict[str, Any], username: str) -> Profile:
        resolved = dig_any(user, Paths.USERNAME) or username
        return Profile(
            platform=Platform.INSTAGRAM,
            user_id=str(dig_any(user, Paths.USER_ID) or "") or None,
            username=str(resolved).lower(),
            full_name=dig_any(user, Paths.FULL_NAME) or None,
            biography=dig_any(user, Paths.BIOGRAPHY) or None,
            followers=to_int(dig_any(user, Paths.FOLLOWERS)),
            following=to_int(dig_any(user, Paths.FOLLOWING)),
            total_posts=to_int(dig_any(user, Paths.POST_COUNT)),
            profile_image=dig_any(user, Paths.PROFILE_PIC) or None,
            is_verified=bool(dig_any(user, Paths.IS_VERIFIED)),
            is_private=bool(dig_any(user, Paths.IS_PRIVATE)),
            is_business=bool(dig_any(user, Paths.IS_BUSINESS)),
            category=dig_any(user, Paths.CATEGORY) or None,
            external_links=_external_links(user),
            url=Endpoints.PROFILE.format(username=resolved),
            followed_by_viewer=bool(dig_any(user, Paths.FOLLOWED_BY_VIEWER)),
        )

    # -- timeline ----------------------------------------------------------- #
    async def latest_posts(self, username: str, limit: int = 5) -> list[Post]:
        """The newest `limit` posts, newest first.

        Ordering is enforced here rather than trusted: Instagram returns the feed
        in reverse-chronological order in practice, but pinned posts break that —
        they come back first regardless of age. A monitoring loop that trusts the
        feed order would treat a pinned two-year-old post as today's newest.
        """
        username = normalize_username(username)
        if limit <= 0:
            return []

        user_id, is_private, followed = await self._identity(username)
        if is_private and not followed:
            raise PrivateProfile(
                f"@{username} is private and the logged-in account does not follow it"
            )

        posts = await self._from_feed(username, user_id, limit) if user_id else []
        if not posts:
            self._log.debug(f"@{username}: feed endpoint empty — using the profile timeline")
            posts = await self._from_timeline(username, limit)

        # Undated posts sort last rather than blowing up the comparison.
        posts.sort(key=lambda p: p.published_at or _EPOCH, reverse=True)
        self._log.info(f"@{username}: {len(posts[:limit])} recent post(s)")
        return posts[:limit]

    async def _identity(self, username: str) -> tuple[str, bool, bool]:
        if username not in self._cache:
            await self._fetch_user_blob(username)
        return self._cache[username]

    async def _from_feed(self, username: str, user_id: str, limit: int) -> list[Post]:
        """Page `/api/v1/feed/user/` until we have `limit` posts or run out."""
        posts: list[Post] = []
        seen: set[str] = set()
        cursor: str | None = None

        for page_number in range(_MAX_PAGES):
            remaining = limit - len(posts)
            if remaining <= 0:
                break

            count = min(max(remaining, 12), _MAX_PAGE_SIZE)
            url = (
                Endpoints.USER_FEED_PAGED.format(user_id=user_id, count=count, max_id=cursor)
                if cursor
                else Endpoints.USER_FEED.format(user_id=user_id, count=count)
            )

            if page_number:
                await self._limiter.between_posts()

            try:
                data = await self._browser.fetch_json(url)
            except NotFound:
                self._log.debug(f"@{username}: feed endpoint unavailable")
                break

            items = dig_any(data, Paths.FEED_ITEMS) or []
            if not items:
                break

            for item in items:
                try:
                    post = parse_api_item(item, creator=username)
                except SelectorChanged as exc:
                    # One malformed item must not cost the other thirty-two.
                    self._log.warning(f"@{username}: skipping unparseable post ({exc})")
                    continue
                if post.post_id not in seen:
                    seen.add(post.post_id)
                    posts.append(post)

            cursor = dig_any(data, Paths.FEED_NEXT_CURSOR)
            if not cursor or not dig_any(data, Paths.FEED_MORE_AVAILABLE):
                break

        return posts

    async def _from_timeline(self, username: str, limit: int) -> list[Post]:
        """Fallback: the twelve posts embedded in the profile payload."""
        user = await self._fetch_user_blob(username)
        posts: list[Post] = []
        for edge in (dig_any(user, Paths.TIMELINE_EDGES) or [])[: max(limit, 12)]:
            try:
                posts.append(parse_graphql_node(edge, creator=username))
            except SelectorChanged as exc:
                self._log.warning(f"@{username}: skipping unparseable timeline node ({exc})")
        return posts


def _external_links(user: dict[str, Any]) -> list[str]:
    """Bio links, from both places Instagram keeps them.

    `external_url` is the single legacy link; `bio_links` is the newer
    multi-link list. Accounts can have either, and accounts migrated to
    multi-link have both with the first entry duplicated — so this merges and
    dedupes rather than picking one source.
    """
    links: list[str] = []
    if primary := dig_any(user, Paths.EXTERNAL_URL):
        links.append(str(primary))
    for entry in dig_any(user, Paths.BIO_LINKS) or []:
        url = entry.get("url") if isinstance(entry, dict) else entry
        if url:
            links.append(str(url))

    seen: set[str] = set()
    return [link for link in links if not (link in seen or seen.add(link))]
