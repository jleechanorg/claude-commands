# Cloud Build plugin — verified wire shape (2026-07-16)

A reference for future sessions that encounter the **Prime Radiant Cloud Build plugin** or any structurally similar "remote-build-via-SSH-bastion" tool. Captured from a successful end-to-end run.

## What it is

A Superpowers plugin that runs a committed implementation plan on a remote build box and follows it over git. Not CI, not a remote executor — single-plan, single-box, identity-pinned SSH.

**Wire shape (verified end-to-end 2026-07-16):**

- **Host:** `cloud.superpowers.build:22` (SSH, ed25519 only, pinned host key)
- **Host key fingerprint (bundled in plugin config):** `SHA256:uIogunmqBg/yisJwDP3uHHzJ0ualJ9t2EucfrwjxzaQ`
- **Public SSH door user (initial enrollment):** `enroll` (one-shot)
- **Git proxy user (after enrollment):** `cloud-bastion` (the forced-command SSH user)
- **State file:** `${XDG_CONFIG_HOME:-$HOME/.config}/cloud-build/state.json` (chmod 600)
- **SSH identity:** `~/.ssh/cloud-build/id_ed25519` + `~/.ssh/cloud-build/id_ed25519.pub`
- **Known hosts:** `~/.ssh/cloud-build/known_hosts` (single-line, fingerprint-pinned)
- **Protocol:** git-over-SSH (the box is a git remote; no other protocol)
- **Branches:** `cloud/control` (client writes), `cloud/status` (box writes), plus the user's work branch under `private/*`
- **Enrollment:** single-use code from inviter (8-byte hex string), consumed once via stdin
- **Idempotency:** state.json is the marker — second run with state.json present skips enrollment

## Static-review checklist (run this before installing)

The tarball is 26.6 KB. Run these pattern checks against the entire archive:

| Pattern | Expected | Why |
|---|---|---|
| `\beval\b` | 0 | No dynamic code execution |
| `curl ` / `wget ` / `nc ` | 0 | No arbitrary network egress |
| `/dev/tcp` | 0 | No bash-tcp backdoors |
| `base64 -d` | 0 | No hidden payload decoding |
| `scp ` / `rsync ` | 0 | No file copying beyond git-over-SSH |
| `rm -rf /` | 0 | No mass-deletion |
| `python3 -c` | few (≤10) | Local JSON parsing — review each |
| `bash -c` | 0 | No shell injection surface |
| `ssh ` | 1 (the only network primitive) | The pinned-host-key SSH client |

**Verified 2026-07-16:** all counts matched. Plugin is `MIT` licensed (Prime Radiant, Inc., v0.8.1).

## Why it matters beyond this plugin

The pattern "pinned-host-key SSH + git-over-SSH + state.json on disk + single-use enrollment code" is the canonical shape for trust-on-first-use remote build systems. Any future plugin or service following this shape can use this same checklist.

## Full flow (the 6 phases from SKILL.md, observed in practice)

### Phase 1 — preflight (local, no network)

```
$ bash scripts/preflight-local.sh <project_dir> <plan_rel>
preflight OK
```

Refuses with FATAL on:
- not a git repo
- uncommitted changes
- `.gitmodules` present (multi-repo detection)
- desktop app markers (`*.xcodeproj`, `tauri.conf.json`, `*.app`, etc.)
- plan not committed on HEAD
- `CLOUD_HERMETIC_CONFIRMED` not set (this is the gate that must be set by user, never auto-confirmed by agent)
- work branch not under `private/`

**Real behavior observed:** agent correctly refused to auto-confirm hermeticity on user's behalf, with `preflight FAIL: set CLOUD_HERMETIC_CONFIRMED=1`.

### Phase 2 — enroll (one-time, sets up state.json + SSH identity)

```
$ printf '<enrollment-code>' | bash scripts/cb-client-setup.sh
```

This writes `state.json` (chmod 600) and generates `~/.ssh/cloud-build/id_ed25519`. The enrollment code is consumed via stdin and never persisted to disk.

**State.json shape (verbatim from a real run):**
```json
{
  "client_config_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
  "contract_version": "cloud-build-friend-v0",
  "enrolled_fp_hash": "c709569c7b347527af28cb44079f2aa7e3fa7c0a3a2f0dfc1bee0770b6743c0b",
  "host": "cloud.superpowers.build",
  "identity_file": "$HOME/.ssh/cloud-build/id_ed25519",
  "known_hosts_file": "$HOME/.ssh/cloud-build/known_hosts",
  "last_enrollment_check": "2026-07-16T19:26:34Z",
  "port": 22,
  "public_key_file": "$HOME/.ssh/cloud-build/id_ed25519.pub"
}
```

### Phase 3 — hand-off (one SSH transaction: frozen work branch + control frame)

The hand-off is one atomic-ish unit. The lib-client.sh code:
1. Computes `run_id = cb-demo-<UTC-timestamp>-<3-bytes-entropy>`
2. Writes `cloud/control` branch with a JSON control frame containing `run_id`, `plan_path`, `work_branch`, `commit_sha`
3. Pushes the frozen work branch (`run_sha`) via SSH to the bastion
4. Pushes `cloud/control` via SSH to the bastion

