---
name: preflight-capability-smoke
description: "Use when a task is large or its host capabilities are uncertain, on any Mac or Linux host. Reuses recent exact receipts where they exist and probes only the missing capabilities: repo read, an isolated write plus one real test, the publish path, the evidence path, auth state and the next one or two gates. Classifies each result as verified, limited, untested, denied, unavailable or capacity, and never creates dummy remote writes, provider charges or credential changes to test permission."
---

# /preflight-capability-smoke — capability probe before a large or uncertain task

Use this when a task is **large or its host capabilities are uncertain** — multi-hour, multi-lane, multi-agent, or a first run on a host or runtime you have not exercised. It is a **capability probe, not a test suite**, and it must not create side effects.

**Reuse first.** If a needed capability already has a recent, exact receipt for the same host, repo and head (a real push, a real test run, a real upload), cite that receipt and probe nothing. Probe only what is missing or stale.

## Procedure

1. **Read** — prove the repo you will edit:
   - `git -C <repo> remote get-url origin`
   - `git rev-parse --abbrev-ref HEAD`
   - `git rev-parse HEAD`
   - `git status --porcelain | wc -l`

   Compare the head against the head you were told to work at. A stale checkout is a finding, not a working copy.

2. **Write and execute** — prefer an existing scratch worktree; create one only if you will actually need it. Run **one real, already-existing focused test** and record the command plus exit code. Do not add a commit, push, or artifact publication **solely** to prove a capability.

3. **Publish path** — if the task will push, prove it with a real branch push, or state an explicit **dry-run**, which is a **limited** result: it shows the path exists, not that a write will be accepted. Never record a dry-run, or a command that was never executed, as `verified`.

4. **Evidence path** — identify where artifacts will land (attachment upload, bucket prefix, PR comment) and say whether that path is verified or only expected. One small real artifact is enough when the task truly needs it.

5. **Auth state** — state whether an authenticated session exists. An unauthenticated `401` has an **unknown cause** until verified: it may be a missing token, an invalid or expired token, or a token for the wrong audience. Do not report it as "no session exists".

6. **Gates** — name the next one or two dependency gates: approvals, credentials, device locks, or temporary slot limits. Identify gates **before** publishing anything.

## Result classification

| Class | Meaning |
|---|---|
| `verified` | The command executed, exited as expected, and its postcondition was confirmed; record command, exit and the observed postcondition |
| `limited` | Partial evidence: a dry-run, a probe against a stub, or a postcondition that was not confirmed |
| `untested` | Not exercised; say so instead of implying success |
| `denied` | Authorization refusal — quote the exact denial text |
| `unavailable` | Tool, binary, or credential is missing |
| `capacity` | Temporary limit (slots, quota, busy pane), not a permission denial |

A failed executed command is never `verified`, and a denial or tool failure is reported **separately** from an ordinary test bug.

## Boundaries

- Never create dummy remote writes, provider charges, or credential/security changes merely to test permission.
- Never infer a capability from a config file, a sync-only receipt, or another host's result.
- A probe that produces a lasting artifact — a commit, a published file, a comment — is allowed only when the task needs that artifact anyway.
- An explicit stop, runtime hold, or safety floor **outranks** this probe: skip the affected step and report the hold instead of working around it.

## Output

One row per capability with command, exit and postcondition behind every `verified` row, and the classified state for the rest.
