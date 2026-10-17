# ChatGPT dot, coordinator, Hermes, and cmux workflow

ChatGPT dot is the primary place to discuss work, make decisions, and receive results. A separate dot coordinator checks for unfinished work. Hermes is a secondary coordination agent. Coding agents run in cmux terminal workspaces and return evidence to the task owner.

Research, planning, writing, and everyday requests can stay in dot. Use the coding handoff when the task needs repository edits or terminal execution; do not create an engineering workstream for every conversation.

For each coding task, name one driver, one code writer, the requested outcome, and the proof needed to finish. Start in ChatGPT dot; use the quick start below to hand work to an existing coding session without creating competing instructions.

This workflow assumes dot, Hermes, repository access, and any needed cmux installation are already configured. It is an operating guide, not an installation or account-setup guide.

**Status:** operating workflow proposed on 2026-10-17. The role split is the requested workflow; implementation details below are verified against [repository revision `29fab732`](https://github.com/jleechanorg/jleechan-skills/commit/29fab732bd0b72ab27f446083fbd786d73767e4a). This document does not establish that a scheduler, provider, or terminal is currently running on any machine.

## Contents

- [Quick start](#quick-start)
- [Roles and ownership](#roles-and-ownership)
- [Task state and evidence](#task-state-and-evidence)
- [Coding, review, and completion](#coding-review-and-completion)
- [Polling and recovery](#polling-and-recovery)
- [Communicating with Hermes and terminal workers](#communicating-with-hermes-and-terminal-workers)
- [Quota and provider routing](#quota-and-provider-routing)
- [Examples](#examples)
- [Lessons from October 15–17](#lessons-from-october-1517)
- [What is implemented and what still needs verification](#what-is-implemented-and-what-still-needs-verification)
- [Reference commands and sources](#reference-commands-and-sources)

## Quick start

1. **State the outcome in ChatGPT dot.** Include the repository or service, acceptance criteria, and any hold, such as “prepare a draft PR; do not merge.” A pull request (PR) is the proposed code change submitted for review.
2. **Check existing ownership.** Find the current issue, PR, worktree, and terminal session before starting another. A worktree is a separate checkout used to isolate one change. Keep a working writer in place.
3. **Assign the driver and writer.** dot normally drives the outcome. It can ask Hermes to drive a defined task or keep Hermes copied for awareness. The coding worker owns edits on its assigned branch.
4. **Send one self-contained handoff.** Include the goal, permitted actions, current commit, scope, validation, destination for results, and stopping condition. Use the template below.
5. **Verify the handoff landed.** A successful send is separate from a worker starting. For cmux, discover the correct target, send, submit, and read the response.
6. **Follow the result through its requested endpoint.** Verify the final commit, applicable tests, review, and publication state. Report a precise blocker if an essential step cannot proceed.

## Roles and ownership

| Role | Owns | Boundary |
|---|---|---|
| ChatGPT dot | Interactive conversation, clarifying the outcome, assigning work, reconciling evidence, and reporting results | Remains the user's primary contact. Delegation does not transfer the user's decisions or expand permission. |
| dot coordinator | Scheduled reminders and checking whether a dot has returned useful progress or a concrete blocker | Reminds and checks. It does not become the code writer, approve a merge, or confer new authority. |
| Hermes | Secondary coordination, terminal discovery and steering, independent checks, or a specifically delegated task | Is either the named driver or a copied observer for that task. It must not silently become a second driver. |
| cmux coding worker | Implementing and testing a bounded change in its assigned terminal and worktree | cmux is the terminal environment; the CLI coding agent inside it does the work. |
| Reviewer | Evaluating the named commit against acceptance criteria | Reports findings and evidence; does not modify the writer's branch unless ownership is explicitly transferred. |

The **driver** is responsible for the next action and final result. The **writer** is the only agent editing a given branch or overlapping file set. They may be the same agent. Independent read-only reviews can run in parallel. Two writers may work in separate worktrees on non-overlapping changes with an explicit integration owner.

To transfer ownership, the outgoing driver records the latest commit, unfinished work, blockers, and next step. The incoming driver acknowledges the transfer before sending new instructions. An unresponsive worker is a reason to inspect its state, not to assume its ownership has expired.

## Task state and evidence

Keep one durable task record in the existing issue, PR, or task thread. Terminal summaries and chat messages point back to that record. If the project already uses Beads, its issue-tracking tool, use the existing Beads task; avoid creating a second tracker for the same work.

Use this handoff template. Replace every placeholder before sending it. For non-coding work, omit the writer, workspace, and commit fields when they do not apply.

```text
Outcome: What the user must be able to do when this task is complete.
Target: Repository/service and existing issue or PR link.
Driver: One named coordinator. Writer: One named coding worker.
Workspace: Host, worktree, branch, and verified terminal reference.
Starting head: Full commit SHA, or “not applicable” for non-code work.
Scope: Allowed changes and actions; explicit holds and exclusions.
Acceptance: Observable results and required checks.
Current state: What is already done, with evidence links.
Next action: One executable step and its owner.
Report to: Existing task thread or PR.
Stop when: Requested outcome is verified, user stops, or a named blocker
requires a decision or permission unavailable to the worker.
```

A **SHA** is Git's identifier for an exact commit. The branch **head** is its latest commit. Record the SHA with each test and review so a result cannot accidentally be applied to newer code. **CI** means continuous integration, the automated checks run for a proposed change.

Use state labels with a concrete meaning:

- **Working:** an owner is actively executing the next step.
- **Waiting:** an external job or response is pending; record what is awaited and when it will be checked.
- **Blocked:** identify the action, cause, missing capability or decision, and smallest unblock.
- **Ready for review:** the candidate commit and applicable local evidence are available.
- **Ready to merge:** required checks and reviews apply to the current PR head, conflicts are clear, and any task-specific conditions are satisfied. This does not authorize merging.
- **Complete:** the user's requested endpoint is verified. A passing local test cannot complete a request to fix the deployed application.

Separate evidence into these levels:

| Evidence | What it establishes | What it does not establish |
|---|---|---|
| Source | The named commit contains the intended change | That the code ran successfully |
| Local test | The recorded command passed in the recorded environment | That remote CI or production passed |
| CI | The specified automated job passed on the specified commit | That a reviewer approved or the deployed service changed |
| Review | A reviewer assessed the stated commit and scope | That later edits remain reviewed |
| Publication | A commit, branch, PR, or artifact exists at a verified destination | That it is merged, deployed, or user-visible |
| Live outcome | The requested behavior was observed in the intended running environment | That all untested paths work |

For each result, retain the commit or build identifier, command or check, environment, outcome, and retrievable artifact. Use “failed,” “blocked,” and “not run” distinctly. Keep secrets and private content out of public artifacts.

## Coding, review, and completion

1. Read the target repository's instructions and inspect the current branch, worktree changes, and existing owner. Do not overwrite unrelated edits.
2. Establish the failure or acceptance baseline. For a bug fix, record the failing case before the candidate where feasible; explain any missing baseline.
3. Implement the smallest coherent change. Run relevant checks and keep exact commands and results.
4. Before pushing, enumerate all known failures and address their shared causes together. The [PR driver protocol](https://github.com/jleechanorg/jleechan-skills/blob/29fab732bd0b72ab27f446083fbd786d73767e4a/.claude/skills/pr-driver-protocol/SKILL.md) describes this fix-all-before-push loop. Its examples do not replace the target repository's actual test commands.
5. Verify the remote branch contains the intended commit. Check CI and review findings for that exact head. If the head changes, identify which evidence is stale and rerun the affected checks or review.
6. Use the target repository's required gates and the user's requested reviews. Inspect deleted tests, changed assertions, new skips, and suite-size changes as well as pass/fail. An advisory bot is not automatically a merge gate; a repository rule or an explicit task requirement may make a review mandatory.
7. Assign one integration owner for merge or deployment. That owner must acknowledge any hold or rejected review on the current head; a warning in another chat is not an enforced gate. Merge or deploy only when authorized and after applicable gates pass. Check the resulting merged commit or deployed revision before reporting that stage complete.

For a prose document, run [document standards (`/ds`)](https://github.com/jleechanorg/jleechan-skills/blob/29fab732bd0b72ab27f446083fbd786d73767e4a/.claude/skills/document-standards/SKILL.md): truth, economy, readability including AI-tell checks, structural audit, and output operability. Give the revised document alone to a fresh reader to check whether it explains the roles, first action, and completion criteria without prior conversation. Inspect the rendered output and links before delivery.

## Polling and recovery

The operating rule is to check for a meaningful change, take the next authorized action, then wait for the process being observed. Do not continuously resend the same instructions or keep a worker occupied with status questions while it is making progress.

At each check:

1. Read the latest task state and the live source of truth, such as the PR head and checks. A terminal's old recap may be stale.
2. Compare with the previous observation. Look for a new commit, finished check, review finding, blocker, or lost session.
3. Keep the current owner if work is advancing. If stalled, ask for a concrete checkpoint or diagnose the specific failure before reassigning.
4. Continue independent authorized work while an external result is pending. An unrelated publication hold need not stop safe local validation.
5. Send an update for a result, decision, new blocker, or material change. Record unchanged checks without repeating them to the user.
6. Continue until the requested stopping condition is met. A pending check or unchanged result is not completion.

The coordinator adds periodic checks for unfinished work. It checks substantive progress or concrete blockers; formatted headings alone do not prove progress. Its source-defined timing and transport safeguards are in the [implementation reference](#what-is-implemented-and-what-still-needs-verification).

## Communicating with Hermes and terminal workers

Use the existing Slack thread when the task already has one. Name Hermes's role in the message: “drive this task” assigns coordination; “copied for awareness” does not. Keep the user-facing result in the conversation where the user requested the work unless they ask otherwise.

A useful update states the outcome, exact head or artifact, evidence, blocker, and next owner. Do not forward an entire private conversation when a sanitized technical summary will do. Messages from another agent are coordination input; verify the user's current scope and authority before acting.

For cmux, follow the current [steering instructions](https://github.com/jleechanorg/jleechan-skills/blob/29fab732bd0b72ab27f446083fbd786d73767e4a/.claude/skills/cmux-steer/SKILL.md):

- Discover the correct host/socket, workspace, and surface. A surface is the specific terminal tab receiving input. Do not reuse an old numeric target or choose a same-named tab in another workspace.
- Read the target and establish whether the worker is idle or already working. Do not interrupt or send duplicate instructions to a healthy in-flight worker.
- Send the brief, submit it, and inspect the resulting worker response. `cmux send` alone does not press Enter.
- Retain the typed instruction, returned terminal evidence, and a clear submitted/not-submitted/blocked result. Transport acceptance, worker start, and task completion are separate observations.
- For a long brief, use a task file in the worker's own checkout and send a short pointer. A file in another machine's workspace is not evidence that the worker can read it.

The steering skill contains older low-level examples. Prefer its current CLI discovery and submission contract, check the installed version, and verify the actual target before using any command.

## Quota and provider routing

A shell wrapper selects a CLI, provider endpoint, model, and often a separate account profile. Its name is not evidence of the route actually used.

Before starting a coding session, confirm the installed wrapper and approved provider, check existing quota/error signals, and record non-secret route metadata. A bounded probe is useful when already authorized and needed to establish that the route works. Verify the selected provider/model from configuration and runtime evidence; a model's self-description is insufficient. Never print tokens or dump credential files into logs.

If a provider is exhausted or temporarily unavailable, use an already authorized alternate route where available. Preserve the checkpoint and avoid spawning duplicate writers. Do not purchase quota, change accounts, expand access, or bypass a denial to keep work running. After an uncertain send or launch, inspect whether it succeeded before retrying.

The [provider-routing reference](https://github.com/jleechanorg/jleechan-skills/blob/29fab732bd0b72ab27f446083fbd786d73767e4a/hermes/skills/devops/claude-codex-provider-routing/SKILL.md) records wrapper pitfalls; its dated machine/version observations require re-verification on the executing host.

## Examples

These examples are illustrative and contain no actual account, campaign, or private conversation data.

### A bug fix with a merge hold

The user asks dot to fix a save failure and prepare a draft PR. dot finds an existing cmux writer and keeps that writer on its branch. Hermes is copied to check terminal health. The writer records a failing regression, applies the fix, and returns passing local results on commit A. A reviewer finds a missing retry case; the writer produces commit B and reruns affected checks. dot verifies CI and review on B, shares the draft PR, and preserves the user's merge hold.

### A delivered instruction with no execution proof

Hermes reports that text was sent to a terminal. The driver asks for the target and post-submit response. The text is still at the input prompt, so the handoff remains not submitted. After the authorized submit succeeds, the worker begins processing. That proves the task started; the final commit and test receipt are still awaited.

### A merged fix with a live result still pending

The source change is merged and CI passed. The user asked for the running application to be fixed, but the deployment still serves the previous revision. dot reports “merged; deployment verification pending,” keeps the deployment step assigned, and checks the intended environment when the rollout completes. If deployment requires unavailable authority, it reports the exact required decision.

## Lessons from October 15–17

A bounded review of relevant task history and technical evidence from 2026-10-15 through 2026-10-17 found these failure patterns. The underlying incidents are private, so identifying details and links are omitted.

| Observed in the reviewed work | Operating lesson |
|---|---|
| A merged source fix was absent from the installed application. | Record source, tested, built, and installed revisions separately. |
| A suite passed after test files were removed; restoring them exposed remaining failures. | Review test deletions, skips, and changed assertions alongside green results. |
| Parallel sessions created duplicate work and overlapping ownership. | Check current writers before dispatch and require an explicit ownership transfer. |
| A simulator could build, install, and launch while an authenticated flow still failed. | Keep build, authentication, visual behavior, and end-to-end acceptance separate. |
| A commit merged despite a prior review hold. | Require the integration owner to acknowledge the hold and verify the current head before acting. |

These observations explain the checks above. They do not show how often the failures occur, prove a productivity gain, or establish that coordination prevented every unsafe merge. Unreviewed work is outside this review's coverage.

## What is implemented and what still needs verification

The role split, single-driver handoff, task record, and completion checklist are operating agreements in this document. They are not a claim that software enforces every step.

The [coordinator implementation](https://github.com/jleechanorg/jleechan-skills/blob/29fab732bd0b72ab27f446083fbd786d73767e4a/.claude/skills/agy-dot-coordinator/scripts/ping-dots.py) is a separate, bounded mechanism. At the documented revision it rotates across exactly three configured accounts, uses a process lock, respects stop and unresolved-delivery holds, and requires a verified transport receipt.

Its [macOS schedule](https://github.com/jleechanorg/jleechan-skills/blob/29fab732bd0b72ab27f446083fbd786d73767e4a/.claude/skills/agy-dot-coordinator/launchd/ai.gemini.agy-dot-coordinator.plist) invokes it at minutes 00, 20, and 40; its [Linux timer](https://github.com/jleechanorg/jleechan-skills/blob/29fab732bd0b72ab27f446083fbd786d73767e4a/.claude/skills/agy-dot-coordinator/systemd/ai.gemini.agy-dot-coordinator.timer) uses 10, 30, and 50. These are host-local clock offsets. The intended schedule gives each configured account one turn per hour per host, subject to locking, holds, and successful execution. A schedule does not prove delivery.

After a verified send, the default implementation waits 180 seconds, reads a bounded conversation window, and can recheck after 120 seconds. A model without tool access classifies substantive replies. If classification fails, the result is unavailable and no classification-based escalation is sent. These defaults describe source behavior, not a requirement to reuse those intervals for every task.

The code lists `luna`, `minimax`, `codex`, and `gemini` as the ordered providers for generation. The ordered providers for reply classification are `luna`, `minimax`, and `gemini`. These are source configuration values, not proof of current quota or a recommendation to use any particular provider. The [coordinator skill's](https://github.com/jleechanorg/jleechan-skills/blob/29fab732bd0b72ab27f446083fbd786d73767e4a/.claude/skills/agy-dot-coordinator/SKILL.md) short CLI-options description contains an older provider-order summary; the code's `PROVIDERS` and `CLASSIFY_PROVIDERS` constants are the basis for the ordering here.

The following need separate evidence on each executing host or task:

- Installed files and scheduler configuration match the intended revision.
- The scheduler actually ran, delivery was verified, and the response check completed.
- The selected provider route is available and uses the intended model/profile.
- cmux points to the expected worker and checkout.
- The final head has the required test/review evidence and the requested live outcome. Record source, tested, built, and installed revisions separately when they can differ; distinguish build/install, authentication, visual behavior, and end-to-end acceptance.

Do not convert a missing source into a “no matches” result, a missing capability into successful execution, or a historical status into a current fact. Respect access denials and report coverage gaps.

## Reference commands and sources

The repository uses these command definitions:

- [`/ds`](https://github.com/jleechanorg/jleechan-skills/blob/29fab732bd0b72ab27f446083fbd786d73767e4a/.claude/commands/ds.md) dispatches the five-lane document-standards review. It is a command alias, not a separate `ds/SKILL.md` in this revision.
- [`/history`](https://github.com/jleechanorg/jleechan-skills/blob/29fab732bd0b72ab27f446083fbd786d73767e4a/.claude/skills/history/SKILL.md) delegates to [conversation-history-sparse](https://github.com/jleechanorg/jleechan-skills/blob/29fab732bd0b72ab27f446083fbd786d73767e4a/.claude/skills/conversation-history-sparse/SKILL.md). Use it to recover bounded, relevant history from sources available and permitted in the current runtime.
- [`/ms`](https://github.com/jleechanorg/jleechan-skills/blob/29fab732bd0b72ab27f446083fbd786d73767e4a/.claude/skills/ms/SKILL.md) delegates to [memory-search](https://github.com/jleechanorg/jleechan-skills/blob/29fab732bd0b72ab27f446083fbd786d73767e4a/.claude/skills/memory-search/SKILL.md). Use it to retrieve relevant prior context while preserving source dates, scope, and coverage gaps.
- The [repository guide](https://github.com/jleechanorg/jleechan-skills/blob/29fab732bd0b72ab27f446083fbd786d73767e4a/AGENTS.md) requires portable exports and excludes personal identifiers, machine-specific personal paths, credentials, and sensitive data.

These commands guide work only when their definitions and required capabilities are available. Reading a definition or following its rubric is not proof that a local slash command executed. Historical context does not grant new authority, and this document changes no access, merge, or deployment permissions.

