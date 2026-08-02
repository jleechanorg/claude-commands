---
name: single-pr-status-check-no-worker
note: Companion reference for the babysit-ao-pr-loop skill. Verified 2026-07-16 on PR #8418 ($GITHUB_REPOSITORY, thread C0BCVG4F560/1784219487.851579). Captures the four-state cron pattern that runs in this skill's territory but without an AO worker. Updated 2026-07-23 with the "head-advance-while-cron-was-armed" observer-side trap (PR #8488 cron self-check revealed trim commit was no longer the head when the tick ran). Updated 2026-07-24 with six new pitfalls from PR #8545 cron self-check: unauthenticated-curl-404 vs authed-gh, statusCheckRollup:null PR-object pitfall, gh run view --log "still in progress" misreport, AO DB as authoritative state fallback, cron-prompt session-id drift, and pr.last_nudge_signature JSON column. Updated 2026-07-24 (this revision) with three recipes one-shot PR status crons hit and the prompt body usually doesn't cover: cron-runner $CRON_JOB_ID is NOT exported into the env (source-of-truth is jobs.json), hermes CLI venv-broken direct-edit fallback for self-cancel, and the cron-runtime Slack delivery identity gap (HERMES_SLACK_BOT_TOKEN posts under MCP Agent Mail bot, not canonical Hermes bot).
---

# Single-PR Status Check (no worker, one-shot)

A simpler cousin of the AO babysit loop — the cron prompt asks "check PR #N, branch on state, post to the originating thread, stop." No worker session, no continuous tick, no nudges. Just a four-way state branch with a fixed Slack reply per branch.

## When this reference applies

A scheduled cron job prompt is structured around these four branches:

| PR state | Branch action | Slack post shape |
|---|---|---|
| `state == "MERGED"` | Stop. Post the literal closeout sentence from the cron prompt. | One-line terminal ack. |
| Checks red (one or more `conclusion: FAILURE`) | Fetch the failing job log via `gh api repos/<O>/<R>/actions/jobs/<job_id>/logs`, identify the failing step's assertion text or stderr line, post a fix recipe. | Multi-bullet: failing check name + the relevant error line(s) + proposed fix. |
| Checks green AND review approved AND not merged | Summarize final state (mergeable, reviewDecision, total checks, last failing→green transition). Detect Skeptic / merge-automation state (see "Skeptic state detection" below) and report whether auto-merge will fire. | One-paragraph "ready to merge" summary, flag for `MERGE APPROVED`. |
| Still `IN_PROGRESS` (some `conclusion: null` or `state: PENDING`) | Count completed vs total. Post `PR #N still rolling, [N/M] checks green`. | One-line progress note. |
| **Checks red with NON-CODE root cause** (CodeRabbit plan-level rate-limit; MCP smoke transient infra failure; Bugbot `cursor[bot]` usage limit; self-hosted runner 503 timeout) | **Wait for the external signal to clear — DO NOT propose code fixes.** Wait+escalate protocol (see "Wait+escalate protocol" below). At the cron prompt's specified timeout, post ONE escalation. | Multi-bullet: which external signal is blocking + what the expected resolution path is + that no operator action is possible until it clears. |
| **Prompt-stated SHA is no longer the head (head-advance-while-cron-was-armed)** — verified 2026-07-23 on PR #8488 | Report on the *current* head, not the SHA in the cron prompt. Cron prompt's "is `<sha>` green?" question is now ambiguous; the new head may have already healed the issue. | Multi-bullet: current head SHA, head-vs-prompt delta, what the current gates say, why the cron-stated SHA's gate data is stale. |

This 6th row is the **observer-side head-advance trap** — verified 2026-07-23 on PR #8488 ($GITHUB_REPOSITORY, trim commit `3f9f6a67a`). The cron prompt was armed with a specific SHA (the V1-bag trim commit). When the cron tick ran ~20 min after the trim push, two follow-up `ci: re-trigger` empty commits had already landed on the same branch (`a9ec71e5` and `b8595275`), each triggering its own auto-cancel/supersede cycle on the trim commit's Green Gate runs. The trim commit's `Green Gate Precheck (Gates 1-6)` had failed (`GATE-6b FAIL: PR description gate rejected PR body`), but the *current* head's Precheck had already PASSED. Reporting on the trim commit's gate state would have falsely alarmed the operator that the PR was red — when the actual state was "trim pushed, two follow-up commits healed the validator, current head is green."

The counterpart worker-side trap is already documented in v1.8.0 of the parent skill (`references/head-advance-no-green-gate-redispatch.md`); the observer-side equivalent needs the same treatment because the cron self-check is a different code path. It uses `gh pr view`, not `ao session ls`, and the staleness window is bounded by the cron tick interval, not by AO poll cadence.

## Phase 0 — Pre-flight (do FIRST)

Four checks, in this order:

1. **Get the CURRENT head SHA, not the SHA in the prompt.** The prompt's SHA may be stale by the time the cron tick fires. The cron is observing a moving target.

   ```bash
   # Pass 1: current head
   ACTIVE_HEAD=$(gh pr view <N> --repo <OWNER>/<REPO> --json headRefOid --jq '.headRefOid')
   # If the prompt stated a SHA, compare:
   echo "Cron prompt SHA: <prompt-stated-sha>"
   echo "Active head:      $ACTIVE_HEAD"
   if [ "$ACTIVE_HEAD" != "<prompt-stated-sha>" ]; then
     echo "HEAD ADVANCED — prompt SHA is stale. Reporting on current head, not prompt-stated SHA."
   fi
   ```

   When `ACTIVE_HEAD != <prompt-stated-sha>`, the cron is now in the "head-advance-while-cron-was-armed" branch (see the 6th row above). On PR #8488 the gap was 2 commits (the trim commit + two follow-up `ci: re-trigger` commits).

