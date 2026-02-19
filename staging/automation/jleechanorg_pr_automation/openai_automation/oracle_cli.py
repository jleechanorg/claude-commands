#!/usr/bin/env python3
"""
Oracle CLI - Ask GPT-5 Pro questions via browser automation

This tool opens a browser (reusing existing session), navigates to ChatGPT,
and sends a question to GPT-5 Pro (or GPT-4 Pro), then retrieves the answer.

Inspired by the existing Oracle tool's browser-based approach for querying
AI models without needing API keys.

Usage:
    # Ask a question
    oracle "What is the capital of France?"

    # With specific model
    oracle "Explain quantum computing" --model gpt-5-pro

    # Interactive mode
    oracle --interactive

    # Use existing browser (requires start_chrome_debug.sh)
    oracle "Question" --use-existing-browser
"""

import argparse
import asyncio
import traceback
from typing import Optional

from playwright.async_api import (
    Browser,
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)


class OracleCLI:
    """CLI tool to ask GPT-5 Pro questions via browser automation."""

    def __init__(
        self,
        cdp_url: Optional[str] = None,
        model: str = "gpt-5-pro",
        timeout: int = 60
    ):
        """
        Initialize Oracle CLI.

        Args:
            cdp_url: Chrome DevTools Protocol URL (if connecting to existing browser)
            model: Model to use (gpt-5-pro, gpt-4, etc.)
            timeout: Timeout in seconds for response
        """
        self.cdp_url = cdp_url
        self.model = model
        self.timeout = timeout
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def setup(self):
        """Set up browser connection."""
        if self.playwright is None:
            self.playwright = await async_playwright().start()

        if self.cdp_url:
            # Connect to existing browser
            print(f"🔌 Connecting to existing browser at {self.cdp_url}...")
            self.browser = await self.playwright.chromium.connect_over_cdp(self.cdp_url)
            contexts = self.browser.contexts
            if contexts:
                context = contexts[0]
                if context.pages:
                    self.page = context.pages[0]
                else:
                    self.page = await context.new_page()
            else:
                context = await self.browser.new_context()
                self.page = await context.new_page()
        else:
            # Launch new browser (visible)
            self.browser = await self.playwright.chromium.launch(headless=False)
            context = await self.browser.new_context()
            self.page = await context.new_page()

        print("✅ Browser ready")

    async def navigate_to_chatgpt(self):
        """Navigate to ChatGPT and ensure logged in."""
        print("📍 Navigating to ChatGPT...")

        await self.page.goto("https://chatgpt.com/", wait_until="networkidle")
        await asyncio.sleep(2)

        # Check if logged in
        try:
            await self.page.wait_for_selector(
                'button[aria-label*="User"], [data-testid="profile-button"]',
                timeout=5000
            )
            print("✅ Logged in to ChatGPT")
        except PlaywrightTimeoutError:
            print("⚠️  Not logged in - please log in manually")
            print("   Waiting 30 seconds for you to log in...")
            await asyncio.sleep(30)
        except Exception as login_error:
            print(f"⚠️  Unexpected login check error: {login_error}")
            await asyncio.sleep(5)

    async def select_model(self):
        """Select the specified model (GPT-5 Pro, GPT-4, etc.)."""
        print(f"🤖 Selecting model: {self.model}...")

        try:
            # Look for model selector (adjust based on actual UI)
            model_selector = await self.page.wait_for_selector(
                'button:has-text("GPT-"), [data-testid="model-selector"]',
                timeout=5000
            )

            await model_selector.click()
            await asyncio.sleep(1)

            # Click on desired model
            model_option = await self.page.wait_for_selector(
                f'text="{self.model}"',
                timeout=3000
            )

            await model_option.click()
            await asyncio.sleep(1)

            print(f"✅ Selected {self.model}")

        except Exception as e:
            print(f"⚠️  Could not select model: {e}")
            print("   Using default model")

    async def ask_question(self, question: str) -> str:
        """
        Ask a question and get the response.

        Args:
            question: The question to ask

        Returns:
            The AI's response text
        """
        print(f"\n❓ Question: {question}")
        print("=" * 60)

        try:
            # Find the input textarea
            input_box = await self.page.wait_for_selector(
                'textarea[placeholder*="Message"], textarea[data-id="message-input"]',
                timeout=10000
            )

            # Type the question
            await input_box.click()
            await input_box.fill(question)
            await asyncio.sleep(0.5)

            # Find and click send button
            send_button = await self.page.wait_for_selector(
                'button[data-testid="send-button"], button:has-text("Send")',
                timeout=5000
            )

            await send_button.click()

            # Wait for response
            print("⏳ Waiting for response...")

            # Wait for response to appear and complete
            # This is tricky - ChatGPT streams responses
            # We need to wait for the stop button to disappear (indicating response is complete)
            try:
                # Wait for stop button to appear (response started)
                await self.page.wait_for_selector(
                    'button:has-text("Stop"), [data-testid="stop-button"]',
                    timeout=10000
                )

                # Wait for stop button to disappear (response completed)
                await self.page.wait_for_selector(
                    'button:has-text("Stop"), [data-testid="stop-button"]',
                    state="hidden",
                    timeout=self.timeout * 1000
                )

                await asyncio.sleep(1)

            except Exception as e:
                print(f"⚠️  Response detection issue: {e}")
                # Fallback: just wait a bit
                await asyncio.sleep(10)

            # Extract the response
            # Find the last message (should be the AI's response)
            messages = await self.page.locator('[data-message-author-role="assistant"]').all()

            if messages:
                response = await messages[-1].text_content()
                response_text = (response or "").strip()
                return response_text or "❌ Empty response received"
            else:
                return "❌ Could not extract response"

        except Exception as e:
            print(f"❌ Error asking question: {e}")
            traceback.print_exc()
            return f"Error: {e}"

    async def interactive_mode(self):
        """Run in interactive mode for multiple questions."""
        print("\n🎙️  Oracle Interactive Mode")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("Type your questions (or 'exit' to quit)")
        print("")

        while True:
            try:
                question = input("\n❓ Your question: ").strip()

                if not question:
                    continue

                if question.lower() in ['exit', 'quit', 'q']:
                    print("👋 Goodbye!")
                    break

                response = await self.ask_question(question)
                print(f"\n💡 Answer:\n{response}")
                print("\n" + "━" * 60)

            except KeyboardInterrupt:
                print("\n\n👋 Interrupted by user")
                break

    async def run(self, question: Optional[str] = None, interactive: bool = False):
        """
        Main workflow.

        Args:
            question: Single question to ask (if not interactive)
            interactive: Run in interactive mode
        """
        try:
            await self.setup()
            await self.navigate_to_chatgpt()
            await self.select_model()

            if interactive:
                await self.interactive_mode()
            elif question:
                response = await self.ask_question(question)
                print(f"\n💡 Answer:\n{response}")
                return response
            else:
                print("❌ No question provided and not in interactive mode")
                return None

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            return None

        except Exception as e:
            print(f"\n❌ Oracle failed: {e}")
            traceback.print_exc()
            return None

        finally:
            if self.browser and not self.cdp_url:
                # Only close if we launched it (not using existing browser)
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None


