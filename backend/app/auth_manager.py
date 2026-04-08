"""
backend/app/auth_manager.py — Playwright session & cookie handler.

Provides a "Headless Login" flow: opens a Chromium browser window,
waits for the user to complete Google login, then persists the browser
storage state (cookies + localStorage) to `.byegpt/storage.json` so
subsequent runs can skip the login step.
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright, BrowserContext

logger = logging.getLogger(__name__)

_DEFAULT_STORAGE_PATH = Path(".byegpt/storage.json")
_NOTEBOOKLM_URL = "https://notebooklm.google.com/"
_LOGIN_URL = "https://accounts.google.com/ServiceLogin"
_LOGIN_TIMEOUT_MS = 300_000  # 5 minutes for the user to log in

_NOTEBOOKLM_HOST = "notebooklm.google.com"
_GOOGLE_ACCOUNTS_HOST = "accounts.google.com"
_DEFAULT_BROWSER_CANDIDATES = ("chrome", "msedge", "chromium")


def _is_notebooklm_home(url: str) -> bool:
    """
    Return True only when the browser is on the NotebookLM origin and
    *not* on the Google Accounts sign-in page.

    We compare against the parsed hostname to prevent substring-spoofing
    attacks such as ``https://evil.com/notebooklm.google.com/``.
    """
    parsed = urlparse(url)
    host = parsed.netloc.lower().split(":")[0]  # strip optional port
    return host == _NOTEBOOKLM_HOST and host != _GOOGLE_ACCOUNTS_HOST


async def _wait_for_login(context: BrowserContext) -> None:
    """Open NotebookLM and wait until the user is successfully logged in."""
    page = await context.new_page()
    await page.goto(_NOTEBOOKLM_URL)

    logger.info(
        "Waiting for Google login… Please complete the sign-in in the browser window."
    )

    # Poll until we land on the NotebookLM home page (redirected away from accounts.google.com)
    await page.wait_for_url(
        _is_notebooklm_home,
        timeout=_LOGIN_TIMEOUT_MS,
    )
    logger.info("Login detected — saving session.")
    await page.close()


async def _launch_browser(pw, *, headless: bool):
    """
    Launch a Chromium-based browser.

    Prefer a real installed browser channel because Google often rejects the
    bundled Playwright Chromium as "not secure".
    """
    preferred = os.environ.get("BYEGPT_BROWSER_CHANNEL", "").strip()
    candidates = [preferred] if preferred else list(_DEFAULT_BROWSER_CANDIDATES)

    last_error: Exception | None = None
    for channel in candidates:
        if not channel:
            continue
        try:
            logger.info("Launching browser via Playwright channel '%s'", channel)
            return await pw.chromium.launch(headless=headless, channel=channel)
        except Exception as exc:  # pragma: no cover - depends on local browser install
            last_error = exc
            logger.warning("Failed to launch browser channel '%s': %s", channel, exc)

    logger.info("Falling back to bundled Playwright Chromium")
    try:
        return await pw.chromium.launch(headless=headless)
    except Exception as exc:  # pragma: no cover - defensive path
        if last_error is not None:
            raise RuntimeError(
                "Could not launch Chrome/Edge or bundled Chromium. "
                "Install Google Chrome or Microsoft Edge, or set BYEGPT_BROWSER_CHANNEL."
            ) from exc
        raise


async def login_and_save(
    storage_path: Path = _DEFAULT_STORAGE_PATH,
    *,
    headless: bool = False,
) -> None:
    """
    Launch a browser, prompt the user to log in, then save storage state.

    Parameters
    ----------
    storage_path:
        Where to persist the browser storage state (cookies + localStorage).
    headless:
        If ``True``, run in headless mode (useful for automated testing with
        pre-seeded cookies).
    """
    storage_path = Path(storage_path)
    storage_path.parent.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as pw:
        browser = await _launch_browser(pw, headless=headless)
        context = await browser.new_context()
        await _wait_for_login(context)
        await context.storage_state(path=str(storage_path))
        await browser.close()

    logger.info("Session saved to %s", storage_path)


async def load_context(
    storage_path: Path = _DEFAULT_STORAGE_PATH,
    *,
    headless: bool = True,
):
    """
    Return a Playwright browser context pre-loaded with the saved session.

    The *caller* is responsible for closing the returned context and the
    associated Playwright instance.

    Parameters
    ----------
    storage_path:
        Path to the storage state JSON file created by :func:`login_and_save`.
    headless:
        Whether to run the browser in headless mode.

    Returns
    -------
    tuple[playwright, browser, context]
    """
    storage_path = Path(storage_path)
    if not storage_path.exists():
        raise FileNotFoundError(
            f"No saved session found at '{storage_path}'. "
            "Run the /auth/login endpoint first to authenticate."
        )

    pw = await async_playwright().start()
    browser = await _launch_browser(pw, headless=headless)
    context = await browser.new_context(storage_state=str(storage_path))
    return pw, browser, context


def is_authenticated(storage_path: Path = _DEFAULT_STORAGE_PATH) -> bool:
    """Return ``True`` if a saved session file exists."""
    return Path(storage_path).exists()
