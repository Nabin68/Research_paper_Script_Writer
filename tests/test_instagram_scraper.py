#!/usr/bin/env python3
"""Tests for the parts of instagram_scraper that do not need a browser.

That is deliberately most of the risk. The Playwright layer is thin — launch a
browser, fetch a URL, hand back JSON — while the code that actually decides what
your data looks like is the parsing, the deduplication, and the retry policy.
All of that is pure, so all of it is tested here without touching the network.

Runs standalone (`python tests/test_instagram_scraper.py`) so it needs no test
runner installed, and is also collected normally by pytest if you have it.
"""

from __future__ import annotations

import asyncio
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from instagram_scraper.config import Settings, load_settings  # noqa: E402
from instagram_scraper.database import SQLitePostStore  # noqa: E402
from instagram_scraper.exceptions import (  # noqa: E402
    ConfigError,
    ProfileNotFound,
    RateLimited,
    SelectorChanged,
    UnsupportedInput,
)
from instagram_scraper.models import MediaType, Platform, Post  # noqa: E402
from instagram_scraper.profile import _external_links  # noqa: E402
from instagram_scraper.reel import parse_api_item, parse_graphql_node  # noqa: E402
from instagram_scraper.utils import (  # noqa: E402
    classify_input,
    dig,
    dig_any,
    extract_hashtags,
    extract_mentions,
    extract_shortcode,
    media_id_to_shortcode,
    normalize_username,
    safe_filename,
    shortcode_to_media_id,
    to_datetime,
    to_int,
    with_retry,
)

# --------------------------------------------------------------------------- #
# Fixtures — trimmed copies of the shapes Instagram actually returns
# --------------------------------------------------------------------------- #
REEL_ITEM = {
    "pk": "3245678901234567890",
    "id": "3245678901234567890_1234567",
    "code": "C8xYzAbCdEf",
    "taken_at": 1721304000,
    "media_type": 2,
    "product_type": "clips",
    "like_count": 15320,
    "comment_count": 342,
    "play_count": 324000,
    "caption": {"text": "New model drop. #AI #GPT thanks @samaltman and @greg.brockman."},
    "user": {"username": "OpenAI"},
    "image_versions2": {"candidates": [{"url": "https://cdn/thumb.jpg"}, {"url": "https://cdn/small.jpg"}]},
    "video_versions": [{"url": "https://cdn/video.mp4"}],
    "location": {"name": "San Francisco, California"},
    "usertags": {"in": [{"user": {"username": "samaltman"}}, {"user": {"username": "ilyasut"}}]},
}

CAROUSEL_ITEM = {
    "pk": 111222333,
    "code": "C9carousel",
    "taken_at": 1721390400,
    "media_type": 8,
    "like_count": 0,
    "comment_count": 12,
    "caption": {"text": "three slides"},
    "user": {"username": "someone"},
    "carousel_media": [
        {"image_versions2": {"candidates": [{"url": "https://cdn/1.jpg"}]}},
        {"image_versions2": {"candidates": [{"url": "https://cdn/2.jpg"}]}},
        {
            "image_versions2": {"candidates": [{"url": "https://cdn/3.jpg"}]},
            "video_versions": [{"url": "https://cdn/3.mp4"}],
        },
    ],
}

TIMELINE_EDGE = {
    "node": {
        "__typename": "GraphVideo",
        "id": "3245678901234567890",
        "shortcode": "C8xYzAbCdEf",
        "taken_at_timestamp": 1721304000,
        "is_video": True,
        "edge_media_to_caption": {"edges": [{"node": {"text": "hello #world @openai"}}]},
        "edge_media_preview_like": {"count": 900},
        "edge_media_to_comment": {"count": 45},
        "video_play_count": 12345,
        "owner": {"username": "OpenAI"},
        "display_url": "https://cdn/display.jpg",
        "video_url": "https://cdn/v.mp4",
        "edge_media_to_tagged_user": {"edges": [{"node": {"user": {"username": "tagged1"}}}]},
    }
}

