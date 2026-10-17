# Coordinating AI coding agents without losing the thread

## TL;DR

- Keep the conversation, decisions, and final results with **ChatGPT dot**.
- Use **Beads as the shared task and knowledge-coordination record**: owners, state, dependencies, decisions, and evidence links.
- Give each coding task **one driver and one writer**. Use Hermes for explicitly assigned secondary coordination and existing cmux sessions for coding.
- Run independent tasks and read-only reviews in parallel. Keep overlapping edits under one owner.
- Close the loop with evidence tied to the exact version: code, tests, review, and the requested outcome. Preserve approval gates and holds.

Adding another coding agent creates a coordination problem: who owns the next action, which version is under review, and what counts as finished? Answer those questions before another terminal starts working. This workflow divides the responsibilities across dot, Hermes, Beads, and coding agents running in cmux terminal workspaces.

## The workflow at a glance

[![The user exchanges goals, decisions, results, and blockers with dot. dot coordinates directly or delegates a task to Hermes. Independent cmux coding sessions and read-only review run in parallel, each coding task with one driver and one writer. Beads is the shared task and knowledge-coordination record. dot, Hermes, and coding agents read and update it; exact-version evidence returns to dot. A separate coordinator sends reminders, and merge or deployment remains gated by authorization, current checks, and holds.](assets/dot-hermes-cmux-workflow.svg)](assets/dot-hermes-cmux-workflow.svg)

[Open the diagram at full size](assets/dot-hermes-cmux-workflow.svg).

The two coding lanes illustrate independent tasks, not two agents editing the same change. Hermes is optional for a given task; dot can coordinate a coding worker directly. The diagram describes operating responsibilities, not a claim that software enforces them or that these sessions are currently running.

## Keep one place for the conversation

Use dot as the primary place to state the goal, make decisions, and receive the result. Research, planning, writing, and ordinary questions can stay there. A conversation only needs a coding handoff when it requires repository edits or terminal execution.

Hermes can help discover and steer terminal sessions, check their health, or drive a bounded task. Be explicit about its role: “drive this task” assigns responsibility; “copied for awareness” does not.

A separate dot coordinator can remind dot to check unfinished work. That reminder does not make the coordinator a writer, a reviewer, or an approver. Keeping those roles separate makes it easier to tell who should act next.

## Make Beads the shared record

[Beads](https://github.com/jleechanorg/jleechan-skills/blob/29fab732bd0b72ab27f446083fbd786d73767e4a/.claude/skills/beads-issue-tracking/SKILL.md) is the primary task and knowledge-coordination record in this setup. dot, Hermes, and coding agents read and update the same task: who owns it, its state, dependencies, decisions, and evidence links. Chat carries the discussion; Beads preserves the checkpoint another session needs to continue.

Link specifications, design notes, PRs, and test evidence from the Bead. Keep large documents and raw logs in their appropriate repositories or artifact stores. The task record should make the relevant knowledge discoverable without becoming a transcript dump.

## Give every task one driver and one writer

The driver owns the next action and follows the task to its requested endpoint. The writer owns edits on a particular branch or overlapping set of files. They can be the same agent, but the responsibilities should be named.

Before dispatching work, check the existing Bead, PR, worktree, and terminal session. Keep a healthy writer in place. If ownership needs to change, pass along the current version, unfinished work, blockers, and next step, then have the incoming driver acknowledge the transfer.

This avoids a costly coordination failure: two agents confidently acting on different versions of the same task.

## Parallelize work that can stay independent

Separate worktrees help isolate changes, but they do not resolve overlapping ownership by themselves. Two writers can work in parallel when their changes do not overlap and someone owns integration. Read-only review can also proceed alongside implementation, with its findings tied to a named commit.

Give each worker a self-contained brief linked to its Bead: outcome, owner, permitted scope, starting state, required evidence, and stopping condition. This takes more care at dispatch time and reduces conflicting instructions later.

## Ask for evidence you can inspect

“Done” can mean several different things: a source change exists, a local test passed, CI passed, a reviewer approved, or the running application now behaves correctly. Those are separate observations.

Ask for the exact commit or build, the check that ran, its environment, and the result. If the code changes after review, establish which checks and findings still apply. Also inspect deleted tests, skipped cases, and weakened assertions.

For example, a worker might fix a save failure and return passing local tests. That supports the candidate change. If the request was to repair the running application, completion also needs evidence from the intended deployed version. If the request was only to prepare a draft PR, stop there and preserve the merge hold.

## Keep checking until the requested endpoint is verified

Polling is useful when it leads to a decision or an authorized next step. Look for a new commit, a finished check, a review finding, a blocker, or a lost session. Keep independent work moving while an external result is pending.

Avoid repeatedly sending the same instruction to a worker that is making progress. A successful terminal send proves only that input was accepted; it does not establish that the task started or finished. Verify the response and follow the evidence through to the outcome.

Tell the human about results, decisions, material changes, and blockers. Unchanged status checks rarely need another message.

## Keep consequential decisions explicit

“Ready to merge” describes a state. It does not grant permission to merge. Name one integration owner, preserve the user's holds, and require the applicable checks and reviews on the current head before an authorized merge or deployment.

When a route fails, preserve the checkpoint and use an already authorized alternative where available. Missing quota, access, or a required decision is a blocker to report, not permission to expand scope.

## Start with one existing task

Choose one unfinished task. Name its driver and writer, define the observable result, and agree on the proof that will establish it. Update the existing Bead as ownership, state, and evidence change.

The [agent playbook](chatgpt-dot-hermes-cmux-agent-playbook.md) contains the detailed handoff template, terminal-steering checks, polling procedure, evidence definitions, and implementation references. This article and the playbook describe a proposed operating workflow dated 2026-10-17; source configuration and runtime behavior still need separate verification.
