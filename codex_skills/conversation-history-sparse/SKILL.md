---
name: conversation-history-sparse
description: Read ~/.claude/projects and ~/.codex/sessions sparingly to infer what the current directory/worktree/branch was doing, with strict sampling limits.
type: analysis
scope: project
---

# Conversation History Sparse

Use this skill when the user asks to recover recent context from conversation history without consuming much context window.

## Canonical Workflow

Use the repo-local Claude skill as the primary procedure and command cookbook:
- `.claude/skills/conversation-history-sparse.md`

This Codex skill is intentionally thin and delegates operational details there to avoid duplicate instructions.

## Codex-Specific Rules

- Keep extraction sparse (metadata + tiny prompt samples only).
- Prefer `multi_tool_use.parallel` for independent metadata reads.
- Never dump full JSONL lines if they contain large payloads.
- Summarize evidence in 4 sections:
  - Branch/PR
  - Claude sparse history
  - Codex sparse history
  - Inference

## Trigger Cues

- "what was this worktree doing"
- "read convo history sparingly"
- "inspect ~/.codex/sessions and ~/.claude/projects"
- "recover session context without using much tokens"
