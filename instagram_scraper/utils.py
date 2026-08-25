"""Shared helpers: input parsing, JSON digging, number parsing, delays, retries, logging.

Nothing here touches Playwright or Instagram's network. Everything is pure and
individually testable, which is the point — the fiddly logic (shortcode maths,
"12.3K" parsing, hashtag extraction) is exactly the code that benefits from being
exercisable without a browser.
"""

from __future__ import annotations

import asyncio
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Iterable, Sequence, TypeVar

from loguru import logger
from tenacity import (
    AsyncRetrying,
    RetryCallState,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import Settings
from .exceptions import RetryableError, UnsupportedInput

T = TypeVar("T")


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
_LOG_CONFIGURED = False


def setup_logging(settings: Settings, *, force: bool = False) -> None:
    """Point loguru at stderr (and optionally a file) at the configured level.

    Guarded by a module flag so constructing several scrapers in one process does
    not stack duplicate sinks and print every line three times.
    """
    global _LOG_CONFIGURED
    if _LOG_CONFIGURED and not force:
        return

    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format=(
            "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
            "<cyan>{extra[scope]: <9}</cyan> | <level>{message}</level>"
        ),
        backtrace=False,
        diagnose=False,
    )
    if settings.log_file:
        settings.log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            settings.log_file,
            level=settings.log_level,
            rotation="10 MB",
            retention="14 days",
            encoding="utf-8",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[scope]: <9} | {message}",
        )
    logger.configure(extra={"scope": "scraper"})
    _LOG_CONFIGURED = True


def get_logger(scope: str):
    """A logger tagged with which subsystem is speaking (browser, login, profile, ...)."""
    return logger.bind(scope=scope)


# --------------------------------------------------------------------------- #
# Input parsing
# --------------------------------------------------------------------------- #
_USERNAME_RE = re.compile(r"^[A-Za-z0-9._]{1,30}$")
_SHORTCODE_RE = re.compile(r"/(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)")
_PROFILE_PATH_RE = re.compile(r"instagram\.com/([A-Za-z0-9._]+)")

# Instagram paths that look like usernames but are not.
_RESERVED_PATHS = frozenset(
    {"p", "reel", "reels", "tv", "explore", "stories", "accounts", "direct",
     "about", "developer", "legal", "privacy", "terms", "api", "graphql"}
)


def normalize_username(value: str) -> str:
    """`@openai`, `openai`, `https://instagram.com/openai/?hl=en` -> `openai`."""
    raw = (value or "").strip()
    if not raw:
        raise UnsupportedInput("empty username")

    if "instagram.com" in raw:
        match = _PROFILE_PATH_RE.search(raw)
        if not match:
            raise UnsupportedInput(f"cannot read a username out of {value!r}")
        raw = match.group(1)

    raw = raw.lstrip("@").strip("/").split("?")[0].split("/")[0]
    if raw.lower() in _RESERVED_PATHS or not _USERNAME_RE.match(raw):
        raise UnsupportedInput(f"{value!r} is not a valid Instagram username")
    return raw.lower()


def extract_shortcode(value: str) -> str:
    """Pull the shortcode out of a post/reel URL, or accept a bare shortcode."""
    raw = (value or "").strip()
    if not raw:
        raise UnsupportedInput("empty post reference")

    match = _SHORTCODE_RE.search(raw)
    if match:
        return match.group(1)
    # A bare shortcode: 11 chars normally, but Instagram has issued longer ones.
    if re.fullmatch(r"[A-Za-z0-9_-]{5,30}", raw) and "instagram.com" not in raw:
        return raw
    raise UnsupportedInput(f"{value!r} is not a post or reel URL")


def classify_input(value: str) -> tuple[str, str]:
    """`("profile", username)` or `("post", shortcode)`. Raises `UnsupportedInput`."""
    raw = (value or "").strip()
    if _SHORTCODE_RE.search(raw):
        return "post", extract_shortcode(raw)
    return "profile", normalize_username(raw)


# Instagram shortcodes are just the media id written in this base64 alphabet.
_SHORTCODE_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
_ALPHABET_INDEX = {c: i for i, c in enumerate(_SHORTCODE_ALPHABET)}


def shortcode_to_media_id(shortcode: str) -> int:
    """Convert a shortcode to its numeric media id.

    Worth understanding, because it removes a whole class of fragility: the
    obvious way to fetch one post is a GraphQL call keyed by shortcode, which
    needs a `query_hash`/`doc_id` that Instagram rotates every few weeks. But the
    shortcode *is* the media id, base64-encoded in the alphabet above — so
    decoding it locally gets us straight to `/api/v1/media/{id}/info/` with no
    rotating token in the path at all.
    """
    media_id = 0
    for char in shortcode:
        try:
            media_id = media_id * 64 + _ALPHABET_INDEX[char]
        except KeyError as exc:
            raise UnsupportedInput(f"{shortcode!r} contains {char!r}, not a shortcode character") from exc
    return media_id


def media_id_to_shortcode(media_id: int | str) -> str:
    """Inverse of `shortcode_to_media_id`. Accepts `123_456` (id_userid) form."""
    value = int(str(media_id).split("_")[0])
    if value == 0:
        return _SHORTCODE_ALPHABET[0]
    out: list[str] = []
    while value > 0:
        value, remainder = divmod(value, 64)
        out.append(_SHORTCODE_ALPHABET[remainder])
    return "".join(reversed(out))


def post_url(shortcode: str, *, reel: bool = False) -> str:
    kind = "reel" if reel else "p"
    return f"https://www.instagram.com/{kind}/{shortcode}/"


