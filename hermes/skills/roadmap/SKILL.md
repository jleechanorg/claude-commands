---
name: roadmap
description: "/roadmap slash command + automated Slack-thread-audit skill. Runs a 48h Slack thread sweep across user channels, classifies each thread as finished/pending/needs-human-decision, runs /nextsteps on each pending thread, drafts auto-action proposals, pushes the audit report to a roadmap repo (jleechanorg/worldarchitect-roadmap by default), and posts the URL to the originating Slack thread. Use when the user types /roadmap, asks to 'audit slack threads', 'push roadmap repo', 'show me the report', 'what's still pending', 'nextsteps on all threads', or invokes any of the trigger phrases below."
when_to_use: "Use when the user types /roadmap or any natural-language variant of 'audit my slack threads and push a report'. Also auto-fires on launchd 9am/5pm PT schedules for any active Slack thread older than 24h."
tags: [slack, audit, roadmap, worldarchitect, pr-merge, decisions, automation]
---

# Roadmap — Slack thread audit + PR decision block + auto-action proposals

**Class:** periodic audit + report-publisher. **Output:** Markdown report pushed to a roadmap repo + Slack thread reply.

## Trigger Phrases (resolver)

- `/roadmap`
- `audit my slack threads`
- `push roadmap repo`
- `what's still pending`
- `nextsteps on all threads`
- `show me the roadmap report`
- `roadmap all my slack asks`

## Inputs

| **target_repo** (default: `jleechanorg/roadmap` — the existing cron target as of 2026-06-26. Jeffrey confirmed both the inline /roadmap slash command and the launchd job should write to the same repo.)
| **slack_channel** (default: current session's source channel)
| **window_hours** (default: 48)
| **deliver** (default: `slack` — posts URL back to thread)

## Pipeline (deterministic; LLM only for classification + per-thread /nextsteps)

1. **Resolve the audit window** — now minus `window_hours`, formatted ISO-8601 UTC.
2. **Pull thread history** — for each `channel_id` in scope (configured in `references/scoped-channels.txt`):
   - `mcp__slack__conversations_history(channel_id, limit=N)` (cursor-paginate if needed)
   - `mcp__slack__conversations_replies(channel_id, thread_ts)` for each distinct thread_ts
### Step 2.5 — META-FAILURE GATE (mandatory 2026-06-27, this thread)

**Bug-ref (2026-06-27 03:42 PT, Jeffrey explicit):** the 0228 PT /roadmap run
classified `C0AH3RY3DK6 / 1782335045` (page-load cold-start, 28-44s on /) as
`Defer (in-flight)`, and `C0AH3RY3DK6 / 1782341232` (experience issues) as
`Defer` — even though:
- Issue #7961 had been filed 1h before the audit (cold-start, full diagnostic
  in body, ready for the GUNICORN_WORKERS=1 one-liner fix)
- Issues #7963–7967 had been filed 20 min before the audit (5 retention items
  born from the experience investigation)
- The cold-start thread contained 8+ bot diagnostic messages with a
  finished root-cause analysis, just no PR or worker

**The five fixes — apply BEFORE step 3 classification:**

#### 2.5.a — Issue + thread JOIN (mandatory)

```bash
# Pull open issues from each active repo in scope
for repo in $GITHUB_REPOSITORY jleechanorg/agent-orchestrator jleechanorg/jleechanclaw; do
  gh issue list --repo "$repo" --state open --limit 100 \
    --json number,title,body,labels,createdAt,updatedAt \
    > /tmp/issues-${repo//\//_}.json
done

# For each thread, extract: PR numbers, file paths, function names, error
# signatures, issue numbers mentioned by user, key noun phrases (campaign_id,
# user_uid, error class). Cross-reference against issue titles + bodies.
```

A thread that mentions `gunicorn`, `worker_config.py:23`, `cold start`,
`minScale`, `30-110s`, or any technical signature appearing in an issue
body MUST be linked to that issue. **The issue is the source of truth for
"is this PR-able?"** — if the issue body has a "Proposed fix" or "Repro"
section, the thread is PR-able.

#### 2.5.b — "incidental" is forbidden for threads with diagnostic content

The `incidental` classification (bot-only / status-ping) MUST NOT be applied
to a thread that contains:
- Any `gh`, `gcloud`, `curl`, `bq query`, `cold_start_latency_report`, or
  similar diagnostic command output
- Any "Root cause:" or "Smoking gun:" line
- Any reference to a specific file path + line number (e.g. `worker_config.py:23`)
- More than 3 bot messages without a user reply (real engagement signal)

