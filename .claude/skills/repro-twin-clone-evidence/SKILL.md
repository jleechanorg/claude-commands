---
name: repro-twin-clone-evidence
description: Single source of truth for /repro — twin clones, jleechantest alignment, five-class level-up repro suite, repro_copy, exports, env. Slash commands only point here.
---

# Repro evidence (canonical)

**Agents:** Implement repro by following **this file only**. Do not duplicate branching logic in `.claude/commands/repro.md` or `repro_copy.md` — those files only **point** here.

---

## 1. Environment (required for any real Firestore / MCP repro)

Set (or rely on defaults in `scripts/run_level_up_class_repro_suite.sh`):

| Variable | Purpose |
|----------|---------|
| `WORLDAI_DEV_MODE=true` | Required for `mvp_site` clock skew / deployment validation on import (`base_test` → `apply_clock_skew_patch`). **Without this**, `python -c "import testing_mcp"` often fails. |
| `TESTING_AUTH_BYPASS=true` | Local server accepts test requests. |
| `ALLOW_TEST_AUTH_BYPASS=true` | Pairs with bypass. |
| `MCP_TEST_MODE=real` | No mocks. |
| `MOCK_SERVICES_MODE=false` | No mocks. |
| `PYTHONPATH=$REPO_ROOT:$REPO_ROOT/mvp_site` | Imports. |
| `GOOGLE_APPLICATION_CREDENTIALS` | Service account (often `~/serviceAccountKey.json`). |

Use repo venv: `./venv/bin/python` or `LEVEL_UP_REPRO_PYTHON=...` for the suite.

---

## 2. Five original bug reports (level-up Classes 1–5)

**Definition:** The five MCP scripts under `testing_mcp/test_level_up_class_{1..5}_*.py` (stale lockout, story projection strip, narrative XP desync, historical residue, signal-resolver cascade).

**Run all five in order:**

```bash
cd "$REPO_ROOT"
./scripts/run_level_up_class_repro_suite.sh 2>&1 | tee /tmp/your-project.com/level_up_5_class_repro.log
```

The suite script can **clone Class 2 and Class 4 test subjects from baseline campaigns** on the dest user **once per run** (fresh id each time): set `LEVEL_UP_BASELINE_CLASS2_ID` / `LEVEL_UP_BASELINE_CLASS4_ID` to read-only baselines on `MCP_TEST_PARALLEL_USER_ID`, or rely on the script defaults. Use `LEVEL_UP_SKIP_BASELINE_CLONE=1` to keep the old in-test `--find-by-id` clone only.

By default `LEVEL_UP_SUITE_PARALLEL=1` runs all five test files **concurrently** (separate logs under `LEVEL_UP_SUITE_LOG_DIR` or a temp dir); set `LEVEL_UP_SUITE_PARALLEL=0` for sequential runs. When piping to `tee`, use `set -o pipefail` first so the pipeline exit status reflects the suite (otherwise `tee` may mask a non-zero exit).

If you see `Permission denied`, run `chmod +x scripts/run_level_up_class_repro_suite.sh` or invoke with `bash ./scripts/run_level_up_class_repro_suite.sh` (same behavior).

Evidence bundles: `/tmp/your-project.com/<branch-scoped>/level_up_class_*` per harness.

### Reading `SUMMARY: Passed / Failed` (not the same as “bug yes/no”)

The harness prints counts like `Passed: 1` / `Failed: 1` by counting scenarios whose result dict has **`"passed": true`** vs **`false`**. That label is **not** “product bug vs no bug.”

- **`Failed` (harness)** usually means the scenario’s **`errors` list was non-empty**. For many Classes 1, 2, 4, and 5, a **successful reproduction** is recorded as an error string containing **`REPRODUCED`** (or similar). Those scenarios are **`passed: false`** on purpose — they are **RED evidence**, not a broken test run.
- **`Passed` (harness)** means that scenario reported **no errors** — often “bad state not detected” for that step, or a **negative control** behaved as expected, or (Class 3) the narrative/XP check stayed consistent. It does **not** automatically mean “the original bug is fixed.”
- **INCONCLUSIVE** strings (e.g. Class 3 when the LLM never announced `+XP` in narrative) also land in `errors` and count as harness **Failed**; that is flaky LLM coverage, not necessarily the same as RED repro.

