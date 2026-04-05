#!/bin/bash
set -euo pipefail
cd $HOME/.openclaw

git checkout main
git pull origin main
git checkout -b feat/commands-claude-memory-integration

git add \
  .claude/commands/history.md \
  .claude/commands/research.md \
  .claude/commands/debug.md \
  .claude/commands/learn.md \
  .claude/commands/checkpoint.md

git commit -m "feat(commands): integrate Claude auto-memory read/write into /history /research /debug /learn /checkpoint

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

git push -u origin feat/commands-claude-memory-integration

gh api repos/jleechanorg/jleechanclaw/pulls --method POST \
  -f title="feat(commands): integrate Claude auto-memory read/write into /history /research /debug /learn /checkpoint" \
  -f head="feat/commands-claude-memory-integration" \
  -f base="main" \
  -f body="## Background

Added Claude auto-memory Phase 0 (read) to /history, /research, /debug and Phase N+1 (write) to /debug item 14, /learn, and /checkpoint. Before searching history or researching, the commands now check prior memories to avoid re-discovering known facts and surface relevant past learnings.

## Goals

- Commands surface relevant memories before doing new work
- Successful resolutions are captured back to memory for future reuse
- Minimal edits: Phase 0 read-only preamble + one write step per command

## Tenets

- Minimal edits to existing files
- Phase 0 reads only (no breaking structural changes)
- Write on completion only (not on every invocation)

## High-level description of changes

Added Phase 0 memory discovery/read to /history, /research, /debug using glob.glob on ~/.claude/projects/*/memory/*.md. Phase 1 checklist item 14 added to /debug for auto-memory write on success. Phase N+1 write section added to /learn. Memory MCP section added to /checkpoint --summary mode.

## Testing

Files verified by Read tool — no new code, only instruction additions to existing command files.

## Low-level details

- **.claude/commands/history.md**: Added Phase 0 auto-memory discovery using Python glob; surfaces memories before conversation history search.
- **.claude/commands/research.md**: Added Phase 0 memory check filtered by research topic keywords; displays Prior Knowledge Found section.
- **.claude/commands/debug.md**: Added Phase 0 memory check for bug keywords; added Phase 1 item 14 auto-memory write on successful resolution.
- **.claude/commands/learn.md**: Added Phase N+1 write step using Python to create feedback_*.md files in project memory dir and append to MEMORY.md index.
- **.claude/commands/checkpoint.md**: Added Claude Auto-Memory Write section for --summary mode; writes durable insights to project memory.

Generated with Claude Code"
