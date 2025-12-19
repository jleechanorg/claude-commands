"""Playwright automation for managing Codex tasks on ChatGPT."""

from __future__ import annotations

import asyncio
import json
import os
import random
from getpass import getpass
from pathlib import Path
from typing import Dict, Tuple

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    async_playwright,
)
from playwright.async_api import (
    Error as PlaywrightError,
)
from playwright.async_api import (
    TimeoutError as PlaywrightTimeoutError,
)

CHATGPT_CODEX_URL = "https://chatgpt.com/codex"
CREDENTIALS_PATH = Path.home() / ".chatgpt_codex_credentials.json"
AUTH_STATE_PATH = Path.home() / ".chatgpt_codex_auth_state.json"
TASK_CARD_SELECTOR = '[data-testid="codex-task-card"]'
UPDATE_BRANCH_BUTTON_SELECTOR = 'button:has-text("Update Branch")'
TASK_TITLE_SELECTOR = '[data-testid="codex-task-title"]'


def _save_credentials(credentials: Dict[str, str]) -> None:
    """Persist credentials to disk with restrictive permissions."""

    CREDENTIALS_PATH.write_text(json.dumps(credentials, indent=2))
    os.chmod(CREDENTIALS_PATH, 0o600)


def _load_credentials() -> Dict[str, str] | None:
    """Return stored credentials if available and well formed."""

    if not CREDENTIALS_PATH.exists():
        return None

    try:
        data = json.loads(CREDENTIALS_PATH.read_text())
    except json.JSONDecodeError:
        return None

    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return None

    return {"email": email, "password": password}


def prompt_for_credentials() -> Dict[str, str]:
    """Prompt the user for credentials and persist them."""

    print("🔐 ChatGPT Codex credentials not found. They will be stored locally at")
    print(f"    {CREDENTIALS_PATH}")
    email = input("ChatGPT email: ").strip()
    password = getpass("ChatGPT password: ")

    credentials = {"email": email, "password": password}
    _save_credentials(credentials)
    print("✅ Credentials saved locally (chmod 600).")
    return credentials


def get_credentials() -> Dict[str, str]:
    """Load stored credentials or prompt the user."""

    credentials = _load_credentials()
    if credentials is None:
        credentials = prompt_for_credentials()
    return credentials


async def ensure_logged_in(page: Page, context: BrowserContext, credentials: Dict[str, str] | None = None) -> None:
    """Log into ChatGPT Codex if required and save auth state immediately."""

    await page.goto(CHATGPT_CODEX_URL, wait_until="domcontentloaded")

    if await is_task_list_visible(page):
        print("✅ Session still valid (task list visible).")
        return

    print("⚠️  Session expired. Re-authenticating...")
    if credentials is None:
        credentials = get_credentials()

    login_trigger = page.get_by_role("link", name="Log in")
    if await login_trigger.count() == 0:
        login_trigger = page.get_by_role("button", name="Log in")
    if await login_trigger.count():
        await login_trigger.first().click()

    await _complete_login_flow(page, credentials)

    await context.storage_state(path=str(AUTH_STATE_PATH))
    print(f"💾 New authentication state saved immediately to {AUTH_STATE_PATH}.")


async def _complete_login_flow(page: Page, credentials: Dict[str, str]) -> None:
    """Fill in the login flow using the provided credentials."""

    email_field = page.locator("input[type='email']")
    await email_field.first().wait_for(timeout=30000)
    await email_field.first().fill(credentials["email"])

    next_button = page.get_by_role("button", name="Continue")
    if await next_button.count():
        await next_button.first().click()
    else:
        await page.keyboard.press("Enter")

    password_field = page.locator("input[type='password']")
    await password_field.first().wait_for(timeout=30000)
    await password_field.first().fill(credentials["password"])

    signin_button = page.get_by_role("button", name="Continue")
    if await signin_button.count() == 0:
        signin_button = page.get_by_role("button", name="Sign in")
    if await signin_button.count() == 0:
        signin_button = page.get_by_role("button", name="Log in")

    if await signin_button.count():
        await signin_button.first().click()
    else:
        await page.keyboard.press("Enter")

    await page.wait_for_url("**/codex**", timeout=60000)
    await wait_for_task_list(page)


async def is_task_list_visible(page: Page) -> bool:
    """Return True if the Codex task list is visible."""

    task_cards = page.locator(TASK_CARD_SELECTOR)
    try:
        await task_cards.first().wait_for(timeout=5000)
    except PlaywrightTimeoutError:
        return False
    return await task_cards.count() > 0


