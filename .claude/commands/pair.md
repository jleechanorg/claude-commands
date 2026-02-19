---
description: Launch dual-agent pair programming with coder + verifier
argument-hint: '"task description"'
type: llm-orchestration
execution_mode: llm-driven
---

---

# /pair - Dual-Agent Pair Programming

Use Claude Agent Teams behavior that Claude understands natively.

## Design note: native teams first, Task(...) fallback

`/pair` now prefers native Agent Teams language instead of always forcing explicit `Task(...)` calls in the default path. This keeps default behavior aligned with teams-capable runtimes while preserving a deterministic custom fallback for runtimes that do not expose native team controls.

## Default: Native Agent Teams (teams-aware)

When `/pair <task>` is invoked in a Teams-capable runtime:

1. Ask Claude to create a two-teammate pair for the task in natural language.
2. Specify two roles clearly:
   - **Coder**: implements the task and updates tests as needed.
   - **Verifier**: independently reviews code and validates correctness.
3. Keep coordination in normal team workflows (task list, teammate messages, lead synthesis).
4. Gate completion on explicit handoff signals:
   - coder publishes `IMPLEMENTATION_READY` before verifier final pass;
   - verifier publishes `VERIFICATION_COMPLETE` before lead synthesis.
5. Report final result back to the user after both signals are observed.

### Recommended natural-language prompt pattern

Use wording like:

- "Create an agent team for pair programming on this task. One teammate is the coder, one is the verifier. Require coder to emit IMPLEMENTATION_READY and verifier to emit VERIFICATION_COMPLETE."
- "Coder should implement; verifier should review and validate before completion. Do not implement inline in the lead session."
- "Use shared logs at LOG_DIR=/tmp/{repo_name}/{branch}/pair_logs/ with timestamped entries."

#### Coordination parameters

When creating a pair session, include:

- **Shared team identifier** (for example `team_name`) so both roles are tracked as one session.
- **Explicit role names** (`coder` and `verifier`) for directed teammate messages.
- **Shared task context** (`task_id` or equivalent task summary) so verifier can validate coder output against the same scope.
- **Expected turn-taking**: coder implements and signals readiness; verifier validates and signals completion.

## Pair-specific behavior (policy)

The `/pair` command enforces pair discipline at the prompt/policy layer:

- Do not do the implementation inline in the lead session.
- Keep coder/verifier responsibilities separate.
- Require independent verification before declaring done.

This is policy guidance, not a hard runtime sandbox. If strict machine enforcement is required, use the custom scripted fallback below.

## Non-native fallback (only when needed)

Use explicit custom orchestration only when the runtime does not expose native Agent Teams controls or when the user explicitly requests custom scripted behavior.

For scripted/custom environments, use existing project tooling:

```bash
python3 .claude/scripts/pair_execute.py --no-worktree "Your task description here"
```

## CLI-Specific Agents (custom/runtime-dependent)

If using custom scripted orchestration, these agent types are available:

| CLI | Coder subagent_type | Verifier subagent_type |
|-----|---------------------|----------------------|
| Claude (native) | `pair-coder` | `pair-verifier` |
| Claude (CLI) | `claude-pair-coder` | `claude-pair-verifier` |
| Codex | `codex-pair-coder` | `codex-pair-verifier` |
| Gemini | `gemini-pair-coder` | `gemini-pair-verifier` |
| Cursor | `cursor-pair-coder` | `cursor-pair-verifier` |
| MiniMax | `minimax-pair-coder` | `minimax-pair-verifier` |

These mappings are for custom orchestration paths, not required by native Agent Teams.

## Logging Convention

Native teams and scripted pair runs should both write timestamped logs:

- Directory: `/tmp/{repo_name}/{branch}/pair_logs/`
- Files: `coder.log`, `verifier.log`
- Format: `[YYYY-MM-DD HH:MM:SS] [PHASE] message`

## Troubleshooting

- If Teams mode is available, stay in natural-language team control and avoid non-native orchestration syntax.
- If Teams mode is unavailable, use `pair_execute.py`.

### Agent cleanup

- Native Teams mode: Claude manages teammate lifecycle after completion.
- Scripted mode: ensure `pair_execute.py` terminates both agents, including interrupted sessions.
- If a session is interrupted, check for orphaned processes and terminate stale pair agents before rerun.

## Completion criteria

A pair session is complete only when all are true:

1. Coder signals `IMPLEMENTATION_READY`.
2. Verifier signals `VERIFICATION_COMPLETE`.
3. Lead session synthesizes both outputs and reports final result.

**Protocol Version:** 8.1 (native teams default with explicit coordination, logging, and completion guidance)
