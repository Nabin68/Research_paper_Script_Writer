"""Runtime configuration, read from the environment and the local .env file.

Everything tunable lives here as a single frozen `Settings` object that is built
once and passed down the object graph — no module reaches back into `os.environ`
on its own. That is what makes the package testable: a caller can hand in
`Settings(headless=False, post_delay=(0, 0))` and get a headed, undelayed run
without touching a file or an environment variable.

`.env` is read from the project root (the directory containing this package), so
this shares the same file as the rest of the project.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .exceptions import ConfigError

PACKAGE_DIR: Path = Path(__file__).resolve().parent
PROJECT_ROOT: Path = PACKAGE_DIR.parent
ENV_PATH: Path = PROJECT_ROOT / ".env"

# Instagram's own web client identifies itself with this app id on every internal
# API call. Without the header those endpoints answer 401 even with a valid
# session cookie, so it is required, not optional. It is a public constant baked
# into Instagram's JS bundle, not a credential.
DEFAULT_IG_APP_ID = "936619743392459"

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


# --------------------------------------------------------------------------- #
# Environment parsing
# --------------------------------------------------------------------------- #
def _get(key: str, default: str = "") -> str:
    """Read KEY, falling back to IG_KEY.

    The spec names four bare variables (HEADLESS, DOWNLOAD_MEDIA, DATABASE,
    SESSION_FILE). The rest are prefixed to avoid colliding with anything else in
    a shared .env, and the bare form is accepted for all of them anyway so nobody
    has to remember which is which.
    """
    for name in (key, f"IG_{key}"):
        value = os.environ.get(name)
        if value is not None and value.strip():
            return value.strip()
    return default


def _bool(key: str, default: bool) -> bool:
    raw = _get(key).lower()
    if not raw:
        return default
    if raw in {"1", "true", "yes", "y", "on"}:
        return True
    if raw in {"0", "false", "no", "n", "off"}:
        return False
    raise ConfigError(f"{key}={raw!r} is not a boolean (use true/false)")


def _int(key: str, default: int) -> int:
    raw = _get(key)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"{key}={raw!r} is not an integer") from exc


def _float(key: str, default: float) -> float:
    raw = _get(key)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigError(f"{key}={raw!r} is not a number") from exc


def _path(key: str, default: str) -> Path:
    raw = _get(key, default)
    path = Path(raw).expanduser()
    return path if path.is_absolute() else (PROJECT_ROOT / path)


def _range(key: str, default: tuple[float, float]) -> tuple[float, float]:
    """Parse `MIN,MAX` (or a single number meaning a fixed delay)."""
    raw = _get(key)
    if not raw:
        return default
    parts = [p.strip() for p in raw.replace("-", ",").split(",") if p.strip()]
    try:
        values = [float(p) for p in parts]
    except ValueError as exc:
        raise ConfigError(f"{key}={raw!r} is not a 'min,max' range") from exc
    if len(values) == 1:
        return values[0], values[0]
    if len(values) == 2:
        return values[0], values[1]
    raise ConfigError(f"{key}={raw!r} must be one number or two")


# --------------------------------------------------------------------------- #
# Settings
# --------------------------------------------------------------------------- #
class Settings(BaseModel):
    """Immutable runtime configuration for one scraper instance."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    # -- browser ------------------------------------------------------------ #
    headless: bool = True
    slow_mo_ms: int = Field(default=0, ge=0)
    """Milliseconds to pause between Playwright actions. Debugging aid only."""

    user_agent: str = DEFAULT_USER_AGENT
    locale: str = "en-US"
    timezone_id: str = "UTC"
    viewport_width: int = Field(default=1366, gt=0)
    viewport_height: int = Field(default=900, gt=0)
    proxy: str | None = None
    block_assets: bool = True
    """Drop image/font/media requests on scraping pages.

    Every field we extract comes out of Instagram's JSON, never out of a rendered
    pixel, so downloading avatars and video segments on each page load is pure
    cost — it roughly triples page weight for data we already have as URLs.
    Downloads bypass this because they use the context's request API, not a page.
    """

    # -- session ------------------------------------------------------------ #
    session_file: Path = PROJECT_ROOT / "storage_state.json"
    interactive_login: bool = True
    """On an expired session, open a headed window and wait for a human.

    Turn this off for unattended runs: the scraper then raises `LoginRequired`
    immediately instead of blocking on a login window nobody is sitting in front
    of. It would time out eventually, but failing in two seconds beats failing in
    five minutes.
    """
    login_timeout_seconds: int = Field(default=300, gt=0)

    # -- storage ------------------------------------------------------------ #
    database: Literal["sqlite"] = "sqlite"
    db_path: Path = PROJECT_ROOT / "instagram_scraper" / "data" / "instagram.db"
    download_media: bool = False
    download_dir: Path = PROJECT_ROOT / "downloads"

    # -- timeouts and retries ----------------------------------------------- #
    nav_timeout_ms: int = Field(default=45_000, gt=0)
    action_timeout_ms: int = Field(default=15_000, gt=0)
    max_retries: int = Field(default=3, ge=1)
    retry_backoff_seconds: float = Field(default=2.0, gt=0)
    retry_max_backoff_seconds: float = Field(default=60.0, gt=0)

    # -- politeness --------------------------------------------------------- #
    post_delay: tuple[float, float] = (2.0, 6.0)
    """Random pause between individual post/page requests."""
    creator_delay: tuple[float, float] = (5.0, 15.0)
    """Random pause between one creator and the next."""

    # -- misc --------------------------------------------------------------- #
    ig_app_id: str = DEFAULT_IG_APP_ID
    log_level: str = "INFO"
    log_file: Path | None = None

    @field_validator("post_delay", "creator_delay")
    @classmethod
    def _ordered_range(cls, value: tuple[float, float]) -> tuple[float, float]:
        low, high = value
        if low < 0 or high < 0:
            raise ValueError("delays cannot be negative")
        return (low, high) if low <= high else (high, low)

    @field_validator("log_level")
    @classmethod
    def _known_level(cls, value: str) -> str:
        level = value.upper()
        allowed = {"TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"}
        if level not in allowed:
            raise ValueError(f"log_level must be one of {sorted(allowed)}")
        return level

    @model_validator(mode="after")
    def _coherent(self) -> Settings:
        if self.retry_max_backoff_seconds < self.retry_backoff_seconds:
            raise ValueError("retry_max_backoff_seconds must be >= retry_backoff_seconds")
        return self

    # -- derived ------------------------------------------------------------ #
    @property
    def viewport(self) -> dict[str, int]:
        return {"width": self.viewport_width, "height": self.viewport_height}

    def ensure_dirs(self) -> None:
        """Create the directories our writable paths live in."""
        for path in (self.db_path.parent, self.download_dir, self.session_file.parent):
            path.mkdir(parents=True, exist_ok=True)