# --------------------------------------------------------------------------- #
# JSON digging
# --------------------------------------------------------------------------- #
def dig(data: Any, path: str, default: Any = None) -> Any:
    """Read `a.b[0].c` out of nested dicts/lists, returning `default` on any miss.

    Deliberately total: a missing key, a `None` in the middle, or a list index
    off the end all return `default` rather than raising. Instagram omits fields
    per-session and per-account, and a `KeyError` three levels down is never the
    useful error — the useful error is raised by the caller, which knows whether
    the missing field was required.
    """
    current = data
    for segment in path.split("."):
        if current is None:
            return default
        key, *indices = re.split(r"\[(\d+)\]", segment)
        if key:
            if not isinstance(current, dict):
                return default
            current = current.get(key)
        for index in (int(i) for i in indices if i != ""):
            if not isinstance(current, (list, tuple)) or index >= len(current):
                return default
            current = current[index]
    return default if current is None else current


def dig_any(data: Any, paths: Sequence[str], default: Any = None) -> Any:
    """First non-None value among several candidate paths."""
    for path in paths:
        value = dig(data, path)
        if value is not None:
            return value
    return default


# --------------------------------------------------------------------------- #
# Value parsing
# --------------------------------------------------------------------------- #
def to_int(value: Any) -> int | None:
    """`"1,234"`, `"12.3K"`, `"1.2M"`, `1234` -> int. `None`/junk -> `None`.

    Returns `None` rather than 0 for unparseable input so the caller can tell
    "Instagram hid this count" apart from "this post genuinely has zero likes" —
    a distinction that matters when the agent ranks posts by engagement.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)

    text = re.sub(r"[,\s ]", "", str(value)).strip()
    if not text:
        return None
    match = re.match(r"^(\d+(?:\.\d+)?)([KMB])?$", text, re.I)
    if not match:
        digits = re.sub(r"\D", "", text)
        return int(digits) if digits else None
    number = float(match.group(1))
    if match.group(2):
        number *= {"k": 1e3, "m": 1e6, "b": 1e9}[match.group(2).lower()]
    return int(number)


def to_datetime(value: Any) -> datetime | None:
    """Epoch seconds, ISO strings, or `datetime` -> UTC-aware `datetime`."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None

    text = str(value).strip()
    if not text:
        return None
    if text.isdigit():
        return to_datetime(int(text))
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


_HASHTAG_RE = re.compile(r"#([A-Za-z0-9_À-ɏЀ-ӿ]+)")
_MENTION_RE = re.compile(r"@([A-Za-z0-9._]{1,30})")


def extract_hashtags(caption: str | None) -> list[str]:
    """Hashtags without the `#`, deduped, original order preserved."""
    return _dedupe(_HASHTAG_RE.findall(caption or ""))


def extract_mentions(caption: str | None) -> list[str]:
    """@-mentions without the `@`, deduped. Trailing dots stripped (`@foo.` -> `foo`)."""
    return _dedupe(m.rstrip(".") for m in _MENTION_RE.findall(caption or ""))


def _dedupe(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.lower()
        if item and key not in seen:
            seen.add(key)
            out.append(item)
    return out


def safe_filename(value: str, *, max_length: int = 120) -> str:
    """Make a string safe as a filename on Windows and POSIX alike."""
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip(" .")
    return (cleaned or "file")[:max_length]


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


# --------------------------------------------------------------------------- #
# Politeness
# --------------------------------------------------------------------------- #
class RateLimiter:
    """Random pauses between requests, sized differently per boundary.

    Fixed sleeps are a fingerprint — a request exactly every 3.000 seconds is not
    something a human produces. Random uniform delays across the configured range
    cost nothing extra on average and look far less mechanical.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._log = get_logger("limiter")

    async def between_posts(self) -> None:
        await self._sleep(self._settings.post_delay, "post")

    async def between_creators(self) -> None:
        await self._sleep(self._settings.creator_delay, "creator")

    async def _sleep(self, window: tuple[float, float], label: str) -> None:
        low, high = window
        if high <= 0:
            return
        delay = random.uniform(low, high)
        self._log.debug(f"pausing {delay:.1f}s between {label}s")
        await asyncio.sleep(delay)


# --------------------------------------------------------------------------- #
# Retries
# --------------------------------------------------------------------------- #
def _log_retry(scope: str) -> Callable[[RetryCallState], None]:
    log = get_logger(scope)

    def _hook(state: RetryCallState) -> None:
        exc = state.outcome.exception() if state.outcome else None
        wait = getattr(state.next_action, "sleep", 0.0)
        log.warning(
            f"attempt {state.attempt_number} failed "
            f"({type(exc).__name__}: {exc}) — retrying in {wait:.1f}s"
        )

    return _hook


async def with_retry(
    operation: Callable[[], Awaitable[T]],
    settings: Settings,
    *,
    scope: str = "retry",
) -> T:
    """Run `operation`, retrying only `RetryableError` with exponential backoff.

    Terminal errors (`ProfileNotFound`, `PrivateProfile`, `LoginRequired`) pass
    straight through on the first attempt. Retrying them would add a minute of
    backoff to a result that is already final and correct.
    """
    async for attempt in AsyncRetrying(
        retry=retry_if_exception_type(RetryableError),
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(
            multiplier=settings.retry_backoff_seconds,
            max=settings.retry_max_backoff_seconds,
        ),
        before_sleep=_log_retry(scope),
        reraise=True,
    ):
        with attempt:
            return await operation()
    raise AssertionError("unreachable: AsyncRetrying always returns or raises")