PROFILE_USER = {
    "id": "1234567",
    "username": "openai",
    "full_name": "OpenAI",
    "biography": "Creating safe AGI.",
    "edge_followed_by": {"count": 4200000},
    "edge_follow": {"count": 12},
    "edge_owner_to_timeline_media": {"count": 830, "edges": [TIMELINE_EDGE]},
    "profile_pic_url_hd": "https://cdn/pic.jpg",
    "is_verified": True,
    "is_private": False,
    "external_url": "https://openai.com",
    "bio_links": [{"url": "https://openai.com"}, {"url": "https://openai.com/careers"}],
}


# --------------------------------------------------------------------------- #
# Harness
# --------------------------------------------------------------------------- #
_PASSED = 0
_FAILED: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    global _PASSED
    if condition:
        _PASSED += 1
    else:
        _FAILED.append(f"{name}{': ' + detail if detail else ''}")


def raises(name: str, exc_type: type[BaseException], fn, *args, **kwargs) -> None:
    try:
        fn(*args, **kwargs)
    except exc_type:
        check(name, True)
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"raised {type(exc).__name__} instead of {exc_type.__name__}")
    else:
        check(name, False, f"did not raise {exc_type.__name__}")


# --------------------------------------------------------------------------- #
# Input parsing
# --------------------------------------------------------------------------- #
def test_input_parsing() -> None:
    for raw in ("openai", "@openai", "OpenAI", "https://www.instagram.com/openai/",
                "instagram.com/openai/?hl=en", "https://instagram.com/openai"):
        check(f"normalize_username({raw!r})", normalize_username(raw) == "openai",
              f"got {normalize_username(raw)!r}")

    raises("username rejects post URL", UnsupportedInput, normalize_username,
           "https://www.instagram.com/p/ABC123/")
    raises("username rejects empty", UnsupportedInput, normalize_username, "")
    raises("username rejects reserved path", UnsupportedInput, normalize_username, "explore")
    raises("username rejects bad chars", UnsupportedInput, normalize_username, "not a name!")

    for raw, expected in (
        ("https://www.instagram.com/reel/C8xYzAbCdEf/", "C8xYzAbCdEf"),
        ("https://www.instagram.com/p/C8xYzAbCdEf/?img_index=1", "C8xYzAbCdEf"),
        ("https://www.instagram.com/reels/C8xYzAbCdEf/", "C8xYzAbCdEf"),
        ("https://www.instagram.com/tv/C8xYzAbCdEf/", "C8xYzAbCdEf"),
        ("C8xYzAbCdEf", "C8xYzAbCdEf"),
    ):
        check(f"extract_shortcode({raw!r})", extract_shortcode(raw) == expected,
              f"got {extract_shortcode(raw)!r}")

    check("classify profile", classify_input("https://www.instagram.com/openai/") == ("profile", "openai"))
    check("classify post", classify_input("https://www.instagram.com/reel/ABC/") == ("post", "ABC"))
    check("classify handle", classify_input("@openai") == ("profile", "openai"))


def test_shortcode_math() -> None:
    check("shortcode 'A' -> 0", shortcode_to_media_id("A") == 0)
    check("shortcode 'B' -> 1", shortcode_to_media_id("B") == 1)
    check("shortcode 'BA' -> 64", shortcode_to_media_id("BA") == 64)
    check("media_id 0 -> 'A'", media_id_to_shortcode(0) == "A")

    for shortcode in ("C8xYzAbCdEf", "BsOGulcndj-", "Cq_9-_1n7Uz", "C-_a1b2C3d4"):
        roundtrip = media_id_to_shortcode(shortcode_to_media_id(shortcode))
        check(f"roundtrip {shortcode}", roundtrip == shortcode, f"got {roundtrip}")

    check("media_id strips owner suffix",
          media_id_to_shortcode("3245678901234567890_1234567")
          == media_id_to_shortcode(3245678901234567890))
    raises("bad shortcode char", UnsupportedInput, shortcode_to_media_id, "abc!def")


