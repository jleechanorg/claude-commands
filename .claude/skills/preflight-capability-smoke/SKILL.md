---
name: preflight-capability-smoke
description: "Use when starting multi-hour or multi-lane work on any Mac or Linux host. Probes repo read, an isolated write plus one real test, the publish path, the evidence path, auth state and the next one or two gates before capacity is committed. Classifies each result as verified, untested, denied, unavailable or capacity, and never creates dummy remote writes, provider charges or credential changes to test permission."
---

# /preflight-capability-smoke — capability probe before a large task

Run this once per host **before** starting multi-hour, multi-lane, or multi-agent work. It is a **capability probe, not a test suite**, and it must not create side effects.

## Procedure

1. **Read** — prove the repo you will edit:
   - `git -C <repo> remote get-url origin`
   - `git rev-parse --abbrev-ref HEAD`
   - `git rev-parse HEAD`
   - `git status --porcelain | wc -l`

   Compare the head against the head you were told to work at. A stale checkout is a finding, not a working copy.

2. **Write and execute** — create a scratch worktree (`git worktree add`), make one trivial local commit there, and run **one real focused test** in that worktree. Record the command and the exit code.

3. **Publish path** — if the task will push, prove the remote accepts a write **once** (a real branch push, or an explicit dry-run when pushing is inappropriate). Record the exact refspec result or the denial.

4. **Evidence path** — prove where artifacts will land (attachment upload, bucket prefix, or PR comment) with one small real artifact.

5. **Interactive surfaces** — for browser or auth-gated work, state whether an authenticated session exists. An unauthenticated `401` proves **that request carried no token**; it does not prove no session exists.

6. **Gates** — name the next one or two dependency gates: approvals, credentials, device locks, or temporary slot limits.

## Result classification

| Class | Meaning |
|---|---|
| `verified` | The command ran and its exit/output is recorded |
| `untested` | Not exercised; say so instead of implying success |
| `denied` | Authorization refusal — quote the exact denial text |
| `unavailable` | Tool, binary, or credential is missing |
| `capacity` | Temporary limit (slots, quota, busy pane), not a permission denial |

Report a denial or tool failure **separately** from an ordinary test bug.

## Boundaries

- Never create dummy remote writes, provider charges, or credential/security changes merely to test permission.
- Never infer a capability from a config file, a sync-only receipt, or another host's result.
- An explicit stop, runtime hold, or safety floor **outranks** this probe: skip the affected step and report the hold instead of working around it.

## Output

Return one row per capability with the exact command and exit/output behind every `verified` row, plus the classified state for the rest.
