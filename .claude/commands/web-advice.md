---
description: Get multi-model Web Chat (ChatGPT, Grok, Gemini Web) review of PR, evidence bundle, and video via browser / aside-mcp
aliases: [webadvice]
type: command
execution_mode: immediate
---

# `/web-advice`

Thin command pointer for multi-model Web LLM Chat review (ChatGPT, Grok, Gemini Web) of PRs, evidence bundles, and video proof.

## Usage

```bash
/web-advice [pr_number]
```

## Protocol

When invoked, load and follow the canonical skill at `~/.claude/skills/web-advice/SKILL.md`:

1. **Load Skill**: Read `~/.claude/skills/web-advice/SKILL.md` via `view_file`.
2. **Execute 5-Phase Workflow**:
   - **Phase 1**: Context Aggregation (PR diff, evidence bundle, captioned MP4/GIF video proof).
   - **Phase 2**: Browser Session Connection via `aside-mcp` (`gemini.google.com`, `chatgpt.com`, `grok.com`).
   - **Phase 3**: Structured Prompt Submission (Architecture invariants, evidence hashes, video frame breakdown).
   - **Phase 4**: Response Capture & Synthesis (multi-model verdicts table).
   - **Phase 5**: Remediation & Convergence (iterate until all models approve).
