"""Instagram scraper — public profiles and reels via Playwright, for an AI agent.

The interface the agent uses is six coroutines. It never touches Playwright, and
never manages a browser lifecycle:

    import asyncio
    from instagram_scraper import login, get_latest_posts, download_video, close

    async def main():
        await login()                                   # reuses storage_state.json
        posts = await get_latest_posts("openai", limit=5)   # only posts not seen before
        for post in posts:
            print(post.to_json())
            if post.is_video:
                result = await download_video(post)     # only if you ask
                print(result.path)
        await close()

    asyncio.run(main())

For several creators in one pass, `monitor()` paces between them and reports
per-creator failures instead of raising:

    from instagram_scraper import monitor
    for result in await monitor(["openai", "anthropicai"], limit=5):
        print(result.summary())

Adding another platform means subclassing `SocialScraper` (see `base.py`); the
agent's code does not change.
"""

from __future__ import annotations

from .base import SocialScraper
from .config import Settings, get_settings, load_settings
from .database import PostStore, SQLitePostStore, create_store
from .exceptions import (
    BrowserError,
    ChallengeRequired,
    ConfigError,
    DownloadError,
    LoginRequired,
    NetworkError,
    NotFound,
    PostNotFound,
    PrivateProfile,
    ProfileNotFound,
    RateLimited,
    RetryableError,
    ScrapeTimeout,
    ScraperError,
    SelectorChanged,
    UnsupportedInput,
)
from .main import (
    InstagramScraper,
    close,
    download_video,
    get_latest_posts,
    get_post,
    get_profile,
    get_scraper,
    login,
    main,
    monitor,
)
from .models import (
    DownloadResult,
    MediaType,
    MonitorResult,
    Platform,
    Post,
    Profile,
)

__version__ = "1.0.0"

__all__ = [
    # agent interface
    "login",
    "get_profile",
    "get_latest_posts",
    "get_post",
    "download_video",
    "monitor",
    "close",
    "get_scraper",
    # classes
    "InstagramScraper",
    "SocialScraper",
    "Settings",
    "PostStore",
    "SQLitePostStore",
    # models
    "Platform",
    "Post",
    "Profile",
    "MediaType",
    "MonitorResult",
    "DownloadResult",
    # config helpers
    "get_settings",
    "load_settings",
    "create_store",
    # exceptions
    "ScraperError",
    "RetryableError",
    "ConfigError",
    "BrowserError",
    "LoginRequired",
    "ChallengeRequired",
    "NotFound",
    "ProfileNotFound",
    "PostNotFound",
    "PrivateProfile",
    "RateLimited",
    "NetworkError",
    "ScrapeTimeout",
    "SelectorChanged",
    "UnsupportedInput",
    "DownloadError",
    "main",
    "__version__",
]
