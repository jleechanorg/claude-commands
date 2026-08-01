---
name: superpowers-cloud-build
version: 1.5.0
description: Use the superpowers-cloud-build plugin to execute committed implementation plans on a remote build box via SSH to cloud.superpowers.build:22. Covers install (Codex side + Claude Code side), enrollment, preflight, hand-off, follow-loop, land-result, and the "git secret guard rejects pushes with sensitive files in the outgoing commit range" blocker that bites any real project with tracked secrets in history. Load whenever the user says "use superpowers cloud", "run this plan on the cloud", "kick off a cloud build", "build this remotely", or after `codex plugin add cloud-build@superpowers-cloud-build` succeeds. Pairs with `drive-pr-to-green` (hand-off does NOT replace inline PR drive; cloud-build is for new work, not /green on existing PRs).
triggers:
  - run this plan on the cloud
  - superpowers cloud
  - cloud build
  - cloud-build
  - build this on the box
  - execute plan remotely
  - cloud_build_handoff
changelog:
  - "1.5.0 (2026-07-20) **Watchdog probe-mismatch fix shipped upstream.** The `cloud-build-bastion-watchdog.sh` script now iterates the three real handoff users (`git@`, `$USER@`, `cloud-build@`) and returns exit=4 when banner users pass but handoff users fail. Verified live on this Mac (exit 4 with the actual banner-OK-but-handoff-fail state). Companion skill `cloud-build-bastion-watchdog` bumped to v1.2.0. Anti-pattern updated from \"future agents must verify\" to \"future agents can trust exit=4 as the canonical signal; exit=0 now means all six probes pass.\" Also added pitfall P6 + P7 to the watchdog skill covering dual-machine enrolled_fp_hash drift and the `/browser` ≠ enrollment-codes misconception."
  - "1.4.0 (2026-07-20) Added `references/bastion-watchdog-handoff-user-mismatch-2026-07-20.md` + a new Anti-pattern entry. The `cloud-build-bastion-watchdog.sh` only probes `cloud-bastion@` and `enroll@` users (which print success banners) but never probes the actual handoff user (`$(whoami)@cloud.superpowers.build` — `$USER@` on this Mac). Result: watchdog exits 0 while every real `/super` dispatch gets `Permission denied (publickey)`. Verified failure on 2026-07-20 22:18 PT — local key fp rotated to `f1c66c1fb3…` after state.json's `enrolled_fp_hash=c709569c7b…`. Companion probe recipe (`ssh -T $USER@cloud.superpowers.build`) added to the reference; future agents MUST probe the real handoff user before trusting the watchdog's exit 0. Follow-up bead to patch the watchdog itself is filed separately."
  - "1.3.0 (2026-07-20) Added `references/slash-command-cross-machine-shape-2026-07-20.md` covering the `/super` (canonical box dispatch) and `/superlight` (legacy `claudeg` router) slash-command shape, Mac-only-by-design constraint, and the Dropbox+scp cross-machine sync model. Captures the user's 2026-07-20 redirect: 'Wait /super shouldn't be using claudeg it should be using superpowers cloud' — future sessions must NOT re-add `claudeg` to `/super`. Verified file pair on both Mac (8195 B + 3227 B) and jeff-ubuntu (scp-synced). Also added Anti-pattern entry calling out the redirect, so the lesson is searchable from the umbrella SKILL.md body too."
  - "1.2.0 (2026-07-17) Replaced the .gitleaks.toml whitelist recommendation with the user-preferred workflow: `git rm` currently-tracked files + `git filter-repo` for history scrub + force-push. Documents the key-rotation residual risk for `$PROJECT_ROOT/serviceAccountKey.json` and the user's explicit choice to skip rotation on 2026-07-17. Reordered workarounds A→D accordingly in the reference file."
  - "1.1.0 (2026-07-17) Added hello-world validation pattern as Step 0 (build isolated test repo → push → verify `Cloud Build <supervisor@cloud-build.local>` commit landed on `private/hello-world`). Added canonical server-side secret-guard log format. Added anti-pattern #5 — don't trust prior-session logs without re-testing (user correction: 'whats the secret guard? Lets make it do a hello world program'). Confirmed `cloud_build_handoff` is the correct function name (NOT `cloud_build_hand_off_run_plan` as the prior session claimed — that function does not exist)."
  - "1.0.0 (2026-07-17) Initial — installs verified end-to-end (Codex plugin v0.8.1, SSH identity + host key pinned, state.json valid), hand-off executed (worked: connection + bastion reaper + box session slug), hand-off failed on server-side git secret guard because `$PROJECT_ROOT/ai_token_discovery_results.json` + `testing_http/testing_full/.env` + `$PROJECT_ROOT/serviceAccountKey.json` are tracked in main history. Verified on Slack thread C09GRLXF9GR/p1784235917 ($GITHUB_REPOSITORY). Pair with `references/git-secret-guard-blocks-main-derived-pushes-2026-07-17.md` for the blocker + workaround."
