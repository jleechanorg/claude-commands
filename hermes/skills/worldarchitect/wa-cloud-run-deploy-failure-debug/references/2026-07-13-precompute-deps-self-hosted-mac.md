---
title: PRECOMPUTE_FAILED on self-hosted Mac runners — composite action installs fastembed, deploy.sh's probe can't find it
verified-on: $GITHUB_REPOSITORY PR #8380 (fix) / issue #8379 / GH Actions run 29280658965
failure-class: Mode 7 (script-level probe failure, pre-gcloud)
---

## TL;DR

The `setup-precompute-deps` composite action runs `actions/setup-python@v5.0.0` and `pip install fastembed numpy google-cloud-storage jsonschema pydantic cachetools`. The pip install succeeds (`Successfully installed ... fastembed-0.8.0 ...` in the GH Actions log). But on a self-hosted Mac runner (`ez-mac-runner-b-5` on the `jleechanorg/*` fleet), the interpreter lands in the GitHub-Actions-hosted toolcache (`$RUNNER_TOOL_CACHE/python/3.11.x/bin/python`) — NOT on `$PATH` and NOT named `python3` (system Python). `deploy.sh`'s interpreter probe iterated `${VPYTHON:-} ./vpython vpython python3` and found none of those candidates pointed at the just-installed interpreter. The probe exits 1 at `deploy.sh:466` BEFORE `gcloud run deploy` is invoked. The failure-email step fires every push to main.

