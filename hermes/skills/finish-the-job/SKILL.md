---
name: finish-the-job
version: 1.5.0
description: "End-to-end finish protocol for any Slack thread, CLI invocation, or cron task where the user has handed off a goal. Routes to /fs (spec gen) → /f (Dark Factory loop) → drives to a verifiable conclusion (green PR with non-unit-test evidence, finished code change, or dry-run to local machine state). Never stops halfway. Loads automatically when the SOUL.md `finish-the-job` commit fires. Phase 4 enforces a Slack-specific reply shape — a green PR is not enough if the reply is so verbose the user has to scroll past it."
tags: ["autonomy", "finish", "dark-factory", "dispatch", "pr", "evidence", "anti-stop-halfway", "reconfirm", "pushback"]
category: workflow
triggers:
  - finish the job
  - finish it
  - finish this
  - finish that
  - drive to conclusion
  - see it through
  - take it all the way
  - don't stop halfway
  - why did you stop
  - hands off mode
  - hands-off mode
  - fullsend
  - full send
  - take it from here
  - i started but didn't finish
  - work started but didn't finish
  - stalled thread
  - threads that stalled
  - threads i started but didn't finish
  - skillify hermes to be hands off
  - make hermes hands off
  - /finish
  - /auto
  - auto
  - automate this
  - do it autonomously
  - your call
  - handle it
  - ship it
  - merge it
  - is this finished
  - is x finished
  - did you finish
  - where is the report
  - reconstruct from prior session
  - i thought it was
  - there was supposed to be
  - what happened to
  - reconfirm
  - recheck
changelog:
  - '1.6.0 (2026-07-07): Added pitfall "Candidate-list classification trap" + new pre-flight gate "live file-path check before claiming non-prod sweep targets". Verified 2026-07-07 with 32-PR /roadmap + /green non-prod sweep on $GITHUB_REPOSITORY: keyword filter (ci:/docs:/test: etc.) initially classified 32 PRs as non-prod candidates, but `gh pr view --json files` re-classification revealed 17 had ≥1 file under `$PROJECT_ROOT/` or `testing_*/` (Dockerfile changes, bq-logging, LLM provider, frontend JS). The script `green_merge_nonprod.py` enforces this classification via `PROD_PATH_PREFIXES = ($PROJECT_ROOT/, testing_mcp/, testing_ui/)` and refuses to auto-merge prod PRs by design. Lesson: ANY batch /green sweep MUST re-run the script/file-path gate against LIVE `gh pr view --json files` data, NOT trust keyword heuristics from PR titles. Companion reference: finish-the-job/references/nonprod-sweep-candidate-filtering-2026-07-07.md.'
  - '1.5.0 (2026-07-07): Added end-state row "PR open, as-green-as-pool-allows" to the Contract table. Verified 2026-07-07 with PR #8070 on $GITHUB_REPOSITORY: 6 of 7 Skeptic gates PASS, only Gate 8 (Smoke) failed due to self-hosted runner pool exhaustion (verified identical failures across 6+ other PRs in same repo). The MERGE APPROVED against such a state is informed authorization to merge despite documented infra failures, not a false-positive everything-is-green promise. Companion reference: drive-pr-to-green/references/smoke-gate-pool-exhaustion-2026-07-07.md. Lesson: when 6 of 7 gates pass and the 1 failure is the same-name-verified pool-exhaustion pattern, do NOT keep retrying /smoke or workflow_dispatch triggers - both fail the same way. Document the blocker, surface MERGE APPROVED, schedule a cron to re-check at the next 30-min window per followup-promise-requires-cron.'
  - '1.4.0 (2026-07-06): Added pitfall "Green-claim brief from memory, not live state" + new section "Green-claim brief: mandatory live-state verification". The recurring-alert investigation pattern (5+ sessions on the same BQ is_test IS NULL bug, all stopping at the same wall) trains the agent to write green-claim briefs from session_search memory instead of live state. Verified bug case: PR #8070 brief claimed 9 failing gates dismissable as infra, CodeRabbit APPROVED, worktree clean — but live state had 14 failing gates (one violating same-name rule), CodeRabbit with a contradictory CHANGES_REQUESTED on file, and 330 stale staged files polluting the worktree. Dispatched AO worker caught the brief/live-state disagreement and refused to post fake-green, saving the user from a MERGE APPROVED → broken-merge disaster. Lesson: before composing any green-claim brief for a recurring alert with ≥2 prior failed attempts, run the 5-check preflight (worktree scope, unpushed commits, current reviewDecision, failing gate names+URLs, unresolved review threads) against LIVE state and patch the brief to match. Prior session memories are evidence of recurring blockers, not evidence of current green state.'
  - 1.3.0 (2026-07-06): Added "Slack reply format" subsection + new pitfall "verbose multi-section status report overwhelms the reader". The user pushed back with "kind of confusing" after a Phase 4 reply used 5 colored sections (Healthy/Risky/Blocked/Next actions/🧠 Memories used), a wide table, and 3 markdown headers. The reply needs the same rigor as the work itself — if the proof is hidden inside a 40-line report, the user can't find it. New pitfall — a green PR is not enough if the reply is so verbose the user has to scroll past it. Added a Slack-specific reply shape (✅ Done / Proof / Judgment calls / Memories) and an explicit warning that `/advice` synthesis tables, CodeRabbit-style severity matrices, and 5-section status reports are NOT the right format for Slack — they're for terminal log files. Verified 2026-07-06 with ez-gh-actions PR #9 / PR #10 — three iterations of "Status" replies before the user accepted the format.
  - 1.2.0 (2026-07-06): Added "Reconfirm & pushback" subsection + new pitfall "anchored on code, ignored memory terminology". When the user pushes back with "I thought it was X" / "there was supposed to be Y" / "what happened", fan out across all 9 memory stores BEFORE re-anchoring on source code or rejecting the user's framing. Verified 2026-07-06 with ez-gh-actions PR #9 — the user said "there was supposed to be vm inside vm" and the correct answer was YES (container-in-VM-in-host 3-layer stack), per the wiki + roadmap + project memory all using the same terminology. The first commit answered "no" by rejecting the wrong interpretation (nested VM backends) without affirming the right one. Code is truth for behavior; the user-facing name of a strategy lives in their wiki/roadmap/project memory. Cross-referenced in `references/reconfirm-pushback-memory-fanout-2026-07-06.md` with the full 9-store fan-out recipe and the dispatch-task / session_search budget trade-off.
  - 1.1.0 (2026-06-28): Added anti-pattern pitfall for "Is X finished?" → redoing X from scratch. The right pattern is `session_search` + `hermes sessions export` to reconstruct the prior session's final assistant text in one turn instead of re-running 30-day audits. Verified 2026-06-28 with the Gmail daily reports audit reconstruction (10K tokens vs 1.55M, same 3.6KB report). Added `references/reconstruct-from-prior-session-2026-06-28.md` with the 3-step recipe, decision matrix (when reconstruct vs when redo), cost comparison, and pitfalls (session_search returns summary not text; export is single-line JSONL; `session_reset` end_reason ≠ unfinished work).
  - 1.0.0 (2026-06-19): Initial skill — end-state evidence stack, phases 0-4, anti-patterns.