async def wait_for_task_list(page: Page) -> None:
    """Wait until task cards are available."""

    await page.wait_for_selector(TASK_CARD_SELECTOR, timeout=60000)


async def collect_task_metadata(page: Page, index: int) -> Tuple[str, str]:
    """Return the title and status text for a given task card."""

    task_card = page.locator(TASK_CARD_SELECTOR).nth(index)
    title_locator = task_card.locator(TASK_TITLE_SELECTOR)
    title = await title_locator.inner_text() if await title_locator.count() else f"Task #{index + 1}"
    status_locator = task_card.locator("[data-testid='codex-task-status']")
    status = await status_locator.inner_text() if await status_locator.count() else ""
    return title.strip(), status.strip()


async def process_tasks(page: Page) -> None:
    """Iterate through all Codex tasks and click Update Branch when present."""

    processed_indices: set[int] = set()

    while True:
        task_cards = page.locator(TASK_CARD_SELECTOR)
        total_tasks = await task_cards.count()
        if total_tasks == 0:
            print("ℹ️  No tasks detected on Codex dashboard.")
            return

        pending_indices = [idx for idx in range(total_tasks) if idx not in processed_indices]
        if not pending_indices:
            print("🏁 Completed processing available tasks.")
            return

        for index in pending_indices:
            task_card = task_cards.nth(index)
            await task_card.scroll_into_view_if_needed()

            title, status = await collect_task_metadata(page, index)
            print(f"🔍 Inspecting {title} ({status or 'no status'})")

            update_button = task_card.locator(UPDATE_BRANCH_BUTTON_SELECTOR)
            button_count = await update_button.count()
            if button_count:
                try:
                    await update_button.first().click()
                    print("✅ Clicked Update Branch directly from task card.")
                    processed_indices.add(index)
                    await _post_action_delay(page)
                    continue
                except PlaywrightError as exc:
                    print(f"⚠️  Failed to click Update Branch on card: {exc}")

            await task_card.click()
            await page.wait_for_timeout(1000)

            modal_update_button = page.locator(UPDATE_BRANCH_BUTTON_SELECTOR)
            try:
                await modal_update_button.first().wait_for(timeout=5000)
                await modal_update_button.first().click()
                print("✅ Clicked Update Branch inside task detail.")
            except PlaywrightTimeoutError:
                print("➡️  No Update Branch button found for this task. Skipping.")
            except PlaywrightError as exc:
                print(f"⚠️  Error clicking Update Branch in detail view: {exc}")

            await _close_task_detail(page)
            processed_indices.add(index)
            await _post_action_delay(page)


async def _close_task_detail(page: Page) -> None:
    """Attempt to close a task detail view or navigate back."""

    for name in ("Close", "Back", "Done"):
        button = page.get_by_role("button", name=name)
        if await button.count():
            await button.first().click()
            await page.wait_for_timeout(500)
            return

    try:
        await page.go_back(wait_until="domcontentloaded")
        await wait_for_task_list(page)
    except PlaywrightError:
        pass


async def _post_action_delay(page: Page) -> None:
    """Add a small randomized delay to appear human-like."""

    delay_ms = random.randint(1000, 2500)
    await page.wait_for_timeout(delay_ms)


async def run() -> None:
    """Entry point for running the Playwright automation."""

    playwright = await async_playwright().start()
    browser: Browser | None = None
    context: BrowserContext | None = None
    try:
        browser = await playwright.chromium.launch(headless=False)
        context_kwargs = {}
        if AUTH_STATE_PATH.exists():
            print(f"🔄 Loading saved authentication state from {AUTH_STATE_PATH}")
            context_kwargs["storage_state"] = str(AUTH_STATE_PATH)
        else:
            print("ℹ️  No saved authentication state found. Fresh login required.")
        context = await browser.new_context(**context_kwargs)
        page = await context.new_page()

        await ensure_logged_in(page, context)
        await wait_for_task_list(page)
        await process_tasks(page)

        await context.storage_state(path=str(AUTH_STATE_PATH))
        print(f"💾 Final authentication state saved to {AUTH_STATE_PATH}.")
    finally:
        if context is not None:
            await context.close()
        if browser is not None:
            await browser.close()
        await playwright.stop()


def main() -> None:
    """Synchronous wrapper for asyncio entry point."""

    asyncio.run(run())


if __name__ == "__main__":
    main()
