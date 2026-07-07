---
name: browser-headless-default
description: "Enforce headless browser automation by default for Hermes — Playwright MCP and superpowers-chrome. Use when opening browsers, scraping, UI tests, localhost verification, or any chrome_use_browser / Playwright call. Never headed unless Jeffrey explicitly requests visible browser."
when_to_use: Browser automation, scraping, screenshots, localhost UI checks, Luma/cookie flows, /browser command
allowed-tools: mcp__playwright-mcp, mcp__plugin-superpowers-chrome__chrome_use_browser
context: hermes
---

# Browser Headless Default

## Contract

**Default: headless always.** Jeffrey's Mac is not a demo kiosk — do not pop Chrome windows during agent work.

**Primary tool (2026-06-27):** **Aside browser** (`aside` CLI / `aside-mcp`). Use it first for all browser work. This skill is the fallback for Playwright MCP / superpowers-chrome paths.

| Tool | Default | Forbidden unless explicit user opt-in |
|------|---------|--------------------------------------|
| **Aside CLI / `aside-mcp`** | **PRIMARY** — headless or headed per task; verify with `aside account list` | nothing (Aside is the default) |
| **Playwright MCP** | fallback, headless | headed / `headless: false` |
| **superpowers-chrome** (`chrome_use_browser`) | fallback, headless (`hide_browser`, `browser_mode` → `headless: true`) | `show_browser`, headed restart |
| **claude-in-chrome / GUI Chrome** | do not use for localhost | driving Jeffrey's visible Chrome for automation |

**Explicit opt-in phrases only:** Jeffrey says *"show browser"*, *"headed mode"*, *"visible browser"*, or *"I want to see the window"* in the **current thread**.

## Phases

### Phase 1 — Before any browser action

1. Run `bash ~/.hermes/skills/browser-headless-default/scripts/validate-browser-mode.sh` when unsure.
2. For superpowers-chrome: call `browser_mode` first; if not headless, call `hide_browser` before navigate/click.
3. For Playwright MCP: never pass headed options.

### Phase 2 — During automation

- Prefer Playwright MCP for localhost (`http://127.0.0.1`, `http://localhost`).
- Prefer `human_type` only when bot-detection requires it; still stay headless.
- Capture evidence via screenshots in headless mode (works fine).

### Phase 3 — After session

- If you called `show_browser` for debugging, call `hide_browser` before ending the turn.

## Anti-patterns (BANNED)

- Calling `show_browser` "to help Jeffrey see progress"
- Starting Chrome headed on macOS because DISPLAY is available
- Using visible Chrome for Luma scrape / cookie injection without explicit approval
- `mcp__claude-in-chrome__*` for localhost testing (use Playwright MCP)

## Verification

```bash
python3 -m pytest tests/test_browser_headless_policy.py -q
bash ~/.hermes/skills/browser-headless-default/scripts/validate-browser-mode.sh
```

## Output format

When reporting browser work, include: `browser_mode: headless` (or Playwright headless) in the status line.
