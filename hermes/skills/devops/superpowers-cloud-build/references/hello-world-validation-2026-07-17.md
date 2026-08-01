# Hello-world validation — the canonical "does cloud-build actually code" test

**Purpose:** disambiguate "plugin installed" from "box actually executes and writes code." Run this BEFORE attempting any real cloud-build hand-off on a real project.

**Time:** 5-10 minutes total. Push lands in <5s, box runs the plan in 60-120s, status hits `done` within ~5 min.

**Provenance:** built on Slack thread C09GRLXF9GR/p1784235917 (2026-07-17). User correction was *"whats the secret guard? Lets make it do a hello world program"* after I had incorrectly attributed a prior session's failed hand-off to the box without re-testing. The hello-world passed — proving the box is functional and the prior session's blocker was project-specific ($GITHUB_REPOSITORY's tracked secrets), not box-side.

## Step-by-step

### 1. Build isolated test repo (must have ZERO tracked secrets in history)

```bash
HW=/tmp/cb-hello-$RANDOM
mkdir -p "$HW" && cd "$HW"
git init -q -b main
git config user.email harness@hermes.ai
git config user.name hermes-agent
git config commit.gpgsign false

# initial commit on main
cat > README.md <<'EOF'
# cb-hello-test
Test repo for superpowers cloud-build plugin.
EOF
git add README.md && git commit -q -m "initial commit"

# work branch under private/* (required by server-side preflight)
git checkout -q -b private/hello-world

# source + test files
cat > hello.py <<'EOF'
print("Hello, Cloud Build!")
EOF
cat > test_hello.py <<'EOF'
import hello  # noqa: F401
print("test_hello imported OK")
EOF

# plan.md (REQUIRED — preflight fails without it committed on HEAD)
cat > plan.md <<'EOF'
# Plan: Hello World on Cloud Build

## Goal
Run python3 hello.py — should print "Hello, Cloud Build!"

## Steps
1. Run `python3 hello.py` — expect "Hello, Cloud Build!"
2. Run `python3 test_hello.py` — expect "test_hello imported OK"
3. Report stdout from both as the result.
EOF

git add hello.py test_hello.py plan.md
git commit -q -m "feat: add hello world"

# CRITICAL: origin remote required (cloud_build_project_slug parses it)
# The remote URL is used to derive the project slug — it does NOT need to be a real GH repo
git remote add origin https://github.com/jleechanorg/cb-hello-test.git
```

**Why these specific choices:**
- `private/hello-world` branch → server-side preflight requires `private/*` work branches
- `plan.md` committed on HEAD → local preflight fails without it
- `git remote add origin https://github.com/jleechanorg/...` → cloud_build_project_slug parses the owner/repo from origin; the URL doesn't need to exist on github.com, only be syntactically valid
- No `.env` / service-account / credential files anywhere → secret guard has nothing to block on

### 2. Preflight + hand-off

```bash
SKILL=~/.codex/plugins/cache/superpowers-cloud-build/cloud-build/0.8.1/skills/cloud-build
cd "$SKILL"

# Local preflight (must set CLOUD_HERMETIC_CONFIRMED=1 in same shell)
CLOUD_HERMETIC_CONFIRMED=1 bash scripts/preflight-local.sh "$HW" plan.md
# Expect: "preflight OK"

# Generate run_id + control JSON
WORK_BRANCH="private/hello-world"
RUN_ID="$(bash scripts/lib-client.sh cloud_build_run_id "$HW")"
RUN_SHA="$(git -C "$HW" rev-parse HEAD)"
REQUEST="$(bash scripts/lib-client.sh cloud_build_mk_request "$RUN_ID" "plan.md" "$WORK_BRANCH" "$RUN_SHA")"

# The actual hand-off — 5 args, all required
bash scripts/lib-client.sh cloud_build_handoff "$HW" "$RUN_ID" "$WORK_BRANCH" "$RUN_SHA" "$REQUEST"
```

**Expected output on success:**
```
Warning: Permanently added 'stockyard-XXXXXX' (ED25519) to the list of known hosts.
git secret guard: scanning outgoing range <main-sha>..<head-sha> for refs/heads/private/hello-world
To ssh://cloud.superpowers.build:22/cb-hello-test/cb-hello-test-YYYYMMDDHHMMSS-XXXXXX
 * [new branch]      <head-sha> -> private/hello-world
```

**The line `git secret guard: scanning outgoing range ...` is the canonical signal the server-side scan ran.** If you see this line and the push succeeds → guard approved. If you see this line and the push is blocked → guard rejected (this is the bit that bites $GITHUB_REPOSITORY). If you DON'T see this line at all → push was rejected for a non-guard reason (auth, host key, slug not enrolled).

### 3. Poll for `done`

```bash
for i in $(seq 1 30); do
  STATE="$(timeout 15 bash scripts/lib-client.sh cloud_build_status "$HW" state 2>/dev/null | tr -d '[:space:]')"
  echo "poll $i ($(date +%H:%M:%S)): state=$STATE"
  case "$STATE" in
    done|aborted|failed|errored) break ;;
  esac
  sleep 10
done
```

**Typical timing:**
- Poll 1-3: `state=running` (box is spinning up)
- Poll 4-8: `state=running` (box is executing plan)
- Poll 9-15: `state=done` (box finished, wrote cloud/status)

If state stays `running` for >5 min, the box may have hung on something in your plan. Inspect cloud/status for partial progress.

### 4. Verify the box actually wrote code

```bash
RUN_URL_BASE="ssh://cloud-bastion@cloud.superpowers.build:22/cb-hello-test"
GIT_SSH_COMMAND="$(bash scripts/lib-client.sh cloud_build_git_ssh_command)"

# Fetch all remote refs (including cloud/status + the box's commits)
GIT_SSH_COMMAND="$GIT_SSH_COMMAND" git fetch "$RUN_URL_BASE" '+refs/heads/*:refs/cb-test/*'

# Check cloud/status
git -C "$HW" log refs/cb-test/cloud/status --format='%H %an %s' -1
# Expect: commit by "Cloud Build Box <cloud-build@localhost>" or "Cloud Build <supervisor@cloud-build.local>"

git -C "$HW" show refs/cb-test/cloud/status:status.json | python3 -c "
import json, sys
s = json.load(sys.stdin)
print(f'state={s.get(\"state\")}')
print(f'tasks_completed={s.get(\"tasks_completed\")}')
print(f'workflow={s.get(\"workflow\",{})}')
"
# Expect: state=done, tasks_completed >= 1, workflow.harness_version in {"serf-3"} or current

# Check the work branch has new commits from the box
git -C "$HW" log refs/cb-test/private/hello-world --format='%an %s' | head -5
# Expect: at least one commit by Cloud Build / supervisor
```

**Real example output from 2026-07-17 run-id `cb-hello-test-20260717223258-1c073f`:**
```
09786b00563d29078d8463dbe159ee596b8a7dd3 Cloud Build feat: add greet function and guard script print
5485e0c4885918b0c6ba77e3a6c137831f7cf386 hermes-agent plan: hello world test
```

**Diff from the box:**
```diff
diff --git a/hello.py b/hello.py
-print("Hello, Cloud Build!")
+def greet():
+    return "Hello, Cloud Build!"
+
+if __name__ == "__main__":
+    print(greet())
```

## Pass criteria

All three must hold:
1. `state=done` (not `running`, not `failed`, not `aborted`)
2. `tasks_completed >= 1`
3. At least one new commit on `private/hello-world` authored by `Cloud Build`

If any fails, **cloud-build is NOT actually working** — debug before attempting real work.

## What this catches

| Symptom | Root cause | Fix |
|---|---|---|
| `Host key verification failed` on fetch | SSH identity or known_hosts stale | `cat ~/.config/cloud-build/state.json` — verify `identity_file`/`known_hosts_file` paths exist; re-pin via `cb-client-setup.sh` |
| `FATAL: could not derive Cloud Build project slug from origin remote` | No `origin` remote set on test repo | `git remote add origin https://github.com/jleechanorg/<slug>.git` |
| `FATAL: run id required for scoped Cloud Build write remote` | Trying to fetch run-scoped URL without preserving run_id across calls | Re-derive `run_id` from state file or re-run hand-off |
| `state=failed` on poll | Plan hit an error on the box | `git show refs/cb-test/cloud/status:status.json` — check `message` field |
| Push rejected with `git secret guard: push blocked` | Test repo has a tracked secret in history | Verify no `.env`/credential files were added; rebuild test repo from scratch |
| Push rejected WITHOUT `scanning outgoing range` line | Auth/host-key/slug issue, NOT guard | Re-verify SSH identity, re-enroll if needed |

## Pair with

- `references/git-secret-guard-blocks-main-derived-pushes-2026-07-17.md` — the #1 blocker for real projects; this validation recipe is the canonical proof cloud-build IS functional when the blocker isn't engaged
- `~/.codex/plugins/cache/superpowers-cloud-build/cloud-build/0.8.1/skills/cloud-build/SKILL.md` — canonical plugin docs
