---
name: browser-testing
description: "Use when testing localhost URLs or web UIs. Enforces mcp__playwright-mcp (headless); forbids mcp__claude-in-chrome__* (requires extension)."
---

# Browser testing — always use Playwright MCP headless


**Always use `mcp__playwright-mcp` (headless) to test localhost URLs and web UIs.** Never use `mcp__claude-in-chrome__*` tools for localhost testing — those require a connected Chrome extension and will fail or block in headless/CI contexts. `mcp__playwright-mcp` works out-of-the-box with no browser connection required.