async def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ask GPT-5 Pro questions via browser automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Ask a single question
    oracle "What is the meaning of life?"

    # Interactive mode
    oracle --interactive

    # Use specific model
    oracle "Explain AI" --model gpt-4

    # Connect to existing browser
    oracle "Question" --use-existing-browser --cdp-port 9222
        """
    )

    parser.add_argument(
        "question",
        nargs="?",
        help="Question to ask (optional if using --interactive)"
    )

    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run in interactive mode for multiple questions"
    )

    parser.add_argument(
        "--model",
        default="gpt-5-pro",
        help="Model to use (default: gpt-5-pro)"
    )

    parser.add_argument(
        "--use-existing-browser",
        action="store_true",
        help="Connect to existing Chrome instance (requires start_chrome_debug.sh)"
    )

    parser.add_argument(
        "--cdp-port",
        type=int,
        default=9222,
        help="CDP port if using existing browser (default: 9222)"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout in seconds for response (default: 60)"
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.question and not args.interactive:
        parser.error("Must provide either a question or use --interactive mode")

    # Build CDP URL if using existing browser
    cdp_url = f"http://localhost:{args.cdp_port}" if args.use_existing_browser else None

    # Create Oracle instance
    oracle = OracleCLI(
        cdp_url=cdp_url,
        model=args.model,
        timeout=args.timeout
    )

    # Run
    await oracle.run(question=args.question, interactive=args.interactive)


if __name__ == "__main__":
    asyncio.run(main())
