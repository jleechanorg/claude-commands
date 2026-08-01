---
name: playwright-ui-testing
description: Run deterministic Playwright UI tests for local or test environments, including isolated browser profiles, traces, video, and multi-browser coverage. Use when the user asks for /playwright, end-to-end tests, reproducible UI testing, visual regression, or CI-style browser verification.
---

# Playwright UI testing

## Scope

Use this skill for reproducible application testing, not for managing real user accounts, Slack app settings, OAuth consent, or persistent personal browser sessions. Route those tasks to `browser-control` and Aside.

## Preflight

1. Identify the target repository and its existing test runner. Do not assume a framework, dev-server command, port, URL, or test account.
2. Check the available runner before changing anything, for example `npx playwright --version`, the project's package scripts, or its existing browser-test documentation.
3. Prefer the repository's existing tests and server helpers. If a new script is needed, keep it under the project test or temporary artifact path, never in a global skill directory.
4. Use test-only accounts and data. Never inject production credentials, scrape cookies, disable authentication, or run destructive flows against production without explicit approval.

## Test loop

1. Start or attach to the declared test environment.
2. Wait for the rendered application state before selecting elements.
3. Use role, label, test-id, or other stable locators. Avoid arbitrary sleeps and brittle coordinates.
4. Assert the intended behavior and capture useful failure evidence: screenshot, trace, console error, or video when configured.
5. Close isolated browser contexts and preserve only requested artifacts.

## Tool choice

- Use native Playwright tests for repeatable project tests and CI.
- Use the Playwright CLI when terminal-driven interactive automation is specifically requested.
- Use isolated profiles, traces, video, or multi-browser runs only when they add diagnostic or acceptance value.
- For exploratory work in a signed-in live browser, use `browser-control` instead.

## Completion

Report the command or test suite, target environment, pass/fail assertions, and artifact paths. Never claim a UI flow passed from navigation alone; verify the expected rendered state or API-visible result.
