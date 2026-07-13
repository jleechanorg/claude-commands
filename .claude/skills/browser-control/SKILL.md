---
name: browser-control
description: Control real websites and authenticated browser sessions, inspect pages, complete approved UI flows, or troubleshoot browser automation. Use for general browser work, site settings, OAuth consent, existing tabs, and Slack app configuration. Uses Aside first and routes deterministic app testing to playwright-ui-testing.
---

# Browser control

## Route the task

1. **Live websites, authenticated sessions, account settings, OAuth, or existing tabs**: use `aside-browser-default` first. Inspect the active runtime's available browser tools before hard-coding a tool name.
2. **Deterministic local-app testing, CI, isolated profiles, traces, video, or multi-browser coverage**: load `playwright-ui-testing`.
3. **Authorized API discovery only**: use `browserclaw`. Do not use it for Slack app settings, OAuth flows, or any capture likely to retain credentials, cookies, authorization headers, or tokens.

## Live-browser workflow

1. Check for usable existing tabs before opening a new one.
2. Read the page with an accessibility snapshot before acting. Use current refs, not guessed selectors or coordinates.
3. Treat login, consent, chooser, and MFA screens as recoverable states. Never bypass them, extract secrets, or copy cookies between browser profiles.
4. Confirm any side effect from the resulting page state. Before sending, submitting, deleting, installing, authorizing, or publishing, verify the target and requested scope.
5. Close tabs opened solely for the task when they are no longer useful.

## Slack app and credential work

- Configure or rotate Slack credentials through the normal Slack UI. Load `hermes-slack-rotation` for manifest scopes, OAuth and Socket Mode token rotation, protected shell-file updates, and validation.
- Do not put tokens in prompts, screenshots, HAR files, shell output, artifacts, or source control.
- Do not infer a post's identity. Verify it with `auth.test` or the platform's confirmed result before claiming user versus bot behavior.

## Failure classification

Report the precise layer that failed: browser transport, current tab/profile access, page authentication or consent, website UI, or action permission. A CLI failure does not prove an existing browser tab or another browser tool is unavailable.

## Completion

Report browser mode, the confirmed result, and any blocker. For browser-dependent actions, attach a focused screenshot when it is safe and useful.