2. **Get PR state.** Try `gh pr view <N> --repo <O>/<R> --json state,statusCheckRollup,mergeable,reviewDecision` first. **If GraphQL returns `rate limit already exceeded`**, fall back to REST (verified live 2026-07-16 — the user's `jleechan2015` account was rate-limited on GraphQL, REST endpoints stayed usable):

   ```bash
   TOKEN=$(gh auth token 2>/dev/null)
   # PR metadata (state, merged, draft, mergeable)
   curl -fsS -H "Authorization: token $TOKEN" \
     "https://api.github.com/repos/<O>/<R>/pulls/<N>" | python3 -c \
     "import json,sys; d=json.load(sys.stdin); print(f\"state={d['state']} merged={d['merged']} mergeable={d['mergeable']}\")"

   # Check-runs on the CURRENT head SHA (use `head.sha` from the previous response)
   curl -fsS -H "Authorization: token $TOKEN" \
     "https://api.github.com/repos/<O>/<R>/commits/<HEAD_SHA>/check-runs?per_page=30" | python3 -c \
     "import json,sys; rs=json.load(sys.stdin)['check_runs']; \
      print('total:', len(rs)); \
      [print(f\"  {r['conclusion'] or r['status']:>10s}  {r['name']}\") for r in rs]"

   # Reviews (last review's state)
   curl -fsS -H "Authorization: token $TOKEN" \
     "https://api.github.com/repos/<O>/<R>/pulls/<N>/reviews" | python3 -c \
     "import json,sys; rs=json.load(sys.stdin); print('latest review:', rs[-1]['state'] if rs else 'NONE')"
   ```

   Always probe the rate limit FIRST so you don't waste a tool call:
   ```bash
   curl -sS -H "Authorization: token $TOKEN" https://api.github.com/rate_limit | python3 -c \
     "import sys,json; d=json.load(sys.stdin)['resources']; print(f\"core={d['core']['remaining']}/5000 graphql={d['graphql']['remaining']}/5000\")"
   ```
   When `graphql=0` and `core>0`, switch everything else to REST.

3. **If `state == "MERGED"` → post the literal closeout sentence and stop.** Do not proceed to fetch logs, do not re-classify. The cron was structured this way on purpose.

4. **If check-runs surface includes `conclusion == "FAILURE"`** on a your-project.com-style PR, the failing checks are usually one or more of: `Design Doc Grep Gates` (Gate-0 — PR body lacks `## Tenets`/`## Design Decision` section), `Green Gate Precheck (Gates 1-6)` (parent rollup of precheck gates), `<shard-name>` (real test failure in `$PROJECT_ROOT/tests/*.py`). Each has a different fix recipe — see "Failing-check classification" below.

5. **Head-advance cross-check (new 2026-07-23).** When check-runs on the current head show failures, also fetch the check-runs on the prompt-stated SHA. If the prompt-stated SHA's check-runs are MORE recent or DIFFERENT in status (e.g. cancelled/superseded), the cron is observing the aftermath of a head-advance cycle. Report both:

   ```bash
   curl -fsS -H "Authorization: token $TOKEN" \
     "https://api.github.com/repos/<O>/<R>/commits/<prompt-stated-sha>/check-runs?per_page=10" | python3 -c \
     "import json,sys; rs=json.load(sys.stdin)['check_runs']; \
      print('prompt-stated SHA:', sum(1 for r in rs if r['conclusion'] == 'success'), 'success,', \
      sum(1 for r in rs if r['conclusion'] == 'failure'), 'failure,', \
      sum(1 for r in rs if r['conclusion'] == 'cancelled'), 'cancelled')"
   ```

   On PR #8488 the prompt-stated SHA (`3f9f6a67a`) had 4 failures + 3 cancelled (the auto-cancel/supersede chain); the current head (`b8595275`) had 0 failures + 2 success + 11 queued. The right Slack post: "Trim commit was no longer the head — 2 follow-up re-trigger commits had landed. Current head `b8595275` shows Green Gate Precheck PASS; only directory tests still queued."

## Observer-side head-advance trap (NEW 2026-07-23 — PR #8488 cron self-check)

**The trap:** a cron self-check prompt is armed with a specific SHA (e.g. *"verify commit `3f9f6a67a` is green within 30 min of push"*). The tick fires. `gh pr view` returns `headRefOid` = a *different* SHA. The prompt-stated SHA's check-runs are a mix of `success`, `failure`, and `cancelled` because push events to the branch triggered auto-cancel/supersede of the in-flight runs. The observer-facing question "is this commit green?" is now ambiguous — the commit's last check-run is `cancelled` (intermediate state during head-advance), not `success` (truly green) and not `failure` (truly red).

**Symptom pattern (verified 2026-07-23, PR #8488):**

- Cron prompt listed the trim commit `3f9f6a67a` as the "head" to verify.
- 20 min after the trim push, two follow-up `ci: re-trigger` empty commits had landed on `feat/god-mechanics-v2` for unrelated Gate-6b body-validation fixes.
- Each follow-up push triggered `pull_request`-based re-runs on the new SHA AND auto-cancelled the previous SHA's in-flight runs.
- The trim commit's `Green Gate Precheck (Gates 1-6)` had a window of "FAIL at 23:30:15Z" (real `GATE-6b FAIL: PR description gate rejected PR body`) → "CANCELLED at 23:42:42Z" (superseded by the next follow-up's Green Gate).
- The current head `b8595275` had `Green Gate Precheck (Gates 1-6)` = `success` at 23:43:52Z (the follow-up commit's body restructured the PR body to satisfy the validator).

**What the cron self-check should report:**

The prompt-stated SHA's gate state is STALE; the current head is the source of truth. The Slack post should:

1. **Acknowledge the head-advance.** Open with: "The trim commit `3f9f6a67a` is no longer the head. Current head is `<new-sha>`."
2. **Show the head-vs-prompt delta.** List the commits between the prompt-stated SHA and the current head: `git log --oneline <prompt-stated-sha>..HEAD`. Usually 1-3 `ci: re-trigger` empty commits; the substantive scope is the one in the prompt.
3. **Report on the CURRENT head's gates.** `Green Gate Precheck = success` or `failure` based on the current head, not the prompt-stated one.
4. **Explain the prompt-stated SHA's cancelled/failure readings.** "Trim commit's `Green Gate Precheck = cancelled` because the follow-up commits' pushes auto-superseded the in-flight runs. The intermediate `failure` conclusion at 23:30:15Z was a real `GATE-6b FAIL` on the trim commit's PR body, **healed by the follow-up commit `<new-sha>`** which restructured the body to satisfy the validator."
5. **Flag whether the original PR scope is still the same.** If the follow-up commits are only `ci: re-trigger` empty commits with no scope change, the substantive PR is the same — the trim still landed cleanly. If the follow-up commits alter scope, the cron should report the scope change.

**What the cron self-check should NOT do:**

- ❌ Report the prompt-stated SHA's `cancelled`/`failure` as ground truth — it's stale.
- ❌ Report the current head's `queued` checks as "PR is unstable" without context — they're queued behind the self-hosted runner pool, not failing.
- ❌ Confuse `mergeStateStatus: UNSTABLE` (GitHub's render of "head advanced, settling") with a real merge conflict (`mergeStateStatus: DIRTY`).
- ❌ Push retrigger commits — the cron is observe-only. The follow-up commits already happened; the only question is whether to wait for the current head to finish.

**Why this matters for the operator:** the operator armed the cron with a specific SHA to verify their fix landed clean. If the cron reports "trim commit `3f9f6a67a` Green Gate Precheck = failure" without revealing that the head has advanced, the operator will investigate the wrong code path. The right shape is: "trim pushed, post-push validator healed by 2 follow-up empty commits, current head green."

**Diagnostic recipe (cheap, runs in ~2s):**

```bash
# 1. Compare prompt-stated SHA to current head
ACTIVE_HEAD=$(gh pr view <N> --repo <O>/<R> --json headRefOid --jq '.headRefOid')
echo "Cron prompt SHA: <prompt-stated-sha>"
echo "Active head:      $ACTIVE_HEAD"

# 2. Count commits between them (zero = no advance; 1-3 = empty re-triggers; >5 = scope change)
ADVANCE_COUNT=$(gh api repos/<O>/<R>/compare/<prompt-stated-sha>...$ACTIVE_HEAD --jq '.total_commits')
echo "Commits between: $ADVANCE_COUNT"

# 3. Sample the new commits — if all messages are "ci: re-trigger" or "ci: refresh",
#    the follow-ups are empty (no scope change). If substantive messages appear,
#    the cron prompt's scope was amended.
gh api repos/<O>/<R>/compare/<prompt-stated-sha>...$ACTIVE_HEAD --jq '.commits[] | "\(.sha[:10]) \(.commit.message | split("\n")[0])"'
```

**Verification:** on PR #8488 the diagnosis was `ADVANCE_COUNT=2, both messages "ci: re-trigger ..."`, the substantive trim commit was the prompt-stated SHA, and the current head's Green Gate Precheck was `success`. The Slack post correctly reported: "trim commit live + 2 follow-up validator-heal commits; current head green; only directory tests still queued behind the self-hosted runner pool."

**Anti-pattern — reporting on the prompt-stated SHA only:** a cron that runs `gh pr checks <N> --json ...` without first checking `headRefOid` will pick up the auto-cancelled run data from the prompt-stated SHA and report a false RED. The fix is the 5-step Phase 0 cross-check above (current head + prompt-stated SHA + git log delta). Always compare both before composing the Slack post.

## Failing-check classification (verified 2026-07-16, your-project.com)

When the cron prompt says "If red, fetch the failing job log and propose a fix," the recipe needs to handle three structurally different failure classes. **Identifying the class is what makes the post useful; the raw log line is just the symptom.**

1. **Gate-0 `Design Doc Grep Gates`** — failure message always starts `❌ Gate 0 FAIL: PR has N non-test delta lines (>50) but lacks a Tenets / Design Decision section`. Fix: add a `## Tenets` section to the PR body linking a bead (`rev-xxxx`) or roadmap doc. **NOT a code defect.** Verify the parent branch's PR body via REST (`curl ... /pulls/N | python3 -c "import sys,json; print(json.load(sys.stdin)['body'])"`) after the GraphQL fallback above. Confirmed on PR #8418 2026-07-16.

2. **`Green Gate Precheck (Gates 1-6)`** with downstream sub-gate failures visible in `conclusion`: the precheck log has lines like `GATE-3 FAIL: CR=FAIL(CHANGES_REQUESTED)`, `GATE-6 FAIL: evidence required but no evidence link found`, `GATE-6b FAIL: PR description gate rejected PR body`. Fetch the full log and grep:
   ```bash
   TOKEN=$(gh auth token)
   curl -fsS -H "Authorization: token $TOKEN" \
     "https://api.github.com/repos/<O>/<R>/actions/jobs/<JOB_ID>/logs" \
     | grep -E "GATE-[0-9]+(b)? (PASS|FAIL|SKIP)" | head -20
   ```
   Each `GATE-N FAIL` line names the exact sub-condition. The fix is mechanical: CodeRabbit CHANGES_REQUESTED → address the nitpicks; GATE-6 → add evidence link to PR body; GATE-6b → run `python3 .github/scripts/pr_description_gate.py` locally and patch the body to satisfy its rules.

3. **`<shard-name>` (e.g. `Directory tests (core-mvp-1(self hosted))`)** — real pytest failure. The log shows the failing test name + assertion lines. To find the exact failing test inside the noisy per-shard log:
   ```bash
   curl -fsS -H "Authorization: token $TOKEN" \
     "https://api.github.com/repos/<O>/<R>/actions/jobs/<JOB_ID>/logs" \
     | grep -E "FAILED|^E |AssertionError|assert " | head -30
   ```
   pytest output is interleaved with the harness's own per-test `Running test: ...` log lines, so a focused grep is essential. On PR #8418 2026-07-16 the failing test was `test_schema_cache_stale_re_triggers_refresh` — grep pattern `^E |AssertionError|✗ test_` was sufficient. The `FAILURES` header block from pytest appears truncated in many shards because the harness's per-test logger interleaves between test lines, so the standard pytest output ordering (`================== FAILURES ==================`) may be visible but the assertion details may be split. Workaround: read the test function body from the repo at HEAD SHA via REST (`curl /contents/<path>?ref=<sha>`), reproduce the assertion logic locally to confirm the failure surface.

## CR review comment parsing (jleechanorg CodeRabbit format)

When `reviewDecision == "CHANGES_REQUESTED"`, the actionable content is on `/repos/<O>/<R>/pulls/<N>/reviews` (last item's `body`) — NOT in `/comments`. The body has a structured shape:

```
**Actionable comments posted: 6**

<details><summary>🧹 Nitpick comments (4)</summary><blockquote>
<details><summary>$PROJECT_ROOT/tests/test_bq_logging.py (1)</summary><blockquote>
`350-386`: _🎯 Functional Correctness_ | _🔵 Trivial_ | _⚡ Quick win_
**Assert that failed refreshes actually omit every gated field.**
[full comment body]
```

The actionable items are the bolded titles inside each `<details>` block; count them with `grep -c '<summary>.*\.py ('` over the review body. For each nitpick, the file:line range (`350-386`) and the bolded title are sufficient to draft a fix — you don't need to read every embedded `<details>` block.

The `/comments` endpoint is for inline PR-level comments (e.g. `cursor[bot]` usage-limit notices, `github-actions[bot]` coverage reports, `chatgpt-codex-connector[bot]` automated suggestions). CodeRabbit's actual review lives in `/reviews` with `state: "CHANGES_REQUESTED"`.

## Phase 0.5 — Self-cancel applies here too

When the prompt says "post X and stop," the cron itself is one-shot (most common: `--delete-after-run` on `hermes cron create --at`). No further ticks fire. But if the cron is recurring (`--every N` with no `--delete-after-run`), and the post includes the literal terminal token from the cron prompt, the next tick will see the same state and re-post the same message — duplicate closeouts. Always inspect the cron creation flags. If recurring with no `--delete-after-run`, add the self-cancel after the closeout: `hermes cron remove $CRON_JOB_ID`.

**Verified 2026-07-24, PR #8561 followup cron (`8ab9637de843`):** three recipes one-shot status crons WILL hit and the prompt body usually doesn't cover:

1. **`$CRON_JOB_ID` is NOT exported into the cron run-env.** The prompt template's `Use $CRON_JOB_ID env var (set by the runner) to self-cancel` assumes the runner populates it. Verified on the 2026-07-24 20-min status tick: `echo $CRON_JOB_ID` returned empty. The cron source-of-truth is `~/.hermes/cron/jobs.json` — find the job by `name` (e.g. `PR#8561 status followup (20m)`) or by matching the `deliver` field (`slack:<channel>:<thread_ts>`). The discovery pattern:
   ```bash
   python3 -c "
   import json
   d = json.load(open('$HOME/.hermes/cron/jobs.json'))
   for j in d['jobs']:
       if '<topic>' in j.get('name','') or j.get('deliver','') == 'slack:<chan>:<thread_ts>':
           print(j['id'], j['name'])"
   ```
2. **`hermes cron remove <id>` may fail with `bad interpreter: No such file or directory` if the operator's venv is broken.** The `$HOME/.local/bin/hermes` wrapper is a `$HOME/projects_other/hermes-agent/.venv/bin/python` shebang, and that venv's `python` symlink points to `$HOME/.local/share/uv/python/cpython-3.13.9-macos-aarch64-none/bin/python3.13` — which may not exist on the operator's machine (verified on 2026-07-24 after a uv migration). When `hermes cron remove` fails with that error, the direct-edit fallback is:
   ```bash
   python3 -c "
   import json
   path = '$HOME/.hermes/cron/jobs.json'
   d = json.load(open(path))
   d['jobs'] = [j for j in d['jobs'] if j['id'] != '<id>']
   json.dump(d, open(path, 'w'), indent=2)
   print('removed; remaining:', len(d['jobs']))"
   ```
   The file is plain JSON with a stable `jobs: [...]` schema (one row per job); the contract is `id` is the unique key. Hit count of remaining jobs is the verification. Do NOT use this on launchd-managed crons — only JSON jobs where the gateway is the source of truth.

3. **Cron-runtime Slack delivery uses `HERMES_SLACK_BOT_TOKEN`, not `mcp__slack__conversations_add_message`.** The MCP tool is not surfaced in cron runtime (verified 2026-07-24). The cron prompt's `mcp__slack__conversations_add_message(channel_id=..., thread_ts=...)` instruction is unreachable. The working primitive is a Python `urllib.request` `POST` to `chat.postMessage` with bearer auth:
   ```python
   import json, urllib.request, os
   req = urllib.request.Request(
       "https://slack.com/api/chat.postMessage",
       data=json.dumps({"channel": "<chan>", "thread_ts": "<ts>", "text": "<msg>"}).encode("utf-8"),
       headers={"Authorization": f"Bearer {os.environ['HERMES_SLACK_BOT_TOKEN']}",
                "Content-Type": "application/json; charset=utf-8"},
       method="POST",
   )
   data = json.loads(urllib.request.urlopen(req, timeout=30).read())
   # verify: data["ok"] == True, data["ts"] is the new msg id, data["message"]["thread_ts"] == "<ts>"
   ```
   IMPORTANT: the message will post under the **MCP Agent Mail bot identity** (`U0A4G7LDJ4R` / `app_id A0A3WSV6BM1`, `bot_profile.name = "MCP Agent Mail"`), NOT the canonical Hermes bot identity (`U0AEZC7RX1Q`). The `HERMES_SLACK_BOT_TOKEN` is associated with the MCP Agent Mail Slack app on this operator's workspace. This is the cron-runtime contract — different from the `prefer-builtin-slack-mcp` COMMIT which applies to interactive sessions, not cron ticks. If the operator's mental model is "Hermes says X", the cron posts will appear as "MCP Agent Mail says X" in the thread.

## Skeptic state detection (verified 2026-07-19, your-project.com PR #8455)

When a PR is green-but-not-merged, the next question is "**why hasn't it auto-merged?**" Three shapes are possible on `jleechanorg/*` repos, and the cron needs to detect which one applies so the Slack post correctly distinguishes "auto-merge will land it" from "human must click":

| Skeptic state | Detection | Implication for cron post |
|---|---|---|
| Skeptic cron active + dispatched | Look for `<!-- skeptic-gate-verdict -->` comment with `skeptic-cron-trigger-${SHA}` marker. If `VERDICT: PASS` already on the PR, auto-merge will fire shortly. | "PR #N 7-green, skeptic PASS — auto-merge imminent, no action needed." |
| Skeptic cron active, verdict pending | Same as above but no verdict comment yet for current SHA. | "PR #N 7-green ≥N min, awaiting Skeptic verdict (≤30 min). Auto-merge will fire on PASS." |
| **Skeptic workflow present but `disabled_manually`** (verified 2026-07-19 on PR #8455) | `gh api repos/<O>/<R>/actions/workflows?per_page=100 --jq '.workflows[] \| select(.name \| test("skeptic"; "i")) \| select(.state == "disabled_manually")'` returns 1+ rows. The launchd-managed skeptic-auto-merge (`ai.hermes.schedule.skeptic-auto-merge.plist`) is also NOT running on this machine (verify with `ls ~/Library/LaunchAgents/ | grep skeptic`). | **🔴 Human merge required.** Skeptic cron is off, no auto-merge daemon — the merge button is the operator's. The Slack post MUST say "skeptic-cron is disabled_manually, no auto-merge" and explicitly request `MERGE APPROVED`. **Do not just say "ready to merge"** — that's misleading. |

Detection recipe (cheap, runs in ~1s):

```bash
# Are skeptic workflows disabled in the repo?
DISABLED=$(gh api "repos/<O>/<R>/actions/workflows?per_page=100" \
  --jq '[.workflows[] | select(.name | test("skeptic"; "i")) | select(.state == "disabled_manually")] | length')

# Is a launchd skeptic-auto-merge daemon installed?
LAUNCHD=$(ls ~/Library/LaunchAgents/ 2>/dev/null | grep -c skeptic-auto-merge)

if [ "$DISABLED" -gt 0 ] && [ "$LAUNCHD" -eq 0 ]; then
  echo "MERGE_NEEDS_HUMAN: skeptic workflow disabled_manually and no launchd daemon"
fi
```

**This pitfall is load-bearing:** a cron that just says "PR #N ready to merge" when skeptic is disabled will silently wait for auto-merge that will never come. The user comes back hours later to find the PR still open. Verified live 2026-07-19 on PR #8455 (thread `C0BDEAJH8PK/1784447975.997199`): 7-gate rollup was green, but `gh api .../actions/workflows?per_page=100` showed `265950193 Skeptic Self-Verify (disabled_manually)` + `266061222 Post Skeptic Verdict (one-shot) (disabled_manually)`, and no launchd skeptic daemon was installed locally. The cron MUST report this in the Slack post so the operator knows their click is required.

**Anti-pattern:** saying "ready to merge" + flagging for `MERGE APPROVED` without explaining *why* it's not auto-merging. The user has to read the entire thread to figure out the blocker. Always name the blocker explicitly in the Slack post.

## Wait+escalate protocol (verified 2026-07-20, your-project.com PR #8462)

When the checks are RED but the root cause is an EXTERNAL SIGNAL the agent cannot unblock — CodeRabbit plan-level rate-limit, MCP smoke transient infra, Bugbot `cursor[bot]` usage cap, self-hosted runner 503 — the cron MUST follow the wait+escalate protocol instead of the "Red: post fix recipe" branch. Posting a code-fix recipe is **actively harmful** because it tells the user to modify code when no code change is needed; the user wastes cycles investigating a non-defect.

### How to detect "external signal, not code defect"

The four shapes that look like RED but aren't:

| External signal | Detection | Why it's not code-fixable |
|---|---|---|
| CodeRabbit plan-level rate-limit | `gh api repos/<O>/<R>/commits/<sha>/status` shows `context=CodeRabbit state=failure description="Review rate limited"`. Also visible as Green Gate Precheck `GATE-3 FAIL: CR=FAIL(status=failure comment=none)`. | CodeRabbit's account-level rate limit clears on its own. Per `env-preferences.mdc` 2026-07-16 rule, the agent MUST NOT manually re-trigger a CR review — wait for the natural retry. |
| Bugbot `cursor[bot]` usage limit | `cursor[bot]` posts `<h3>Bugbot couldn't run - usage limit reached</h3>` as an issue comment. Green Gate Precheck may show `GATE-3 PASS` because CR is the primary reviewer signal. | Cursor account-level cap. Not a code defect; no agent action available. |
| MCP Smoke Tests `[Preview E2E]` transient infra failure | Workflow run log shows `❌ MCP Smoke Tests Failed ... Reason: No deployed GCP preview service was found for this PR head SHA` OR a self-hosted runner 503 timeout. | Preview slot rotation, or transient runner unavailability. Push an empty commit to retrigger (`git commit --allow-empty -m "<reason>" && git push`), or wait for the next rotation. |
| Self-hosted runner 503 timeout | Per `gh-actions-transient-failure-diagnosis`, an HTTP 503 from `actions/github-script` in a workflow step looks like a step failure but is infra. | Push empty commit to retrigger, or `gh run rerun`. The PR code is unchanged. |

### Decision rule

**Default to wait+escalate when ALL of:**
- Code-side checks (unit, lint, type, mypy, ruff, eslint) all PASS in the latest run.
- The failing check's `description` field names an external system (`Review rate limited`, `Bugbot couldn't run - usage limit reached`, `No deployed GCP preview service was found`, `503 Service Unavailable`).
- The PR has not been touched (no new commits since the failing run started).

If ANY of the above is false, fall through to the "Red: post fix recipe" branch.

### Wait+escalate cadence

1. **First tick (T=0)**: detect external-signal root cause. Post ONE message to the thread: `⏳ PR #<N> waiting on <signal name> — cannot auto-unblock. Will escalate at T+<cron prompt's specified timeout>.`
2. **Mid ticks (T+5min, T+10min, ...)**: poll REST for status change. Do NOT post to Slack on each mid-tick — silence is correct when nothing changed. The cron playbook's `[SILENT]` contract applies.
3. **Final tick (T+<cron prompt's specified timeout, typically 30m)**: if still red, post ONE escalation: `🔴 PR #<N> still not merged (<elapsed> min). Current state: <state>. Blockers: <list>. Manual intervention needed: <suggested action>.`
4. **Always self-cancel after the final escalation** via `hermes cron remove $CRON_JOB_ID`. The babysit has done its job; no further ticks should fire.

### Verification

Verified 2026-07-20 on PR #8462 ($GITHUB_REPOSITORY, thread `C0BCVG4F560/1784219487.851579`):
- T=0 detected: `CodeRabbit state=failure description="Review rate limited"`, Green Gate Precheck failing on GATE-1 (CI=failure, inherits CR) and GATE-3 (CR=FAIL); Gates 2/5/6/6b all PASS; MCP Smoke Tests [Preview E2E] ✅ SUCCESS.
- Mid ticks T+5min, T+10min, ..., T+25min: polled REST, no state change, no Slack post (correctly silent per cron playbook).
- Final tick T+30min: posted escalation to thread `C0BCVG4F560/1784219487.851579` with the explicit blocker list and the manual-intervention suggestion (wait for CR rate-limit to clear, then re-trigger Green Gate via workflow_dispatch since Gates 6/6b already PASS and `OVERRIDE_EVIDENCE_GATE=ok` won't help).
- Self-cancel: `hermes cron remove a679edc9079d` → `Removed job: babysit-pr-8462-green (one-shot, fires once at +30m) (a679edc9079d)`.

The user's followup cron `verify-pr-8462-rollout` (separate one-shot, schedule `once in 24h`) was already armed to verify post-merge rollout — so the babysit can exit without losing monitoring coverage.

### Anti-patterns

- **Don't propose code fixes when the failure is an external rate-limit.** Telling the user "add evidence to Gate-6" or "fix the lint error" when the actual cause is `Review rate limited` wastes their time and erodes trust in the babysit's signal.
- **Don't poll Slack every tick.** A 30-minute babysit that posts 5 "still waiting on CodeRabbit" messages to the thread is worse than one that posts zero mid-ticks and one escalation at the end.
- **Don't re-trigger CR review manually.** Per `env-preferences.mdc` 2026-07-16: when `CodeRabbit state=failure description="Review rate limited"`, the agent MUST wait. Triggering a manual review either fails (same rate-limit) or, worse, consumes the user's paid CR quota to bypass a temporary cap.
- **Don't skip the final self-cancel.** A babysit that escalates correctly but leaves the cron enabled will keep ticking on the same RED state and posting duplicate escalations every interval.

## Phase 3 — Single Slack message shape

The cron prompt usually specifies the exact wording. Otherwise, the canonical shape is:

- **Merged:** one-line terminal ack, no body, no proof needed beyond the PR URL.
- **Red (code defect):** 4-6 bullets — (1) failing check name + run URL, (2) the failing log line verbatim (one or two lines max), (3) the failing-class identification (Gate-0 / Gate-3 / test shard), (4) proposed fix in one sentence, (5) PR URL + state line. Avoid multi-page dumps of the log.
- **Red (external wait):** see "Wait+escalate protocol" above — single mid-tick message + one final escalation at T+<timeout>. NO code-fix recipe. Always name the external signal explicitly.
- **Green-not-merged:** one-paragraph state summary + explicit flag for `MERGE APPROVED`. Include `mergeable`, `reviewDecision`, total check count, last failing→green transition.
- **In-progress:** single line — `PR #N still rolling, [N/M] checks green.` Include the PR URL. Do not re-list every check name (that becomes noise).
- **Head-advance (NEW 2026-07-23):** see "Observer-side head-advance trap" above — open with "the prompt-stated SHA is no longer the head," report on the current head, explain the head-vs-prompt delta, flag whether the original PR scope is still the same.

## Pitfalls

- **Don't trust `gh pr view --json` when GraphQL is rate-limited.** Use the REST fallback recipe in Phase 0. Always probe the rate limit FIRST so you don't waste a tool call.
- **Don't fail to check `headRefOid` against the prompt-stated SHA (NEW 2026-07-23).** On PR #8488 the cron prompt's SHA was 2 commits behind the head by the time the tick ran. Always cross-check. See the "Observer-side head-advance trap" section above.
- **Don't post the failing log as a wall of text.** 1-2 lines verbatim, plus the class identification, is enough.
- **Don't re-classify a merged PR.** If `state == MERGED`, post the literal closeout sentence and stop. Even if you also notice "checks are red on the last green run before merge," that's irrelevant — the PR is merged.
- **Don't include the bead ID from the cron prompt verbatim in a non-merged post.** The cron prompt typically has a literal closeout sentence for the MERGED branch; preserve it verbatim. The non-merged branches should NOT mention beads — beads close on merge, not on green.
- **Don't fetch the body of `/comments` for the CodeRabbit CHANGES_REQUESTED details.** The actionable content is on `/reviews` (last item's body).
- **CR review body is structured but verbose.** Grep for `<summary>` to count actionable items, then extract just the file:line range and bolded title for each. Don't try to parse the embedded `<details>` blocks.
- **PR body in REST response contains literal LF/CR.** When parsing `curl ... /pulls/N | python3 -c "import json,sys; json.load(sys.stdin)"` and the body is multi-paragraph Markdown, `json.loads` rejects with `json.decoder.JSONDecodeError: Invalid control character`. Use the `gh_safe_json_loads()` helper from `scripts/gh_pr_json.py` in the parent skill, or pipe through `sed 's/[\x00-\x1f]/?/g'` before parse.
- **CR review `body` field can also have LF/CR.** Same parse pitfall applies — read the body field via `gh_safe_json_loads()` or extract just the bolded titles with `grep -oE '\*\*[^*]+\*\*'`.
- **`curl ... | python3 -c "json.load(sys.stdin)"` "Invalid control character" can be a truncation red herring (verified 2026-07-16, disk_magician PR #21).** When the curl-and-pipe form fails with `json.decoder.JSONDecodeError: Invalid control character at: line N column M (char K)`, the actual cause may NOT be LF/CR in the body — it may be that the response was silently truncated mid-stream by the shell pipeline. Diagnostic: rerun with `curl ... -o /tmp/out.json` and check `ls -la /tmp/out.json` — if the file size is far smaller than expected (e.g. 597 bytes for a PR with full body, when the canonical response is 12–25 KiB), the pipe form was cutting off. The fix is always the file-first pattern, not `gh_safe_json_loads()`:

  ```bash
  TOKEN=$(gh auth token 2>/dev/null)
  rm -f /tmp/prN.json
  curl -fsS -H "Authorization: token $TOKEN" \
    "https://api.github.com/repos/<O>/<R>/pulls/<N>" -o /tmp/prN.json
  ls -la /tmp/prN.json   # sanity: should be ~10-25 KiB for a real PR
  python3 -c "import json; d=json.load(open('/tmp/prN.json')); print(d['state'], d['merged'], d['mergeable'])"
  ```

  Or for crons that want minimal memory pressure, use the parent skill's `gh_pr_json.py --state-only` CLI:

  ```bash
  python3 ~/.hermes/skills/devops/babysit-ao-pr-loop/scripts/gh_pr_json.py --state-only "$(gh auth token)" <O>/<R> <N>
  # → PR #21 [jleechanorg/disk_magician] state=open merged=False mergeable=True
  ```

  Distinguishing signal: if `wc -c /tmp/out.json` reports the file is well under 1 KiB for a known-large response, the pipe form truncated — NOT a JSON control-char issue. The "Invalid control character" error message is misleading because it points at the parser position at end-of-stream, not at a real control char in the body.
- **Bugbot `cursor[bot]` comment failure modes look like CodeRabbit failures but aren't.** If you see `<h3>Bugbot couldn't run - usage limit reached</h3>`, the cursor[bot] account hit a usage cap; this is NOT a code defect. Don't propose a fix; just note that Bugbot didn't run and rely on Gate-3 (CodeRabbit) for the review signal.
- **Unauthenticated `curl https://api.github.com/repos/...` returns 404 for repos visible only to authenticated users (NEW 2026-07-24, PR #8545 cron self-check, thread C0BDEAJH8PK/1784861747.944149).** On `$GITHUB_REPOSITORY`, hitting `curl https://api.github.com/repos/$GITHUB_REPOSITORY/pulls/8545` from an unauthenticated shell returns `{"message":"Not Found"}` with HTTP 404 — the repo exists (verified via `gh pr view 8545 --repo ...` which used the authed token), but the GitHub REST API hides it from anonymous callers. Diagnostic recipe: as soon as you see a 404 on a repo that should exist, immediately try `gh pr view <N> --repo <O>/<R>` (which uses `gh auth token` automatically) before assuming the PR is gone. The first 404 in the cron tick wasted 4 tool calls investigating nonexistent path variations (`/pulls/8545`, `/issues/8545`, repo listing pages, GraphQL search) before re-trying with auth. The fallback chain in Phase 0 must authenticate FIRST (use `TOKEN=$(gh auth token 2>/dev/null)` for the REST `curl` path), not as a last resort. This is a jleechanorg-specific class pattern: many `jleechanorg/*` repos are internal/limited-visibility and 404 to anonymous REST callers.
- **`gh api .../pulls/N` returns `statusCheckRollup: null` even when the check-runs endpoint has full data (NEW 2026-07-24, PR #8545).** When `merge_state_status` and `statusCheckRollup` both come back null from the PR object, the rollup aggregation hasn't materialized yet (or the PR was created very recently — `merge_state_status: null` paired with `mergeable: true` and `statusCheckRollup: null` is the signature). Don't conclude "no checks" — pivot to `curl .../commits/<head_sha>/check-runs?per_page=30` which returns the raw check-run list independently with full `name/status/conclusion/started_at/completed_at/html_url`. Verified live 2026-07-24 on PR #8545 head_sha `1f224e1d`: PR-object rollup was `null`, but the check-runs endpoint returned 32 entries (28 completed + 4 queued). Combined with the unauth-404 pitfall above, the canonical Phase 0 sequence is: (1) `gh pr view --json` (uses auth automatically), (2) if rate-limited OR rollup=null, REST with `gh auth token`, (3) REST `/commits/<sha>/check-runs` for per-check detail.
- **`gh run view --job <id> --log` returns "still in progress; logs will be available when it is complete" for jobs that are completed but whose logs are not visible to the calling account (NEW 2026-07-24, PR #8545).** On PR #8545 Green Gate Precheck job 89390579088 (conclusion=failure, completed), `gh run view --job 89390579088 --log` reported "still in progress" rather than the actual log output. Diagnostic: check `gh run view <run-id> --job <job-id>` (no `--log`) for the per-step conclusion; the failing step's name + conclusion is enough to classify without reading the log. When logs aren't accessible, fall through to: (a) `gh api repos/<O>/<R>/check-runs/<check_run_id>/annotations` for the annotations list (verified earlier on PR #8290 per v1.9.0 of the parent skill), or (b) accept the conclusion-only signal and report the failing check name + run URL. This is also a jleechanorg self-hosted-runner visibility pattern — the cron calling user may not have permission to read logs from runs triggered by other actors.
- **AO DB as authoritative state source when GitHub API access is degraded (NEW 2026-07-24, PR #8545).** When REST endpoints are slow, GraphQL is rate-limited, and `gh run view --log` is inaccessible, the local AO database at `~/.ao/data/ao.db` carries comprehensive PR state. The `pr` table has `pr_state`, `review_decision`, `ci_state`, `mergeability`, `head_sha`, `is_merged`, `provider_merge_state_status` (often `UNSTABLE` when the API rollup is null), and `metadata_hash/ci_hash/review_hash` for change detection. The `pr_checks` table has per-check `name/status/conclusion/details/url` keyed on `pr_url + name + commit_hash`. The `pr_reviews` table has every CodeRabbit/Bugbot approval with `state + submitted_at + body`. The `sessions` table has `id/activity_state/is_terminated/harness/updated_at` for worker liveness. The `pr_comment` table has recent issue comments. This is the canonical fallback for "I can't see the PR from the GitHub side but I need to know its state." Recipe:

  ```bash
  sqlite3 ~/.ao/data/ao.db <<'SQL'
  SELECT url, pr_state, review_decision, ci_state, mergeability,
         head_sha, is_merged, provider_merge_state_status, updated_at
  FROM pr WHERE number = <N>;

  SELECT name, status, conclusion, created_at
  FROM pr_checks
  WHERE pr_url = 'https://github.com/<O>/<R>/pull/<N>'
  ORDER BY created_at DESC LIMIT 20;

  SELECT id, activity_state, is_terminated, harness, updated_at
  FROM sessions
  WHERE id LIKE 'worldarchitect-%' OR id LIKE 'wa-%'
  ORDER BY updated_at DESC LIMIT 10;
  SQL
  ```

  Verified live 2026-07-24 on PR #8545: AO DB had `pr_state=open, ci_state=failing, mergeability=blocked, head_sha=1f224e1d...`, the `pr_checks` table had 15 entries including the cancelled Green Gate Precheck (job 89390579088) and the queued Green Gate (job 89390703915), and the `sessions` table showed `worldarchitect-114 exited/terminated` + `worldarchitect-116 idle` — the actual active worker.
- **Cron-prompt session-id drift: prompt names session X but actual worker is session Y (NEW 2026-07-24, PR #8545).** The cron prompt may hardcode a specific worker session ID (e.g. `worldarchitect-114`) that was correct at spawn time but has since been re-spawned as `worldarchitect-116` after `114` exited. The cron should always source the active session from the AO DB (`SELECT id FROM sessions WHERE id LIKE '<prefix>%' AND is_terminated=0 ORDER BY updated_at DESC LIMIT 1`) rather than echoing the prompt's literal value. Verified live 2026-07-24: cron prompt named `worldarchitect-114`, the actual active session was `worldarchitect-116` (AGY harness, idle since 03:20:35). The Slack post said "Worker is `worldarchitect-116` ... note: the user-referenced `worldarchitect-114` (claude-code) exited at 03:04:20 without merging" — the parenthetical reframe was important for the operator to understand the work-handoff.
- **AO DB `last_nudge_signature` field captures what the babysit already saw (NEW 2026-07-24, PR #8545).** The `pr.last_nudge_signature` JSON column has a `seen` map of `ci:<pr_url>:<check-name>` → `<head_sha>:<last_observed_at>Z <failure-log-tail>` and an `attempts` counter per check. This is the babysit's own memory of which checks it last saw fail and how many times it nudged. Useful for distinguishing "first time I'm seeing this failure" from "the babysit has been here 3 times already, no point re-nudging." Verified live 2026-07-24 on PR #8545: the `seen` map showed `Evidence Gate` had its gist-freshness issue already addressed (gist `3847290122203485198a3089078c56b9dfa5ec37`) and `Green Gate Precheck (Gates 1-6)` had attempt count = 2. For a cron that's been ticking for a while, this is the cheapest signal for "is the failure new or am I re-reporting the same thing?"
- **`$CRON_JOB_ID` is NOT exported into the cron run-env (NEW 2026-07-24, PR #8561).** The cron prompt template's `Use $CRON_JOB_ID env var (set by the runner) to self-cancel` assumes the runner populates it. Verified on the 2026-07-24 20-min status tick: `echo $CRON_JOB_ID` returned empty. The cron source-of-truth is `~/.hermes/cron/jobs.json` — find the job by `name` (e.g. `PR#8561 status followup (20m)`) or by matching the `deliver` field (`slack:<channel>:<thread_ts>`). Discovery pattern:
  ```bash
  python3 -c "
  import json
  d = json.load(open('$HOME/.hermes/cron/jobs.json'))
  for j in d['jobs']:
      if '<topic>' in j.get('name','') or j.get('deliver','') == 'slack:<chan>:<thread_ts>':
          print(j['id'], j['name'])"
  ```
- **`hermes cron remove <id>` may fail with `bad interpreter: No such file or directory` if the operator's venv is broken (NEW 2026-07-24, PR #8561).** The venv `python` symlink at `$HOME/projects_other/hermes-agent/.venv/bin/python` can point to a missing CPython binary (`$HOME/.local/share/uv/python/cpython-3.13.9-macos-aarch64-none/bin/python3.13`) after a uv migration. Direct-edit fallback: `python3 -c "import json; d=json.load(open('$HOME/.hermes/cron/jobs.json')); d['jobs']=[j for j in d['jobs'] if j['id']!='<id>']; json.dump(d, open('$HOME/.hermes/cron/jobs.json','w'), indent=2)"`. Verify by re-reading the file and counting `len(d['jobs'])`. Do NOT use this on launchd-managed crons — only JSON jobs where the gateway is the source of truth.
- **Cron-runtime Slack delivery uses `HERMES_SLACK_BOT_TOKEN`, not `mcp__slack__conversations_add_message` (NEW 2026-07-24, PR #8561).** The MCP tool is not surfaced in cron runtime. The cron prompt's `mcp__slack__conversations_add_message(channel_id=..., thread_ts=...)` instruction is unreachable. The working primitive is `urllib.request` `POST` to `chat.postMessage` with bearer auth (`Authorization: Bearer $HERMES_SLACK_BOT_TOKEN`). IMPORTANT: the post lands under the **MCP Agent Mail bot identity** (`U0A4G7LDJ4R` / `app_id A0A3WSV6BM1`, `bot_profile.name = "MCP Agent Mail"`), NOT the canonical Hermes bot identity (`U0AEZC7RX1Q`). If the operator's mental model is "Hermes says X", the cron posts will appear as "MCP Agent Mail says X" in the thread. This is the cron-runtime contract — different from the `prefer-builtin-slack-mcp` COMMIT which applies to interactive sessions, not cron ticks.

## Worked example: PR #8418 ($GITHUB_REPOSITORY, 2026-07-16)

Cron prompt: "Check PR #8418 status: gh pr view 8418 --json state,statusCheckRollup,mergeable. If state=MERGED, post 'PR #8418 merged — is_test IS NULL race fixed. Bead rev-l27zc closed.' to Slack thread C0BCVG4F560/1784219487.851579 and stop. If checks are green and review approved but not merged, summarize final state. If red, fetch the failing job log (gh run view --log-failed <id>) and post the relevant error line + propose fix. If still IN_PROGRESS, say 'PR #8418 still rolling, [N/M] checks green' with the count of completed checks."

Actual outcome:
1. Phase 0.1 — `gh pr view 8418 --json state,...` returned `GraphQL: API rate limit already exceeded for user ID 13840161.` Pivoted to REST.
2. Phase 0.2 — REST `curl /pulls/8418` returned `state=open merged=false mergeable=MERGEABLE`. NOT MERGED.
3. Phase 0.3 — REST `curl /commits/<sha>/check-runs` returned 36 check-runs. Counted: 24 SUCCESS, 3 FAILURE, 1 NEUTRAL (Bugbot usage-limit), 1 SKIPPED, 7 CANCELLED (superseded retries). RED.
4. Classified the 3 FAILURE checks: `Design Doc Grep Gates` (Gate-0), `Green Gate Precheck (Gates 1-6)` (GATE-3 + GATE-6 + GATE-6b sub-failures), `Directory tests (core-mvp-1(self hosted))` (real test failure).
5. Phase 3 — Posted 4-bullet summary to thread C0BCVG4F560/1784219487.851579: (1) the three failing checks with run URLs, (2) Gate-0 fix recipe, (3) Gate-3/Gate-6/Gate-6b fix recipe, (4) the test failure name + likely fix recipe. PR URL + state line at the end.

Outcome for the cron was correct (RED state, multi-class failure identified, fix recipes posted). One-shot cron — no further ticks expected.

### Worked example: PR #8462 ($GITHUB_REPOSITORY, 2026-07-20, wait+escalate branch)

Cron prompt: "Background babysit task for PR #8462 ... drive it to merged state. ... EVERY 5 MINUTES ... If after 30 minutes no merge has happened: post ONE escalation message to thread ... Then remove this cron via cronjob action=remove job_id=<this-id>. STOP."

Actual outcome (wait+escalate, NOT the code-fix branch):
1. Phase 0.1 — `gh pr view 8462 --json ...` returned full PR data. PR state=open, head_sha=68df3793d8, mergeable=MERGEABLE, mergeable_state=UNSTABLE.
2. Phase 0.2 — Check-runs: MCP Smoke Tests [Preview E2E] ✅ SUCCESS, Green Gate Precheck FAILURE on GATE-1 (CI=failure, inherits CR) and GATE-3 (CR=FAIL); Cursor Bugbot NEUTRAL (usage-limit). All other Gates (2, 5, 6, 6b) PASS. **External-signal root cause detected**: `context=CodeRabbit state=failure description="Review rate limited"`.
3. Wait+escalate protocol: Mid ticks T+5min, T+10min, T+15min, T+20min, T+25min — polled REST, status unchanged, no Slack posts (correctly silent per cron playbook).
4. Final tick T+30min: posted escalation to thread `C0BCVG4F560/1784219487.851579` with the explicit blocker list and the manual-intervention suggestion (wait for CR rate-limit to clear, then re-trigger Green Gate via workflow_dispatch since Gates 6/6b already PASS and `OVERRIDE_EVIDENCE_GATE=ok` won't help).
5. Self-cancel: `hermes cron remove a679edc9079d` → `Removed job: babysit-pr-8462-green (one-shot, fires once at +30m) (a679edc9079d)`.

Notable signal: at the dispatch prompt template level, `cronjob action=remove job_id=<this-id>` was templated, but the actual CLI is `hermes cron remove <id>` per `babysit-ao-pr-loop` v1.3.1 (2026-07-13). The dispatch prompt template still uses the obsolete form — when authoring future babysit cron prompts, use `hermes cron remove $CRON_JOB_ID`. See the v1.3.1 changelog entry in the parent SKILL.md.

Outcome for the cron was correct (wait+escalate branch correctly identified, no false code-fix recipe, single escalation posted at T+30min, cron cleanly self-cancelled). The user's sibling cron `verify-pr-8462-rollout` (separate one-shot, `once in 24h`) was already armed to verify post-merge rollout.

### Worked example: PR #8488 ($GITHUB_REPOSITORY, 2026-07-23, head-advance branch)

Cron prompt: "Self-check on PR #8488 after the V1-bag trim push (head 3f9f6a67abf0ca462d026251de887de713cb3596 on feat/god-mechanics-v2, ~20 minutes from now). [...] Tests already confirmed green pre-push (196/196 OK in 0.634s for divine_prompts_setting_agnostic + test_prompts). Report: (a) current head SHA, (b) reviewDecision, (c) mergeStateStatus, (d) any new GH Actions failures or CodeRabbit / Bugbot comments triggered by the trim, (e) which Green Gate / Directory tests have settled vs still running. Do NOT modify the PR. If everything is green and reviewDecision is APPROVED, say so plainly."

Actual outcome (head-advance branch, not the "is prompt-stated SHA green?" branch):
1. Phase 0.1 — `gh pr view 8488 --json headRefOid` returned `b8595275388ccb8bbdd2d49fc15df42f06c94efe`, NOT the prompt-stated `3f9f6a67a`. **HEAD ADVANCED.**
2. Phase 0.2 — `gh api repos/$GITHUB_REPOSITORY/compare/3f9f6a67a...b8595275` returned `total_commits=2`, both messages `ci: re-trigger ... (anchored Unit Test Evidence)`. Empty validator-heal commits; the substantive scope (the V1-bag trim) was unchanged.
3. Phase 0.3 — `gh pr view 8488 --json state,reviewDecision,mergeStateStatus` returned `state=OPEN, reviewDecision="", mergeStateStatus=UNSTABLE, mergeable=MERGEABLE`. NOT MERGED.
4. Phase 0.4 — Check-runs on the CURRENT HEAD (`b8595275`): `Design Doc Grep Gates = success`, `Evidence Gate = success`, `Green Gate Precheck (Gates 1-6) = success`. 11 still queued (directory tests, coverage, deploy-preview). The precheck had PASSED at 23:43:52Z. NO red on the current head.
5. Phase 0.5 — Check-runs on the PROMPT-STATED SHA (`3f9f6a67a`): `Green Gate Precheck (Gates 1-6) = failure` (real GATE-6b validator miss at 23:30:15Z) + `Green Gate = cancelled` (auto-superseded at 23:42:42Z) + `Bugbot Gate Wait = skipped`. The prompt-stated SHA's gates tell the cancellation story, not the current shape.
6. Phase 3 — Posted 5-section report: (a) current head SHA + committer + headline, (b) reviewDecision="", (c) mergeStateStatus=UNSTABLE / mergeable=MERGEABLE, (d) trim commit's intermediate failure + follow-up heal, (e) Green Gate Precheck PASS on current head + 11 directory tests still queued. Cross-referenced the prompt's "V1-bag trim — 2026-07-23 (head 3f9f6a67ab)" PR-body section.

Outcome for the cron was correct: trim commit `3f9f6a67a` was no longer the head by the time the tick ran. Reporting on the trim commit alone would have falsely alarmed the operator. The right shape is: "trim pushed, 2 follow-up validator-heal commits landed, current head green, only directory tests still queued."

### Worked example: PR #8561 ($GITHUB_REPOSITORY, 2026-07-24, single-PR one-shot status cron)

Cron prompt: "You are a one-time 20-min status followup for PR #8561 ... Slack thread: C0AH3RY3DK6 / ts 1784894152.572209. Every tick (you only run once at +20 min, then auto-delete), do this exact sequence: [gh pr view, gh pr checks, gh api comments verdict check]. Terminal check BEFORE posting: if MERGED → [SILENT]; if CLOSED → one-line warning. Otherwise post one short status message to thread. CRITICAL: self-cancel via `cronjob action=remove job_id=$CRON_JOB_ID`."

Actual outcome (clean one-shot status post):
1. Phase 0.1 — `gh pr view 8561 --json state,...` returned `state=OPEN, headRefOid=8b2e65ac11, mergeable=UNKNOWN, mergeStateStatus=UNKNOWN, reviewDecision=""`. NOT MERGED.
2. Phase 0.2 — `gh pr checks 8561` text output: 13 PASS, 5 FAIL (`Directory tests (core-mvp-1)`, `Directory tests (core-mvp-2)`, `Green Gate`, `Wizard Mobile Scroll/CSS Regression`, `Green Gate Precheck (Gates 1-6)`); 2 PENDING; 19 SKIPPED. RED.
3. Phase 0.3 — `gh api .../comments` for VERDICT: empty (no Skeptic verdict yet).
4. Phase 0.4 — Comment scan: latest comments are `chatgpt-codex-connector[bot]` (usage-limit), `cursor[bot]` (usage-limit), `jleechan2015` (v2 evidence), `coderabbitai[bot]` (rate-limited), `github-actions[bot]` (deploy preview). All reviews either rate-limited or the operator's own post.
5. Phase 3 — Posted the cron prompt's exact format: hourglass emoji + HEAD/state/CI/Review/Evidence bundle/Next. Identified CodeRabbit and Bugbot both rate-limited, three real CI failures (core-mvp-1, core-mvp-2, Wizard Mobile Scroll/CSS Regression), explicit "blocking on 3 real CI failures; cannot yet reach MERGE APPROVED".
6. Phase 0.5a — `echo $CRON_JOB_ID` returned empty (env-var not exported). Fell back to discovery pattern: `python3 -c "import json; ..."` to find `8ab9637de843` by name match.
7. Phase 0.5b — `hermes cron remove 8ab9637de843` failed with `bad interpreter: No such file or directory` (broken venv). Fell back to direct JSON edit: rewrote `~/.hermes/cron/jobs.json` with the job filtered out, verified count `36 → 37 → 1 removed → 37`. Success.

Notable lessons:
- The cron prompt's `Use $CRON_JOB_ID env var (set by the runner)` self-cancel is unreliable — the env var is NOT exported. The source-of-truth is `~/.hermes/cron/jobs.json`.
- The CLI `hermes cron remove <id>` is the documented canonical; when the venv is broken, the direct-edit fallback is the durable path.
- The cron prompt's `mcp__slack__conversations_add_message` instruction is unreachable in cron runtime. The working primitive is `urllib.request` `POST chat.postMessage` with `HERMES_SLACK_BOT_TOKEN`.
- The post lands under **MCP Agent Mail bot identity** (`U0A4G7LDJ4R`), not the canonical Hermes bot. This is the cron-runtime contract distinct from `prefer-builtin-slack-mcp` (which applies to interactive sessions).
- The cron prompt's `gh pr checks ... | tail -40` text output is the simplest PASS/FAIL counter — no need to parse JSON. The text shows `pass/fail/pending/skipping` per line; a quick `grep -c pass`/`grep -c fail` is sufficient.

## Parent skill pointer

`babysit-ao-pr-loop` SKILL.md — Phase 0 terminal-state probe, Phase 0.5 self-cancel (note: v1.3.1 obsoleted `cronjob action=remove` to `hermes cron remove <id>`), Phase 3 single-message-post shape. The six-state branch above (5 documented previously + the new head-advance row added 2026-07-23) is the single-PR, no-worker instance of the same protocol. The worker-side head-advance trap is documented separately at `references/head-advance-no-green-gate-redispatch.md` (v1.8.0 of the parent skill); the observer-side head-advance trap added in this update is the cron-self-check counterpart.