# --------------------------------------------------------------------------- #
# Value helpers
# --------------------------------------------------------------------------- #
def test_dig() -> None:
    data = {"a": {"b": [{"c": 1}, {"c": 2}]}, "empty": None, "list": [10, 20]}
    check("dig nested list", dig(data, "a.b[1].c") == 2)
    check("dig missing key", dig(data, "a.zzz", "fallback") == "fallback")
    check("dig through None", dig(data, "empty.b.c", "fallback") == "fallback")
    check("dig index overflow", dig(data, "list[9]", "fallback") == "fallback")
    check("dig wrong type", dig(data, "list.key", "fallback") == "fallback")
    check("dig top level", dig(data, "list") == [10, 20])
    check("dig_any first hit", dig_any(data, ("nope.x", "a.b[0].c")) == 1)
    check("dig_any all miss", dig_any(data, ("x", "y"), "d") == "d")


def test_to_int() -> None:
    cases = {
        "1,234": 1234, "12.3K": 12300, "1.2M": 1200000, "3B": 3000000000,
        "45": 45, 45: 45, 45.9: 45, "": None, None: None, "abc": None,
        "1 234": 1234, True: None,
    }
    for raw, expected in cases.items():
        check(f"to_int({raw!r})", to_int(raw) == expected, f"got {to_int(raw)!r}")
    # The distinction the whole model depends on: hidden count vs real zero.
    check("to_int None is not 0", to_int(None) is None)
    check("to_int 0 is 0", to_int(0) == 0)


def test_to_datetime() -> None:
    expected = datetime(2024, 7, 18, 12, 0, tzinfo=timezone.utc)
    check("epoch int", to_datetime(1721304000) == expected)
    check("epoch string", to_datetime("1721304000") == expected)
    check("iso with Z", to_datetime("2024-07-18T12:00:00Z") == expected)
    check("iso with offset", to_datetime("2024-07-18T12:00:00+00:00") == expected)
    check("naive becomes utc", to_datetime(datetime(2024, 7, 18, 12, 0)) == expected)
    check("none", to_datetime(None) is None)
    check("junk", to_datetime("not a date") is None)


def test_caption_extraction() -> None:
    caption = "Big #AI news! #ai again, #GPT-4 out. cc @samaltman @greg.brockman @samaltman."
    tags = extract_hashtags(caption)
    check("hashtags found", tags == ["AI", "GPT"], f"got {tags}")
    mentions = extract_mentions(caption)
    check("mentions deduped case-insensitively", mentions == ["samaltman", "greg.brockman"],
          f"got {mentions}")
    check("empty caption", extract_hashtags(None) == [] and extract_mentions(None) == [])
    check("safe_filename strips separators",
          "/" not in safe_filename("a/b:c*d") and safe_filename("") == "file")


# --------------------------------------------------------------------------- #
# Parsers
# --------------------------------------------------------------------------- #
def test_parse_reel() -> None:
    post = parse_api_item(REEL_ITEM)
    check("reel post_id", post.post_id == "3245678901234567890", post.post_id)
    check("reel shortcode", post.shortcode == "C8xYzAbCdEf")
    check("reel creator lowercased", post.creator == "openai", post.creator)
    check("reel media type", post.media_type is MediaType.REEL, str(post.media_type))
    check("reel url is /reel/", post.url == "https://www.instagram.com/reel/C8xYzAbCdEf/", post.url)
    check("reel likes", post.likes == 15320)
    check("reel comments", post.comments == 342)
    check("reel views", post.views == 324000)
    check("reel published", post.published_at == datetime(2024, 7, 18, 12, 0, tzinfo=timezone.utc))
    check("reel hashtags", post.hashtags == ["AI", "GPT"], str(post.hashtags))
    check("reel mentions", post.mentions == ["samaltman", "greg.brockman"], str(post.mentions))
    check("reel tagged users", post.tagged_users == ["samaltman", "ilyasut"])
    check("reel location", post.location == "San Francisco, California")
    check("reel thumbnail is first candidate", post.thumbnail == "https://cdn/thumb.jpg")
    check("reel video", post.video == "https://cdn/video.mp4")
    check("reel is_video", post.is_video is True)
    check("reel platform", post.platform is Platform.INSTAGRAM)

    # The exact JSON contract promised in the brief.
    payload = post.model_dump(mode="json")
    for field in ("platform", "creator", "post_id", "caption", "likes", "comments",
                  "views", "hashtags", "mentions", "published_at", "url", "thumbnail", "video"):
        check(f"schema has {field}", field in payload)
    check("schema platform value", payload["platform"] == "instagram")
    check("published_at serialises to iso", payload["published_at"].startswith("2024-07-18T12:00:00"))