**What to do:** Open `scenario_results_checkpoint.json` (or the console block for each `=== SCENARIO ===`) and read the **`errors`** strings. Treat **`REPRODUCED`** as “bug observed this run.” Treat **`INCONCLUSIVE`** as “contract not exercised; rerun or adjust.”

**Exit codes:** Each class script exits **1** if **any** scenario has `passed: false`. The five-class shell script then exits non-zero if any class did. That is **expected** when you are collecting RED repro evidence, not proof that the skill or harness crashed.

---

## 3. Align harness user with jleechantest (optional but required for “clone to jleechantest”)

Firestore copies use `--dest-user-id` = **`ctx.user_id`** from `MCPTestBase`. The MCP client must use the **same** UID as the account that owns the cloned campaigns.

To run the five-class suite so clones land under **`<your-email@gmail.com>`** (`0wf6sCREyLcgynidU5LjyZEfm7D2`):

```bash
export MCP_TEST_PARALLEL_USER_ID=0wf6sCREyLcgynidU5LjyZEfm7D2
./scripts/run_level_up_class_repro_suite.sh
```

`MCP_TEST_PARALLEL_USER_ID` is read first in `testing_mcp/lib/base_test.py` `_resolve_user_id()` and sets `X-Test-User-ID` for the local server.

If unset, the harness generates a synthetic id (`test-<TEST_NAME>-<run_id>`). That is fine for CI smoke; it is **not** the same as “copy to jleechantest” evidence.

---

## 4. Twin baseline + test subject (no contamination)

Use when the **first** copy must never receive `process_action`, GOD_MODE, or destructive edits.

1. Two independent `scripts/copy_campaign.py --find-by-id <SOURCE>` runs with the **same** `--dest-user-id` (typically `0wf6sCRE…` when §3 is applied).
2. Suffix examples: ` (repro-baseline read-only)` and ` (repro-test subject)`.
3. **Baseline:** read-only; optional parity (story count) vs test clone.
4. **Test clone:** all scans, replays, `process_action`, `repro_copy_campaign.py` replay.
5. **Story alignment to bug instant:** `copy_campaign` does **not** truncate. Optional: manual delete of newer story docs on **test** only, or compare to an earlier `download_campaign` export. Document the gap if automation is missing.

Helper: `testing_mcp/lib/campaign_clone_for_repro.py` (`run_copy_campaign_find_by_id`, `default_clone_env`).

---

## 5. `scripts/repro_copy_campaign.py` (canonical + variant)

- Produces **canonical** and **variant** copies (variant may delete last scene with explicit flags).
- Replays the **same** user input on **both** — different from §4 (baseline never replayed).
- Invocation and evidence layout: `wiki/concepts/ReproCopyCampaignProcedure.md`.
- Evidence standards: `~/.claude/skills/evidence-standards/SKILL.md` (if present).

---

## 6. Save state after repro (avoid drift)

```bash
export WORLDAI_DEV_MODE=true
export WORLDAI_GOOGLE_APPLICATION_CREDENTIALS="${WORLDAI_GOOGLE_APPLICATION_CREDENTIALS:-$HOME/serviceAccountKey.json}"
./venv/bin/python scripts/download_campaign.py \
  --uid 0wf6sCREyLcgynidU5LjyZEfm7D2 \
  --campaign-id <TEST_CAMPAIGN_ID> \
  --output-dir /tmp/your-project.com/repro-exports/<slug> \
  --format txt
```

---

## 7. Slash command behavior (`/repro`)

- **No conditional logic** in the command file — only: “Read **`repro-twin-clone-evidence`** (`/.claude/skills/repro-twin-clone-evidence/SKILL.md`) and execute the sections above as appropriate to `$ARGUMENTS`.”
- **`/repro_copy`**: Still documented in `.claude/commands/repro_copy.md` as “read `repro-copy.md` skill”; detailed routing for copy+replay lives in **`repro-copy.md`** + §5 here.

---

## 8. Related wiki

- `wiki/concepts/ReproCopyCampaignProcedure.md`
- `wiki/concepts/NormalizationAtomicity.md`
- `wiki/concepts/MCPTestFirebaseAdminStall.md` — raw Firestore in harness vs CLI

---

## 9. Honest checklist

| Step | Done? |
|------|--------|
| §1 env set; import `testing_mcp` works | |
| §2 five scripts run (or intentional subset) | |
| §3 if claiming jleechantest: `MCP_TEST_PARALLEL_USER_ID` set | |
| §4 twin procedure if baseline must stay clean | |
| §6 export saved for test campaign | |