**Real output from a successful run:**
```
bastion: starting box for cb-demo
git secret guard: scanning outgoing range aff5337..0d9d509 for refs/heads/private/demo-cloud-run
To ssh://cloud.superpowers.build:22/cb-demo/cb-demo-20260716192922-e331d7
 * [new branch]      0d9d509 -> private/demo-cloud-run
```

Note the three observable side effects:
1. `bastion: starting box` — box provisioning started
2. `git secret guard: scanning outgoing range` — server-side secret scan
3. `[new branch]` — branch accepted on the remote

### Phase 4 — follow loop (poll cloud/status)

`cloud_build_fetch_status` does a `git ls-remote --exit-code` on `refs/heads/cloud/status`. Exit 2 (ref absent) is benign (box hasn't created the status yet); any other nonzero is a transport/host-key failure and the follow loop should STOP.

**`cloud/status:status.json` shape (verbatim from a real `done` state):**
```json
{
  "head_sha": "2f396bc181ceded6e4a9bfc25d1efd8a86643931",
  "run_id": "cb-demo-20260716192922-e331d7",
  "schema_version": 1,
  "state": "done",
  "tasks_completed": 1,
  "tasks_total": 0,
  "updated_at": "2026-07-16T19:34:46Z",
  "work_branch": "private/demo-cloud-run",
  "workflow": {
    "config_digest": "sha256:735edb733d3baf52e55240d620b8d2321a551f6c2780de4f355908b69e6dbcee",
    "harness_version": "serf-3",
    "id": "serf",
    "model": "",
    "runner": "exec",
    "transport": "local"
  }
}
```

The `workflow` block tells you which harness the box used (`serf-3` in this case). `runner: exec` means it ran commands directly, not in a sandboxed container.

**State transitions observed in a 4-min real run:**
- `accepted` (briefly) → `running` (cold start)
- `running` with `current_task` = "feat: add farewell feature" (mid-execution)
- `done` with `head_sha` = new commit (completion)

### Phase 5 — abort (optional, only if user asks)

`bash scripts/lib-client.sh cloud_build_push_control <repo> "$(bash scripts/lib-client.sh cloud_build_mk_abort <run_id> <plan> <branch> <sha>)" <run_id>`

Writes `command: abort` to `cloud/control`. The box supervisor reads it, kills the engine, writes `state: aborted`.

### Phase 6 — land result (fast-forward onto local work branch)

`bash scripts/lib-client.sh cloud_build_land_result <repo> <work_branch> <head_sha> <run_id>`

Returns either `LANDED` (success) or `SAVED refs/cloud-build/landed/<run_id>` (local branch diverged; the box's commit is preserved on a recovery ref). On success, send the pull-ack:

`bash scripts/lib-client.sh cloud_build_push_control <repo> "$(bash scripts/lib-client.sh cloud_build_mk_pulled <run_id> <plan> <branch> <run_sha> <head_sha>)" <run_id>`

**Observed post-land state on the local repo:**
```
2f396bc feat: add farewell feature   <- authored by "Cloud Build <supervisor@cloud-build.local>"
0d9d509 chore: ignore proof/ artifacts
4cf891e docs: add demo implementation plan
aff5337 init: hello-world app + pytest suite
```

## What I would NOT do again

1. **Tried `codex exec` 3 times to drive the full protocol.** 2 of the 3 runs failed at the hermeticity gate due to the `bash -lc` env-scrub. 1 run "succeeded" but the agent burned 33k tokens re-reading SKILL.md between phases. The direct-from-gateway script driving (Phase 1 → 2 → 3 → 4 → 6 in a sequence of subprocess.run calls) was 10x faster and used 0 tokens.

2. **Created a fake `origin` remote** to satisfy the project-slug requirement. The plugin's `cloud_build_project_slug` derives the slug from `git remote get-url origin`'s basename — it doesn't actually reach the URL, just needs a value to hash. The fake origin (e.g. `git@github.com:jleechanorg/cb-demo.git`) was enough. In a real setup, the project IS hosted on GitHub so this is automatic.

3. **Started the screencap BEFORE installing git/gitignore updates.** The 935 frames polluted git status until I added `proof/` to `.gitignore` and committed it on the work branch. Add the gitignore first.

## Repo for re-runs

If you want to reproduce the demo:
- Sandbox repo: `~/cb-demo` (private, throwaway)
- Plan: `plans/demo-plan.md` (committed on `private/demo-cloud-run`)
- Plugin: `~/superpowers-cloud-build-main` (extracted from the invite tarball)
- Codex install: `codex plugin marketplace add ~/superpowers-cloud-build-main && codex plugin add cloud-build@superpowers-cloud-build`

The enrollment code is single-use; you'd need a new invite for a fresh run. The SSH identity at `~/.ssh/cloud-build/id_ed25519` is reusable across enrollments.