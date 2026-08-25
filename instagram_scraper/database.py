"""The seen-posts ledger — what makes daily monitoring incremental.

Without this the agent re-reads and re-processes the same twelve posts every
morning. With it, `get_latest_posts()` still asks Instagram for the newest posts
(there is no way to ask "only what is new"), but everything already recorded is
filtered out before it reaches the agent, so a quiet day costs one request and
returns an empty list.

Storage is behind the `PostStore` interface rather than called directly, because
the brief flags PostgreSQL as a later option. Swapping backends means adding one
class and one line in `create_store` — nothing above this file changes.

Concurrency: sqlite3 is synchronous, so every call is pushed to a worker thread
with `asyncio.to_thread` and serialised behind a lock. One connection, one writer
at a time — which is what sqlite wants anyway, and this workload is a handful of
writes per creator per day, not a throughput problem.
"""

from __future__ import annotations

import asyncio
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

from .config import Settings
from .exceptions import ConfigError
from .models import Post
from .utils import get_logger

_SCHEMA = """
CREATE TABLE IF NOT EXISTS seen_posts (
    platform    TEXT NOT NULL,
    post_id     TEXT NOT NULL,
    creator     TEXT NOT NULL,
    shortcode   TEXT,
    url         TEXT,
    created_at  TEXT,
    scraped_at  TEXT NOT NULL,
    media_type  TEXT,
    likes       INTEGER,
    comments    INTEGER,
    views       INTEGER,
    payload     TEXT,
    PRIMARY KEY (platform, post_id)
);

CREATE INDEX IF NOT EXISTS idx_seen_creator
    ON seen_posts (platform, creator, created_at DESC);

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


class PostStore(ABC):
    """What the scraper needs from a datastore. Implement this to add a backend."""

    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def close(self) -> None: ...

    @abstractmethod
    async def is_seen(self, platform: str, post_id: str) -> bool: ...

    @abstractmethod
    async def seen_ids(self, platform: str, post_ids: Sequence[str]) -> set[str]: ...

    @abstractmethod
    async def record(self, posts: Iterable[Post]) -> int: ...

    @abstractmethod
    async def latest_seen(self, platform: str, creator: str) -> datetime | None: ...

    @abstractmethod
    async def stats(self) -> dict[str, Any]: ...

    async def filter_new(self, posts: Sequence[Post]) -> tuple[list[Post], int]:
        """Split posts into (unseen, count_skipped).

        Implemented once here on the interface: it is one set lookup over
        `seen_ids`, and no backend has a reason to do it differently.
        """
        if not posts:
            return [], 0
        platform = str(posts[0].platform.value)
        known = await self.seen_ids(platform, [p.post_id for p in posts])
        fresh = [p for p in posts if p.post_id not in known]
        return fresh, len(posts) - len(fresh)


class SQLitePostStore(PostStore):
    """SQLite-backed ledger. Default, and enough for a single-machine daily agent."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._conn: sqlite3.Connection | None = None
        self._lock = asyncio.Lock()
        self._log = get_logger("database")

    async def connect(self) -> None:
        if self._conn is not None:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)

        def _open() -> sqlite3.Connection:
            conn = sqlite3.connect(self._path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            # WAL so a long read cannot block the write that follows it, and
            # because it survives an interrupted run far better than the default.
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.executescript(_SCHEMA)
            conn.commit()
            return conn

        self._conn = await asyncio.to_thread(_open)
        self._log.debug(f"ledger open at {self._path}")

    async def close(self) -> None:
        if self._conn is None:
            return
        conn, self._conn = self._conn, None
        await asyncio.to_thread(conn.close)

    def _require(self) -> sqlite3.Connection:
        if self._conn is None:
            raise ConfigError("database not connected — call connect() first")
        return self._conn

    async def _run(self, fn, *args):  # type: ignore[no-untyped-def]
        conn = self._require()
        async with self._lock:
            return await asyncio.to_thread(fn, conn, *args)

    # -- reads -------------------------------------------------------------- #
    async def is_seen(self, platform: str, post_id: str) -> bool:
        def _query(conn: sqlite3.Connection) -> bool:
            row = conn.execute(
                "SELECT 1 FROM seen_posts WHERE platform = ? AND post_id = ?",
                (platform, post_id),
            ).fetchone()
            return row is not None

        return await self._run(_query)

    async def seen_ids(self, platform: str, post_ids: Sequence[str]) -> set[str]:
        if not post_ids:
            return set()

        def _query(conn: sqlite3.Connection) -> set[str]:
            found: set[str] = set()
            # Chunked to stay under SQLite's variable limit (999 by default);
            # a limit=500 monitoring call would otherwise blow up here.
            for start in range(0, len(post_ids), 400):
                chunk = post_ids[start : start + 400]
                placeholders = ",".join("?" * len(chunk))
                rows = conn.execute(
                    f"SELECT post_id FROM seen_posts WHERE platform = ? AND post_id IN ({placeholders})",
                    (platform, *chunk),
                ).fetchall()
                found.update(row["post_id"] for row in rows)
            return found

        return await self._run(_query)

    async def latest_seen(self, platform: str, creator: str) -> datetime | None:
        def _query(conn: sqlite3.Connection) -> datetime | None:
            row = conn.execute(
                "SELECT MAX(created_at) AS newest FROM seen_posts "
                "WHERE platform = ? AND creator = ?",
                (platform, creator.lower()),
            ).fetchone()
            if not row or not row["newest"]:
                return None
            try:
                return datetime.fromisoformat(row["newest"])
            except ValueError:
                return None

        return await self._run(_query)

    async def stats(self) -> dict[str, Any]:
        def _query(conn: sqlite3.Connection) -> dict[str, Any]:
            total = conn.execute("SELECT COUNT(*) AS n FROM seen_posts").fetchone()["n"]
            creators = conn.execute(
                "SELECT creator, COUNT(*) AS n FROM seen_posts "
                "GROUP BY creator ORDER BY n DESC"
            ).fetchall()
            return {
                "total_posts": total,
                "creators": {row["creator"]: row["n"] for row in creators},
                "path": str(self._path),
            }

        return await self._run(_query)

    # -- writes ------------------------------------------------------------- #
    async def record(self, posts: Iterable[Post]) -> int:
        """Insert posts that are not already stored. Returns how many were new.

        `INSERT OR IGNORE` rather than upsert, on purpose: `scraped_at` means
        "when we first saw this", and re-recording a post on a later run would
        overwrite that with today. Engagement counts do drift after the fact, but
        the ledger's job is deduplication, not analytics — the full payload of
        the first sighting is kept, and anything wanting live counts should
        re-fetch the post.
        """
        rows = [
            (
                str(post.platform.value),
                post.post_id,
                post.creator.lower(),
                post.shortcode,
                post.url,
                post.published_at.isoformat() if post.published_at else None,
                (post.scraped_at or datetime.now(timezone.utc)).isoformat(),
                str(post.media_type.value),
                post.likes,
                post.comments,
                post.views,
                post.model_dump_json(),
            )
            for post in posts
        ]
        if not rows:
            return 0

        def _insert(conn: sqlite3.Connection) -> int:
            cursor = conn.executemany(
                "INSERT OR IGNORE INTO seen_posts "
                "(platform, post_id, creator, shortcode, url, created_at, scraped_at, "
                " media_type, likes, comments, views, payload) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()
            return cursor.rowcount or 0

        written = await self._run(_insert)
        if written:
            self._log.debug(f"recorded {written} new post(s)")
        return written

    # -- meta --------------------------------------------------------------- #
    async def set_meta(self, key: str, value: str) -> None:
        def _write(conn: sqlite3.Connection) -> None:
            conn.execute(
                "INSERT INTO meta (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )
            conn.commit()

        await self._run(_write)

    async def get_meta(self, key: str) -> str | None:
        def _read(conn: sqlite3.Connection) -> str | None:
            row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else None

        return await self._run(_read)


def create_store(settings: Settings) -> PostStore:
    """Build the configured backend. The one place a new backend gets wired in."""
    if settings.database == "sqlite":
        return SQLitePostStore(settings.db_path)
    raise ConfigError(f"unsupported DATABASE={settings.database!r} (only 'sqlite' is implemented)")
