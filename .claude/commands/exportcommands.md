# /exportcommands — Export the superset of ~/.claude/ + ~/.hermes/ + project .claude/ (and root orchestration/automation/ralph) to jleechanorg/claude-commands

This slash-command orchestrates the canonical "export Claude commands" pipeline.
It is a **thin wrapper** over `~/.claude/commands/exportcommands.sh`. Anything this
file documents that the script does not also do is a bug — either in the docs or in
the script.

## Two layers — pick the right entry point

`/exportcommands` is the **file-export** layer. It does **not** run agents; it
ships commands + skills + hooks to `jleechanorg/claude-commands`. If you want to
**run a profile of agents** (e.g. `minimax` + `codex` + `claude-code` in parallel)
against a task, that is the **orchestration** layer, not this one.

| Layer | Entry point | Use when |
| --- | --- | --- |
| **File export** (this doc) | `bash ~/.claude/commands/exportcommands.sh` | Syncing `~/.claude/` + `~/.hermes/` + project `.claude/` to `jleechanorg/claude-commands` |
| **Agent orchestration** | `ai_orch run --agent-cli minimax --task ...` (via `orchestration/runner.py`) | Dispatching a multi-agent task with explicit CLI profiles |
| **Legacy entry (DO NOT USE)** | `orchestrate_unified.py` | Stub — kept for back-compat; emits a warning when invoked. Always prefer `ai_orch run`. |
| **Comma-chain fallback** | `TaskDispatcher foo,bar,baz` | Quick local chain — fine for one-off tasks, but loses profile isolation. `ai_orch run` is the canonical path. |

The single-profile `ai_orch run --agent-cli <name>` form is one CLI per profile
(`minimax`, `claude`, `codex`, etc.). It reads profile keys from `CLI_PROFILES`
(see `~/.hermes/config.yaml`). `TaskDispatcher` comma-chains, by contrast,
spawn everything in one process — fine for "I just want results", wrong for
"each agent needs its own model + tool budget".

## When to use

Run `/exportcommands` whenever any of the following changes:

- A new skill, slash-command, hook, agent, or script in `~/.claude/` or in this
  repo's `.claude/` dir.
- A new skill in `~/.hermes/skills/` or command in `~/.hermes/commands/`
  (Hermes-managed surfaces — see "Hermes skills" below).
- A change to any file under `orchestration/`, `automation/`, or `ralph/` at the
  repo root.
- The content-filter regex set needs a new substitution (e.g. a new project name).

It is safe to run repeatedly. The script preserves files only present in the
target repo (rsync default; no `--delete`).

## What it does (the superset definition)

The script exports the **union** of the following source surfaces into a fresh
clone of `jleechanorg/claude-commands` on a timestamped branch
(`export-YYYYMMDD-HHMMSS`), opens a PR, then optionally pushes/regenerates README.

### Source surface 1 — global (`~/.claude/`)

| Subdir | What lives there |
| --- | --- |
| `commands/` | Slash-command Markdown files (e.g. `a.md`, `ms.md`, `exportcommands.md`). Aliases are symlinks here. |
| `skills/` | Personal skill directories, each with `SKILL.md`. |
| `hooks/` | Shell hooks invoked at Claude session boundaries. |
| `agents/` | Markdown agent definitions. |
| `scripts/` | Helper scripts called from commands. |

### Source surface 1.5 — Hermes-managed (`~/.hermes/`)

Exported to a **separate top-level** `hermes/` dir in the target repo (NOT under
`.claude/`), so the upstream Claude Code config layer stays clean. The script
soft-skips a `~/.hermes/<dir>` that does not exist (Hermes may not be installed
on every machine) — that is not a hard failure.

| Subdir | What lives there |
| --- | --- |
| `skills/` | Hermes skill directories, each with `SKILL.md`. The canonical source of truth is `~/projects/hermes-agent/` (per the `hermes-deploy-pipeline` skill); this export ships a downstream mirror. |
| `commands/` | Hermes slash-commands and supporting scripts. Same source-of-truth relationship. |

**Precedence note.** `~/.hermes/skills/` is exported to a *separate top-level*
`hermes/` directory in the target repo (not merged into `.claude/skills/`), so
`union_dir`'s mtime collision rule does not apply. The hermes-deploy-pipeline
copy is authoritative — see "Source of truth" below.