**Important operator reassurance (the live service was fine):** `gcloud run services describe mvp-site-app-dev --format='value(metadata.labels.commit-sha-full)'` returns `cc7ec0a06a47ddfa497dc2af1ee1b1677b0efe96` (PR #8337's merge commit). `latestReadyRevisionName == latestCreatedRevisionName == mvp-site-app-dev-03841-ftq`. `/health` returns HTTP 200. PR #8337 IS live on dev — the user's work shipped via a sibling run at 20:00:18 UTC; the 20:00:20 run failed at Mode 7 and the failure-email step fired. The right user-facing answer was "your PR is fine, this is a CI infra bug" — NOT "we need to roll back."

## Timeline (UTC, 2026-07-13)

| Time | Event |
|---|---|
| 18:53 | PR #8337 commit `96e0b6affa` lands on `codex/gpt-5: warning-surface cleanup nits` branch |
| 20:00:18 | PR #8337 squash-merge into `main` as `cc7ec0a06a47ddfa497dc2af1ee1b1677b0efe96` |
| 20:00:18 | 3 sibling Auto-Deploy Dev runs trigger (IDs 29280657362, 29280657422, 29280657574) — `conclusion: success` for all three. PR #8337's image `mvp-site-app:dev-cc7ec0a` is built and Cloud Run revision `mvp-site-app-dev-03841-ftq` is created at 20:04:00.998353Z. |
| 20:00:20 | Auto-Deploy Dev run 29280658965 triggers (different ID, but same commit SHA). Job 86920749719, runner `ez-mac-runner-b-5` (self-hosted Mac). |
| 20:01:46 | `Setup precompute Python deps` step — `actions/setup-python@v5.0.0` succeeds, `pip install` succeeds (log line 632: `Successfully installed ... fastembed-0.8.0 ...`) |
| 20:02:09 | `Deploy to Cloud Run` step begins — `./deploy.sh mvp_site` |
| 20:02:43 | Image build `gcb-build-id 6a49e2b3-d447-4e5c-baed-a433847df57f` submitted |
| 20:05:03 | Image build succeeds (Build status: SUCCESS); `gcr.io/worldarchitecture-ai/mvp-site-app:dev-latest` tagged |
| 20:05:07 | **`PRECOMPUTE_FAILED: no interpreter with fastembed+numpy+google-cloud-storage+mvp_site.agent_prompts found; aborting deploy`** at `deploy.sh:466`. Deploy step exits 1 BEFORE `gcloud run deploy`. |
| 20:05:07 | `Get deployment URL`, `Health check` steps skipped |
| 20:05:07 | `Notify on failure` step runs (uncoditionally on `if: failure()`) — writes summary |
| 20:05:08 | `Send failure email notification` step runs — emails `$USER@gmail.com` with subject `❌ FAILED: dev Deployment - mvp-site-app-dev` |
| 20:05:15 | `smoke-tests` job cancelled (depends on `deploy` job which failed) |
| 22:16:35 | User reply in Slack thread `C0BDEAJH8PK/p1783980995.978159`: "Investigate and fix fullrun and lets root cause why it happened and make gh issue too" |
| ~22:25 | Investigation + fix lands as PR #8380 on branch `fix/precompute-deps-self-hosted-runner` (10 regression tests pass) + GH issue #8379 + one-time status cron `992155ae4a68` |

## Root cause

Two-surface bug, both MUST be fixed:

### Surface A — `setup-precompute-deps/action.yml` doesn't export the interpreter

```yaml
# BEFORE (the regression)
- name: Install embedding precompute deps
  continue-on-error: true
  shell: bash
  run: python -m pip install --no-cache-dir fastembed numpy google-cloud-storage jsonschema pydantic cachetools || true
```

The `pip install` succeeds but the interpreter lives at `$RUNNER_TOOL_CACHE/python/3.11.x/bin/python` and is invisible to subsequent steps (no `$GITHUB_ENV` write, no `$GITHUB_PATH` prepend). The deploy step has no way to find it.

### Surface B — `deploy.sh` probe loop's `python3` candidate is wrong on self-hosted Mac runners

```bash
# BEFORE (the regression)
for _cand in "${VPYTHON:-}" ./vpython vpython python3; do
    [ -n "$_cand" ] || continue
    command -v "$_cand" >/dev/null 2>&1 || continue
    if "$_cand" -c 'import fastembed, numpy, google.cloud.storage; import mvp_site.agent_prompts' >/dev/null 2>&1; then
        _EMBED_PY="$_cand"
        break
    fi
done
```

On a self-hosted Mac runner (the deploy job runs on `fromJson(vars.SELF_HOSTED_RUNNER_LABELS || '["self-hosted"]')` per `deploy-dev.yml:33`), `$VPYTHON` is unset (the action never exports it), `./vpython` doesn't exist on a fresh checkout, `vpython` is not in PATH, and `python3` is the system Python which lacks fastembed. The probe falls through all four candidates and exits 1 at line 430 with `PRECOMPUTE_FAILED: no interpreter with fastembed+numpy+google-cloud-storage+mvp_site.agent_prompts found; aborting deploy`.

## Fix (verified in PR #8380)

### Composite action side

```yaml
# AFTER (PR #8380)
runs:
  using: 'composite'
  steps:
    - name: Set up Python for embedding precompute
      id: setup-python
      uses: actions/setup-python@0a5c61591373683505ea898e09a3ea4f39ef2b9c  # v5.0.0
      continue-on-error: true
      with:
        python-version: '3.11'

    - name: Export precompute interpreter to VPYTHON
      id: set-python
      shell: bash
      if: always()
      run: |
        set -u
        python_path="${{ steps.setup-python.outputs.python-path }}"
        if [ -z "$python_path" ] || [ ! -x "$python_path" ]; then
          echo "WARNING: setup-python did not yield a usable interpreter" >&2
          echo "python-path=" >> "$GITHUB_OUTPUT"
          echo "precompute-ready=false" >> "$GITHUB_OUTPUT"
          exit 0
        fi
        echo "VPYTHON=$python_path" >> "$GITHUB_ENV"
        echo "$(dirname "$python_path")" >> "$GITHUB_PATH"
        if "$python_path" -c 'import fastembed, numpy, google.cloud.storage; import mvp_site.agent_prompts' >/dev/null 2>&1; then
          echo "precompute-ready=true" >> "$GITHUB_OUTPUT"
        else
          echo "precompute-ready=false" >> "$GITHUB_OUTPUT"
        fi
        echo "python-path=$python_path" >> "$GITHUB_OUTPUT"

    - name: Install embedding precompute deps
      continue-on-error: true
      shell: bash
      run: python -m pip install --no-cache-dir fastembed numpy google-cloud-storage jsonschema pydantic cachetools || true
```

Two load-bearing details:

1. **Export `VPYTHON` as an absolute path** — the deploy step's `[ -x "${VPYTHON}" ]` check is the contract that makes the toolcache path resolvable. `command -v` would only find executables on `$PATH`; the toolcache path is not on `$PATH` at the point the deploy step runs (the `$GITHUB_PATH` prepend from step N only takes effect for steps that run AFTER the action).
2. **Probe the same import surface `deploy.sh` probes** — surface the success/failure signal as an output so callers can short-circuit the probe loop with a known outcome. The probe's stdout goes to the action's log; the result goes to `$GITHUB_OUTPUT`. If the probe fails, `deploy.sh` will fail at the same step but at least the operator sees BOTH the action-level failure AND the script-level failure in the same job log.

### Deploy script side

```bash
# AFTER (PR #8380)
_EMBED_PY=""
# Always trust the explicit VPYTHON override first — bypass command -v so an
# absolute path the calling workflow exported resolves directly without
# needing to be on $PATH.
if [ -n "${VPYTHON:-}" ] && [ -x "${VPYTHON}" ]; then
    if "${VPYTHON}" -c 'import fastembed, numpy, google.cloud.storage; import mvp_site.agent_prompts' >/dev/null 2>&1; then
        _EMBED_PY="${VPYTHON}"
    else
        echo "WARNING: VPYTHON='${VPYTHON}' set but failed import probe — falling through to PATH lookup" >&2
    fi
fi
if [ -z "$_EMBED_PY" ]; then
    for _cand in ./vpython vpython python; do
        [ -n "$_cand" ] || continue
        command -v "$_cand" >/dev/null 2>&1 || continue
        if "$_cand" -c 'import fastembed, numpy, google.cloud.storage; import mvp_site.agent_prompts' >/dev/null 2>&1; then
            _EMBED_PY="$_cand"
            break
        fi
    done
fi
```

The `python3` candidate is dropped because:
- On a self-hosted Mac runner, `python3` is the system Python (no fastembed)
- `python` is what `actions/setup-python` prepends to `$PATH` via `$GITHUB_PATH`
- On a GitHub-hosted runner both work; on self-hosted only `python` works

### Diagnostic message discipline

The `PRECOMPUTE_FAILED` message expanded from 1 line to 6 lines:

```bash
echo "PRECOMPUTE_FAILED: no interpreter with fastembed+numpy+google-cloud-storage+mvp_site.agent_prompts found; aborting deploy" >&2
echo "  Tried (in order):" >&2
if [ -n "${VPYTHON:-}" ]; then
    echo "    VPYTHON='${VPYTHON}' (exists: $([ -x "${VPYTHON}" ] && echo yes || echo no))" >&2
else
    echo "    VPYTHON=(unset — set by .github/actions/setup-precompute-deps when pip install succeeds)" >&2
fi
echo "    ./vpython, vpython, python (PATH lookup; python3 was deliberately removed — system Python on" >&2
echo "      self-hosted Mac runners has no fastembed and was the failure mode)" >&2
echo "  To bypass for this deploy, set SKIP_PROMPT_EMBEDDINGS_PRECOMPUTE=true" >&2
echo "  Diagnostic: run 'gh workflow run auto-deploy-dev.yml -r main' after pulling this PR's fix; the" >&2
echo "  action should now export VPYTHON=$pythonPath from setup-python's outputs.python-path." >&2
```

The next failure is debuggable from the failure email alone — the operator doesn't need to read source.

## Regression test (verified, 10/10 pass)

`tests/test_precompute_deps_self_hosted.py` enforces all three surfaces:

| Class | Test | Enforces |
|---|---|---|
| `TestSetupPrecomputeActionExportsVpython` | `test_action_uses_composite_run` | Action is composite (not reusable workflow) |
| | `test_action_calls_setup_python` | setup-python is invoked |
| | `test_action_exports_vpython_to_github_env` | VPYTHON written to `$GITHUB_ENV` AND sourced from `setup-python.outputs.python-path` |
| | `test_action_declares_precompute_ready_output` | `precompute-ready` output is declared AND sourced from probe step |
| `TestDeployShHonorsVpython` | `test_deploy_sh_references_vpython_env` | deploy.sh reads `$VPYTHON` |
| | `test_deploy_sh_does_not_python3_first` | Old `${VPYTHON:-} ./vpython vpython python3` loop is forbidden |
| | `test_deploy_sh_vpython_branch_is_absolute_path` | deploy.sh uses `[ -x "${VPYTHON}" ]` (not `command -v`) |
| | `test_precompute_failed_message_lists_candidates` | Error message lists candidates + VPYTHON status |
| | `test_precompute_failed_message_suggests_setup_precompute_action` | Error message references the action |
| `TestDocCommentInDeploySh` | `test_deploy_sh_documents_self_hosted_runner_root_cause` | Source comment documents the 2026-07-13 root cause |

```bash
PYTHONPATH=. python3 -m pytest tests/test_precompute_deps_self_hosted.py -v
# 10 passed in 0.13s
```

## "Is the deploy actually live?" sanity check recipe (the Step 5.5 contract)

Whenever a `❌ FAILED: dev Deployment` email arrives, BEFORE claiming the user's PR is broken:

```bash
# 1. What revision is live?
gcloud run services describe mvp-site-app-dev \
  --region=us-central1 --project=worldarchitecture-ai \
  --format='value(status.latestReadyRevisionName, status.latestCreatedRevisionName, metadata.labels.commit-sha-full)'

# 2. Is /health returning 200?
URL=$(gcloud run services describe mvp-site-app-dev \
  --region=us-central1 --project=worldarchitecture-ai \
  --format='value(status.url)')
curl -fsS "${URL}/health"
```

Decision matrix:

| Live state | User-facing answer |
|---|---|
| Live revision == PR HEAD AND /health returns 200 | "Your PR is live and healthy. The failing deploy step is a CI infra issue, not your PR's fault." Diagnose the CI infra failure separately. |
| Live revision == PR HEAD AND /health returns 5xx | Mode 1-6 territory. Pull revision logs from the current (live) revision. |
| Live revision != PR HEAD | Compare timestamps. May have shipped via earlier deploy. |
| No new revision since PR HEAD timestamp | The failing run never reached `gcloud run deploy` (Mode 7 territory). Verify whether a sibling run shipped the commit. |

For PR #8380 / cc7ec0a: `latestReadyRevisionName == latestCreatedRevisionName == mvp-site-app-dev-03841-ftq`, `commit-sha-full=cc7ec0a06`, `/health` returns 200 → the user's PR #8337 shipped via the 20:00:18 sibling run; the 20:00:20 run failed at Mode 7 (PRECOMPUTE_FAILED) and the failure-email step fired. The right answer was "your PR is fine, only the deploy CI is broken."

## Why this is a NEW failure class (not just another revision-start failure)

`wa-cloud-run-deploy-failure-debug` Modes 1-6 all describe failures AT THE REVISION START (container startup, ENTRYPOINT, health check, OOM, env var, protobuf). Mode 7 is a failure BEFORE the revision is even attempted — the deploy script's interpreter probe exits 1 at `deploy.sh:466` and `gcloud run deploy` never runs. Different diagnosis path, different fix surface, different user-facing answer.

| Question | Mode 1-6 (revision start) | Mode 7 (script probe) |
|---|---|---|
| Where does it fail? | `gcloud run deploy` step, Cloud Run revision logs | `deploy.sh` step, before `gcloud run deploy` runs |
| What's the symptom? | `latestCreatedRevisionName != latestReadyRevisionName` OR revision logs show `can't open`, `SIGKILL`, `ModuleNotFoundError` | Deploy step exit code 1 with `PRECOMPUTE_FAILED:` in stdout |
| Is the user's PR on the live service? | Depends on whether a sibling deploy succeeded | **Probably yes** — sibling deploys in the same push window often shipped it |
| First-place fix | Revision-log diagnosis (Modes 1-6) | Composite-action env-export contract (Mode 7) |

## Related historic commits (the precompute install lineage)

| SHA | Description | Pattern |
|---|---|---|
| `508cdad544` | precompute fail-loud + drop silent FIREBASE_STORAGE_BUCKET fallback | First fail-loud precompute probe |
| `4d3a684176` | install pydantic+cachetools for precompute GHA setup | Add missing transitive deps |
| `c341787f` | CI tolerate python3-only precompute runners | **Inverse of this fix** — accepts the failure instead of fixing it |
| `1edc6733fc` | reduce default precompute batch size to 8 to prevent runner OOM | Capacity fix, not architecture fix |
| `d85d05979b` | skip precompute in PR preview to prevent OOM | Escape hatch, not root-cause fix |

PR #8380 is the first root-cause fix at the action↔script contract level; everything else was a capacity/transitive-dep/policy fix.

## PR + issue links

- Fix PR: https://github.com/$GITHUB_REPOSITORY/pull/8380
- GH issue: https://github.com/$GITHUB_REPOSITORY/issues/8379
- Originating GHA run: https://github.com/$GITHUB_REPOSITORY/actions/runs/29280658965
- Local debug log (78KB of `gh api jobs/logs` output, 944 lines): `/tmp/job_86920749719.log`
- Triggering merge commit (PR #8337 merge, NOT the failing commit itself): `cc7ec0a06a47ddfa497dc2af1ee1b1677b0efe96`
- PR #8337 (the user's actual work — fine): https://github.com/$GITHUB_REPOSITORY/pull/8337