related_skills:
  - dark-factory
  - drive-pr-to-green
  - always-pr-never-local-edit
  - ao-babysit
  - dropped-messages
  - skillify
  - hermes-deploy-pipeline
  - memory-search
---

# finish-the-job

**The hands-off finish protocol.** When a user hands you a goal — in Slack, in a CLI turn, or via a cron task that wasn't finished — this skill is the *single* pipeline that drives it to a verifiable conclusion. It composes existing primitives (`/fs`, `/f`, `workflow/drive-pr-to-green`, `workflow/always-pr-never-local-edit`) so the assistant stops halfway **never**.

## Why this skill exists

Three drift patterns were observed in the user's last week of Slack threads (2026-06-12 to 2026-06-19, C0AH3RY3DK6 / C09GRLXF9GR):

1. **"Ack + design prose + silence"** — agent acknowledges, writes 200 lines of design options, asks one more clarifying question, never executes. The dropped-thread-followup cron fires 4h later.
2. **"Started + fork + multi-option question"** — agent reads files, makes a local commit, hits a judgment call, posts a 3-option menu. User doesn't reply (busy). Thread goes cold.
3. **"Investigation without end-state"** — agent reads 6 files, posts "Here's what I found: …" with no PR, no commit, no dry-run. The "I'm waiting for the right moment to ship" trap.

**The pattern in all three:** the agent stopped at a place that required *the user* to make a decision or supply a follow-up, instead of making the call itself and posting the result. The user's explicit rule (2026-06-19): *"I am ok with outcomes that aren't my goal as long as they are correct ie. Green PR, real evidence, like correct but misinterpret is fine but stopping halfway is not."*

## Contract

**When this skill fires, the work is not done until ONE of these end-states is provably true:**

| End-state | Proof artifact |
|---|---|
| **Green PR merged** | `gh pr view <N> --json state` = `MERGED` + Green Gate workflow log gate-by-gate PASS + non-unit-test evidence bundle URL |
| **PR open with green CI awaiting user merge** | `gh pr view <N> --json mergeStateStatus,reviewDecision` shows `MERGEABLE` + review clean; ONE-LINE message naming PR URL + the one gate the user must clear |
| **PR open, as-green-as-pool-allows** (added 2026-07-07) | Skeptic verdict shows 6 of 7 gates PASS with only Gate 8 (Smoke) failing due to documented global pool exhaustion (verified via same-name dismissal against 4+ other PRs in same repo). The agent's job: confirm Skeptic verdict is fresh, document the pool exhaustion as the blocker, surface `MERGE APPROVED` as the only user action, schedule a one-shot cron for re-check. Do NOT keep retrying `/smoke` or `workflow_dispatch` — they fail the same way. Verified recipe: `drive-pr-to-green/references/smoke-gate-pool-exhaustion-2026-07-07.md`. |
| **Local state change verified** | `git diff` + `git log --oneline -3` + the actual test run output captured in the final reply (not described — shown) |
| **Dry-run to local machine** | The exact commands the user would run, executed against a fresh worktree, output captured; the user can paste the same commands and get the same result |

