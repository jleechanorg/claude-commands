---
name: ao-spawn-prompt-length-and-respawn
version: 1.0.0
description: Two non-obvious failure modes of `ao spawn` that hit on every multi-cycle green loop — the hard prompt-length cap, and the rate-limit cascade across harnesses. Both are silent (no helpful error text) and the spawn returns success; you only learn the loop is dead when the worker pane stays idle for >90s. Recovery recipes included.
---

# `ao spawn` prompt-length cap + rate-limit cascade recovery

Two failure modes hit on virtually every `ao spawn` for a multi-cycle CI fix:

1. **`PROMPT_TOO_LONG` hard cap** — the daemon rejects the spawn BEFORE the worker boots. No retry, no auto-shortening, no exit code >0 with a useful message. The spawn *appears* to succeed (returns `(idle) (claimed ...)` line) but the session never starts tool calls. Verified 2026-07-23 on $GITHUB_REPOSITORY PR #8545.
2. **Harness rate-limit cascade** — the first harness boots and then immediately fails with `You've hit your weekly limit · resets Jul 27 at 8pm`. Respawning on a different harness hits the same wall until you find one whose account pool isn't exhausted.

Both are silent in the `ao spawn` return text. The diagnostic signal is the worker's tmux pane staying empty / "idle" past the 90-second preflight window.

## Failure mode 1: `PROMPT_TOO_LONG`

**Symptom:**

```
$ ao spawn ... --prompt "$(cat /tmp/<brief>.md)"
prompt is too long (PROMPT_TOO_LONG) [request jeffreys-macbook-pro.local/CrxVDtRLV0-000163]
```

But also: even slightly-longer prompts succeed at the shell layer and the daemon returns `spawned session worldarchitect-114 (idle) (claimed ...)` — but the worker's tmux pane never shows tool calls. If `ao session get <id>` shows `activity: idle` for >90s, the spawn died silently and the daemon is reporting the *claimed-PR* state, not the *worker-booted* state.

**Recipe:**

1. Write the full brief to `/tmp/<topic>-brief.md` (or `~/.hermes/var/<topic>-brief.md`). Include everything: CI status, root cause, command recipes, constraints, end-state definition.
2. Spawn with a SHORT `--prompt` that points at the brief file: `--prompt "$(printf 'Fix CI for ... PR #N. Full brief: /tmp/<topic>-brief.md (READ THIS FIRST). End-state: ...')"`.
3. Verify the worker actually booted: `tmux capture-pane -t <session-id> -p | tail -20` — must show tool calls (Read, Bash, etc.) within 60s of spawn. If still empty/idle, the spawn died.
4. The short pointer prompt must include enough context for the worker to know what to do (`End-state: ...`, the PR number, the action verb). ~300-600 chars works reliably.

**Why the cap exists (and why we don't know the exact limit):** the AO daemon forwards the prompt to the harness CLI, and each harness has its own (different) prompt-length limit. The daemon does NOT pre-flight the prompt length. There is NO `ao spawn --max-prompt-length` flag.

**Anti-pattern:** pasting the full brief inline into `--prompt` "to keep it simple" — fails on any brief >~3KB. The brief-in-file + pointer pattern is the canonical form.

**Verified case 2026-07-23, PR #8545:** first spawn with 5150-char brief returned `PROMPT_TOO_LONG` immediately. Second spawn with a 528-char pointer prompt referencing `/tmp/fix-pr-8545-brief.md` succeeded; worker booted and started reading the brief file within 30s.

## Failure mode 2: rate-limit cascade across harnesses

**Symptom (in tmux pane after spawn):**

```
❯ CI is failing on PR #8545 ...
  <failing log>
  ⎿  You've hit your weekly limit · resets Jul 27 at 8pm (America/Los_Angeles)
     /usage-credits to finish what you're working on.

✻ Crunched for 0s

  ⏵⏵ bypass permissions on ...
```

The worker has booted but the model refuses to run because the account's weekly limit is hit. The session state is `activity: idle` indefinitely.

**Recipe (3-step cascade recovery):**

1. **Kill the dead session:** `ao session kill <id>` (do not let it linger — it blocks the claimed PR slot).
2. **List authorized harnesses:** `ao agent list` — look for `installed/authorized` rows. As of 2026-07-23 the reliable four are: `agy`, `claude-code`, `codex`, `cursor`. `aider`, `opencode` may also be authorized for some accounts.
3. **Respawn on a different authorized harness:**
   ```bash
   ao session kill <id>           # kill the rate-limited one
   cd ~/.hermes && ao spawn \
     --project <project> \
     --agent <different-harness> \
     --name "<topic>" \
     --claim-pr <N> \
     --prompt "<short pointer>"
   ```
   Try the cascade in this order if the previous failed: `claude-code` → `agy` (Gemini) → `codex` → `cursor`. Each harness has its own account pool with separate limits, so one being rate-limited does not affect the others.
4. **Verify the new worker actually boots** — same check: `tmux capture-pane` shows tool calls within 60s. If it shows a fresh rate-limit message, kill and try the next harness.

**Anti-patterns:**

- Retrying the same rate-limited harness 3 times — each retry just re-extends the ETA (claude-code in particular observed 18min→57min→58min across 3 retries same day, 2026-07-16 incident).
- Letting a dead session linger — it blocks the claimed PR slot, so the next `ao spawn --claim-pr <N>` will see the existing owner and refuse.

**Verification that the spawn actually worked (not just claimed):**

```bash
ao session get <id> | grep -E "(status|activity|created)"
# status: ci_failed       <- initial state, OK
# activity: running       <- MUST be this or "tool_use"
# created: <recent>
```

If `activity: idle` for >90s while `status: ci_failed`, the spawn died. Kill and respawn.

## Cross-reference

- `references/spawn-model-preflight.md` — the upstream preflight that motivated this reference; the recovery recipe here EXTENDS that preflight with the actual kill+respawn commands.
- `~/.hermes/skills/agento/SKILL.md` "Spawn-time model preflight" — the canonical preflight section that points here.

## Source provenance

This reference was written after a 2026-07-23 PR #8545 fix dispatch on $GITHUB_REPOSITORY where:
- First spawn (claude-code) → worker booted, model refused with weekly limit.
- Second spawn (codex) → worker booted, model refused with weekly limit (resets Jul 28).
- Third spawn (agy / Gemini 3.6 Flash) → worker booted and ran successfully.

The prompt-length cap was hit on an earlier test of the same dispatch when the full 5150-char brief was passed inline. The brief-to-file + pointer pattern fixed it.