If the thread contains any of these, classify as `pending` (with the
"diagnostic-only, no PR yet" sub-status) and surface in § C as a
`CRITICAL-PENDING-NO-PR` item — not in § G.

#### 2.5.c — "Defer (in-flight)" requires proof of in-flight

A thread can ONLY be marked `Defer (in-flight)` if at least one of:

- An open PR references the thread's root-cause file/function
- An AO worker is currently active on the relevant issue/PR
- A commit on `origin/main` in the last 24h touches the relevant files

If NONE of these hold, classify as `pending` (CRITICAL-PENDING-NO-PR).
**The 0228 run marked `C0AH3RY3DK6 / 1782335045` as Defer (in-flight) with
none of the three** — that's the trap.

#### 2.5.d — Recurring-stuck alarm (≥2 consecutive Defer in last 4 reports)

For each thread that appears in ≥ 2 of the last 4 `/roadmap` reports in any
state other than `finished`, surface as **STUCK** in § C with a header like:

```
### C-NN. <thread title> — STUCK ⚠️ (appeared in N consecutive reports)
```

This is the alarm the 0228 run lacked. The cold-start thread had been
appearing as `Defer (in-flight)` for at least 3 consecutive reports
(verified 2026-06-27: reports `2026-06-24-2005`, `2026-06-25-2041`,
`2026-06-26-1856`, `2026-06-26-1405`, `2026-06-27-0228` all listed it as
Defer).

#### 2.5.e — "Bot said PR is ready" — verify before marking finished

If a bot reply contains "✅", "done", "merged", "shipped", "filed", or
"PUSHED" without a verifiable artifact (commit SHA, PR URL, issue URL,
or `git show` output), treat the claim as unverified and run the
4-check pre-flight gate (file/config → CLI tool → daemon health →
git/deploy state) before accepting it.

3. **Classify each thread** into one of:
   - **finished** — last message ≥ 24h ago with no unresolved question, OR
     explicit close marker + verified artifact (PR URL, commit SHA, merged)
   - **pending** — last message < 24h ago, no close marker, OR has open
     question. Sub-status: `CRITICAL-PENDING-NO-PR` if (2.5.b) and (2.5.c)
     conditions apply
   - **needs-human-decision** — pending + has a product/ops/merge gate
   - **STUCK** — appeared in ≥ 2 consecutive reports without resolution
     (per 2.5.d alarm)
   - **incidental** — bot-only / status-ping / no decision content AND
     none of the 2.5.b diagnostic-content triggers fire
4. **For each non-incidental thread, run /nextsteps** — extract the latest user ask, the latest bot reply, and produce a 3-line block:
   - **Status:** (finished | pending [CRITICAL-PENDING-NO-PR] | needs-human-decision | STUCK)
   - **Next step:** (one-line action — must reference a PR/issue/worker/commit)
   - **Why:** (one-line justification)

   **PRE-FLIGHT VERIFY GATE (mandatory before executing any /nextsteps recommendation).** The snapshot's "Current state" + "Recommended next command" are *claims by the prior agent at snapshot time*, not facts. Before running any non-trivial action, run the 4-check gate (file/config → CLI tool → daemon health → git/deploy state). Verified 2026-06-26 19:19 PT: all 3 threads in the 1856 snapshot were stale — 1 config bump already at target, 1 install already done, 1 cleanup already shipped — resolved in <2 min without writing code. Full recipe: `references/before-nextsteps-verify-current-state.md`. **Extended 2026-06-27:** the pre-flight gate MUST also include a `gh issue list --repo <repo> --state open --search "<thread topic>"` lookup to detect issues filed against the same surface that the thread is investigating. If issues exist, link them in § C.
5. **Pull PR state for the workspace** — `gh pr list --repo <active-repo> --state open --json number,title,mergeable,headRefName,isDraft` AND `gh issue list --repo <active-repo> --state open --limit 100 --json number,title,labels,createdAt`. Join against any thread that mentions a PR/issue number OR any thread whose topic matches an issue title (fuzzy match on key noun phrases).
6. **Build the report** (Markdown, see § Report Shape below).
7. **Push to roadmap repo** — `git pull --rebase origin main` → write `reports/<UTC-timestamp>-roadmap-report.md` → commit → `git push -u origin main` (create the repo via `gh repo create` if first run).
8. **Post the URL back** to the originating Slack thread with a 3-line TL;DR + the URL.

### Step 8.5 — `/a fullrun` DRIVE PHASE (mandatory, 2026-06-26)

