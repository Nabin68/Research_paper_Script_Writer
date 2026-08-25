"""Playwright lifecycle: one browser, one context, many short-lived pages.

The performance requirement in the brief — never launch Chromium per creator — is
enforced structurally here rather than by convention. `BrowserManager` owns the
only `Browser` and the only `BrowserContext` in the process; every scraping module
borrows a `Page` from it and gives it back. Nothing outside this file imports
Playwright, so no other module *can* launch a browser even by accident.

The second thing this file owns is `fetch_json`, which is how the rest of the
package actually reads Instagram. See `selectors.py` for why the data comes from
Instagram's JSON API rather than from the DOM; the short version is that the DOM
does not contain most of the fields the brief asks for. The calls are issued by
`fetch()` from inside a real page on the instagram.com origin, so they carry the
session cookies, the CSRF token, and the origin headers exactly as Instagram's
own client sends them — which a bare HTTP client outside the browser does not.
"""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable

from playwright.async_api import (
    Browser,
    BrowserContext,
    Error as PlaywrightError,
    Page,
    Playwright,
    Response,
    TimeoutError as PlaywrightTimeout,
    async_playwright,
)

from .config import Settings
from .exceptions import (
    BrowserError,
    LoginRequired,
    NetworkError,
    NotFound,
    RateLimited,
    ScrapeTimeout,
)
from .selectors import RATE_LIMIT_BODY_MARKERS, Endpoints, Headers
from .utils import get_logger

# Assets we never need: every URL we care about arrives as a string in a JSON
# payload, so actually fetching the bytes only costs bandwidth and time.
_BLOCKED_RESOURCE_TYPES = frozenset({"image", "media", "font"})

_LAUNCH_ARGS = [
    # Playwright sets this flag by default and Instagram checks for it.
    "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage",
    "--no-first-run",
    "--no-default-browser-check",
]

# Trim the most obvious automation tells. This is not a serious anti-detection
# suite and is not trying to be — the session cookie from a real human login is
# what actually carries us. This just avoids failing the cheapest checks.
_STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
window.chrome = window.chrome || {runtime: {}};
"""


@dataclass(slots=True)
class JsonResponse:
    """One internal-API call's outcome."""

    status: int
    body: str
    data: Any = None

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300


