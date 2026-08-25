"""Session management: log in once by hand, then never again.

The brief asks for login-once-and-reuse, and the way to get that reliably on
Instagram is to not automate the login at all. Typing credentials into the form
with Playwright works right up until Instagram decides it wants a checkpoint, an
emailed code, a 2FA prompt, or a "was this you?" screen — and it decides that
most often for exactly the traffic pattern a scraper produces. Automating that
means writing a handler per interstitial and rewriting them whenever the flow
changes.

So `interactive_login()` opens a visible Chromium, hands the keyboard to the
human, and waits. Whatever Instagram asks for — password, code, checkpoint,
CAPTCHA — a person answers it. The moment a real session cookie appears we save
`storage_state.json` and close the window. Every run after that is headless and
silent, and the credentials never touch this codebase or the .env file.

`ensure_session()` is what the scraper calls before doing any work: it validates
the stored session and, if it has expired, reopens that login window.
"""

from __future__ import annotations

import asyncio
import time

from playwright.async_api import Error as PlaywrightError, Page

from .browser import BrowserManager
from .config import Settings
from .exceptions import (
    ChallengeRequired,
    LoginRequired,
    NetworkError,
    RateLimited,
    ScrapeTimeout,
)
from .selectors import Dom, Endpoints
from .utils import dig_any, get_logger

# Instagram sets several cookies on login; these two together mean an
# authenticated session rather than the anonymous one every visitor gets.
_SESSION_COOKIES = ("sessionid", "ds_user_id")

_POLL_INTERVAL_SECONDS = 2.0
# Cookies land a moment before Instagram finishes writing localStorage. Saving
# instantly can capture a session that is missing pieces it needs later.
_SETTLE_SECONDS = 3.0


class SessionManager:
    """Validates, repairs, and persists the logged-in Instagram session."""

    def __init__(self, browser: BrowserManager, settings: Settings) -> None:
        self._browser = browser
        self._settings = settings
        self._log = get_logger("login")
        self._verified = False

    # -- validation --------------------------------------------------------- #
    async def has_session_cookies(self) -> bool:
        """Cheap local check: are the auth cookies present at all?"""
        try:
            cookies = await self._browser.context.cookies("https://www.instagram.com")
        except PlaywrightError:
            return False
        present = {c["name"] for c in cookies if c.get("value")}
        return all(name in present for name in _SESSION_COOKIES)

    async def is_logged_in(self) -> bool:
        """Is the stored session actually accepted by Instagram right now?

        Two steps, because either alone is wrong. The cookie check is free but
        cannot tell a live session from one Instagram invalidated an hour ago.
        The API probe is authoritative but costs a request, so it runs only when
        the cookies are there to be tested.
        """
        if not await self.has_session_cookies():
            self._log.debug("no session cookies present")
            return False

        try:
            data = await self._browser.fetch_json(Endpoints.CURRENT_USER)
        except LoginRequired:
            self._log.debug("session cookies present but rejected by Instagram")
            return False
        except (RateLimited, NetworkError, ScrapeTimeout) as exc:
            # Cannot reach Instagram is not the same as not logged in. Trusting
            # the cookies here means a network blip does not throw away a
            # perfectly good session and demand a fresh manual login.
            self._log.warning(f"could not verify session ({exc}) — assuming it is still valid")
            return True

        username = dig_any(data, ("user.username", "username", "user.pk"))
        if username:
            self._log.debug(f"session valid (logged in as {username})")
            return True
        return False

    async def ensure_session(self, *, force: bool = False) -> None:
        """Guarantee a working session, opening an interactive login if needed.

        Called before every scraping operation, but the result is cached for the
        life of the scraper — re-probing before each of fifty posts would add
        fifty pointless requests to a run that is already trying to look calm.
        """
        if self._verified and not force:
            return

        if await self.is_logged_in():
            self._verified = True
            return

        if not self._settings.interactive_login:
            raise LoginRequired(
                "No valid Instagram session and interactive login is disabled. "
                "Run:  python -m instagram_scraper login"
            )

        self._log.warning("session missing or expired — starting interactive login")
        await self.interactive_login()
        await self._browser.reset_context()

        if not await self.is_logged_in():
            raise LoginRequired("login completed but the session still is not accepted")
        self._verified = True

    # -- interactive login -------------------------------------------------- #
    async def interactive_login(self) -> None:
        """Open a visible browser, wait for a human to log in, save the session.

        Runs in its own browser instance rather than the scraper's, so it works
        identically whether the main run is headless or not.
        """
        settings = self._settings.model_copy(update={"headless": False, "block_assets": False})
        helper = BrowserManager(settings)
        await helper.start(headless=False)

        try:
            async with helper.page(block_assets=False) as page:
                await helper.goto(page, Endpoints.LOGIN, wait_until="domcontentloaded")
                self._announce()

                if not await self._wait_for_login(page):
                    raise ChallengeRequired(
                        f"no Instagram session appeared within {settings.login_timeout_seconds}s. "
                        "If a checkpoint or 2FA prompt was showing, finish it and run "
                        "'python -m instagram_scraper login' again."
                    )

                await asyncio.sleep(_SETTLE_SECONDS)
                await self._dismiss_dialogs(page)
                await helper.save_state()
                self._log.success(f"logged in — session saved to {settings.session_file.name}")
        finally:
            await helper.stop()

    def _announce(self) -> None:
        timeout = self._settings.login_timeout_seconds
        self._log.info("=" * 68)
        self._log.info("A Chromium window is open on the Instagram login page.")
        self._log.info("Log in there by hand — password, 2FA, and any checkpoint.")
        self._log.info(f"This will wait up to {timeout}s and close the window itself.")
        self._log.info("Credentials are typed only into Instagram; nothing is stored here.")
        self._log.info("=" * 68)

    async def _wait_for_login(self, page: Page) -> bool:
        """Poll until the auth cookies appear, or the deadline passes."""
        deadline = time.monotonic() + self._settings.login_timeout_seconds
        announced_challenge = False

        while time.monotonic() < deadline:
            if page.is_closed():
                self._log.warning("login window was closed before a session appeared")
                return False

            cookies = await page.context.cookies("https://www.instagram.com")
            present = {c["name"] for c in cookies if c.get("value")}
            if all(name in present for name in _SESSION_COOKIES):
                return True

            if not announced_challenge and await self._showing_challenge(page):
                self._log.info("Instagram is asking for a verification step — complete it in the window")
                announced_challenge = True

            await asyncio.sleep(_POLL_INTERVAL_SECONDS)

        return False

    async def _showing_challenge(self, page: Page) -> bool:
        for selector in Dom.CHALLENGE_MARKERS:
            try:
                if await page.locator(selector).count():
                    return True
            except PlaywrightError:
                continue
        return "challenge" in page.url or "two_factor" in page.url

    async def _dismiss_dialogs(self, page: Page) -> None:
        """Clear cookie banners and 'Save your login info?' before saving state.

        These sit on top of the page and, left alone, are the first thing the next
        headless run has to deal with. Dismissing them once here means they are
        already answered in the saved state.
        """
        for selector in Dom.DISMISS_BUTTONS:
            try:
                button = page.locator(selector).first
                if await button.count() and await button.is_visible():
                    await button.click(timeout=3000)
                    self._log.debug(f"dismissed dialog via {selector}")
                    await asyncio.sleep(1.0)
            except PlaywrightError:
                continue

    def invalidate(self) -> None:
        """Forget the cached verdict, forcing the next `ensure_session` to re-probe."""
        self._verified = False