**NOT acceptable end-states:**

- ❌ "Here's the design, want me to ship it?" — that's design-proposal-and-silence
- ❌ "Tests pass locally, PR is ready, want me to push?" — that's local-commit-and-ask
- ❌ "Investigation complete, here are the findings" without a commit, PR, or dry-run
- ❌ "I've started the worker, will update when done" — that's ack-and-walk-away
- ❌ Mid-stream question without first exhausting the LLM's own judgment (per the user's rule: "in the middle I want AI to use its best judgement")

## Reconfirm & pushback (added 2026-07-06)

**Trigger phrases:** user reply contains any of:
- "I thought it was X" / "isn't this X?" / "shouldn't this be X?"
- "there was supposed to be Y" / "what happened to Y" / "where is Y"
- "reconfirm" / "recheck" / "are you sure"
- "Run /history and /ms" / "search your memories" / "look it up"
- "why does X say no when the wiki says yes?" / contradictory evidence between sources

**The trap:** anchoring on source code or the current PR diff as the only source of truth. When the user pushes back with a "what happened to X" question, the agent's instinct is to re-read `DESIGN.md`, the source files, and the PR body — but the user is usually pointing at something they **remembered** from their own memory stores (wiki, roadmap, project memory, prior sessions). Code is truth for **behavior**; memory stores are truth for **what the strategy/feature is called** and **what was supposed to happen**.