class BrowserManager:
    """Owns the Playwright lifecycle. Start once, stop once, borrow pages in between."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._log = get_logger("browser")
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._api_page: Page | None = None

    # -- lifecycle ---------------------------------------------------------- #
    @property
    def started(self) -> bool:
        return self._context is not None

    @property
    def context(self) -> BrowserContext:
        if self._context is None:
            raise BrowserError("browser not started — call start() first")
        return self._context

    async def start(self, *, headless: bool | None = None) -> None:
        """Launch Chromium and build the context, restoring a saved session if present."""
        if self._context is not None:
            return

        headless = self._settings.headless if headless is None else headless
        self._log.debug(f"launching chromium (headless={headless})")
        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=headless,
                slow_mo=self._settings.slow_mo_ms or 0,
                args=_LAUNCH_ARGS,
                proxy={"server": self._settings.proxy} if self._settings.proxy else None,
            )
            self._context = await self._new_context()
        except PlaywrightError as exc:
            await self.stop()
            raise BrowserError(
                f"could not launch Chromium: {exc}. "
                "If this is a fresh install, run: python -m playwright install chromium"
            ) from exc

    async def _new_context(self) -> BrowserContext:
        if self._browser is None:
            raise BrowserError("browser not launched")

        state_file = self._settings.session_file
        has_state = state_file.exists() and state_file.stat().st_size > 0
        if has_state:
            self._log.debug(f"restoring session from {state_file.name}")

        context = await self._browser.new_context(
            storage_state=str(state_file) if has_state else None,
            user_agent=self._settings.user_agent,
            locale=self._settings.locale,
            timezone_id=self._settings.timezone_id,
            viewport=self._settings.viewport,
            java_script_enabled=True,
        )
        context.set_default_timeout(self._settings.action_timeout_ms)
        context.set_default_navigation_timeout(self._settings.nav_timeout_ms)
        await context.add_init_script(_STEALTH_SCRIPT)
        return context

    async def reset_context(self) -> None:
        """Rebuild the context, picking up whatever is now in the session file.

        Used after an interactive login: the running context still holds the dead
        cookies, and Playwright cannot swap a context's storage state in place.
        """
        self._log.debug("rebuilding browser context with the refreshed session")
        if self._api_page is not None:
            self._api_page = None
        if self._context is not None:
            await self._context.close()
            self._context = None
        self._context = await self._new_context()

    async def save_state(self) -> None:
        """Persist cookies + localStorage so the next run does not log in again."""
        if self._context is None:
            return
        self._settings.session_file.parent.mkdir(parents=True, exist_ok=True)
        await self._context.storage_state(path=str(self._settings.session_file))
        self._log.debug(f"session saved to {self._settings.session_file.name}")

    async def stop(self) -> None:
        """Close everything. Safe to call twice, and safe to call after a failed start."""
        for name, closer in (
            ("context", getattr(self._context, "close", None)),
            ("browser", getattr(self._browser, "close", None)),
            ("playwright", getattr(self._playwright, "stop", None)),
        ):
            if closer is None:
                continue
            try:
                await closer()
            except Exception as exc:  # noqa: BLE001 - teardown must never mask the real error
                self._log.debug(f"ignoring error closing {name}: {exc}")
        self._api_page = None
        self._context = None
        self._browser = None
        self._playwright = None

    # -- pages -------------------------------------------------------------- #
    @asynccontextmanager
    async def page(self, *, block_assets: bool | None = None) -> AsyncIterator[Page]:
        """Borrow a page, guaranteed closed afterwards even if the caller raises."""
        page = await self.context.new_page()
        if block_assets if block_assets is not None else self._settings.block_assets:
            await self._install_asset_blocker(page)
        try:
            yield page
        finally:
            try:
                await page.close()
            except Exception:  # noqa: BLE001 - the page may already be gone
                pass

    async def _install_asset_blocker(self, page: Page) -> None:
        """Abort image/font/video requests on this page.

        Registered on the page rather than the context on purpose: the context's
        `request` API is what `downloader.py` uses, and a context-level route
        would abort the very downloads it is trying to make.
        """

        async def _route(route, request) -> None:
            if request.resource_type in _BLOCKED_RESOURCE_TYPES:
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", _route)

    async def api_page(self) -> Page:
        """A long-lived page parked on instagram.com, used for every JSON call.

        `fetch()` is same-origin, so the calls have to be issued from a page that
        is already on instagram.com. Keeping one such page alive for the whole run
        means a twenty-creator monitoring pass costs one navigation total instead
        of twenty.
        """
        if self._api_page is not None and not self._api_page.is_closed():
            return self._api_page

        page = await self.context.new_page()
        if self._settings.block_assets:
            await self._install_asset_blocker(page)
        await self.goto(page, Endpoints.HOME, wait_until="domcontentloaded")
        self._api_page = page
        return page

    # -- navigation --------------------------------------------------------- #
    async def goto(
        self,
        page: Page,
        url: str,
        *,
        wait_until: str = "domcontentloaded",
    ) -> Response | None:
        """Navigate, translating Playwright's failures into our exception vocabulary."""
        try:
            return await page.goto(url, wait_until=wait_until, timeout=self._settings.nav_timeout_ms)
        except PlaywrightTimeout as exc:
            raise ScrapeTimeout(f"timed out loading {url}") from exc
        except PlaywrightError as exc:
            message = str(exc)
            if any(marker in message for marker in ("ERR_INTERNET", "ERR_NAME_NOT", "ERR_CONNECTION")):
                raise NetworkError(f"network failure loading {url}: {message}") from exc
            raise BrowserError(f"navigation to {url} failed: {message}") from exc

    # -- the JSON API ------------------------------------------------------- #
    async def fetch_json(self, url: str, *, page: Page | None = None) -> Any:
        """GET `url` from inside the browser and return the parsed JSON body.

        Status handling is centralised here so no caller has to remember what a
        401 from Instagram means. Every error raised is one of ours.
        """
        target = page or await self.api_page()
        headers = {k: v.format(app_id=self._settings.ig_app_id) for k, v in Headers.API.items()}

        try:
            raw = await target.evaluate(
                """async ([url, headers]) => {
                    const res = await fetch(url, {
                        headers,
                        credentials: 'include',
                        method: 'GET',
                    });
                    return {status: res.status, body: await res.text()};
                }""",
                [url, headers],
            )
        except PlaywrightTimeout as exc:
            raise ScrapeTimeout(f"timed out calling {url}") from exc
        except PlaywrightError as exc:
            raise NetworkError(f"failed calling {url}: {exc}") from exc

        response = JsonResponse(status=int(raw.get("status", 0)), body=str(raw.get("body", "")))
        self._raise_for_status(response, url)

        try:
            response.data = json.loads(response.body)
        except json.JSONDecodeError as exc:
            # A JSON endpoint answering with HTML is nearly always the login wall.
            if "<html" in response.body[:200].lower():
                raise LoginRequired(
                    f"{url} returned an HTML page instead of JSON — the session is no longer valid"
                ) from exc
            raise NetworkError(f"{url} returned a body that is not JSON") from exc
        return response.data

    def _raise_for_status(self, response: JsonResponse, url: str) -> None:
        body_preview = response.body[:400].lower()

        if any(marker in body_preview for marker in RATE_LIMIT_BODY_MARKERS):
            raise RateLimited(f"Instagram is throttling us on {url}")

        if response.ok:
            return
        if response.status == 429:
            raise RateLimited(f"HTTP 429 from {url}")
        if response.status in (400, 401, 403):
            # 400 belongs in this group, unintuitively. Instagram's internal API
            # answers an unauthenticated `web_profile_info` with 400, not 401 —
            # verified against a logged-out session. Classifying it as a generic
            # error instead would make a dead session look transient, so every
            # call would burn three retries and exponential backoff before
            # failing with "HTTP 400" rather than "log in again".
            #
            # A genuinely malformed request would also land here, but that costs
            # only one `current_user` probe: `ensure_session` re-validates before
            # it prompts, so a live session never triggers a spurious login.
            raise LoginRequired(
                f"HTTP {response.status} from {url} — session expired, rejected, or absent"
            )
        if response.status == 404:
            raise NotFound(f"HTTP 404 from {url}")
        if response.status in (500, 502, 503, 504):
            raise NetworkError(f"HTTP {response.status} from {url} — Instagram-side error")
        raise NetworkError(f"HTTP {response.status} from {url}")

    # -- response capture (fallback path) ----------------------------------- #
    async def capture_json(
        self,
        page: Page,
        url: str,
        predicate: Callable[[Any], bool],
        *,
        timeout_ms: int | None = None,
    ) -> Any | None:
        """Navigate to `url` and return the first JSON response matching `predicate`.

        The fallback for when a direct API call is refused. Instead of guessing
        which GraphQL `doc_id` Instagram is using this week, we let Instagram's own
        page make whatever call it makes and read the payload out of the response
        stream. Slower than `fetch_json` — a full page load — so it is only used
        when the direct path has already failed.
        """
        captured: list[Any] = []

        async def _on_response(response: Response) -> None:
            if captured or "instagram.com" not in response.url:
                return
            content_type = (response.headers or {}).get("content-type", "")
            if "json" not in content_type:
                return
            try:
                payload = await response.json()
            except Exception:  # noqa: BLE001 - streamed/aborted bodies are common and uninteresting
                return
            if predicate(payload):
                captured.append(payload)

        page.on("response", _on_response)
        try:
            await self.goto(page, url, wait_until="domcontentloaded")
            if not captured:
                # The payload frequently lands just after DOMContentLoaded.
                try:
                    await page.wait_for_timeout(timeout_ms or self._settings.action_timeout_ms)
                except PlaywrightError:
                    pass
        finally:
            page.remove_listener("response", _on_response)

        return captured[0] if captured else None
