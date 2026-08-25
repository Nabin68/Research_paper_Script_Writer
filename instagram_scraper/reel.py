"""Reels and posts: fetching one, and turning Instagram's JSON into a `Post`.

Instagram serves post data in two different shapes and this module understands
both, because the choice is not ours:

  * the **private-API shape** (`items[]`, snake_case, `pk`/`code`/`taken_at`) —
    what `/api/v1/media/.../info/` and `/api/v1/feed/user/...` return. This is
    the shape we get on the fast paths, so it is the one that matters most.
  * the **GraphQL shape** (`edge_media_to_caption`, `taken_at_timestamp`) — what
    the profile page embeds and what a page navigation yields.

Both parsers land on the same `Post`, so nothing downstream ever learns which
path the data came from.

Fetching one post prefers `/api/v1/media/{id}/info/`, reached by decoding the
shortcode into a media id locally (see `utils.shortcode_to_media_id`). That is a
single request with no page load and no rotating query token. The page-navigation
fallback exists for when Instagram refuses that endpoint, and costs a full render.
"""

from __future__ import annotations

from typing import Any

from playwright.async_api import Error as PlaywrightError, Page

from .browser import BrowserManager
from .config import Settings
from .exceptions import NotFound, PostNotFound, SelectorChanged
from .models import MediaType, Platform, Post
from .selectors import Dom, Endpoints, MediaTypeCodes, Paths
from .utils import (
    dig,
    dig_any,
    extract_hashtags,
    extract_mentions,
    get_logger,
    post_url,
    shortcode_to_media_id,
    to_datetime,
    to_int,
)

_log = get_logger("post")


# --------------------------------------------------------------------------- #
# Parsers
# --------------------------------------------------------------------------- #
def parse_api_item(item: dict[str, Any], *, creator: str | None = None) -> Post:
    """Parse one `items[]` entry from the private API into a `Post`."""
    if not isinstance(item, dict):
        raise SelectorChanged(f"expected a post object, got {type(item).__name__}")

    post_id = dig_any(item, Paths.API_ID)
    if post_id is None:
        raise SelectorChanged("post has no 'pk' — the media payload shape changed")
    # `id` arrives as "3123456789_17841400000", and only the first half is the media id.
    post_id = str(post_id).split("_")[0]

    shortcode = dig_any(item, Paths.API_SHORTCODE)
    caption = dig_any(item, Paths.API_CAPTION)
    owner = dig_any(item, Paths.API_OWNER) or creator
    if not owner:
        raise SelectorChanged(f"post {post_id} has no owner username")

    media_type = _api_media_type(item)
    thumbnail = dig_any(item, Paths.API_THUMBNAIL)
    video = dig_any(item, Paths.API_VIDEO)

    images: list[str] = []
    videos: list[str] = []
    for child in dig_any(item, Paths.API_CAROUSEL) or []:
        child_image = dig_any(child, Paths.API_THUMBNAIL)
        child_video = dig_any(child, Paths.API_VIDEO)
        if child_image:
            images.append(child_image)
        if child_video:
            videos.append(child_video)
    if not images and thumbnail:
        images = [thumbnail]
    # A carousel's own `video_versions` is absent; the first child's video is the
    # sensible thing to hand to `download_video`.
    if not video and videos:
        video = videos[0]

    tagged = [
        username
        for tag in (dig_any(item, Paths.API_TAGGED) or [])
        if (username := dig_any(tag, Paths.API_TAGGED_USER))
    ]

    return _build(
        post_id=post_id,
        shortcode=shortcode,
        creator=owner,
        caption=caption,
        published_at=to_datetime(dig_any(item, Paths.API_TAKEN_AT)),
        likes=to_int(dig_any(item, Paths.API_LIKES)),
        comments=to_int(dig_any(item, Paths.API_COMMENTS)),
        views=to_int(dig_any(item, Paths.API_VIEWS)),
        media_type=media_type,
        thumbnail=thumbnail,
        video=video,
        images=images,
        location=dig_any(item, Paths.API_LOCATION),
        tagged_users=tagged,
    )


