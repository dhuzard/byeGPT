from __future__ import annotations

import asyncio
import os
from pathlib import Path

from playwright.async_api import async_playwright


NOTEBOOKLM_URL = "https://notebooklm.google.com/"


async def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    storage_path = Path(os.environ.get("BYEGPT_STORAGE", repo_root / ".byegpt")) / "storage.json"
    storage_path.parent.mkdir(parents=True, exist_ok=True)

    print("Connecting to Chrome on http://127.0.0.1:9222 ...")
    print("Make sure Chrome was started manually with --remote-debugging-port=9222")

    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp("http://127.0.0.1:9222")

        if browser.contexts:
            context = browser.contexts[0]
        else:
            context = await browser.new_context()

        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto(NOTEBOOKLM_URL)

        print("")
        print("Complete the login manually in the Chrome window.")
        print("When NotebookLM is open and working, press Enter here to save the session.")
        await asyncio.to_thread(input)

        await context.storage_state(path=str(storage_path))
        print(f"Saved session to {storage_path}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