related_skills:
  - drive-pr-to-green
  - dispatch-task
  - finish-the-job
  - pr-cleanup-replay
---

# superpowers-cloud-build

The third execution mode for a Superpowers plan: instead of running subagent-driven-development in this session, hand the plan to a remote build box that runs it headless, and follow along over git.

## What this skill is and is NOT

**Is:** an operational skill for the cloud-build plugin (Codex + Claude Code). Covers install, enrollment, hand-off, follow-loop, land-result.

**Is NOT:** a substitute for `drive-pr-to-green` on existing PRs. Cloud-build cannot land work on an existing PR's `headRefName` — it creates fresh `cloud/control` + `cloud/status` branches on the box. To /green existing PRs, use `drive-pr-to-green` inline or dispatch via AO.

## Install (Codex side — verified 2026-07-17)

```bash
# 1. Extract the archive (only needed if you don't already have the source dir)
cd ~
tar xzf superpowers-cloud-build.tgz  # creates ~/superpowers-cloud-build-main/

# 2. Add the local marketplace + install the plugin
codex plugin marketplace add ~/superpowers-cloud-build-main
codex plugin add cloud-build@superpowers-cloud-build

# 3. Verify
codex plugin list | grep -A1 "Marketplace \`superpowers-cloud-build\`"
# Expected: cloud-build@superpowers-cloud-build  installed, enabled  0.8.1

# 4. Verify enrollment state
cat ~/.config/cloud-build/state.json
# Expected keys: contract_version=cloud-build-friend-v0, host=cloud.superpowers.build,
#                port=22, identity_file, known_hosts_file, enrolled_fp_hash, last_enrollment_check
```

If `state.json` is missing, run `bash scripts/cb-client-setup.sh` from the plugin's `scripts/` dir and pipe the enrollment code on stdin: `printf %s "$code" | bash scripts/cb-client-setup.sh`.

## Step 0 — Hello-world validation (ALWAYS run before real work)

**Lesson learned the hard way (2026-07-17):** do not trust that "the plugin installed" means "the box can code." Run a hello-world hand-off against an isolated test repo first to prove the full SSH → bastion → box → `Cloud Build <supervisor@cloud-build.local>` commit chain works end-to-end. This takes 5-10 min and is the only way to disambiguate "plugin enrolled" from "box actually accepts + executes + writes code."