def parse_graphql_node(node: dict[str, Any], *, creator: str | None = None) -> Post:
    """Parse one GraphQL media node (timeline edge or captured page payload)."""
    if not isinstance(node, dict):
        raise SelectorChanged(f"expected a media node, got {type(node).__name__}")
    # Timeline edges arrive wrapped as {"node": {...}}.
    node = node.get("node", node) if "node" in node and isinstance(node.get("node"), dict) else node

    post_id = dig_any(node, Paths.GQL_ID)
    shortcode = dig_any(node, Paths.GQL_SHORTCODE)
    if post_id is None and shortcode is None:
        raise SelectorChanged("media node has neither 'id' nor 'shortcode'")
    post_id = str(post_id).split("_")[0] if post_id is not None else str(shortcode_to_media_id(shortcode))

    owner = dig_any(node, Paths.GQL_OWNER) or creator
    if not owner:
        raise SelectorChanged(f"post {post_id} has no owner username")

    images: list[str] = []
    videos: list[str] = []
    for child in dig_any(node, Paths.GQL_CAROUSEL) or []:
        child_node = child.get("node", child) if isinstance(child, dict) else {}
        if url := dig_any(child_node, Paths.GQL_THUMBNAIL):
            images.append(url)
        if url := dig_any(child_node, Paths.GQL_VIDEO):
            videos.append(url)

    thumbnail = dig_any(node, Paths.GQL_THUMBNAIL)
    video = dig_any(node, Paths.GQL_VIDEO) or (videos[0] if videos else None)
    if not images and thumbnail:
        images = [thumbnail]

    tagged = [
        username
        for edge in (dig_any(node, Paths.GQL_TAGGED) or [])
        if (username := dig_any(edge, Paths.GQL_TAGGED_USER))
    ]

    return _build(
        post_id=post_id,
        shortcode=shortcode,
        creator=owner,
        caption=dig_any(node, Paths.GQL_CAPTION),
        published_at=to_datetime(dig_any(node, Paths.GQL_TAKEN_AT)),
        likes=to_int(dig_any(node, Paths.GQL_LIKES)),
        comments=to_int(dig_any(node, Paths.GQL_COMMENTS)),
        views=to_int(dig_any(node, Paths.GQL_VIEWS)),
        media_type=_graphql_media_type(node),
        thumbnail=thumbnail,
        video=video,
        images=images,
        location=dig_any(node, Paths.GQL_LOCATION),
        tagged_users=tagged,
    )


def _build(
    *,
    post_id: str,
    shortcode: str | None,
    creator: str,
    caption: str | None,
    published_at: Any,
    likes: int | None,
    comments: int | None,
    views: int | None,
    media_type: MediaType,
    thumbnail: str | None,
    video: str | None,
    images: list[str],
    location: str | None,
    tagged_users: list[str],
) -> Post:
    """Assemble the `Post`, deriving everything that comes from the caption."""
    return Post(
        platform=Platform.INSTAGRAM,
        creator=str(creator).lower(),
        post_id=str(post_id),
        shortcode=shortcode,
        url=post_url(shortcode, reel=media_type is MediaType.REEL) if shortcode else "",
        caption=caption,
        published_at=published_at,
        likes=likes,
        comments=comments,
        views=views,
        hashtags=extract_hashtags(caption),
        mentions=extract_mentions(caption),
        tagged_users=tagged_users,
        location=location,
        media_type=media_type,
        thumbnail=thumbnail,
        video=video,
        images=images,
    )


def _api_media_type(item: dict[str, Any]) -> MediaType:
    product = str(dig_any(item, Paths.API_PRODUCT_TYPE) or "").lower()
    code = to_int(dig_any(item, Paths.API_MEDIA_TYPE))
    if product in MediaTypeCodes.REEL_PRODUCT_TYPES:
        return MediaType.REEL
    if code == MediaTypeCodes.CAROUSEL:
        return MediaType.CAROUSEL
    if code == MediaTypeCodes.VIDEO:
        return MediaType.VIDEO
    return MediaType.IMAGE


def _graphql_media_type(node: dict[str, Any]) -> MediaType:
    product = str(dig_any(node, Paths.API_PRODUCT_TYPE) or "").lower()
    typename = str(dig_any(node, Paths.GQL_TYPENAME) or "")
    if product in MediaTypeCodes.REEL_PRODUCT_TYPES:
        return MediaType.REEL
    if typename == MediaTypeCodes.GQL_CAROUSEL:
        return MediaType.CAROUSEL
    if typename == MediaTypeCodes.GQL_VIDEO or dig_any(node, Paths.GQL_IS_VIDEO) is True:
        return MediaType.VIDEO
    return MediaType.IMAGE


