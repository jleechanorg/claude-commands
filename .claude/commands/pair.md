---
description: Launch dual-agent pair programming with coder + verifier
argument-hint: '"task description"'
type: llm-orchestration
execution_mode: llm-driven
---

---

# /pair - Dual-Agent Pair Programming (Teams-Native)

## Primary: Teams-native (default)

When `/pair <task>` is invoked, use the Teams-native path:

### Step-by-step

1. **Create team**
   ```
   TeamCreate("pair-{hash}")
   ```
   where `{hash}` is a short identifier derived from the task (e.g., first 8 chars of SHA256).

2. **Create tasks with dependency**
   ```
   implement_task = TaskCreate("Implement: {task}", ...)
   verify_task    = TaskCreate("Verify: {task}",    blockedBy=[implement_task.id])
   ```
   The verify task is blocked until implement is marked complete.

3. **Launch coder**
   ```
   Task(subagent_type="pair-coder", model="sonnet",
        instructions="Implement {task}. Signal IMPLEMENTATION_READY when done.")
   ```

4. **Launch verifier** (after IMPLEMENTATION_READY received)
   ```
   Task(subagent_type="pair-verifier", model="haiku",
        instructions="Verify {task}. Signal VERIFICATION_COMPLETE when done.")
   ```

5. **Wait for completion signals**
   - Poll teammate messages for `IMPLEMENTATION_READY` from coder.
   - Only after `IMPLEMENTATION_READY`: unblock verify task and launch verifier.
   - Poll for `VERIFICATION_COMPLETE` from verifier.

6. **Synthesize result**
   Report final outcome to the user after both signals are observed.

### Policy

- Do not implement inline in the lead session.
- Keep coder/verifier responsibilities separate.
- Require independent verification before declaring done.

## Fallback: --scripted

Use `--scripted` when the runtime does not expose native Teams controls or when the user explicitly requests scripted behavior.

### --scripted primary (pairv2)

```bash
python3 .claude/pair/pair_execute_v2.py \
  --left-contract .claude/contracts/left_contract.template.json \
  --right-contract .claude/contracts/right_contract.template.json \
  --no-worktree "Your task description here"
```

### --scripted last resort (pairv1)

```bash
python3 .claude/pair/pair_execute.py --no-worktree "Your task description here"
```

See `/pairv1` for full legacy CLI reference.

## Logging Convention

Both Teams and --scripted runs write timestamped logs:

- Directory: `/tmp/{repo_name}/{branch}/pair_logs/`
- Files: `coder.log`, `verifier.log`
- Format: `[YYYY-MM-DD HH:MM:SS] [PHASE] message`

## Completion criteria

A pair session is complete only when all are true:

1. Coder signals `IMPLEMENTATION_READY`.
2. Verifier signals `VERIFICATION_COMPLETE`.
3. Lead session synthesizes both outputs and reports final result.

## Agent cleanup

- Teams mode: Claude manages teammate lifecycle after completion.
- --scripted mode: `pair_execute_v2.py` terminates/observes both agents.
- Legacy fallback: `pair_execute.py` terminates both agents.
- If a session is interrupted, check for orphaned processes before rerun.

**Protocol Version:** 9.1 (TeamCreate primary with TaskCreate dependency; --scripted fallback)