```bash
# 1. Build isolated test repo (NOT a real project — must have ZERO tracked secrets in history)
HW=/tmp/cb-hello-$RANDOM
mkdir "$HW" && cd "$HW"
git init -q -b main
git config user.email harness@hermes.ai
git config user.name hermes-agent
git config commit.gpgsign false
printf '# cb-hello-test\nTest repo for superpowers cloud-build.\n' > README.md
git add README.md && git commit -q -m "initial commit"

git checkout -q -b private/hello-world
printf 'print("Hello, Cloud Build!")\n' > hello.py
printf 'import hello\n' > test_hello.py
cat > plan.md <<'PLAN'
# Plan: Hello World on Cloud Build
## Goal
Run python3 hello.py — should print "Hello, Cloud Build!"
## Steps
1. python3 hello.py
2. python3 test_hello.py
3. Report stdout
PLAN
git add hello.py test_hello.py plan.md
git commit -q -m "feat: hello world"

# CRITICAL: origin remote required (cloud_build_project_slug parses it)
git remote add origin https://github.com/jleechanorg/cb-hello-test.git

# 2. Preflight + hand-off
SKILL=~/.codex/plugins/cache/superpowers-cloud-build/cloud-build/0.8.1/skills/cloud-build
cd "$SKILL"
CLOUD_HERMETIC_CONFIRMED=1 bash scripts/preflight-local.sh "$HW" plan.md
# Expect: "preflight OK"

WORK_BRANCH="private/hello-world"
RUN_ID="$(bash scripts/lib-client.sh cloud_build_run_id "$HW")"
RUN_SHA="$(git -C "$HW" rev-parse HEAD)"
REQUEST="$(bash scripts/lib-client.sh cloud_build_mk_request "$RUN_ID" "plan.md" "$WORK_BRANCH" "$RUN_SHA")"
bash scripts/lib-client.sh cloud_build_handoff "$HW" "$RUN_ID" "$WORK_BRANCH" "$RUN_SHA" "$REQUEST"
# Expect: "git secret guard: scanning outgoing range ..." then push accepted

# 3. Poll status (90-300s typical)
for i in $(seq 1 30); do
  STATE="$(timeout 15 bash scripts/lib-client.sh cloud_build_status "$HW" state 2>/dev/null | tr -d '[:space:]')"
  echo "poll $i: state=$STATE"
  [ "$STATE" = "done" ] && break
  sleep 10
done

# 4. Verify box actually wrote code
RUN_URL_BASE="ssh://cloud-bastion@cloud.superpowers.build:22/cb-hello-test"
GIT_SSH_COMMAND="$(bash scripts/lib-client.sh cloud_build_git_ssh_command)"
GIT_SSH_COMMAND="$GIT_SSH_COMMAND" git fetch "$RUN_URL_BASE" '+refs/heads/*:refs/cb-test/*'
git -C "$HW" log refs/cb-test/cloud/status --format='%H %an %s' -1
# Expect: commit by "Cloud Build Box <cloud-build@localhost>" or "Cloud Build <supervisor@cloud-build.local>"
git -C "$HW" show refs/cb-test/cloud/status:status.json | jq '.state, .tasks_completed'
# Expect: "done", 1
git -C "$HW" log refs/cb-test/private/hello-world --format='%an %s' | head -5
# Expect: a commit by Cloud Build / supervisor
```

**Pass criteria:** `state=done`, `tasks_completed >= 1`, at least one new commit on `private/hello-world` authored by `Cloud Build`. If any of these is missing, **cloud-build is NOT actually working** — investigate before attempting real work.

**What this catches:**
- Plugin installed but SSH identity stale → fetches fail with `Host key verification failed`
- Enrollment expired → `enrolled_fp_hash` mismatch
- Server-side policy blocks the project slug → push rejected at the bastion
- Function name confusion (use `cloud_build_handoff`, NOT `cloud_build_hand_off_run_plan` — that function does not exist as of v0.8.1)

## Install (Claude Code side)

```text
/plugin marketplace add ~/superpowers-cloud-build-main
/plugin install cloud-build@superpowers-cloud-build
```

## The hand-off flow