**The recipe (verified 2026-07-06, ez-gh-actions PR #9 commit `055ff31`):**

1. **Acknowledge immediately** that the user is pointing at a real signal. Don't defend the prior answer yet.
2. **Fan out across all 9 memory stores in parallel** via `delegate_task` (Hermes) or `/ms <query>` (Claude Code/Codex). The 9 stores:
   - `~/roadmap` (project learnings, decisions)
   - `beads` (`br search <query>`)
   - `~/.claude/projects/*/memory/` (per-project session memory)
   - `~/.hermes/state.db` (messages + FTS5)
   - `~/.hermes/memory/briefing-*.md` + `mcp-mail-ack-log.md`
   - `~/.hermes/MEMORY.md` (hermes index)
   - `~/llm_wiki/` (the canonical knowledge wiki)
   - `~/.claude/projects/*/*.jsonl` (history)
   - Slack (via `mcp__slack__conversations_search_messages`)
3. **Include the original proposal / gist / RFC** if one exists — fetch it via `web_extract` to check whether the original wording contradicts the current implementation.
4. **Check open + closed PRs** for the same terminology: `gh pr list --repo OWNER/REPO --state all --limit 20 --json number,title,body,headRefName` and grep bodies for the term.
5. **Reconcile**: when the memory store uses term X to mean Y, and the source code uses term X to mean Z, both can be true — disambiguate explicitly in the answer (e.g. "VM-in-VM means container-in-VM-in-host 3-layer stack in wiki/roadmap; means nested VM backends if you read it as 'backend nesting' from the code; the deployed reality is the first").
6. **Ship a correction**: amend the prior PR with a follow-up commit + new PR body, link the memory evidence in the PR description, and reply to the user with the file:line citations.
7. **Post the corrected answer in the same turn** as the fan-out, per `finish-the-job` Phase 4 (no follow-up question).

**Budget trade-off:** the fan-out costs ~6–10 tool calls (parallel delegate_task). It is always cheaper than re-doing the work after the user pushes back a second time, and it surfaces evidence the source-code-only read would have missed.

See `references/reconfirm-pushback-memory-fanout-2026-07-06.md` for the full 9-store fan-out shell command, the original ez-gh-actions incident transcript, and the 4 checks that distinguish "user is right, I was wrong" from "user is misremembering, code is correct".

See `references/green-claim-brief-fabrication-pr-8070-2026-07-06.md` for the verified bug case where the agent composed a green-claim dispatch brief from `session_search` memory and the dispatched AO worker caught the brief/live-state disagreement (worktree dirty, CodeRabbit with contradictory `CHANGES_REQUESTED` on file, 14 failing gates not 9, AGY gate violating same-name rule) — saving the user from a `MERGE APPROVED` → broken-merge disaster. This is the canonical "recurring-alert investigation, ≥2 prior failed attempts" pattern: prior session memories are evidence of recurring blockers, not evidence of current green state.

## Phases (execute in order, no pauses between)

### Phase 0 — Classify the goal (one decision, ≤30 seconds)

Classify the user's goal into ONE of:

| Goal shape | Examples | Routing |
|---|---|---|
| **PR fix** | "fix the CI on PR #N", "/green this PR", "address CodeRabbit on PR #N" | `workflow/drive-pr-to-green` |
| **New code / new feature** | "add X to the repo", "implement Y", "build a Z" | `/fs` then `/f` (feature-mode) |
| **New PR for existing work** | "open a PR for my branch", "ship my changes", "merge my draft" | `workflow/always-pr-never-local-edit` |
| **Docs-only PR** | "review readme and update", "add an architecture diagram", "update docs for X" | Inline worktree → `gh pr create`; skip `/fs` and AO dispatch (see below) |
| **Investigation / read-only** | "find out which key leaked", "what does X do", "review my plan" | Inline research → answer with **proof artifact** (file:line + quoted text + reproducible command) |
| **Reconfirm / pushback** | "I thought it was X", "what happened to Y", "reconfirm if Z" | See "Reconfirm & pushback" section above — fan out across 9 memory stores, reconcile, ship correction |
| **Ops / config / infra** | "rotate the key", "bump the Cloud Run memory", "fix the daily cron" | Inline gcloud/kubectl/etc. with output captured; if a code PR is also needed, file as follow-up |
| **Meta / about-Hermes** | "skillify X", "make this a skill", "improve Y workflow" | `skillify` skill |

**Docs-only PR fast path (added 2026-07-06, ez-gh-actions PR #9):** When the user asks to review/update docs (README, DESIGN.md, architecture diagrams, SVG), classify as **docs-only PR** and execute inline in a fresh worktree — do NOT route to `/fs` (overkill for prose) and do NOT dispatch via `ao spawn` unless the repo is already a configured AO project. Wasted 4-5 tool calls probing `agent-orchestrator.yaml` and `ao spawn --help` before realizing `ez-gh-actions` wasn't in AO. The inline recipe: (1) `git fetch origin main && git worktree add -b docs/<slug> <path> origin/main`; (2) `write_file` / `patch` the docs; (3) run whichever CI commands the repo uses (cargo test, npm test, etc.) to prove docs didn't break anything; (4) `git commit && git push origin <branch>`; (5) `gh pr create` with the answer to the user's question in the PR body. This is a valid `finish-the-job` end-state (#2: PR open with green CI awaiting user merge).

**If the classification is ambiguous after 30 seconds, ASK ONE QUESTION** (the only question in this whole pipeline). The user is willing to invest up-front in Q&A specifically to avoid mid-stream steering. Use `clarify`.

### Phase 1 — `/fs` first if the goal is non-trivial

**Trigger `/fs` if ANY of these are true:**

- Goal is a new feature or non-trivial refactor (not a 1-line fix)
- Goal mentions multiple components, files, or repos
- Goal has ambiguous wording that the agent could misinterpret in 2+ ways
- Goal is a design task the user wants reviewed

`/fs` produces `spec.md` + `attractor_spec.md`, both codex-cold-reviewed, before any code is written. The user's up-front Q&A investment pays off here — by the time the worker starts, the spec is unambiguous.

**Skip `/fs` if:**

- Goal is a PR fix on an existing branch (the PR diff IS the spec)
- Goal is <50 lines of mechanical change
- Goal is investigation / read-only (no code to spec)

### Phase 2 — Dispatch (do not self-execute multi-step code work)

For PR fixes: load `workflow/drive-pr-to-green` and follow its full sequence (worktree at explicit SHA → fix → push → watch CI → clear review → self-merge when authorized).

For new features: dispatch via `dispatch-task` skill (`ao spawn`) so the worker gets its own tool-call budget. Inline gateway sessions cap at ~25 tool calls; AO workers have their own budget.

**AO availability check (added 2026-07-06, ez-gh-actions PR #9):** Before dispatching, confirm the target repo is a configured AO project. The `dispatch-task` skill says "ao spawn -p <project>" but not every `jleechanorg/*` repo is in `agent-orchestrator.yaml`. Quick probe: `ps aux | grep "ao start"` shows running AO daemons and their project names. If the repo isn't there, skip AO and execute inline in a worktree — don't burn 4-5 tool calls probing filesystem paths that are unreliable (the `~/.agent-orchestrator/` dir on this host has thousands of session subdirs that make `find` / `ls` pathologically slow). For docs-only work, inline is always the right answer regardless of AO availability.

For new PR from local branch: `workflow/always-pr-never-local-edit` → fresh worktree from `origin/main` → port the local diff if needed → push → `gh pr create`.

For ops/investigation: execute inline (gcloud, curl, file reads). The "inline-able" boundary is one tool call OR a tight sequence with no fork.

### Phase 3 — Drive to conclusion

The dispatched worker OR inline execution runs until one of the end-states in the Contract is provably true. If the worker hits a fork mid-stream:

1. Apply the user's rule: make the call yourself, surface it in the final reply ("I picked X over Y because Z; if you wanted Y, here's the one-line revert").
2. **Never post a multi-option question to the user mid-stream.** The exception is Phase 0 — that's up-front Q&A, which is allowed.
3. If the fork is *truly* unrecoverable without user input (e.g. force-push authorization, secrets the agent can't see, env-specific config only the user has), halt with the ONE-LINE BLOCKER shape: "PR #N is at <state>; one blocker: <one command the user runs>."

### Phase 4 — Final reply shape (mandatory)

Every completion reply MUST contain:

1. **End-state declaration** — "✅ Done: <green PR #N merged> | <PR #N open + green, awaiting your review> | <local state X verified>"
2. **Proof artifact** — PR URL, `gh pr view` JSON, or `git log` + `git diff --stat` output, or the actual command output captured
3. **What was decided mid-stream** (if anything) — every judgment call the agent made instead of asking, with one-line rationale
4. **No follow-up question** — "want me to X?" is the violation. The work is done; the user reviews.

## Slack reply format (added 2026-07-06)

**The Phase 4 reply is the user's only artifact.** If they can't find the proof in the first 3 lines of your reply, the work didn't land — even if the green PR is real.

**Mandatory Slack reply shape** (for any task with a verifiable end-state):

```
✅ Done: <one-line end-state declaration — green PR #N merged | PR #N open awaiting review | local state X verified>

**Proof:** <PR URL + 1-3 lines of `gh pr view` / `git log` / command output>
**Judgment calls:** <2-3 bullets max — what was decided mid-stream that the user might want to override>
🧠 Memories used: [<source>, ids_or_labels, effect> — one line]
```

**Forbidden Slack patterns (verified 2026-07-06, ez-gh-actions PR #9/10 — three iterations of user pushback before accepted):**

- ❌ 5-section status reports (Healthy/Risky/Blocked/Next actions/🧠 Memories used) with colored status icons — those are for terminal log files and CodeRabbit severity matrices, NOT Slack. Slack collapses wide tables into narrow scrollable panes; a 5-section table reads as a wall.
- ❌ Wide tables with >4 columns in Slack — wrap in a bullet list instead.
- ❌ Multi-paragraph proof sections — paste the actual command output as a fenced code block (≤10 lines) or a single PR URL. The proof should be 1-2 lines, not a page.
- ❌ "Summary / Body / Impact / Risk / Test Plan" section headers — those are PR descriptions, not Slack replies. Save them for `gh pr create --body`.
- ❌ Re-listing the user's question in the reply — they know what they asked. Lead with the answer.
- ❌ Re-explaining the work that was done in a separate paragraph before the proof — Slack collapses consecutive paragraphs; put the proof at the top.

**Channel-specific overrides (verified via the Slack rendering contract in `~/.hermes/skills/slack-thread-routing-investigation`):**

- **DM / direct thread**: terse, lead with end-state + proof URL. The user wants to know what landed, not be re-taught.
- **Channel post**: include enough context for someone reading the channel (not just the OP) to know what PR #N is about — 1 sentence of context is fine, full re-explanation is not.
- **`raw shell tab`**: only shell-safe text — no markdown, no emoji, no wide tables. The `🧠` emoji gets replaced with `Memories used:` per SOUL.md `Response guardrail`.

**When the reply NEEDS to be longer (10+ lines):** split it into numbered sections with bold headers (`**1. Confirm**`, `**2. What changed**`, `**3. Proof**`) — NOT into colored-icon status sections. Each section ≤5 lines. The user's reading flow is left-to-right and top-to-bottom; optimize for that.

**Anti-pattern example (what NOT to do, verified pushback 2026-07-06):**

```
🟢 Healthy
- State: OPEN, MERGEABLE
- Files: 3 changed (+331 / -33)

🟡 Risky
- CI test (ubuntu-latest) FAILURE on cargo fmt --check
- Pre-existing fmt drift in src/service.rs

🔵 Next actions
- Option A: merge as-is
- Option B: fix fmt in this PR
- Option C: wait for maintainer

🧠 Memories used: [...]
```

vs. the correct shape:

```
✅ Done: PR #9 MERGED into origin/main (commit 63dcd4f).

**Proof:** https://github.com/jleechanorg/ez-gh-actions/pull/9 — `gh pr view 9 --json state,merged` returns `state:closed, merged:true`. Local CI green: `cargo test` 46 passed, `cargo clippy -- -D warnings` clean.

**Judgment calls:** I fixed the pre-existing cargo fmt drift on src/service.rs in the same PR rather than opening a separate fix/fmt PR — kept the merge clean.

🧠 Memories used: [finish-the-job + push-pr-donot-stop-halfway, confirmed merged end-state via gh api]
```

The second shape puts the PR URL at the top, makes the state searchable, and gets out of the way. The first shape buries the answer under 5 sections.

## Anti-patterns (do not do)

- ❌ **"I started the worker, will update when done"** — the agent has 25 calls; the worker has its own budget. The reply IS the worker. If you have to wait, write the cron babysit reference (see `babysit-openclaw` skill) and post a status link.
- ❌ **"Here's a design with 3 options, which would you like?"** — that's Phase 0 question-count inflation. ONE option (your best judgment) + the path forward. The user's rule: "correct but misinterpret is fine."
- ❌ **"Local commit + ask 'want me to push?'"** — `always-pr-never-local-edit` is in the same skill family; do not violate it.
- ❌ **"Tests pass locally, opening PR now"** (then going silent) — the PR URL goes in the final reply, not in a follow-up.
- ❌ **"Investigation complete, here are 6 findings"** — every finding needs a "what to do about it" line, and at least one finding must be acted on.
- ❌ **Stopping at "I asked AO to spawn a worker"** — that's an ack. The work isn't done until the worker reports OR the cron takes over.
- ❌ **"Is X finished?" → redo X from scratch (added 2026-06-28).** When the user asks whether a recent non-trivial task was finished, do NOT re-pull gog / re-run searches / regenerate the report from scratch. Use `session_search` + `hermes sessions export <path> --session-id <id>` to surface the prior session's final assistant text in one turn. The 2026-06-28 audit-recovery case reconstructed a 67-message / 1.55M-cache-token prior session in ~10K tokens by exporting session `20260627_162502_ba20f748`. ~150x cheaper, same answer, one reply. **Only redo from scratch if** the prior session's final text ends in a multi-option menu (it stalled) OR the underlying data has gone stale (the user said "verify it's still correct" not "is it finished"). See `references/reconstruct-from-prior-session-2026-06-28.md` for the 3-step recipe and decision matrix.
- ❌ **"Anchored on code, ignored memory terminology" (added 2026-07-06).** When the user pushes back on a yes/no question (e.g. "is it doing X?", "there was supposed to be Y"), do NOT anchor on the source code / current DESIGN.md as the only source of truth. Code is truth for **behavior**; the user's memory stores (wiki, roadmap, project memory, prior sessions) are truth for **what the strategy is called** and **what was supposed to happen**. The trap is rejecting the user's framing by answering "no" without first checking whether their memory stores use the term to mean something different (or something the code comment simply doesn't surface). Recipe: see "Reconfirm & pushback" above — fan out across all 9 memory stores in parallel, reconcile terminology, ship a correction. Verified 2026-07-06 with ez-gh-actions PR #9 — the user was right that ezgha uses VM-in-VM isolation (container-in-VM-in-host 3-layer stack per wiki + roadmap + project memory); the first commit wrongly said "no" because it rejected the nested-VM-backend interpretation without affirming the deployed 3-layer one.
- ❌ **"Verbose multi-section status report overwhelms the reader" (added 2026-07-06).** A green PR is not enough if the Phase 4 reply uses 5 colored-icon status sections (Healthy/Risky/Blocked/Next actions/🧠 Memories used), wide tables with >4 columns, or "Summary / Body / Impact / Risk / Test Plan" PR-description headers. The user's reading flow on Slack collapses wide tables into scrollable panes; the answer gets buried. Use the Slack-specific reply shape in §"Slack reply format" — lead with the end-state + proof URL, keep judgment calls to 2-3 bullets, drop the colored-icon sections. Verified 2026-07-06 with ez-gh-actions PR #9 → "Status" reply → user pushed back "kind of confusing" → switched to the Slack-specific shape → accepted.

- ❌ **"Candidate-list classification trap" (added 2026-07-07, $GITHUB_REPOSITORY /roadmap sweep).** When the user asks to find "all non-prod / safe / logging-only PRs" or similar batch queries, the agent's instinct is to filter by PR title keywords (`ci:`, `docs:`, `test:`, `chore(`, etc.). This is wrong: title keywords are not authoritative — a `chore(Dockerfile)` PR can touch `$PROJECT_ROOT/Dockerfile` and be PROD; a `feat(bq-logging)` PR can include `$PROJECT_ROOT/bq_logging.py` and be PROD. The authoritative classification is **per-file path** against the project's prod path prefixes (e.g. `PROD_PATH_PREFIXES = ($PROJECT_ROOT/, testing_mcp/, testing_ui/)` in `scripts/green_merge_nonprod.py`). Verified incident: 32-PR candidate list from title keywords → 17 had ≥1 file under a prod prefix after live `gh pr view --json files` check. The "lite-green sweep" must always re-run a file-path gate against LIVE PR data BEFORE claiming a target list. Companion reference: `references/nonprod-sweep-candidate-filtering-2026-07-07.md`.

- ❌ **"Green-claim brief from memory, not live state" (added 2026-07-06, PR #8070 on $GITHUB_REPOSITORY).** When a recurring alert fires for the 5th time and prior session_search shows 4 prior attempts that all stopped at the same wall, the agent's instinct is to write a green-claim brief for the dispatched worker ("the worktree is clean, CodeRabbit is APPROVED, all 9 failing gates are dismissable as infra") based on what the prior sessions said. **This is fabrication, not investigation.** Prior sessions that ALSO stopped at the wall are not evidence of current green state — they are evidence of a recurring blocker. Before composing any green-claim brief (or any "drive to merge" instruction to a dispatched worker), run these 5 ground-truth checks against LIVE state and report each result inline:
  1. `git status -sb` + `git diff origin/main..HEAD --stat` in the named worktree → worktree scope is what you claim?
  2. `git rev-parse HEAD` vs `git rev-parse origin/<branch>` → unpushed commits?
  3. `gh pr view <N> --json reviewDecision,mergeStateStatus,mergeable` → current CodeRabbit state (not "APPROVED last week" — current state)
  4. `gh pr checks <N> --repo OWNER/REPO | grep -E "fail"` → failing gate NAMES + URLs (not just a count)
  5. `gh api repos/OWNER/REPO/pulls/<N>/reviews --jq '.[] | select(.state=="CHANGES_REQUESTED") | {ts, user, body_preview}'` → unresolved review threads
  If any check disagrees with the brief, the brief is wrong. Patch the brief OR halt per the dispatch-on-install / pr-green-dispatch rules — do NOT ship a brief that asserts green when live state is not green. The verified bug case: 2026-07-06, PR #8070, agent wrote a brief saying "9 failing gates dismissable, CodeRabbit APPROVED, worktree clean" — actually 14 failing gates, CodeRabbit had a contradictory CHANGES_REQUESTED on file, worktree had 330 staged files / +16,481 / -32,997 polluting it. The dispatched worker caught the brief/live-state disagreement and refused to post fake-green. Saving the user from a `MERGE APPROVED` → broken-merge disaster is the right outcome; never assume the brief is correct just because prior sessions claimed green.

## Green-claim brief: mandatory live-state verification (added 2026-07-06)

When the goal shape is **drive PR #N to green** AND prior session_search shows ≥2 prior attempts that all stopped at the same wall (recurring-alert pattern), do NOT compose a green-claim brief from session memory. Run this 5-check preflight and patch the brief to match the live results:

```bash
# 1. Worktree scope
cd <WORKTREE_PATH>
git status -s | wc -l                      # 0 = clean; >0 = stale residue
git diff --cached --shortstat               # staged changes — NOT in PR diff
git diff origin/main..HEAD --stat           # this IS the PR diff

# 2. Unpushed commits + head SHA match
git rev-parse HEAD
git rev-parse origin/<branch>
git log origin/<branch>..HEAD --oneline      # must be empty

# 3. CodeRabbit current state (NOT "APPROVED last week")
gh pr view <N> --repo <OWNER>/<REPO> \
  --json reviewDecision,mergeStateStatus,mergeable

# 4. Failing gate names + URLs (not just count)
gh pr checks <N> --repo <OWNER>/<REPO> 2>&1 | grep -E "fail" | head -30

# 5. Unresolved review threads
gh api repos/<OWNER>/<REPO>/pulls/<N>/reviews \
  --jq '.[] | select(.state=="CHANGES_REQUESTED") | {ts, user, body: (.body | .[0:200])}'
```

Also run the same-name dismissal check rigorously — one failing gate that passes on a comparison PR (`gh pr checks <OTHER_PR>`) VIOLATES the `qa-test-failure-dismissal-anti-pattern` rule. Do not blanket-dismiss a count of failing gates; verify each individually.

The brief must include the LIVE numbers, not what session_search memories claim. If the live numbers show the work is not green, the brief must say so explicitly. Shipping a green-claim brief from stale memory is the #1 failure mode for recurring-alert investigations — it wastes an AO worker's tool budget, erodes user trust when the worker posts "blocker, not green," and trains the user to expect fake-green on every recurring alert.

## Loader / auto-fire contract

This skill is registered in `~/.hermes_prod/skills/RESOLVER.md` and the `## COMMIT: finish-the-job` block in `SOUL.md` makes it load automatically for any user message that contains a goal phrase ("can you X", "please Y", "make Z", "investigate A", "fix B"). The trigger phrases are listed in the YAML frontmatter at the top of this file.

**When auto-fired:** Phase 0 runs first. If classification returns PR-fix / new-code / new-PR, the skill proceeds autonomously. If classification returns investigation / ops, the skill executes inline and posts the final reply with proof.

**When explicitly invoked (`/finish <goal>`):** Same as auto-fire, but the user has signaled they want this pipeline regardless of the goal shape.

## Deploy sync awareness (read this before rolling out a finish-the-job artifact)

**`scripts/deploy.sh` Stage 4.5 only syncs `POLICY_FILES=(CLAUDE.md SOUL.md TOOLS.md HEARTBEAT.md)`.** It does NOT sync `skills/` or `skills/RESOLVER.md`. A skillify pass that creates `~/.hermes_prod/skills/<name>/` works locally, but:

1. If you only wrote to prod, the staging git checkout at `~/.hermes/skills/<name>/` is empty — a future `git pull --ff-only` won't reintroduce it.
2. If you wrote to staging only, the prod resolver won't see the skill — `~/.hermes_prod/skills/RESOLVER.md` won't have the trigger entry.
3. If you wrote both, you still need a manual `cp ~/.hermes/SOUL.md ~/.hermes_prod/SOUL.md` (the symlink at `~/.hermes/SOUL.md` → `~/.hermes/workspace/SOUL.md` lands in the staging tree; deploy copies it to prod) — UNLESS you run `deploy.sh` end-to-end and accept the canary + restart.

**The skillify anti-pattern guard (run in the same turn as any rollout claim):**

```bash
echo "1. SKILL.md:           $(test -f ~/.hermes_prod/skills/<name>/SKILL.md && echo PRESENT || echo MISSING)"
echo "2. tests pass:         $(cd ~/.hermes_prod/skills/<name>/tests && python3 -m pytest -q 2>&1 | tail -1)"
echo "3. cron executable:    $(test -x ~/.hermes/scripts/<script>.sh && echo YES || echo NO)"
echo "4. plist template:     $(plutil -lint ~/.hermes/launchd/<label>.plist.template 2>&1 | tail -1)"
echo "5. RESOLVER entry:     $(grep -c '^## <name>$' ~/.hermes_prod/skills/RESOLVER.md) match"
echo "6. resolver triggers:  $(grep -c '<user-phrase>' ~/.hermes_prod/skills/RESOLVER.md) match"
echo "7. SOUL.md staging:    $(grep -c '^## COMMIT: <name>$' ~/.hermes/SOUL.md)/1"
echo "8. SOUL.md prod:       $(grep -c '^## COMMIT: <name>$' ~/.hermes_prod/SOUL.md)/1"
echo "9. SOUL.md in sync:    $(diff -q ~/.hermes/SOUL.md ~/.hermes_prod/SOUL.md >/dev/null && echo YES || echo DRIFT)"
```

**Test portability (CodeRabbit MAJOR, 2026-06-19):** the test file `tests/test_finish_the_job_contract.py` uses `HERMES_PROD_SKILLS` (env var, defaults to `$HERMES_HOME/skills`) instead of a hardcoded `$HOME/...` path. Run the tests with:

```bash
# Default (Hermes dev machine: $HOME/.hermes_prod/skills)
cd ~/.hermes/skills/finish-the-job/tests && python3 -m pytest -q

# Other developer checkout
HERMES_HOME=~/my-hermes HERMES_PROD_SKILLS=~/my-hermes/skills/finish-the-job python3 -m pytest -q
```

If items 1-7 land in the same turn as the rollout and 8-9 land within the next deploy cycle, the work is done. Anything outside that pattern is a half-finished rollout — apply the same anti-pattern audit you'd apply to a PR.

## Related skills — load order when this fires

1. `dark-factory` (always — for the `/f` and `/fs` definitions)
2. `drive-pr-to-green` (only if goal shape is PR-fix)
3. `always-pr-never-local-edit` (only if goal shape is new-PR or local-changes-exist)
4. `dispatch-task` (only if Phase 2 decides to dispatch via `ao spawn`)
5. `dropped-messages` (only if the goal was itself a dropped-thread recovery — meta-finish)
6. `session-history-search` (only if the user's question is "is X finished?" — reconstruct from prior session before redoing work; see `references/reconstruct-from-prior-session-2026-06-28.md`)
7. `memory-search` (only if Phase 0 classifies as **reconfirm / pushback** — fan out across 9 stores; see `references/reconfirm-pushback-memory-fanout-2026-07-06.md`)
8. `slack-thread-routing-investigation` (always when the Phase 4 reply lands in Slack — encodes the channel/thread/DM/raw-shell-tab rendering contract; see §"Slack reply format" above for the channel-specific shape)

## Worked example — the 2026-06-19 incident

User said: *"Look at the last week of slack threads with work that started but didn't finish. … Is there some way we can /skillify Hermes to be more hands off? I want it to fully drive everything to a conclusion like a final /green PR … correct but misinterpret is fine but stopping halfway is not."*

Phase 0 classified: meta / about-Hermes (`skillify` skill).

Phase 1: `/fs` was unnecessary — the request itself is a skillify task, not a feature implementation.

Phase 2: Inline execution (single-session skillify pass). No dispatch needed.

Phase 3: Built the skill, ran the 10-item checklist, deployed, verified all artifacts in the same turn.

Phase 4: Final reply with the 10-item re-audit (counts of files, line numbers, deploy SHA) — no follow-up question. The user's rule is satisfied: the work landed, the skill is reachable from the resolver, the SOUL.md commit fires it automatically on the next goal-shaped message.

## Worked example — the 2026-07-06 ez-gh-actions reconfirm incident

User said: *"Review readme and update as needed and let's add an architecture diagram and let's reconfirm if it's doing a VM inside VM strategy to isolate the workers"*.

Phase 0 classified: docs-only PR (review + diagram). Executed inline in worktree, opened [PR #9](https://github.com/jleechanorg/ez-gh-actions/pull/9) with "Reconfirm — is `ezgha` doing VM-in-VM? **No**." framing.

User pushed back: *"Run /history and /ms there was supposed to be vm inside vm, what happened"*.

Phase 0 (re-classified): **reconfirm / pushback**. Loaded `memory-search` overlay, fanned out across all 9 stores in parallel via `delegate_task`. Found:
- `$HOME/llm_wiki/wiki/concepts/vm-within-vm-isolation.md` — canonical page defining VM-within-VM as **container-in-VM-in-host 3-layer stack**.
- `$HOME/roadmap/learnings-2026-07.md` line 267 — "Rust ezgha daemon, JIT registration, VM-within-VM isolation".
- `.claude/projects/.../memory/project_2026-07-05_ezgha_supersedes_self_hosted_oss.md` line 44 — same terminology.

Phase 3 (reconciliation): the deployed reality IS VM-within-VM (Mac: container → Docker daemon → Colima Lima VM → Darwin host; jeff-ubuntu: container → Docker daemon → QEMU microVM → Ubuntu host). The prior commit wrongly answered "no" because it rejected the **nested-VM-backend** interpretation without affirming the **3-layer container-in-VM-in-host** interpretation. Both interpretations exist in the literature; the wiki + roadmap + project memory all use the 3-layer meaning.

Phase 4 (correction shipped): pushed follow-up commit `055ff31` reframing README + DESIGN.md + architecture.svg to lead with VM-within-VM as the canonical strategy, then disambiguate nested-VM-backend as the actual non-goal. PR body updated. Same-turn reply with the corrected answer + memory evidence. Zero follow-up questions.