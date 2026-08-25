"""The typed shapes this package returns.

These models are the contract between the scraper and the AI agent driving it.
They are deliberately platform-neutral: `Post` carries a `platform` field and no
Instagram-specific naming, so when an X or LinkedIn backend is added later the
agent keeps consuming the same objects and needs no changes of its own.

Everything optional is genuinely optional. Instagram hides view counts on some
posts, omits like counts on others, and returns no location for most — modelling
those as required fields would mean either inventing zeros (a lie the agent
cannot distinguish from a real zero) or failing the scrape over a field nobody
needed. `None` means "Instagram did not tell us"; `0` means "Instagram said zero".
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class Platform(str, Enum):
    """Every platform the agent may eventually talk to, through one interface."""

    INSTAGRAM = "instagram"
    X = "x"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    THREADS = "threads"
    REDDIT = "reddit"


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    CAROUSEL = "carousel"
    REEL = "reel"


class _Base(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True, use_enum_values=False)


class Profile(_Base):
    """A creator's public profile."""

    platform: Platform = Platform.INSTAGRAM
    user_id: str | None = None
    username: str
    full_name: str | None = None
    biography: str | None = None
    followers: int | None = None
    following: int | None = None
    posts_count: int | None = Field(default=None, alias="total_posts")
    profile_image: str | None = None
    is_verified: bool = False
    is_private: bool = False
    is_business: bool = False
    category: str | None = None
    external_links: list[str] = Field(default_factory=list)
    url: str | None = None
    followed_by_viewer: bool = False
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_serializer("scraped_at")
    def _iso_scraped(self, value: datetime) -> str:
        return value.isoformat()


class Post(_Base):
    """One post or reel.

    Field order and naming follow the output schema in the brief, so
    `post.model_dump_json()` is the JSON the agent was promised.
    """

    platform: Platform = Platform.INSTAGRAM
    creator: str
    post_id: str
    shortcode: str | None = None
    url: str
    caption: str | None = None
    published_at: datetime | None = None
    likes: int | None = None
    comments: int | None = None
    views: int | None = None
    hashtags: list[str] = Field(default_factory=list)
    mentions: list[str] = Field(default_factory=list)
    tagged_users: list[str] = Field(default_factory=list)
    location: str | None = None
    media_type: MediaType = MediaType.IMAGE
    thumbnail: str | None = None
    video: str | None = None
    """Direct CDN video URL. Time-limited and signed — download promptly or re-scrape."""
    images: list[str] = Field(default_factory=list)
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("published_at", "scraped_at")
    @classmethod
    def _aware(cls, value: datetime | None) -> datetime | None:
        """Force UTC-aware datetimes.

        Naive and aware datetimes cannot be compared, and "is this post newer
        than the last one I stored" is the single most important comparison this
        package supports. Normalising on the way in means that comparison never
        raises at 2am inside the monitoring loop.
        """
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)

    @field_serializer("published_at", "scraped_at")
    def _iso(self, value: datetime | None) -> str | None:
        return value.isoformat() if value else None

    @property
    def is_video(self) -> bool:
        return self.media_type in (MediaType.VIDEO, MediaType.REEL)

    def to_json(self, indent: int | None = 2) -> str:
        return self.model_dump_json(indent=indent, exclude_none=False)


class DownloadResult(_Base):
    """Where a downloaded file landed."""

    post_id: str
    url: str
    path: str
    bytes_written: int
    content_type: str | None = None
    skipped_existing: bool = False


class MonitorResult(_Base):
    """One creator's slice of a daily monitoring run.

    Carries `error` rather than raising, because a monitoring run over twenty
    creators should not lose nineteen good results to one private account.
    """

    platform: Platform = Platform.INSTAGRAM
    creator: str
    new_posts: list[Post] = Field(default_factory=list)
    skipped_count: int = 0
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None

    def summary(self) -> dict[str, Any]:
        return {
            "creator": self.creator,
            "new": len(self.new_posts),
            "skipped": self.skipped_count,
            "error": self.error,
        }
