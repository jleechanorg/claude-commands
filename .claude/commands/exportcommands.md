---
description: /exportcommands - Export Claude Commands to Reference Repository
type: llm-orchestration
execution_mode: immediate
argument-hint: 'Orchestrated runs — use ai_orch (orchestration/runner.py) with --agent-cli minimax (see Orchestrated execution)'
---

## Execution (Claude)

When this slash command is invoked, run the export pipeline immediately. Use `TodoWrite` if the work spans multiple steps (fix env, re-run, capture URL). This file is executable instruction, not background reading.

## Run the export (canonical)

From the project repository root:

```bash
bash .claude/commands/exportcommands.sh
```

`exportcommands.sh` **`exec`**s `python3` on **`.claude/commands/exportcommands.py`** with the same argv (single code path).

**Flags**

- `--dry-run` — clone target repo, build staging, copy into the clone, generate README; **skip** `git` commit, push, and `gh pr create`. Use when validating filters without publishing.

**Auth**

- Full publish requires **`GITHUB_TOKEN`** in the environment (used by `gh` for clone/push/PR). Dry-run does not require a token for those skipped steps.

## What the implementation does (truth in code)

All behavior lives in **`exportcommands.py`**: local `staging/`, clone of `jleechanorg/claude-commands`, filtered copy into the clone (see `_copy_directory_additive` — files from this repo **overwrite** matching paths; **extra files already in the reference repo are left alone**), README generation, then commit/push and **`gh pr create`** unless `--dry-run`.

Do not treat long bash “export protocol” narratives in old docs as specification; **`exportcommands.py` is authoritative.**

## Orchestrated execution (`--agent-cli minimax`)

For orchestrated runs that need the Minimax-backed CLI profile:

- Entry lives under **`orchestration/runner.py`**; invoke via **`ai_orch`** (see repo `CLI_PROFILES` / `MINIMAX_API_KEY` for credentials).
- Prefer a **single** `ai_orch run ... --agent-cli minimax` (or equivalent single-profile invocation). **`TaskDispatcher`** comma-separated agent chains are a different mechanism — do not assume they substitute for an explicit **`--agent-cli`** profile on `ai_orch run`.
- **`orchestrate_unified`** is **not** the supported entrypoint for this flow (legacy/stub naming); use **`ai_orch`** + **`orchestration/runner.py`** instead.

## REFERENCE DOCUMENTATION

**Repository safety:** Export only writes under the exporter’s temp/staging area and the **cloned** `claude-commands` checkout. It does **not** delete or rewrite arbitrary paths in your working project tree beyond what the Python exporter implements.

**Output contract:** On a **full** publish, the exporter must print the **real GitHub PR URL** as the **final line** of stdout. With **`--dry-run`**, the final line must be the canonical compare URL (see implementation: `https://github.com/jleechanorg/claude-commands/compare/main...DRY-RUN`). Automation keys off that last URL line.

## Success criteria

1. Full run: last stdout line is a real **`https://github.com/.../pull/...`** URL.  
2. `--dry-run`: last line is the dry-run compare URL; no PR created.  
3. Project repo remains safe per “Repository safety” above.
