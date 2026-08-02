# exportcommands.sh Contract Reference

Canonical contract for the live `your-project.com/.claude/commands/exportcommands.sh` script (the
hermes-aware version, per Pitfall 3 of the parent SKILL.md). Sources for this doc: the script
itself (parsed 2026-07-13) + the `testing_mcp/test_exportcommands_orchestration_contract.py`
contract tests.

## Variables & Inputs

| Variable | Source | Required | Default |
|---|---|---|---|
| `TARGET_REPO` | hardcoded | yes | `jleechanorg/claude-commands` |
| `BRANCH` | script-generated | yes | `export-$(date +%Y%m%d-%H%M%S)` |
| `REPO_DIR` | `mktemp -d` | yes | ephemeral, trap'd EXIT |
| `GLOBAL_CLAUDE` | `$HOME/.claude` | yes | — |
| `PROJECT_ROOT` | `$PROJECT_ROOT` env var OR `git rev-parse --show-toplevel` | yes | fails fast if both absent |
| `PROJECT_CLAUDE` | `$PROJECT_ROOT/.claude` | derived | — |
| `CLAUDE_DIRS` | hardcoded | yes | `(commands skills hooks agents scripts)` |
| `ROOT_DIRS` | hardcoded | yes | `(orchestration automation ralph)` |
| `HERMES_DIRS` | hardcoded (live version only) | yes | `(skills commands)` — separate top-level `hermes/` dir in target |
| `FILTER_SKIP` | hardcoded | yes | `(exportcommands.py exportcommands.sh loc_simple.sh test_exportcommands.py)` |
| `SUBS` | hardcoded | yes | 8 perl one-liners — see below |
| `MVp_SITE_SUB` | hardcoded | yes | `s\|$PROJECT_ROOT/\|$PROJECT_ROOT/\|g` (skipped for `workflows/*.yml`) |

## Filter Substitution Order (CRITICAL — specific before general)

```bash
declare -a SUBS=(
  's|jleechanorg/worldarchitect\.ai|\$GITHUB_REPOSITORY|g'    # specific FIRST
  's|worldarchitect\.ai|your-project.com|g'                  # general AFTER
  's|${PROJECT_NAME:-your-project}-ci|\$\{PROJECT_NAME:-your-project\}-ci|g'
  's|$HOME|\$HOME|g'
  's|\bjleechan\b|\$USER|g'
  's|jleechantest\@gmail\.com|<your-email\@gmail.com>|g'
  's|WorldArchitect\.AI|Your Project|g'
  's|TESTING=true python|TESTING=true python|g'
)
```

**Why specific-before-general matters:** if `your-project.com` runs first, it consumes the
`$GITHUB_REPOSITORY` pattern and produces `jleechanorg/your-project.com` — a malformed
URL that breaks downstream GitHub Actions.

## `apply_filters(file)` Behavior

For each file:
1. If `basename $file` is in `FILTER_SKIP` → return without filtering.
2. Apply each `SUBS[i]` via `perl -pi -e "$sub" "$file"` (supports `\b` word boundary on macOS).
3. If file is NOT `workflows/*.yml` or `workflows/*.yaml`, also apply `MVp_SITE_SUB`.
   - Reason: GitHub Actions does NOT expand `$PROJECT_ROOT` in `paths:` filters or `hashFiles()`
     calls, so substituting into workflows would silently break CI triggers.

## `union_dir(dir)` Behavior

Inputs: `$GLOBAL_CLAUDE/$dir` (e.g. `~/.claude/commands`), `$PROJECT_CLAUDE/$dir` (e.g. `your-project.com/.claude/commands`), target `.claude/$dir`.

Resolution rules:
- File only in GLOBAL → use GLOBAL
- File only in PROJECT → use PROJECT
- File in both, identical → use either
- File in both, project newer (mtime) → use PROJECT
- File in both, global newer (mtime) → use GLOBAL
- File in both, same mtime, differ → CONFLICT, use PROJECT as tiebreak (report to `CONFLICTS` array)

**Pitfall:** mtime is the only tiebreak. If you `touch` a local file to force-include it, the
script will pick up the touched version even if the content is older. Don't rely on `touch` for
forcing inclusion.

## Auto-Open PR Behavior

After the merge + filter pass:
1. `gh repo clone jleechanorg/claude-commands $REPO_DIR`
2. `git checkout main && git pull --ff-only origin main`
3. `git checkout -b "$BRANCH"` (where `BRANCH = export-YYYYMMDD-HHMMSS`)
4. Auto-generated commit message: `export: <DATE> — N files changed, +A/-D`
5. `git secret guard` runs on the outgoing range and prints to stdout
6. `gh pr create --head $BRANCH --base main --title "Claude Commands Export <DATE>" --body "<auto summary>"`

The script does NOT wait for review or merge. It posts "✅ Export complete! PR: <URL>" and exits.

## Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| `ERROR: PROJECT_ROOT is unset and git rev-parse failed` | Not in a git repo AND env var unset | `cd ~/your-project.com` first |
| `⚠️ Claude CLI failed — keeping existing README unchanged` | `claude` CLI auth or network error | Non-blocking; README regenerates next run. But if it keeps failing, the export script can't progress. |
| Empty PR (0 files changed) | `~/.claude/` and project's `.claude/` are byte-identical to last export | Expected; close the PR as no-op |
| 100+ workflow conflicts at `git merge --no-ff origin/main` | Trying to merge a stale-base export PR | Re-run from fresh `main` checkout instead |
| CodeRabbit "Review limit reached" on every auto-PR | User/org hit the CodeRabbit quota | Document per Pitfall 4 of parent SKILL.md; not the script's bug |

## Contract Tests (in testing_mcp/)

The script's contract is enforced by `testing_mcp/test_exportcommands_orchestration_contract.py`.
The required substrings in `.claude/commands/exportcommands.md`:

```python
required = [
    ("--agent-cli minimax", "document minimax CLI flag"),
    ("orchestration/runner.py", "point to runner implementation"),
    ("ai_orch", "document ai_orch entry"),
    ("orchestrate_unified", "warn about stub or name it"),
    ("CLI_PROFILES", "tie to profile keys"),
    ("TaskDispatcher", "clarify comma chains vs ai_orch run"),
    ("hermes/skills", "include hermes skills in superset"),
    ("hermes/commands", "include hermes commands in superset"),
]
```

If you modify the script, run the contract tests before committing:

```bash
cd ~/your-project.com
PYTHONPATH=. python -m pytest testing_mcp/test_exportcommands_orchestration_contract.py -x -v
```

## "This script was just here before PR #8135" — a note for the curious

The 466-line `~/.claude/commands/exportcommands.sh` (the older, non-hermes version) was committed
sometime in 2024-06 and has been stable since. The hermes-aware version lives ONLY in the WA
repo's `.claude/commands/exportcommands.sh` because of how the contract tests are wired. Future
work to consolidate the two versions should land in a single source-of-truth (probably the WA
repo's `.claude/commands/`), and the contract tests should be updated to enforce hermes presence
in the global script too. That's a separate bead — not in scope for this skill.