```bash
SKILL=~/superpowers-cloud-build-main/skills/cloud-build
PROJECT=/absolute/path/to/repo
cd "$SKILL"

work_branch="$(git -C "$PROJECT" branch --show-current)"
run_id="$(bash scripts/lib-client.sh cloud_build_run_id "$PROJECT")"   # slug-YYYYMMDDHHMMSS-randhex
run_sha="$(git -C "$PROJECT" rev-parse HEAD)"

CLOUD_HERMETIC_CONFIRMED=1 bash scripts/preflight-local.sh "$PROJECT" plan.md

request="$(bash scripts/lib-client.sh cloud_build_mk_request "$run_id" plan.md "$work_branch" "$run_sha")"
bash scripts/lib-client.sh cloud_build_handoff "$PROJECT" "$run_id" "$work_branch" "$run_sha" "$request"
```

## Follow-loop (foreground, 10-min cadence)

```bash
bash scripts/lib-client.sh cloud_build_fetch_status "$PROJECT"
bash scripts/lib-client.sh cloud_build_check_heartbeat "$PROJECT"
bash scripts/lib-client.sh cloud_build_status "$PROJECT" state
```

States:
- `running` — report `tasks_completed`/`tasks_total`/`current_task`/`head_sha`
- `needs_input` — read `qid`/`prompt`, push answer via `cloud_build_mk_answer`
- `done` — run `cloud_build_land_result` + send pull-ack via `cloud_build_mk_pulled`
- `failed` / `aborted` — read `message`, partial commits fetchable on work branch

## Land the result on `done`

```bash
head_sha="$(bash scripts/lib-client.sh cloud_build_status "$PROJECT" head_sha)"
landed="$(bash scripts/lib-client.sh cloud_build_land_result "$PROJECT" "$work_branch" "$head_sha" "$run_id")"
# Expect "LANDED". If "SAVED refs/cloud-build/landed/$run_id" — reconcile before ack.
# On LANDED:
bash scripts/lib-client.sh cloud_build_push_control "$PROJECT" \
  "$(bash scripts/lib-client.sh cloud_build_mk_pulled "$run_id" plan.md "$work_branch" "$run_sha" "$head_sha")" \
  "$run_id"
```

After ack, the box is reaped within seconds. Do NOT poll `cloud/status` again.

## Red flags

- **Never push to the work branch while a run is active** — the box owns it during the run.
- **Never bypass preflight or auto-confirm hermeticity** on the user's behalf.
- **Never start the box yourself** — the door provisions it on demand; you only connect.
- **Never disable strict host-key checking** — the helper pins the host key.

## Critical pitfalls (CLASS-LEVEL — see references for full transcripts)

1. **Git secret guard blocks pushes whose ancestors contain tracked secrets** (verified on `$PROJECT_ROOT/ai_token_discovery_results.json`, `.env`, `serviceAccountKey.json`, and `$PROJECT_ROOT/venv/.../googleapiclient/.../*.json`). The guard walks the range of commits being pushed and rejects if any commit in that range introduces a sensitive file. **This is the #1 reason cloud-build fails on real projects that worked fine on the hello-world test repo.** See `references/git-secret-guard-blocks-main-derived-pushes-2026-07-17.md` for the workaround (user-preferred: `git rm` from HEAD + `git filter-repo` for history scrub + force-push).

   **Canonical server-side log format (use this to recognize a real guard rejection):**
   ```
   git secret guard: scanning outgoing range <main-sha>..<head-sha> for refs/heads/private/<topic>
   git secret guard: blocked sensitive file in outgoing commit <sha>: <path>
   ...
   git secret guard: push blocked. Remove the secret from the outgoing history before pushing.
   fatal: failed to push some refs to 'ssh://cloud.superpowers.build:22/<slug>/<slug>-<run_id>'
   ```
   If you see "scanning outgoing range" + "blocked sensitive file in outgoing commit" → it's the guard. If you see "scanning outgoing range" but push succeeds → guard scanned and approved. If you see NO "scanning outgoing range" line at all → push was rejected for a DIFFERENT reason (auth, host-key, slug not enrolled, etc.) — investigate `_cloud_build_run_capture` output before blaming the guard.

   **User-preference note (2026-07-17):** the user explicitly preferred `git rm` + history scrub over `.gitleaks.toml` whitelisting. Surface the key-rotation risk (the real `serviceAccountKey.json` is a live GCP service account credential that remains valid even after git-history scrub unless rotated) and ask whether to skip rotation. On 2026-07-17 the user said "Don't rotate any keys" — the secret is now in known-stub state pending future rotation.

