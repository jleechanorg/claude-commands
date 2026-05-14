---
name: repro-twin-clone-evidence
description: Canonical /repro — default copy+targeted bug repro; optional level-up five-class suite, twin clones, repro_copy, exports, env. Slash commands only point here.
---

# Repro evidence (canonical)

**Agents:** Implement repro by following **this file only**. Do not duplicate branching logic in `.claude/commands/repro.md` or `repro_copy.md` — those files only **point** here.

---

## 0. Routing: what to run (read first)

| User intent | Run |
|-------------|-----|
| **`/repro`**, `/repro <campaign_id>`, or “copy and reproduce *this* bug” | **§2** only — **do not** run `testing_mcp/run_level_up_class_repro_suite.sh` unless the user (or args) explicitly opts in per §5. (`scripts/run_level_up_class_repro_suite.sh` is a legacy forwarder.) |
| “Five-class”, “level-up suite”, “run all level_up_class”, `MCP` harness RED suite | **§5** (heavy opt-in) after §1 env. |
| “repro_copy”, canonical+variant replay | **§6** and `wiki/concepts/ReproCopyCampaignProcedure.md`. |
| First copy read-only, second copy gets all actions | **§4** (twin) within §2. |

---

## 1. Environment (required for any real Firestore / MCP repro)

| Variable | Purpose |
|----------|---------|
| `WORLDAI_DEV_MODE=true` | Required for `mvp_site` clock skew / deployment validation on import (`base_test` → `apply_clock_skew_patch`). **Without this**, `python -c "import testing_mcp"` often fails. |
| `TESTING_AUTH_BYPASS=true` | Local server accepts test requests. |
| `ALLOW_TEST_AUTH_BYPASS=true` | Pairs with bypass. |
| `MCP_TEST_MODE=real` | No mocks. |
| `MOCK_SERVICES_MODE=false` | No mocks. |
| `PYTHONPATH=$REPO_ROOT:$REPO_ROOT/mvp_site` | Imports. |
| `GOOGLE_APPLICATION_CREDENTIALS` | Service account (often `~/serviceAccountKey.json`). |

Use repo venv: `./venv/bin/python` or `LEVEL_UP_REPRO_PYTHON=...` for the optional suite in §5.

---

## 2. Default: copy campaign + targeted bug repro (most `/repro` sessions)

**Goal:** Get a **safe** Firestore copy under the test user, then **reproduce one reported bug** (UI, API, or a **narrow** test), not the full five-class harness.

1. **Resolve source** — **ALWAYS** use `scripts/copy_campaign.py --find-by-id <CAMPAIGN_ID>` — this resolves the owner UID dynamically via Firestore collection group scan. **Never** pass a hardcoded or guessed `source_user_id` — the MCP `admin_copy_campaign_user_to_user` tool requires exact UIDs and fails with "Source campaign not found" when wrong. The Python script is the only reliable path.
2. **Destination** — Default **jleechantest** uid: `0wf6sCREyLcgynidU5LjyZEfm7D2` (`--dest-user-id`).
3. **Twin (recommended for destructive repro)** — Two independent runs with the same dest uid and different `--suffix` values, per §4.
4. **Single copy (quick smoke)** — One `--find-by-id` + `--dest-user-id` + `--suffix` if the bug does not need a clean baseline.
5. **Targeted repro** (pick what matches the report):
   - **Level-up / time / planning** — e.g. `./run_tests.sh $PROJECT_ROOT/tests/test_freeze_time_choices.py` on the branch with the fix; or manual UI on preview with the **test-subject** campaign id; look for `TIME_FREEZE` / turn counter in logs.
   - **Narrow MCP** — a **single** `testing_mcp/test_*.py` if it maps to the bug; **not** the whole `run_level_up_class_repro_suite` unless §5.
   - **Replay** — `scripts/repro_copy_campaign.py` (§6) when the procedure needs dual-track replay.
6. **Evidence** — `scenario_results_*.json`, server logs, or `download_campaign.py` (§7) as appropriate; follow `~/.claude/skills/evidence-standards/SKILL.md` for video/tmux if non-trivial.

**Anti-pattern:** Always chaining `./testing_mcp/run_level_up_class_repro_suite.sh` for every `/repro` — that script clones extra baselines, runs **five** long LLM-heavy classes, and is for **level-up class RED** collection, not generic bugs.

**Anti-pattern:** Using MCP `admin_copy_campaign_user_to_user` with a guessed or hardcoded `source_user_id`. This tool does NOT resolve UIDs dynamically — if the UID is wrong, it fails silently. Always use `scripts/copy_campaign.py --find-by-id <CAMPAIGN_ID>` which performs a Firestore collection group scan.

---

## 3. Align harness user with jleechantest (for MCP or §5)

Firestore copies for MCP tests use `--dest-user-id` = harness user. For **`<your-email@gmail.com>`** (`0wf6sCREyLcgynidU5LjyZEfm7D2`):