def load_settings(**overrides: object) -> Settings:
    """Build `Settings` from .env + environment, with explicit keyword overrides on top."""
    load_dotenv(ENV_PATH, override=False)

    values: dict[str, object] = {
        "headless": _bool("HEADLESS", True),
        "slow_mo_ms": _int("SLOW_MO_MS", 0),
        "user_agent": _get("USER_AGENT", DEFAULT_USER_AGENT),
        "locale": _get("LOCALE", "en-US"),
        "timezone_id": _get("TIMEZONE", "UTC"),
        "viewport_width": _int("VIEWPORT_WIDTH", 1366),
        "viewport_height": _int("VIEWPORT_HEIGHT", 900),
        "proxy": _get("PROXY") or None,
        "block_assets": _bool("BLOCK_ASSETS", True),
        "session_file": _path("SESSION_FILE", "storage_state.json"),
        "interactive_login": _bool("INTERACTIVE_LOGIN", True),
        "login_timeout_seconds": _int("LOGIN_TIMEOUT_SECONDS", 300),
        "database": _get("DATABASE", "sqlite").lower(),
        "db_path": _path("DB_PATH", "instagram_scraper/data/instagram.db"),
        "download_media": _bool("DOWNLOAD_MEDIA", False),
        "download_dir": _path("DOWNLOAD_DIR", "downloads"),
        "nav_timeout_ms": _int("NAV_TIMEOUT_MS", 45_000),
        "action_timeout_ms": _int("ACTION_TIMEOUT_MS", 15_000),
        "max_retries": _int("MAX_RETRIES", 3),
        "retry_backoff_seconds": _float("RETRY_BACKOFF_SECONDS", 2.0),
        "retry_max_backoff_seconds": _float("RETRY_MAX_BACKOFF_SECONDS", 60.0),
        "post_delay": _range("POST_DELAY", (2.0, 6.0)),
        "creator_delay": _range("CREATOR_DELAY", (5.0, 15.0)),
        "ig_app_id": _get("APP_ID", DEFAULT_IG_APP_ID),
        "log_level": _get("LOG_LEVEL", "INFO"),
        "log_file": _path("LOG_FILE", "") if _get("LOG_FILE") else None,
    }
    values.update(overrides)

    try:
        return Settings(**values)  # type: ignore[arg-type]
    except ValueError as exc:  # pydantic ValidationError is a ValueError
        raise ConfigError(f"invalid configuration: {exc}") from exc


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Process-wide default settings, built on first use."""
    return load_settings()