# --------------------------------------------------------------------------- #
# Fetching
# --------------------------------------------------------------------------- #
class PostScraper:
    """Fetches a single post or reel by shortcode."""

    def __init__(self, browser: BrowserManager, settings: Settings) -> None:
        self._browser = browser
        self._settings = settings
        self._log = get_logger("post")

    async def fetch(self, shortcode: str) -> Post:
        """One post, by shortcode. Tries the cheap path first, then the expensive one."""
        try:
            post = await self._via_media_info(shortcode)
            self._log.info(f"scraped reel/post {shortcode} by @{post.creator}")
            return post
        except PostNotFound:
            # A 404 on the media endpoint is usually a real deletion, but it is
            # also what a restricted post returns. Confirm with a page load
            # before telling the caller the post is gone.
            self._log.debug(f"{shortcode}: media info 404 — confirming via page load")
        except SelectorChanged as exc:
            self._log.warning(f"{shortcode}: {exc} — falling back to page capture")

        post = await self._via_page(shortcode)
        self._log.info(f"scraped reel/post {shortcode} by @{post.creator} (fallback path)")
        return post

    async def _via_media_info(self, shortcode: str) -> Post:
        media_id = shortcode_to_media_id(shortcode)
        try:
            data = await self._browser.fetch_json(Endpoints.MEDIA_INFO.format(media_id=media_id))
        except NotFound as exc:
            raise PostNotFound(f"post {shortcode} not found") from exc

        item = dig_any(data, Paths.MEDIA_ITEM)
        if not item:
            raise SelectorChanged(f"media info for {shortcode} contained no items")
        return parse_api_item(item)

    async def _via_page(self, shortcode: str) -> Post:
        """Load the post page and read whichever JSON payload Instagram itself fetches."""
        url = post_url(shortcode)

        async with self._browser.page() as page:
            payload = await self._browser.capture_json(page, url, _looks_like_post)

            if payload is not None:
                node = dig_any(payload, Paths.PAGE_MEDIA)
                if node:
                    parser = parse_api_item if "pk" in node else parse_graphql_node
                    return parser(node)

            if await self._page_says_unavailable(page):
                raise PostNotFound(f"post {shortcode} is deleted or unavailable")

            self._log.warning(f"{shortcode}: no JSON payload captured — reading the DOM")
            return await self._from_dom(page, shortcode)

    async def _page_says_unavailable(self, page: Page) -> bool:
        try:
            return bool(await page.locator(Dom.POST_UNAVAILABLE).count())
        except PlaywrightError:
            return False

    async def _from_dom(self, page: Page, shortcode: str) -> Post:
        """Last resort. Honest about its limits: engagement counts are rarely in the DOM.

        This exists so a payload change degrades the result instead of failing the
        run — the agent still gets the caption, the timestamp, and the media URL,
        which is enough to write from. `likes`/`comments`/`views` come back `None`
        rather than 0, so nobody mistakes a fallback scrape for a post nobody liked.
        """

        async def text_of(selector: str) -> str | None:
            try:
                node = page.locator(selector).first
                return (await node.inner_text(timeout=3000)).strip() if await node.count() else None
            except PlaywrightError:
                return None

        async def attr_of(selector: str, name: str) -> str | None:
            try:
                node = page.locator(selector).first
                return await node.get_attribute(name, timeout=3000) if await node.count() else None
            except PlaywrightError:
                return None

        caption = await text_of(Dom.POST_CAPTION)
        creator = None
        try:
            # The canonical owner link is the first profile link in the article.
            href = await attr_of(f"{Dom.POST_ARTICLE} a[href^='/']", "href")
            if href:
                creator = href.strip("/").split("/")[0] or None
        except PlaywrightError:
            creator = None

        video = await attr_of(Dom.POST_VIDEO, "src")
        thumbnail = await attr_of(Dom.POST_IMAGE, "src")

        return _build(
            post_id=str(shortcode_to_media_id(shortcode)),
            shortcode=shortcode,
            creator=creator or "unknown",
            caption=caption,
            published_at=to_datetime(await attr_of(Dom.POST_TIME, "datetime")),
            likes=None,
            comments=None,
            views=None,
            media_type=MediaType.VIDEO if video else MediaType.IMAGE,
            thumbnail=thumbnail,
            video=video,
            images=[thumbnail] if thumbnail else [],
            location=None,
            tagged_users=[],
        )


def _looks_like_post(payload: Any) -> bool:
    """Does this captured response carry a single post's data?"""
    if not isinstance(payload, dict):
        return False
    if dig_any(payload, Paths.PAGE_MEDIA):
        return True
    items = dig(payload, "items")
    return isinstance(items, list) and len(items) == 1 and isinstance(items[0], dict)
