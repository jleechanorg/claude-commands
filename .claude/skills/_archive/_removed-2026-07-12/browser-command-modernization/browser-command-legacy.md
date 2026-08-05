---
description: Unified browser automation - intelligently uses Playwright or Superpowers Chrome
type: skill
scope: project
execution_mode: immediate
---

# /browser [task description] | subcommand

Intelligent browser automation — auto-selects Playwright (visual/multi-step/
multi-browser) or Superpowers Chrome (quick/debug/persistent-session) based
on the request.

Read `~/.claude/skills/browser/SKILL.md` and execute the full workflow with
the provided task or subcommand.

## Subcommands

| Subcommand | Tool | Purpose |
|---|---|---|
| `/browser smoke [url]` | Chrome | Quick smoke test, ~15-30s |
| `/browser campaign [url] [name]` | Auto | Campaign creation flow |
| `/browser visual [url] [name]` | Playwright | Visual regression (desktop/tablet/mobile) |
| `/browser debug [url]` | Chrome | Interactive debug session |
| `/browser e2e [test-name]` | Playwright | Full E2E test suite |
| `/browser playwright <task>` | Playwright | Force Playwright |
| `/browser chrome <task>` | Chrome | Force Superpowers Chrome |
