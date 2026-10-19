---
name: hermes
description: Coordinate authorized engineering work with Hermes through Slack, verify acknowledgment and evidence, and recover genuinely inactive ownership after 45 minutes.
---

# Hermes coordination

Use the existing authorized private Slack conversation with Hermes. This skill
does not grant communication, repository, publication, merge, credential, or
machine access beyond the current user's authorization.

## Slack-only transport

- Resolve the recipient through the connected Slack directory and existing
  conversation history. Keep recipient IDs in machine-local configuration or
  the task checkpoint, never in this portable skill.
- Use a supported connected Slack send/read capability. Keep follow-ups in the
  verified task thread and retain its permalink.
- Do not invoke `hermes chat`, local HTTP gateways/proxies, SSH, terminal input,
  or another messaging platform as a fallback for contacting Hermes.
- If Slack is unavailable, denied, or its destination is ambiguous, report the
  exact blocker. Preserve the unsent request; do not bypass the restriction or
  create credentials, a gateway, or a new recipient.
- Before retrying an uncertain send, read the intended thread to determine
  whether it arrived. Never duplicate an already delivered or queued request.

## Request, acknowledgment, execution

Send a bounded handoff: task/goal, existing owner, repository and branch/head,
acceptance checks, evidence already available, permitted next step, holds, and
a unique task marker. Ask Hermes to review, monitor, and report a concrete next
action. Include takeover permission only when the user has authorized it.

Track these states separately:

1. SENT: the transport returned a message reference.
2. ACKNOWLEDGED: a fresh Hermes-authored reply names the task and disposition.
3. EXECUTING: a current command/run or source artifact substantiates work.
4. COMPLETE: the acceptance checks are verified at the evidenced head.
5. BLOCKED: the exact missing capability, approval, or artifact is recorded.

A reaction, echoed input, queue entry, process age, spinner, assignment, or
status claim alone is not an acknowledgment or proof of execution. Verify
results against source: head SHA, true test exit, raw log, capture, deployment
revision, or applicable operation receipt. Request a partial result promptly
rather than waiting for every lane to finish.

## Monitor and review

When the user asks to "cc Hermes" or have Hermes review a task, include
monitoring and authorized Dot nudges for that same task in the handoff. Do not
require a second request just to follow up. This does not authorize monitoring
unrelated work, new schedules, a second writer, or broader communication.
Explicit review-only/no-follow-up instructions override this default.

For work the user asked Hermes to oversee, agree on the monitored tasks and
reuse their existing checkpoints. Record owner, current operation, last
meaningful progress time with timezone, artifact, next action, and resumption
trigger. Check original sources and later cancellations before acting.

Meaningful progress changes the acceptance evidence: a relevant commit,
advancing test/build output, a captured result, or a verified unblock.
A repeated status message, poll, acknowledgment, or changed timestamp does not
reset the inactivity clock. A long-running operation with fresh advancing
output remains active even without a commit.

Use the current runtime's supported waits or existing authorized monitoring.
Do not install daemons, create competing monitors, or change schedules merely
by loading this skill. If the runtime cannot maintain checks, report the last
observation and arrange an authorized existing owner; do not promise coverage.

Hermes reviews exact-head evidence and reports findings to the current writer.
Review ownership does not itself transfer the writer role or grant merges.

## 45-minute inactivity recovery

At 45 minutes without meaningful progress, investigate rather than
automatically stealing the branch:

1. Re-read the original task, latest owner messages, PR/worktree changes, and
   actual run status. Missing or failed reads mean UNVERIFIED, not inactive.
2. Nudge the current owner with the last artifact and ask for its present
   action, blocker, or explicit handoff. Inspect delivery and response before
   retrying. Preserve peer drafts and any uncertain in-flight operation.
3. If a process is advancing, retain its owner. If approval, quota, access,
   device availability, or another real dependency blocks it, keep that lane
   BLOCKED and continue independent authorized work.
4. Take over only when the user authorized continuation/takeover, the task is
   still wanted, and source evidence establishes no competing live writer.
   Require an explicit handoff or independently verified ended/stopped owner;
   silence or an expired timer alone is insufficient.
5. Record the ownership change in the existing task/PR thread, preserving the
   branch, dirty files, evidence and all holds. Re-pin the head immediately
   before editing and stop if another writer has advanced it.
6. Resume the smallest authorized reversible step. Report the actual command
   and result. Never re-run a cancelled action, publish, merge, alter access,
   restart a service, or incur new provider usage merely to clear inactivity.

For a newly dispatched task with no progress yet, start the clock at its first
verified dispatch timestamp. Missing send confirmation leaves the task
UNVERIFIED rather than inventing a start time. The 45-minute threshold is then
measured from the last verified progress, not from the latest reminder. A resumed task resets it only after new meaningful
progress. Keep one writer and one monitoring record per task.

## Dot nudges

Hermes may nudge Dot when authorized for the same engineering task. Read the
installed [Dot skill](../dot/SKILL.md) and use its existing verified account and
conversation. Set `DOT_ROTATE_ON_LIMIT=0` on every Dot transport invocation
and pass the verified account/chat explicitly; the transport otherwise rotates
by default. A quota limit remains a blocker for that same target. Preserve its
peer-draft and submission rules; confirm the exact
message was submitted, then obtain an attributable Dot response. A staged
composer or queued send is not delivery or acknowledgment.

Include the task marker, last progress artifact/time, current owner, blocker
and requested next action. Do not rotate accounts, bypass a denied route, or
share credentials. Keep this Hermes monitor's 45-minute evidence rule rather
than restarting its clock because a nudge was sent. No new recurring sender
is authorized by this section.

## Canonical installation and Linux sync

This repository copy is the source of truth. Do not maintain divergent local
Hermes instructions. After review and applicable approval, inspect the current
installer's scope before using it: a whole-catalog or `--merge` overwrite is not
a narrow Hermes install. Read the installed
[Linux workflow](../linux-remote/SKILL.md) for a requested Linux sync.

For this scoped change, install only the reviewed Hermes skill and its command
pointer using an existing supported selective installer. If none exists, compare
the exact destination files and use a permitted file-copy operation limited to
those approved files, retaining recoverable originals. Do not overwrite Dot,
Linux, or other installed packages to deploy Hermes. Divergent target content
requires reconciliation first. If the runtime cannot perform that scoped copy,
report installation blocked and leave the canonical PR ready for its authorized
installer; do not silently broaden the install.

Use only a connection permitted by the active runtime. An SSH example in a
skill does not override a requirement to use a registered remote executor.
If the Linux environment is disconnected or unauthorized, keep sync pending
with the exact blocker; do not use a different route to evade it.

Compare source and installed hashes on each host, preserve unrelated local
changes, and report canonical SHA, installed paths, validation exits and sync
result. Never sync credentials, browser profiles, account IDs, or secrets.
Installation alone does not establish Slack access or a running monitor.
