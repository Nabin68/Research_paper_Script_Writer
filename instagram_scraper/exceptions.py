"""Every error this package raises.

The rule for the AI agent driving this scraper: a `ScraperError` is a normal,
expected outcome that carries information (this account is private, this post was
deleted, this session expired). Anything else escaping the package is a bug.

The split that matters operationally is `RetryableError` vs the rest. Retryable
means "the same call might work in thirty seconds" — rate limits, timeouts,
network blips. Everything else is a fact about the world that retrying cannot
change, so `utils.with_retry` gives up on it immediately instead of burning three
attempts and 30 seconds of backoff on an account that does not exist.
"""

from __future__ import annotations


class ScraperError(Exception):
    """Base class for every error this package raises on purpose."""


class RetryableError(ScraperError):
    """Transient failure. Retrying the same call may succeed."""


# --------------------------------------------------------------------------- #
# Retryable
# --------------------------------------------------------------------------- #
class RateLimited(RetryableError):
    """Instagram asked us to slow down (HTTP 429, or its 'please wait' body)."""


class NetworkError(RetryableError):
    """DNS/connection/socket failure while talking to Instagram."""


class TimeoutError_(RetryableError):  # noqa: N801 - trailing _ avoids shadowing the builtin
    """A navigation or action exceeded its timeout."""


# Exported under the friendlier name; the class name keeps the underscore so it
# never shadows the builtin for anyone doing `from .exceptions import *`.
ScrapeTimeout = TimeoutError_


# --------------------------------------------------------------------------- #
# Terminal — retrying will not help
# --------------------------------------------------------------------------- #
class ConfigError(ScraperError):
    """The .env / Settings combination cannot work as given."""


class BrowserError(ScraperError):
    """Chromium could not be launched, or the context died mid-run."""


class LoginRequired(ScraperError):
    """No usable session. The user must complete an interactive login."""


class ChallengeRequired(LoginRequired):
    """Instagram is holding the session behind a checkpoint / 2FA / suspicious-login screen."""


class NotFound(ScraperError):
    """The requested thing is not there."""


class ProfileNotFound(NotFound):
    """No such username."""


class PostNotFound(NotFound):
    """The post/reel was deleted, or the shortcode is wrong."""


class PrivateProfile(ScraperError):
    """The account is private and the logged-in user does not follow it."""


class SelectorChanged(ScraperError):
    """Instagram's payload/DOM no longer contains a field we require.

    Raised instead of letting a `KeyError` or `None` propagate, so the failure
    names the field that moved rather than surfacing three frames deeper as an
    `AttributeError` on `NoneType`.
    """


class UnsupportedInput(ScraperError):
    """The given string is not a username, profile URL, post URL, or reel URL."""


class DownloadError(ScraperError):
    """A media file could not be fetched or written to disk."""