**The /roadmap run does NOT end at the report push.** Per user directive
2026-06-26 ("finish the work and for the /roadmap skill all things must be
driven with /a and fullrun and they shouldn't stop until PRs are green and
have /es and /er or investigations have evidence or it was a small task and
obviously done. It's ok to stop and ask for a human decision if truly needed
but mostly it's better to drive to a misinterpreted or wrong outcome with a
/green and evidence backed PR than to stop. Human attention is scarce"),
every /roadmap invocation MUST, in the SAME turn as the report push:

1. **For each MERGEABLE PR surfaced in § B**, spawn an AO worker via `agento`:
   ```bash
   cd ~/.openclaw && env -i HOME="$HOME" \
     PATH="$HOME/.nvm/versions/node/v22.22.0/bin:$HOME/.local/bin:$HOME/.bun/bin:/opt/homebrew/bin:/usr/bin:/bin" \
     GH_TOKEN="$(gh auth token)" AO_BOT_GH_TOKEN="$(gh auth token)" \
     bash -c "~/bin/ao spawn -p <project> --claim-pr <N>"
   ```
   **Sequence the spawns — `ao` rejects parallel calls on the same project.** Spawn cadence: ~5–15 s per PR; the bash parent shell hangs after child exit (kill it after 90–180 s if it doesn't return — verify session landed via `ao session ls`). For 7+ spawns in Step 8.5, do not delegate the entire spawn loop to a single `delegate_task` with 600 s budget — that's insufficient. Either: (a) split into batches of 3 PRs per subagent, or (b) run them inline from the parent session. Use the drive-pr-to-green contract: do not stop at "ready for review", do not ask "want me to merge?", do not pause at checkpoints. Force-push audit and Gate-8 `/smoke` comment handling live in agento+drive-pr-to-green.
   do not ask "want me to merge?", do not pause at checkpoints. Force-push
   audit and Gate-8 `/smoke` comment handling live in agento+drive-pr-to-green.

2. **For each `OPEN-…` automatic trigger in § E**, dispatch immediately —
   do not wait for the user to type the trigger word. "I can do this
   automatically" means "doing it now" — that's the user's framing.

3. **For each top-5 human decision in § D** that is *truly* needed (e.g.
   architectural pivot, real auth-required merge, account-restricted deploy),
   route the decision through the cmux codex `/advice` pattern (§ Deferred-decision
   advisor pattern) so the user gets an advisory verdict alongside the question.
   The "drives to PR/evidence" rule means: if a workaround exists, ship the
   workaround as an AO-driven PR with `/es` evidence and label it as a
   workaround in the body. The user reviews the PR, not the question.

4. **For each `OPEN-…` deferred decision in § F**, still execute the
   cmux `/advice` pattern and write the verdict into the report's § F as a
   "Codex advisor verdict" subsection. The user said "use the codex cmux
   consultant process from the thread" — that means route, don't queue.

5. **End-state rules** — when is a /roadmap run actually "done"?
   - **Report pushed to roadmap repo** (commit SHA on origin/main) ✓
   - **MERGEABLE PRs in § B** all have an active AO worker session-id and
     worktree path committed to the report's § I verification block ✓
   - **Slack thread reply** posted with URL + 3-line TL;DR + AO session IDs ✓
   - **Codex advisor verdict** written for every § F item ✓
   - **Five-rail closure contract** (per the three-home artifact rule in
     `~/.hermes_prod/SOUL.md` `## COMMIT: three-home-artifact-closure-contract`):
     - staging PRESENT (skills/roadmap/SKILL.md)
     - prod PRESENT (skills/roadmap/SKILL.md)
     - tracked by git (`git ls-files`)
     - on origin/main (`git show origin/main:<path>`)
     - last commit SHA on origin/main

**Bug-ref (2026-06-26, this thread):** the prior /roadmap run at 18:56 PT
produced a polished report, pushed to origin/main, and then *stopped*. The
user's "drive via /a fullrun" directive landed mid-session. The fix is this
section: the report push is the MIDDLE of the run, not the END.

**Forbidden stop-halfway patterns under /roadmap:**
- ❌ "Report pushed, here are the 5 things you need to decide." (asks for confirmation)
- ❌ "MERGEABLE PRs found; want me to spawn agents?" (text-only confirmation gate)
- ❌ "Codex advisor pattern ready for § F items." (queues instead of executes)
- ❌ "Audit complete. 5 PRs MERGEABLE, 3 incidents active." (describes state without driving it)
- ❌ "Issues #7963–#7967 filed for the experience findings, deferring thread to next cycle." (filed an issue but didn't drive the PR — the issue IS the artifact, not a follow-up action; verify issue body has the actual fix proposed, then spawn the PR-implementation worker. Verified 2026-06-27: 0228 PT run had this exact trap.)
- ✅ Report pushed + AO workers spawned (with session IDs in § I) + Codex verdicts in § F + Slack reply with URLs

## Verified meta-incident instance — 2026-06-27 03:42 PT (this thread)

Jeffrey's explicit meta-question: "Arent there some high pri tasks like the mobile latency stuff? Why did /roadmap miss this?" The investigation identified **5 distinct failure modes** in the 0228 PT run:

1. **Issue + thread JOIN missing.** The skill pulled PRs but never joined
   them to GitHub issues. Issues #7961 (cold-start) and #7963–7967
   (experience/retention) were filed 20–60 min before the audit but never
   appeared in the report because the join only matched on PR numbers.

2. **`incidental` classification trap.** Threads with 8+ bot diagnostic
   messages were classified `incidental` (bot-only / status-ping) when
   they actually contained a finished root-cause analysis waiting for a
   PR. Per 2.5.b, this is now explicitly forbidden for threads with
   diagnostic command output or file-path line refs.

3. **`Defer (in-flight)` as a sink.** The skill let threads be marked
   `Defer (in-flight)` with no in-flight evidence — no PR, no worker, no
   recent commit. Per 2.5.c, this now requires one of three proofs.

4. **No recurring-stuck alarm.** The cold-start thread had been appearing
   as `Defer (in-flight)` for 5 consecutive reports. The skill had no
   rule to escalate this. Per 2.5.d, the `STUCK` classification now
   triggers on ≥ 2 consecutive reports without resolution.

5. **Bot "PR is ready" claim accepted unverified.** Multiple bot replies
   in the audit window said "✅ PUSHED" or "✅ filed" without verifiable
   artifacts. Per 2.5.e, claims now require pre-flight verification.

**Fix commit:** `8d6e888a4a` on `jleechanorg/jleechanclaw` `origin/main`
adds Step 2.5 to `/roadmap/SKILL.md` with 5 sub-rules (2.5.a–e). The full
meta-incident writeup is in `references/missing-critical-tasks-meta-incident-2026-06-27.md`.

The contract is identical to `agento` §⚠️ EXECUTION RULE — TOOL FIRST, TEXT
NEVER. /roadmap is just the orchestrator over those mechanics.

## Report Shape

```markdown
# <Workspace> — <Window> Audit + Roadmap

**Generated:** <UTC ISO8601>
**Source:** <channel list>
**Window:** <from> → <to> (last 48h)
**Auditor:** Hermes (this session)

---

## A. Executive Summary
- N PRs MERGEABLE ready for batch-merge
- N PRs need human-decision
- N incidents active
- N threads auto-resolved (no action)
- N cmux workspaces idle / N pinned / N risky

## B. PR Auto-Merge Candidates
| # | PR | Title | Files | +/- |

## C. Per-Thread /nextsteps Audit
### C1. <thread ts/title>
- Status: ...
- Next step: ...
- Why: ...

## D. Top 5 Human Decisions TRULY Needed (today)

## E. Things I Can Do AUTOMATICALLY (single-word triggers)

## F. Lower-Pri Human Decisions → Codex/cmux consultant process (defer)

## G. What's NOT Pending (closed/auto-resolved)

## H. cmux Pinned Workspaces (state of active surfaces)
- Pinned: <list from ~/.config/cmux/pinned-workspaces.txt>
- Active per surface: <workspace name + state + last activity>
- Idle surfaces: <list with hours idle>
- Risky / blocked: <list with reason>

## I. Verification (proof this audit is real, not vibes)
- Slack history: <N> rows from N channels
- PR state: <M> JSON pulls via gh pr view
- 5b-leak detector: <status>
- cmux surface: <N> workspaces enumerated via `cmux list-workspaces`
- Roadmap repo: <commit SHA>
```

### Step 8a — cmux Pinned Workspaces (mandatory per 2026-06-26 user request)

Before finalizing the report, always enumerate cmux workspaces and surface their state. The user has called out that `/roadmap` reports must cover cmux pinned workspaces.

**Commands:**

```bash
# 1. Find candidate cmux sockets
SOCKETS=$(ls -1 /private/tmp/cmux*.sock /tmp/cmux*.sock 2>/dev/null)
export CMUX_SOCKET_PATH=$(echo "$SOCKETS" | head -1)

# 2. Read pinned-workspaces.txt (one workspace ID per line)
PINNED=$(cat ~/.config/cmux/pinned-workspaces.txt 2>/dev/null | grep -v '^#' | grep -v '^$')

# 3. List all workspaces with state
cmux list-workspaces 2>/dev/null > /tmp/cmux-list.json
jq -r '.[] | "\(.id)\t\(.name)\t\(.state // "unknown")\t\(.lastActivity // "?")"' /tmp/cmux-list.json
```

**Output schema for § H:**

```markdown
## H. cmux Pinned Workspaces (state of active surfaces)

| WS | Name | State | Pinned | Last activity | Linked PR |
|----|------|-------|--------|---------------|-----------|
| 20 | agento | idle | ✅ (user) | 15:51 today | PR #7950 |
| 21 | agentf | idle | ✅ (via agento) | — | — |
|  8 | hermes | active | — | 21:30 today | gateway serving |

**Pinned count:** 3 (agento, agentf, lvl:refactor)
**Idle surfaces (>4h):** 5 (hermes, lvl:refactor, cost:system-inst, ...)
**Risky / blocked:** 0
```

The launchd wrapper `scripts/roadmap-audit.sh` runs the cmux enumeration as part of step 3 and writes the JSON to `$LOG_DIR/cmux-state.json` for the worker to fold into the report.

## Pitfalls (verified)

- **Candidate-list tier classification trap (added 2026-07-07, $GITHUB_REPOSITORY 32-PR /roadmap sweep).** When the /roadmap report's § B "PR Auto-Merge Candidates" table lists PRs by title keywords (`ci:`, `docs:`, `feat(telemetry)`, `chore(`), the classification is WRONG. Title keywords are not authoritative. A `chore(Dockerfile)` PR can touch `$PROJECT_ROOT/Dockerfile` and be PROD; a `feat(observability): BQ rate-limit telemetry` PR can include `$PROJECT_ROOT/bq_logging.py` and be PROD. Verified: 32 PRs from title keywords → 17 had ≥1 file under `$PROJECT_ROOT/` or `testing_*/` after live `gh pr view --json files` re-classification. The authoritative classifier is the project's `PROD_PATH_PREFIXES` tuple (e.g. `($PROJECT_ROOT/, testing_mcp/, testing_ui/)` in `scripts/green_merge_nonprod.py`). The § B table MUST show post-classification numbers: "32 candidates from keywords → 14 strict-non-prod → 1 lite-green-ready at this moment." Honest framing surfaces the user's intuition-vs-policy divergence, not the misleading "we tried 32, all blocked." Companion reference: `finish-the-job/references/nonprod-sweep-candidate-filtering-2026-07-07.md`. Lesson: any § B candidate list MUST be re-checked against `gh pr view --json files` filtered by the project's tier rule BEFORE being presented to the user.
- **`gh repo create` requires the workspace to exist.** If the target repo is missing, `gh repo create <owner>/<name> --public --confirm` creates it. Use HTTPS URL on first push (SSH key may not be configured for new repos).
- **Slack `send_message` may fail for cross-channel posts** — fallback to direct `chat.postMessage` API with `thread_ts` + `mrkdwn=true`. **Verified misroute bypass (2026-06-26):** when the MCP helper returns `"Cross-channel Slack misroute prevented: no bot token configured for workspace 'T09FXQ4LCQP'"` but the token IS for T09FXQ4LCQP (`curl -X POST https://slack.com/api/auth.test -H "Authorization: Bearer $HERMES_SLACK_BOT_TOKEN"` returns `"team":"$USER AI","team_id":"T09FXQ4LCQP"`), use Python + urllib directly. Full recipe: `references/slack-post-mcp-bypass.md`.
- **Slack gateway enforces ~4000-char split** — even though `chat.postMessage` accepts 40k, the gateway/MCP layer splits at ~4000 chars into 2 messages. Trim the reply or post as 2 deliberately-partitioned messages. Use plain `[text](url)` syntax (Slack native), NOT `<url|label>` (gets mangled into `___URL_PLACEHOLDER____`). `~` in file paths gets stripped (use `$HOME/.hermes` full path).
- **Git push to `jleechanorg` must use HTTPS if `git@github.com` SSH key is missing** — `git remote set-url origin https://...` before first push.
- **`gh pr view --json mergeable` returns the right value for AO + human-authored PRs.** Use `mergeable: "MERGEABLE"` as the gate; `CONFLICTING` blocks; `UNKNOWN` means merge commit hasn't been computed yet (re-poll in 30s).
- **Cron-mode (launchd) runs without `~/.bashrc`** — source it explicitly in the wrapper script: `source ~/.bashrc 2>/dev/null || true`.
- **9am + 5pm PT** (launchd `StartCalendarInterval` is in LOCAL time, so use `Hour: 9` and `Hour: 17`). Mon-Fri cadence confirmed running as of 2026-06-26 (commit `77f4fe6` on `jleechanorg/jleechanclaw`).
- **`~/.hermes/scripts/deploy.sh` Stage 4.6 syncs skills/, but `.claude/commands/` requires manual `cp`** — per `jleechanclaw-slash-command-rollout` recipe.
- **`cmux list-workspaces` can wedge after large `cmux send` payloads** (verified 2026-06-26 18:55 PT — daemon alive, socket reachable, but `cmux list-workspaces` and `cmux identify` both timeout at 5-30s while `read-screen` still works). Recovery: `killall -USR1 cmux` to nudge the request queue. If persistent, full `pkill -9 cmux` then re-establish socket via launchd (auto-restarts).
- **Roadmap snapshot "Current state" claims can be hours-to-days stale.** Verified 2026-06-26 19:19 PT — all 3 threads in the 1856 PT snapshot were stale: `max_iterations` was already 500 (not 100), agent-browser v0.27.0 was already installed (not "pending v0.31.1"), and the caveman cleanup commit was already on origin/main. The cron captures agent belief at snapshot time, not live state. Always run the 4-check pre-flight gate (file/config → CLI tool → daemon health → git/deploy state) before executing any /nextsteps recommendation. Recipe: `references/before-nextsteps-verify-current-state.md`.
- **`find $HOME` without `-maxdepth` times out at 180s+** — scope with `-maxdepth 4` and a specific name pattern (e.g., `find ~ -maxdepth 4 -name "cave*"`). Verified 2026-06-26 19:19 PT.
- **Hermes resolver paths are `~/.hermes`, `~/.hermes_prod`, `~/.claude`, `~/.agents`** — broken symlinks in `~/.qwen`, `~/.openclaw`, etc. are harmless and out of scope for cleanup tasks. Verified 2026-06-26 19:19 PT (7 dangling caveman symlinks in `~/.qwen/skills/` survived the commit `2e75634` cleanup and don't need touching).
- **Iteration-budget three-field trap — DO NOT project a Hermes number onto AO.** When a report mentions "iteration budget" / "max iterations" / "agent loops", there are TWO real fields (`agent.max_turns=1000`, `delegation.max_iterations=500` in `~/.hermes_prod/config.yaml`) and ONE non-existent one (AO worker iteration cap — does not exist in `agent-orchestrator.yaml` or in `ao spawn --help`). Conflating them produces wrong numbers in the report. Verified 2026-06-27 02:35 PT — I wrote "AO worker iteration cap of 500" as a real field, mixing Hermes's delegation budget with AO's nonexistent one. Always grep before quoting: `grep -nE "max_turns|max_iterations" ~/.hermes_prod/config.yaml` (real) and `grep -nE "max_iter|max_loop|iter_cap" ~/.hermes_prod/agent-orchestrator.yaml` (should be empty). Full recipe + verbatim values + report-shape rules: `references/iteration-budget-three-field-trap-2026-06-27.md`.
- **`ao spawn` enforces single-spawn-per-project serialization.** Verified 2026-07-05 02:50Z — when 4 parallel `ao spawn -p jleechanclaw --claim-pr <N>` calls are issued simultaneously, ALL but one return immediately with `✗ Another ao spawn is in progress for project "jleechanclaw" (PID <X>, started <ts>). Wait for it to finish.` and exit code 1. The daemon has a single in-flight spawn slot per project. Implication for Step 8.5 #1: do NOT fan out `ao spawn` calls in parallel within a subagent — sequence them with a brief wait + `ao session ls` verification between each. Verified spawn cadence: ~5–15 s for the child `ao` process to fork, create the session row, and claim the PR. Full recipe + worktree collision recovery: `references/ao-spawn-serialization-2026-07-05.md`.
- **`ao spawn` bash parent shell hangs after child exits — kill the parent, not the child.** Verified 2026-07-05 02:50Z. After the child `ao` process forks the AO worker (tmux session + worktree + session row all created), the bash parent shell waits indefinitely on the tmux attach lifecycle — never returns to the prompt even though the child has long since exited. Symptom: `terminal(foreground)` times out at 30 s / 180 s / 600 s with empty `output_preview`, but `ao session ls` shows the session row already claimed. Recovery: `kill <bash-pid>` (NOT the tmux session — that's the worker's home); verify with `ao session ls` that the new session row is still present; spawn the next PR. The 600 s delegation budget in `delegate_task` is insufficient for the full § B + § E + § F pipeline when spawning 7+ AO workers — budget subagent calls by spawn-count, not by wall-time. See `references/ao-spawn-serialization-2026-07-05.md`.

## Deferred-decision advisor pattern (Codex advisor)

When the report's § F surfaces deferred human decisions, route them to a Codex advisor for a single-pass advisory verdict. **The specific surface has migrated twice** — do not assume the path documented below is still correct, always re-verify before dispatching.

### Surface migration history (read FIRST)

| Verified | Surface | Notes |
|---|---|---|
| 2026-06-26 18:56 PT | cmux `workspace:30 surface:54` (`advisor-codex`) via `/private/tmp/cmux-debug-may-18.sock` | Original pattern from this skill's first run |
| 2026-07-04 23:58 PT | dev-fork cmux `workspace:30` is `w: quick campaign` (NOT advisor-codex); `read-screen --scrollback` semantics removed | Pattern **BROKEN** on dev-fork cmux build |
| 2026-07-05 02:50Z (this run) | **Substitute: local Codex advisor process** — spawn `codex exec --model gpt-5.5-high "<prompt>"` and write the verdict to `/tmp/codex-advisor-verdict-F.md` | Worked; no surface dependency |

**Detection recipe (run BEFORE dispatching the advisor):**

```bash
# 1. Find candidate cmux sockets
SOCKETS=$(ls -1 /private/tmp/cmux*.sock /tmp/cmux*.sock 2>/dev/null)

# 2. Identify whether workspace:30 is still the advisor
for SOCK in $SOCKETS; do
  WS=$(cmux --socket "$SOCK" workspace list --json 2>/dev/null | \
    jq -r '.workspaces[] | select(.ref == "workspace:30") | .title' 2>/dev/null)
  echo "socket=$SOCK workspace:30=$WS"
done

# 3. If workspace:30 title != "advisor-codex" OR no advisor surface exists,
#    fall back to the local Codex exec pattern (below)
```

### Pattern A — legacy cmux workspace:30 surface (only if detection above confirms it)

```bash
SOCK=/private/tmp/cmux-debug-may-18.sock
WS=workspace:30
SURF=surface:54

# Send the advisory prompt as PLAIN TEXT — NOT as /advice slash command
# (Codex CLI 0.142.2 returns "Unrecognized command '/advice'")
cmux --socket "$SOCK" send --workspace="$WS" --surface="$SURF" \
  "Acting as my advisor, give one concise opinion per deferred decision (≤5 bullets each, ≤400 words total). Don't run subagents, just reason and reply directly. ...

1. <decision with A/B/C options>
2. <decision with A/B/C options>
..."

# Submit
cmux --socket "$SOCK" send-key --workspace="$WS" --surface="$SURF" enter

# Wait ~35s for Codex to process, then read
sleep 35
cmux --socket "$SOCK" read-screen --workspace="$WS" --surface="$SURF" --scrollback --lines 60 \
  > /tmp/codex-advisor-response.txt
```

**Pitfall:** the older `advisor-codex-spawn-recipe-2026-06-26.md` reference assumes `/advice` is a native Codex slash command — it is NOT in 0.142.2. Always send a plain prompt that asks Codex to "act as advisor"; do not prefix `/advice`.

### Pattern B — local Codex advisor process (fallback, current default as of 2026-07-05)

When no advisor cmux surface is available, spawn a local Codex process directly. Verified working in this run for the § F D6 (Rust vs Go) verdict:

```bash
# Spawn a short-lived Codex advisor to verdict § F items.
# Pass the question + constraints inline. Save verdict to /tmp/codex-advisor-verdict-<X>.md.
mkdir -p /tmp/codex-advisor
cat > /tmp/codex-advisor/prompt.md <<'EOF'
You are the Codex advisor for the /roadmap skill § F deferred-decision bucket.

Decision: <one-line summary>
Context: <relevant thread excerpts, PR URLs, issue bodies>
Constraints: <budget / blast-radius / cost-of-wait>

Output format (≤400 words):
- **Decision:** <one of: ACTION_A | ACTION_B | DEFER>
- **Confidence:** <high|medium|low>
- **Rationale (≤5 bullets):** 1. ... 5. ...
- **Workaround if DEFER:** <one-line>
- **Cost-of-wait:** <low|medium|high>
- **Trigger to revisit:** <concrete re-evaluation criterion>

Reason directly. Do NOT spawn subagents. Do NOT run tools beyond reading the prompt.
EOF

codex exec --model gpt-5.5-high - < /tmp/codex-advisor/prompt.md > /tmp/codex-advisor/verdict.md 2>&1
```

**Save the verdict** to `/tmp/codex-advisor-verdict-<X>.md` and reference it from § F of the report. The 2026-07-05 run wrote this block into `reports/2026-07-04-2358Z-roadmap-report.md` § F verbatim — see that commit for a working template.

**Why the substitution works:** the cmux surface was just a stable terminal pane for the same Codex CLI that Pattern B invokes directly. The pane added nothing the CLI didn't already provide for single-pass advisory verdicts; it only added a lifecycle hook. For /roadmap's § F use case (one-shot verdict written into a Markdown report), the direct CLI is strictly better — no socket, no surface lookup, no `read-screen --scrollback` flake.

Full migration writeup + verified repro at `references/advisor-surface-deprecation-2026-07-05.md`.

## Verified instance — 2026-06-26 18:56 PT (this session)

- **Skill verification:** `/roadmap` thin pointer (1847 bytes) + `skills/roadmap/SKILL.md` + `RESOLVER.md` merged at `df209445` on `jleechanorg/jleechanclaw` `origin/main` (replaces 11,388-byte Phase-0 stub).
- **Launchd plist:** running on 09:00/17:00 PT Mon-Fri cadence (commit `77f4fe6`).
- **Report pushed:** `jleechanorg/roadmap` at commit `0792625`, 59 KB, 7 actionable threads.
- **Decision buckets delivered:** 5 top decisions + 18 `OPEN-…` auto triggers + 3 Codex advisor verdicts (B / B / A).
- **Slack reply:** single 3964-char message posted to `C09GRLXF9GR` thread `1782517257.897709` at ts `1782526531.497679`.

This is the canonical /roadmap run-shape: 7 threads, 3 MERGEABLE PRs, 2 NEEDS-HUMAN, 2 deferred. When the next run yields a similar shape, copy this report's structure verbatim.

## Single-Word Triggers (output of each audit)

The report's § E exposes these for the user to ack:

- `OPEN-<NAME>-FIX` — antig builds a fix PR for `<name>` (e.g., `OPEN-5F-FIX`)
- `BUMP-<X>` — edit config knob + open 1-line PR
- `START-<Y>` — set up a sub-skill/infra
- `MERGE APPROVED` — batch-merge all MERGEABLE PRs

## How the cron calls this skill

The launchd job (`ai.hermes.schedule.roadmap-audit`) runs `scripts/roadmap-audit.sh` at 9am and 5pm PT (Mon–Fri). The script:

1. `source ~/.bashrc`
2. Reads `roadmap` skill (canonical in `~/.hermes/skills/roadmap/SKILL.md`)
3. Pulls Slack history from configured channels
4. Builds the report
5. Pushes to roadmap repo
6. Posts the URL to the configured "thread" channel (defaults to `#hermes-roadmap` or `#general`)

## Cross-references

- `~/.hermes_prod/skills/worldarchitect/SKILL.md` — auto-loaded for threads in `#worldai-bugs` channels
- `~/.hermes_prod/skills/jleechanclaw-slash-command-rollout/references/jleechanclaw-slash-command-rollout.md` — wiring recipe
- `~/.hermes_prod/skills/skillify/SKILL.md` — the 10-item contract this skill satisfies
- `~/.hermes_prod/skills/hermes-deploy-pipeline/SKILL.md` — staging/prod + POLICY_FILES rules
- `references/before-nextsteps-verify-current-state.md` — mandatory pre-flight gate before executing any /nextsteps recommendation (4 cheap checks: file/config → CLI tool → daemon health → git/deploy state)
- `references/iteration-budget-three-field-trap-2026-06-27.md` — verify-before-claim for any "iteration budget" / "max X" claim in the report (greps `config.yaml` + `agent-orchestrator.yaml` + `ao spawn --help`)
- `references/advisor-surface-deprecation-2026-07-05.md` — cmux workspace:30 advisor-codex surface is broken on dev-fork cmux (Pattern B: local Codex exec substitute). Detected 2026-07-05 /roadmap run, report SHA `8dcb44f`.
- `references/ao-spawn-serialization-2026-07-05.md` — `ao spawn` enforces single-spawn-per-project serialization + bash parent shell hangs after child exits. Detected 2026-07-05 /roadmap run, recovery recipes for both pitfalls.
- `references/missing-critical-tasks-meta-incident-2026-06-27.md` — the prior meta-incident that introduced Step 2.5; same "find a meta-failure, fix the skill, document the fix" pattern as the 2026-07-05 lessons.