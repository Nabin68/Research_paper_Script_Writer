"""Optional media downloads.

Nothing here runs unless the caller explicitly asks. The brief is firm that media
is not downloaded by default and that transcription belongs to another project —
so this module's whole job is to put a file on disk and hand back the path. What
happens to that file afterwards is somebody else's concern.

Downloads go through the browser context's request API rather than a separate
HTTP client, for two reasons: the CDN URLs are signed and expect the session's
cookies and a matching `Referer`, and reusing the context means no second TLS
stack, no second set of headers to keep in sync, and no chance of the two
disagreeing about who we are.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from playwright.async_api import Error as PlaywrightError

from .browser import BrowserManager
from .config import Settings
from .exceptions import DownloadError
from .models import DownloadResult, Post
from .utils import ensure_dir, get_logger, safe_filename

_EXTENSIONS = {
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

# Instagram's CDN happily serves multi-hundred-megabyte files; a runaway response
# should fail loudly rather than fill the disk.
_MAX_BYTES = 512 * 1024 * 1024


class MediaDownloader:
    """Writes a post's media to disk. Never called implicitly."""

    def __init__(self, browser: BrowserManager, settings: Settings) -> None:
        self._browser = browser
        self._settings = settings
        self._log = get_logger("download")

    async def download_video(self, post: Post, *, dest: Path | None = None) -> DownloadResult:
        """Download a post's video. Raises `DownloadError` if it has none."""
        if not post.video:
            raise DownloadError(
                f"post {post.shortcode or post.post_id} has no video URL "
                f"(media_type={post.media_type.value})"
            )
        return await self._download(post, post.video, dest=dest, kind="video")

    async def download_thumbnail(self, post: Post, *, dest: Path | None = None) -> DownloadResult:
        if not post.thumbnail:
            raise DownloadError(f"post {post.shortcode or post.post_id} has no thumbnail URL")
        return await self._download(post, post.thumbnail, dest=dest, kind="thumb")

    async def download_media(self, post: Post, *, dest: Path | None = None) -> DownloadResult:
        """Whatever this post's primary media is — video if there is one, else the image."""
        if post.video:
            return await self.download_video(post, dest=dest)
        return await self.download_thumbnail(post, dest=dest)

    # -- internals ---------------------------------------------------------- #
    async def _download(
        self, post: Post, url: str, *, dest: Path | None, kind: str
    ) -> DownloadResult:
        target = dest or self._default_path(post, url, kind)
        ensure_dir(target.parent)

        if target.exists() and target.stat().st_size > 0:
            self._log.info(f"already downloaded, skipping: {target.name}")
            return DownloadResult(
                post_id=post.post_id,
                url=url,
                path=str(target),
                bytes_written=target.stat().st_size,
                skipped_existing=True,
            )

        try:
            response = await self._browser.context.request.get(
                url,
                headers={
                    "referer": post.url or "https://www.instagram.com/",
                    "user-agent": self._settings.user_agent,
                },
                timeout=self._settings.nav_timeout_ms,
            )
        except PlaywrightError as exc:
            raise DownloadError(f"could not fetch {kind} for {post.post_id}: {exc}") from exc

        if not response.ok:
            # 403 here is nearly always an expired signature rather than a block:
            # these URLs are minted per-scrape and stop working within hours.
            hint = " (the CDN URL has likely expired — re-scrape the post)" if response.status == 403 else ""
            raise DownloadError(f"HTTP {response.status} downloading {kind} for {post.post_id}{hint}")

        body = await response.body()
        if len(body) > _MAX_BYTES:
            raise DownloadError(f"{kind} for {post.post_id} exceeds {_MAX_BYTES // 1024 // 1024}MB")
        if not body:
            raise DownloadError(f"{kind} for {post.post_id} came back empty")

        content_type = (response.headers or {}).get("content-type", "").split(";")[0].strip()
        target = self._with_extension(target, content_type)

        await asyncio.to_thread(target.write_bytes, body)
        self._log.success(f"saved {target.name} ({len(body) / 1_048_576:.1f} MB)")

        return DownloadResult(
            post_id=post.post_id,
            url=url,
            path=str(target),
            bytes_written=len(body),
            content_type=content_type or None,
        )

    def _default_path(self, post: Post, url: str, kind: str) -> Path:
        """`downloads/<creator>/<creator>_<shortcode>[_thumb].<ext>`.

        Named from the shortcode rather than a timestamp so the same post always
        maps to the same file — which is what makes the skip-if-exists check
        above actually prevent repeat downloads across runs.
        """
        stem = safe_filename(f"{post.creator}_{post.shortcode or post.post_id}")
        if kind != "video":
            stem = f"{stem}_{kind}"
        suffix = Path(url.split("?")[0]).suffix
        if suffix.lower() not in {".mp4", ".mov", ".jpg", ".jpeg", ".png", ".webp"}:
            suffix = ".mp4" if kind == "video" else ".jpg"
        return self._settings.download_dir / safe_filename(post.creator) / f"{stem}{suffix}"

    @staticmethod
    def _with_extension(path: Path, content_type: str) -> Path:
        """Correct the extension once the server has told us the real type."""
        expected = _EXTENSIONS.get(content_type)
        return path.with_suffix(expected) if expected and path.suffix != expected else path