def test_parse_carousel() -> None:
    post = parse_api_item(CAROUSEL_ITEM)
    check("carousel type", post.media_type is MediaType.CAROUSEL)
    check("carousel images", post.images == ["https://cdn/1.jpg", "https://cdn/2.jpg", "https://cdn/3.jpg"],
          str(post.images))
    check("carousel video from child", post.video == "https://cdn/3.mp4", str(post.video))
    check("carousel int pk becomes str", post.post_id == "111222333")
    # A real zero must survive as 0, not become None.
    check("carousel zero likes preserved", post.likes == 0, str(post.likes))
    check("carousel views absent", post.views is None)
    check("carousel url is /p/", post.url == "https://www.instagram.com/p/C9carousel/")


def test_parse_graphql() -> None:
    post = parse_graphql_node(TIMELINE_EDGE)
    check("gql unwraps node", post.shortcode == "C8xYzAbCdEf")
    check("gql creator", post.creator == "openai")
    check("gql video type", post.media_type is MediaType.VIDEO)
    check("gql likes", post.likes == 900)
    check("gql comments", post.comments == 45)
    check("gql views", post.views == 12345)
    check("gql tagged", post.tagged_users == ["tagged1"])
    check("gql hashtags", post.hashtags == ["world"])
    check("gql thumbnail", post.thumbnail == "https://cdn/display.jpg")

    # Creator fallback when the payload omits the owner (feed responses do this).
    stripped = {k: v for k, v in TIMELINE_EDGE["node"].items() if k != "owner"}
    check("gql creator fallback", parse_graphql_node(stripped, creator="fallback").creator == "fallback")
    raises("gql no creator anywhere", SelectorChanged, parse_graphql_node, stripped)
    raises("api no pk", SelectorChanged, parse_api_item, {"code": "x", "user": {"username": "u"}})
    raises("api not a dict", SelectorChanged, parse_api_item, ["not", "a", "dict"])


def test_profile_links() -> None:
    links = _external_links(PROFILE_USER)
    check("links merged and deduped",
          links == ["https://openai.com", "https://openai.com/careers"], str(links))
    check("no links", _external_links({}) == [])


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
def test_settings() -> None:
    settings = Settings()
    check("default headless", settings.headless is True)
    check("default no media download", settings.download_media is False)
    check("default post delay", settings.post_delay == (2.0, 6.0))
    check("default creator delay", settings.creator_delay == (5.0, 15.0))
    check("viewport dict", settings.viewport == {"width": 1366, "height": 900})

    check("reversed range is corrected", Settings(post_delay=(9.0, 1.0)).post_delay == (1.0, 9.0))
    raises("bad log level", ValueError, Settings, log_level="CHATTY")
    raises("negative delay", ValueError, Settings, post_delay=(-1.0, 5.0))
    raises("incoherent backoff", ValueError, Settings,
           retry_backoff_seconds=10.0, retry_max_backoff_seconds=1.0)
    raises("unknown field", ValueError, Settings, nonsense=True)

    frozen = Settings()
    try:
        frozen.headless = False  # type: ignore[misc]
        check("settings frozen", False, "mutation allowed")
    except Exception:
        check("settings frozen", True)

    check("override applies", load_settings(headless=False).headless is False)
    raises("bad env value", ConfigError, load_settings, log_level="NOPE")