**Source of truth.** Hermes skills are versioned in `~/projects/hermes-agent/`
and deployed via the `hermes-deploy-pipeline` skill. The `claude-commands`
export is a **downstream mirror only** — never edit a hermes skill in
`jleechanorg/claude-commands` and expect it to propagate back. Always edit in
`~/projects/hermes-agent/` and re-run the deploy.

### Source surface 2 — project (this repo's `.claude/`)

Same five subdirs as Source Surface 1. Where a file exists in both surfaces, content is
compared (not blindly overwritten by age); mismatches are flagged. Project wins
on age tiebreak with the newer-file-by-age heuristic as a fallback only.

For the your-project.com repo specifically, this surface includes
`your-project.com`'s `.claude/commands/*.md` (e.g. `pr.md`, `green.md`, `er.md`,
`babysit.md`) and `.claude/skills/` (e.g. `baby-skill-onboard`, `evidence-review`,
`gcp-deployments`, `worldarchitect-ai-evidence`).

### Source surface 3 — repo-root dirs

`orchestration/`, `automation/`, `ralph/` from the project root, exported as-is
at the repo root of the target.

### What this export does NOT cover (and why)

| Surface | Reason excluded |
| --- | --- |
| `$PROJECT_ROOT/` source files | These are project runtime code, not commands. The script's content filter rewrites `$PROJECT_ROOT/` references in commands to `$PROJECT_ROOT/` so the exported commands stay project-agnostic. |
| `.git/`, `.venv/`, `__pycache__/` | Repo hygiene; never exported. |
| `.mcp_config*`, `plugin.json`, `package-lock.json` under `~/.hermes/` | Hermes runtime config / plugin state — not portable. Excluded from the hermes rsync. |
| Anything under `~/.hermes/profiles/<name>/skills` or `commands` | Profile-scoped skills are not part of the cross-machine default; they live where Hermes expects them on the host that owns the profile. |

## How to run

### Standard run (from the project root)

```bash
cd ~/your-project.com
bash ~/.claude/commands/exportcommands.sh      # auto-pushes branch + opens PR
```

### Worktree run (current working dir)

```bash
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
bash ~/.claude/commands/exportcommands.sh
```

> Run from a worktree only if the worktree HEAD matches `origin/main` for the
> files you intend to export. Otherwise worktree-only edits leak into the
> superset. The script does NOT verify this — you must.

### Dry run (still invokes `claude` CLI for README — not a fast preview)

```bash
bash ~/.claude/commands/exportcommands.sh --dry-run
```

### Hermes-only run (env var override)

```bash
HERMES_HOME=/path/to/other/hermes bash ~/.claude/commands/exportcommands.sh
```

## What lands in `jleechanorg/claude-commands`

After the script finishes, the target branch has:

```text
.claude/commands/    # all slash-command .md files (union of ~/.claude + project)
.claude/skills/      # all skill SKILL.md files
.claude/hooks/       # all hook scripts
.claude/agents/      # all agent .md files
.claude/scripts/     # all helper scripts
hermes/skills/       # hermes skill SKILL.md files (downstream mirror)
hermes/commands/     # hermes command files
orchestration/       # project-root orchestration
automation/          # project-root automation
ralph/               # project-root ralph
workflows/           # example GitHub Actions workflows (subset)
```

Then a PR is opened against `jleechanorg/claude-commands:main`.

## CI on the resulting PR

The `jleechanorg/claude-commands` repo has its own CI that:

- Runs `bash tests/test_exportcommands_orchestration_contract.py` to assert the
  `/exportcommands.md` doc covers the orchestrator plumbing layer
  (`orchestration/runner.py`, `ai_orch`, `--agent-cli minimax`,
  `orchestrate_unified`, `CLI_PROFILES`, `TaskDispatcher`).
- Runs `bash -n` on the script.
- Verifies the new hermes/skills + hermes/commands contract substrings (added
  in this change).

## Related

- The export runs `claude` CLI to regenerate `README.md` after the file copy
  step. The prompt instructs Claude to make **minimal** updates: add a
  `## Changelog` section, list new commands, update counts. It explicitly
  preserves all other text.
- If you only want to view a preview of the change without pushing, use
  `--dry-run` — the script still runs the README regen (writes
  `README.md.new`) but does not push or open a PR.
- The hermes-deploy-pipeline is the source of truth for hermes skills; the
  claude-commands export is a downstream mirror. If a hermes skill diverges
  between the two, the hermes-deploy-pipeline copy wins.
