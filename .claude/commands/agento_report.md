---
name: agento_report
aliases:
  - agentor
description: Get a status report of all PRs agento is handling — merged vs not merged, green status breakdown
type: git
execution_mode: background
---

## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE

Load and execute the skill at `.claude/skills/agento_report.md` (or `~/.claude/skills/agento_report.md`).

That skill contains the full step-by-step logic:
1. Collect open + recently-merged PRs via GitHub API
2. Apply 6-point green check per PR
3. Check AO session status
4. **Display the full report inline here** (table format with per-PR status)
5. **Post Slack summary** to `#ai-slack-test` (C0AKALZ4CKW) via `mcp__slack__conversations_add_message`