# --------------------------------------------------------------------------- #
# Async: ledger + retries
# --------------------------------------------------------------------------- #
def _post(post_id: str, creator: str = "openai", when: int = 1721304000) -> Post:
    return Post(
        creator=creator,
        post_id=post_id,
        shortcode=f"sc{post_id}",
        url=f"https://www.instagram.com/p/sc{post_id}/",
        caption="x",
        published_at=to_datetime(when),
        media_type=MediaType.REEL,
    )


async def test_store() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = SQLitePostStore(Path(tmp) / "test.db")
        await store.connect()

        posts = [_post("1"), _post("2"), _post("3")]
        fresh, skipped = await store.filter_new(posts)
        check("nothing seen initially", len(fresh) == 3 and skipped == 0)

        written = await store.record(posts)
        check("recorded three", written == 3, str(written))

        fresh, skipped = await store.filter_new(posts)
        check("all seen on second pass", fresh == [] and skipped == 3, f"{len(fresh)}/{skipped}")

        mixed = [_post("2"), _post("4")]
        fresh, skipped = await store.filter_new(mixed)
        check("only the new one survives", [p.post_id for p in fresh] == ["4"] and skipped == 1)

        check("is_seen true", await store.is_seen("instagram", "1") is True)
        check("is_seen false", await store.is_seen("instagram", "999") is False)

        # Re-recording must not duplicate or bump scraped_at.
        check("re-record is a no-op", await store.record(posts) == 0)

        newest = await store.latest_seen("instagram", "openai")
        check("latest_seen returns publish time", newest == to_datetime(1721304000), str(newest))
        check("latest_seen unknown creator", await store.latest_seen("instagram", "nobody") is None)

        stats = await store.stats()
        check("stats total", stats["total_posts"] == 3, str(stats))
        check("stats by creator", stats["creators"].get("openai") == 3)

        # Chunking path: more IDs than the SQLite variable limit allows in one IN().
        many = [_post(str(i)) for i in range(1200)]
        await store.record(many)
        fresh, skipped = await store.filter_new(many)
        check("1200-post dedup chunks correctly", fresh == [] and skipped == 1200, f"{len(fresh)}")

        await store.set_meta("last_run", "2026-07-20")
        check("meta roundtrip", await store.get_meta("last_run") == "2026-07-20")
        check("meta missing", await store.get_meta("nope") is None)

        await store.close()


async def test_retry() -> None:
    settings = Settings(max_retries=3, retry_backoff_seconds=0.001, retry_max_backoff_seconds=0.002)

    attempts = {"n": 0}

    async def flaky():
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise RateLimited("slow down")
        return "recovered"

    result = await with_retry(flaky, settings)
    check("retries transient errors", result == "recovered" and attempts["n"] == 3, str(attempts))

    terminal = {"n": 0}

    async def missing():
        terminal["n"] += 1
        raise ProfileNotFound("no such user")

    try:
        await with_retry(missing, settings)
        check("terminal error propagates", False, "no exception")
    except ProfileNotFound:
        check("terminal error propagates", True)
    check("terminal error not retried", terminal["n"] == 1, f"tried {terminal['n']} times")

    exhausted = {"n": 0}

    async def always_limited():
        exhausted["n"] += 1
        raise RateLimited("nope")

    try:
        await with_retry(always_limited, settings)
        check("gives up after max_retries", False, "no exception")
    except RateLimited:
        check("gives up after max_retries", exhausted["n"] == 3, f"tried {exhausted['n']} times")


# --------------------------------------------------------------------------- #
def run() -> int:
    for test in (test_input_parsing, test_shortcode_math, test_dig, test_to_int,
                 test_to_datetime, test_caption_extraction, test_parse_reel,
                 test_parse_carousel, test_parse_graphql, test_profile_links, test_settings):
        test()

    asyncio.run(test_store())
    asyncio.run(test_retry())

    print(f"\n{_PASSED} passed, {len(_FAILED)} failed")
    for failure in _FAILED:
        print(f"  FAIL  {failure}")
    return 1 if _FAILED else 0


if __name__ == "__main__":
    raise SystemExit(run())
