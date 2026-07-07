# /exportcommands — Export ~/.claude/ to jleechanorg/claude-commands

Periodic export of Claude commands, skills, hooks, and agents from `~/.claude/` + project `.claude/` to the public reference repo `jleechanorg/claude-commands`.

## Prerequisites

- Must run from a **git repo root** (the script uses `git rev-parse --show-toplevel` for `PROJECT_ROOT`).
  - From `~/your-project.com/`: works directly.
  - From `~/.hermes_prod/` or `/tmp/`: fails with `ERROR: PROJECT_ROOT is unset and git rev-parse failed`.
  - Override: `PROJECT_ROOT=~/your-project.com bash ~/.claude/commands/exportcommands.sh`
- Requires `claude` CLI on PATH (for README.md regeneration step).
- Requires `gh` auth for `jleechanorg/claude-commands` repo.

## Timeout

- **≥300 seconds** required. The Claude CLI README generation step is slow and will timeout at 120s.
- Dry-run (`--dry-run`) also invokes Claude CLI for README — same timeout issue.

## Workflow

1. **Phase 0 (fast, no script):** Run scope counts and content filter audit inline:
   ```bash
   echo "~/.claude/commands/: $(ls ~/.claude/commands/*.md 2>/dev/null | wc -l) .md files"
   echo "~/.claude/skills/:   $(ls ~/.claude/skills/ 2>/dev/null | wc -l) skill dirs"
   echo "~/.claude/hooks/:    $(ls ~/.claude/hooks/*.sh 2>/dev/null | wc -l) hooks"
   echo "~/.claude/agents/:   $(ls ~/.claude/agents/*.md 2>/dev/null | wc -l) agents"
   grep -rl "worldarchitect\|jleechanorg\|serviceAccountKey\|GOOGLE_APPLICATION\|mvp_site" ~/.claude/commands/ ~/.claude/skills/ 2>/dev/null | head -20
   ```
   Content filter matches are expected — the script has 8 `perl -pi -e` substitutions covering them. Only flag matches NOT in the 8 patterns.

2. **Phase 1 (real run):**
   ```bash
   cd ~/your-project.com && bash ~/.claude/commands/exportcommands.sh
   ```
   Creates a temp clone, union-merges global + project dirs, applies content filters, generates README, commits, pushes branch, opens PR.

3. **Output:** PR URL (e.g., `https://github.com/jleechanorg/claude-commands/pull/309`).

## Content Filters (8 patterns applied automatically)

1. `$GITHUB_REPOSITORY` → `$GITHUB_REPOSITORY`
2. `your-project.com` → `$PROJECT_NAME`
3. `$HOME` → `$HOME`
4. `\bjleechan\b` → `$USER`
5. Email addresses → redacted
6. `Your Project` → `$PROJECT_DISPLAY_NAME`
7. `TESTING=true python` → `pytest`
8. `$PROJECT_ROOT/` → `src/`

Files in `FILTER_SKIP` list are excluded from filtering (they contain literal regex patterns or test assertions on source strings).

When global (`~/.claude/`) and project (`.claude/`) have the same file:
- Identical content → either copy (no-op)
- Different content → call out content mismatches explicitly. The newer-file-by-age rule (age diff > 60s) should only be used as a heuristic fallback when content cannot be otherwise reconciled.
- Unresolved conflict / same age → project wins as tiebreak, flagged for review

## Pitfalls

- **Must run from git repo root** — not `~/.hermes_prod/`, not `/tmp/`.
- **120s timeout is too short** — use 300s.
- **`--dry-run` still invokes Claude CLI** for README generation — it's not a fast preview.
- **`exportcommands.py` is excluded** from export (deprecated, hardcoded paths in FILTER_SKIP).
- **`.claude_reference/commands/`** (~204 archived files) exports to `repo/.claude_reference/commands/`.