2. **Workflow has to land on `private/*` branches** — the server-side preflight rejects pushes to `feat/*`, `fix/*`, `dependabot/*`, etc. Re-base your work onto `private/<topic>` off `origin/main` before hand-off.

3. **Hermetic confirmation required** — `bash scripts/preflight-local.sh "$PROJECT" plan.md` fails closed unless `CLOUD_HERMETIC_CONFIRMED=1` is set in the same shell. The hermeticity claim is the operator's, not the agent's.

4. **macOS zsh refspec corruption** — `bash scripts/lib-client.sh <fn>` from a zsh shell will silently corrupt `:refs/...` push refspecs. Always run from bash, never source `lib-client.sh` into the session shell.

5. **Enrollment code is one-shot** — `cb-client-setup.sh` reads the code from stdin once. Persist it via `~/.config/cloud-build/state.json`, not in shell env or `~/.bashrc`. The code expires; the state persists.

6. **Function name confusion is real.** The hand-off function is `cloud_build_handoff` — five args: `<repo> <run_id> <work_branch> <run_sha> <control_json>`. It is NOT `cloud_build_hand_off_run_plan` (which does not exist as of plugin v0.8.1). If a prior session's transcript references the wrong function name, treat the whole prior transcript as suspect — the function name is the most load-bearing detail in the entire flow.

## Anti-patterns

- ❌ "Cloud-build can land existing PRs" — it cannot. It writes to `cloud/control` + `cloud/status` branches on the box, not to the user's existing `headRefName`. Use `drive-pr-to-green` for /green on existing PRs.
- ❌ "Cloud-build handles the secret guard for me" — it does not. The guard is upstream policy. Whitelist known paths or use a clean test repo.
- ❌ "Re-running cloud-build hand-off will fix a failed push" — only the standalone `cloud-bastion: CLOUD_BUILD_RETRYABLE=provisioning_timed_out` signal replays once. Every other failure is final.
- ❌ **"Make `/super` call `claudeg` because it's faster"** (added 2026-07-20). The user's 2026-07-20 redirect: *"Wait `/super` shouldn't be using claudeg it should be using superpowers cloud"*. `/super` is the canonical box dispatch; `/superlight` is the legacy `claudeg` escape hatch. If a future session sees `/super` described as a `claudeg` router, that's stale — see `references/slash-command-cross-machine-shape-2026-07-20.md` for the canonical shape.
- ❌ "The prior session said cloud-build worked" — verify by reading `state.json` and `codex plugin list` in the current session. The previous session may have only installed the marketplace, not the plugin itself (verified gap 2026-07-17, prior session claimed "Codex plugin installed, v0.8.1" but `codex plugin list` showed it was NOT installed — marketplace only).
- ❌ "The prior session said the secret guard rejected the push, so I won't test" — verified failure mode (2026-07-17, Slack C09GRLXF9GR). I repeated a prior session's "secret guard rejected" framing WITHOUT re-running the actual hand-off, and told the user "cloud-build can't be used for real work." The user's response was *"what's the secret guard? Lets make it do a hello world program"* — the box actually works fine on clean repos. **Rule: any claim about cloud-build behavior that comes from a prior-session log or a third-party account must be re-verified in the current session before being reported as a blocker.** The five-minute Step 0 hello-world validation is the canonical proof.
- ❌ **"Watchdog reports green → /super works"** (verified on Slack thread `C09GRLXF9GR/p1784582518.247009`, FIX SHIPPED 2026-07-20 in `cloud-build-bastion-watchdog` v1.2.0). The v1.1.0 watchdog only probed `cloud-bastion@` and `enroll@` users (which print success banners: "interactive shell is not permitted" + "invalid or expired token") and **never probed the actual handoff user** (`git@` / `$USER@` / `cloud-build@` at `cloud.superpowers.build`). The dispatch helper authenticates as those users; if the local key fp rotated (`ssh-keygen` regenerated after the last `cb-client-setup.sh`) or the bastion pruned `authorized_keys`, every real `/super` call returned `Permission denied (publickey)` while the watchdog kept exiting 0. **The v1.2.0 fix adds a third probe block that iterates all three real handoff users and returns exit=4 when banner users pass but handoff users fail.** Future agents can now trust exit=0 as the canonical signal that ALL six probes passed (banner users + handoff users + known_hosts + age). If you see exit=4, the operator must re-enroll before dispatch. See `references/bastion-watchdog-handoff-user-mismatch-2026-07-20.md` for the full reproduction transcript. **Still-required pre-dispatch probe (defense in depth)**: even with the watchdog fix, any agent about to call `/super` should run the three-user probe inline as a final sanity check — the watchdog is 12h-cadence, not per-dispatch. Recipe:

