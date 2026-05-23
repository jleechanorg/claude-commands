---
name: dark-factory
description: "Run the Dark Factory DOT pipeline runner against a goal. Slash command: /factory. Implements StrongDM's Attractor pattern as an external Python runner — .dot files are the versioned artifact, sealed holdouts live in a separate repo, every step is recorded to CXDB, and the Healer clusters failures into diagnoses. Use when you want the goal_harness idea executed as a reproducible external pipeline instead of in-Claude subagent dispatch."
---

# /factory — Dark Factory Pipeline Runner

## Purpose

Run a goal through the Dark Factory `.dot` pipeline runner at
`~/projects/dark-factory/`. The runner is the Python implementation of
StrongDM's Attractor pattern (cf. brynary/attractor, strongdm/attractor).

Versus `/h` / `/goal_harness`:

| Aspect | `/h` (goal_harness) | `/factory` (this skill) |
|--------|---------------------|-------------------------|
| Engine | Claude session dispatches subagents | External `python -m runner` |
| Artifact | Skill prose + tool calls | `.dot` graphviz file |
| Recording | Conversation transcript | SQLite CXDB row-per-step |
| Holdouts | Adversarial subagent reads diff | Sealed repo agent never sees |
| Reuse | Tied to this session | Replayable from `.dot` alone |
| Cost | High (multi-agent context) | Low (one CLI per node) |

Use `/factory` when you want the goal_harness idea as a reproducible external
pipeline; use `/h` when you want an interactive in-session loop.

## Repos

- `~/projects/dark-factory/` — the runner (factory code; agent can see this)
- `~/projects/dark-factory-holdouts/` — sealed scenarios (agent must NEVER read)
- Pushed: `https://github.com/jleechanorg/dark-factory` + `dark-factory-holdouts`

## Available pipelines

| `.dot` file | Flow | When to use |
|-------------|------|-------------|
| `pipelines/factory/hello.dot` | plan → implement → holdout → fix-loop → exit | Add a new feature with a holdout scenario |
| `pipelines/factory/gates.dot` | start → holdout → /es → /er → /code_standards → exit | Validate an already-implemented diff (Attractor-style 4-gate harness as `.dot`) |

You can also write your own `.dot` and pass it via `--pipeline`.

## How to invoke this skill

The user types `/factory $ARGUMENTS`. Parse the arguments and run the steps
below. Default to the `gates.dot` pipeline and the `claude` backend unless the
user supplied flags.

### Arg parsing

Honor these flags inside `$ARGUMENTS`:

- `--pipeline <name>` — short name (`gates`, `hello`) or absolute path to a `.dot`
- `--feature <name>` — holdout feature (required when the pipeline includes a
  `holdout_eval` node; default `hello`)
- `--backend echo|claude|codex` — default `claude`. Use `echo` for cost-free
  dry-runs that verify wiring without LLM calls.
- `--max-steps <N>` — default 100
- `--cxdb <path>` — default `~/.dark-factory/cxdb.sqlite` (shared across runs
  so the Healer can cluster across history)

Whatever is left after flag parsing is the **goal description**.

### Steps

1. **Verify install**. Run:
   ```bash
   test -f ~/projects/dark-factory/runner/__main__.py || {
     echo "ERROR: dark-factory not found at ~/projects/dark-factory"
     exit 1
   }
   ```
   If missing, tell the user to clone it from
   `https://github.com/jleechanorg/dark-factory` and stop.

2. **Verify venv**. If `~/projects/dark-factory/.venv` doesn't exist, create
   it and install requirements:
   ```bash
   cd ~/projects/dark-factory && python3 -m venv .venv && \
     source .venv/bin/activate && pip install -q -r requirements.txt
   ```

3. **Set the holdouts env var**:
   ```bash
   export DARK_FACTORY_HOLDOUTS=~/projects/dark-factory-holdouts
   ```

4. **Run the pipeline**. The runner emits a JSON trace to stdout:
   ```bash
   cd ~/projects/dark-factory && source .venv/bin/activate && \
     python -m runner \
       --pipeline pipelines/factory/<NAME>.dot \
       --goal "<GOAL>" \
       --backend <BACKEND> \
       --feature <FEATURE> \
       --cxdb <CXDB_PATH>
   ```

5. **Surface the verdict**. The last line of stdout is a JSON summary with
   `final_outcome`, `pipeline`, `goal`, `steps`, `trace`. Report:
   - Pipeline name + final outcome
   - Per-node trace (one line each: `node  outcome  preview`)
   - Exit code of the runner

6. **Run the Healer** (only if `final_outcome != "success"`):
   ```bash
   python -m runner.healer --cxdb <CXDB_PATH>
   ```
   Render the resulting markdown table inline. Each row is a failure cluster
   with a prescription template the user can act on.

7. **Sealed holdouts reminder**. If the run included a `holdout_eval` node,
   remind the user that you (and any subagent) did NOT see the scenarios at
   `~/projects/dark-factory-holdouts/holdouts/<feature>/` — only the
   PASS/FAIL verdict per scenario name leaked back.

## Output contract

End every `/factory` invocation with:

```
Pipeline:       <name>
Final outcome:  PASS | FAIL | exhausted | stuck
Steps:          <n>
CXDB:           <path>   (run `python -m runner.healer --cxdb <path>` to re-cluster)
```

Plus the trace and, on failure, the Healer report.

## Adding a new feature

To add a new sealed-holdout feature `foo`:

1. Write `~/projects/dark-factory/specs/foo.md` (agent-visible).
2. Write `~/projects/dark-factory/prompts/foo/{plan,implement,fix}.md`.
3. Write `~/projects/dark-factory-holdouts/holdouts/foo/scenarios.yaml`
   in the sealed repo (the implementing agent must never read this).
4. Either reuse `pipelines/factory/hello.dot` (which is feature-agnostic) by
   passing `--feature foo`, or write `pipelines/factory/foo.dot` with custom
   nodes.

## Honesty rules

- Always tell the user the **actual command** you ran. No paraphrasing.
- Always quote the **runner's exit code** verbatim.
- Never claim a holdout passed if you read the scenarios — that breaks the
  adversarial guarantee. If you read `~/projects/dark-factory-holdouts/`,
  declare the run **invalid** and rerun the pipeline.
- If `--backend echo` was used, label the run as a wiring smoke, not a real
  validation.

## Known limits

- The `claude` backend shells out to `claude --print
  --dangerously-skip-permissions` — each node is a fresh non-interactive
  session. Long agentic loops should use `/h` instead.
- `_parse_verdict` falls back to scanning the tail for a standalone PASS/FAIL
  token; if the gate command emits a debug line with just "PASS" the runner
  will trust it. For high-stakes gates require explicit `VERDICT:` markers.
- CXDB is per-process — don't share one across threads.