```bash
export MCP_TEST_PARALLEL_USER_ID=0wf6sCREyLcgynidU5LjyZEfm7D2
```

`MCP_TEST_PARALLEL_USER_ID` is read in `testing_mcp/lib/base_test.py` and sets `X-Test-User-ID` for the local server. If unset, the harness may use a synthetic id — not the same as “clone to jleechantest” evidence.

---

## 4. Twin baseline + test subject (no contamination)

When the **first** copy must never receive `process_action`, GOD_MODE, or destructive edits:

1. Two independent `scripts/copy_campaign.py --find-by-id <SOURCE>` runs with the **same** `--dest-user-id` (typically `0wf6sCRE…` when §3 applies).
2. Suffix examples: ` (repro-baseline read-only)` and ` (repro-test subject)`.
3. **Baseline:** read-only; optional parity (story count) vs test clone.
4. **Test clone:** all scans, replays, `process_action`, `repro_copy_campaign.py` replay.
5. **Story alignment to bug instant:** `copy_campaign` does **not** truncate. Optional: manual delete of newer story docs on **test** only, or compare to an earlier `download_campaign` export. Document the gap if automation is missing.

Helper (if present in tree): `testing_mcp/lib/campaign_clone_for_repro.py` (`run_copy_campaign_find_by_id`, `default_clone_env`).

---

## 5. Optional: level-up “five-class” harness (heavy, opt-in)

**When:** User explicitly requests the full RED suite, or arguments mention: `five-class`, `level-up-suite`, `run_level_up_class_repro`, or all `test_level_up_class_*.py` together.

**Definition:** The five MCP scripts under `testing_mcp/test_level_up_class_{1..5}_*.py` (stale lockout, story projection strip, narrative XP desync, historical residue, signal-resolver cascade).

**Run:** Canonical path: **`testing_mcp/run_level_up_class_repro_suite.sh`** (orchestrates the five `test_level_up_class_*.py` files; twin baseline parsing uses a **`read` loop**, not `mapfile`, so macOS `/bin/bash` 3.2 works). A thin **`scripts/run_level_up_class_repro_suite.sh`** forwarder exists for older docs.

```bash
cd "$REPO_ROOT"
set -o pipefail
./testing_mcp/run_level_up_class_repro_suite.sh 2>&1 | tee /tmp/your-project.com/level_up_5_class_repro.log
```

The suite can **clone Class 2 and Class 4** test subjects from baseline campaigns once per run: set `LEVEL_UP_SOURCE_CLASS2_ID` / `LEVEL_UP_SOURCE_CLASS4_ID`, or rely on script defaults. `LEVEL_UP_SKIP_BASELINE_CLONE=1` keeps in-test `--find-by-id` clone only. `LEVEL_UP_SUITE_PARALLEL=1` (default) runs all five **concurrently**; `LEVEL_UP_SUITE_PARALLEL=0` for sequential. When piping to `tee`, `set -o pipefail` so exit status reflects the suite. If you see `Permission denied` on the canonical script, `chmod +x testing_mcp/run_level_up_class_repro_suite.sh` or run `bash ./testing_mcp/run_level_up_class_repro_suite.sh`.

Evidence bundles: `/tmp/your-project.com/<branch-scoped>/level_up_class_*` per harness.

### Reading `SUMMARY: Passed / Failed` (not the same as “bug yes/no”)

- Harness **Failed** often means `errors` non-empty; many scenarios record **`REPRODUCED`** in errors on purpose (RED), with `passed: false`.
- **`Passed`** is not “bug fixed” — it may mean the bad state was not hit.
- Exit code **1** is common when collecting RED evidence.

---

## 6. `scripts/repro_copy_campaign.py` (canonical + variant)

- Produces **canonical** and **variant** copies (variant may delete last scene with explicit flags).
- Replays the **same** user input on **both** — different from §4 (baseline never replayed).
- Invocation: `wiki/concepts/ReproCopyCampaignProcedure.md`.
- Evidence standards: `~/.claude/skills/evidence-standards/SKILL.md` (if present).

---

## 7. Save state after repro (avoid drift)

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

## 8. Slash command behavior (`/repro` / `repro.md`)

`repro.md` is a **pointer only** (no extra routing in the file). The command file only says: read **`repro-twin-clone-evidence/SKILL.md`** and execute per **`$ARGUMENTS`**, with **default = §2** (not §5). **`/repro_copy`**: see `.claude/commands/repro_copy.md` and **`repro-copy.md`**.

---

## 9. Related wiki

- `wiki/concepts/ReproCopyCampaignProcedure.md`
- `wiki/concepts/NormalizationAtomicity.md`
- `wiki/concepts/MCPTestFirebaseAdminStall.md` — raw Firestore in harness vs CLI

---

## 10. Checklist (honest)

| Step | Done? |
|------|--------|
| §1 env; imports work | |
| **§2** copy(ies) created; test subject id recorded | |
| **§2** targeted repro (not auto-five-class) | |
| §5 only if user asked for full suite | |
| §7 export if you need a frozen snapshot | |