```bash
for u in git $USER cloud-build; do
  ssh -i ~/.ssh/cloud-build/id_ed25519 -o IdentitiesOnly=yes \
    -o StrictHostKeyChecking=yes -o UserKnownHostsFile=~/.ssh/cloud-build/known_hosts \
    -o ConnectTimeout=5 -o BatchMode=yes -T "${u}@cloud.superpowers.build" 2>&1 | head -1
done
```

If ANY returns `Permission denied (publickey)`, STOP and surface to the user — do not auto-re-enroll, do not silently route around `/super`.

## Pair with

- `references/local-vs-cloud-decision-tree.md` — the 6-axis comparison table (identity / observability / failure recovery / cost / network / enforcement) + "when to use which" decision rule, with real examples from PR #8466 + #8476. Use this when a user asks "is cloud build different from running locally?" or before choosing between the two execution paths.
- `references/git-secret-guard-blocks-main-derived-pushes-2026-07-17.md` — the #1 blocker, full reproduction + workaround recipe
- `references/hello-world-validation-2026-07-17.md` — the canonical 5-min "does cloud-build actually code" test. Run BEFORE any real hand-off on a real project. Step-by-step recipe + pass criteria + what-this-catches table.
- `references/orphan-snapshot-handoff-port-back-2026-07-20.md` — the orphan-snapshot + port-back recipe that bypasses the server-side git secret guard when the user can't / won't history-scrub. Verified on $GITHUB_REPOSITORY PR #8466 (run `cb-wa-8353-20260720002435-d4fb95`, 4 Cloud Build-authored commits, 12/12 hermetic tests pass).
- `references/slash-command-cross-machine-shape-2026-07-20.md` — the `/super` (canonical box dispatch) and `/superlight` (legacy `claudeg` router) slash-command shape, Mac-only-by-design constraint, and the Dropbox+scp cross-machine sync model. Load whenever a user says "what does /super do?", before editing `~/.claude/commands/super*.md` files, or when /super fails from jeff-ubuntu.
- `references/bastion-watchdog-handoff-user-mismatch-2026-07-20.md` — the watchdog reports-green-while-/super-is-red bug. Reproduction transcript, the watchdog patch recipe (probe the actual handoff user + fail closed), and the workaround probe (`ssh -T $(whoami)@cloud.superpowers.build`) that any future agent can run BEFORE trusting the watchdog's exit 0. Verified on Slack thread `C09GRLXF9GR/p1784582518.247009`.
- `~/.codex/plugins/cache/superpowers-cloud-build/cloud-build/<v>/skills/cloud-build/SKILL.md` — the canonical plugin docs (read this on every drive; this umbrella is the Hermes-side wrapper, not a substitute)"