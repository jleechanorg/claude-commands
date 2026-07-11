# PR Green Definition — Skill

> **SKEPTIC GATE REMOVED (2026-07-09).** The skeptic-cron/self-verify system was deleted from worldarchitect.ai (repo removal PR #8217; lingering workflow registrations disabled 2026-07-09). Ignore every Skeptic/Gate-7 instruction below — the merge bar is now 6-green: CI green + no conflicts + CR APPROVED + Bugbot clean + comments resolved + evidence (/er PASS at head). Do not post /skeptic; nothing answers it.

Design integrity is the mandatory prerequisite. 7-green is the minimum bar. These are not equal — a PR that achieves 7-green while violating the design doc or architecture contract is a regression, not a success. **You must fail such a PR at the design gate, before checking 7-green.**

---

## The Hierarchy (in force, highest to lowest)

```
1. Design Gate        ← prerequisite, must pass first
2. Regression Gate    ← no new boundary violations
3. 7-Green            ← minimum merge bar (CI + CR + Bugbot + comments + evidence + skeptic)
```

If Design Gate fails → **do not check 7-green, do not merge**.

---

## Step 0: Design Decision Gate

**Applies when: PR has >50 non-test production delta lines.**

The PR description MUST contain a `## Design Decision` section with:
1. **What this PR does** — one paragraph
2. **Architectural boundaries affected** — which files/modules, how
3. **Linked artifact** — a bead ID (`rev-xxxx`) OR a `.md` doc in `~/roadmap/` or `docs/design/`
4. **What this PR does NOT do** — explicit out-of-scope (prevents creep)

**If the linked artifact exists and describes invariants or boundaries:**
- READ the artifact
- Verify the diff respects stated boundaries
- FAIL if the diff changes files the design doc said wouldn't be touched
- FAIL if the diff violates an invariant the design doc said would be preserved

**Failure message:**
```
Design gate FAIL:
- PR exceeds 50 non-test production delta lines but lacks ## Design Decision section
OR
- Design doc [link] exists but diff violates its stated boundaries:
  * [specific violation]
Do not merge. Fix the design doc or the diff.
```

---

## Step 1: Regression Gate

After design gate passes, run these checks before touching 7-green.

### 1a. Non-regression check
Does this PR undo or weaken a previously merged architectural gate (e.g., `design-doc-gate.yml`)? Check `design-doc-gate.yml` for current grep gates and verify the diff does not violate them.

### 1b. Evidence quality check
If the PR has a `## Evidence` section in the description:
- Reject fabricated/placeholder patterns (`simulated`, `example.com`, `<screenshot path>`, `TODO`, `TBD`)
- Require real URLs, terminal output, or structured test output
- If evidence section is empty or contains fabrication → FAIL

### 1c. Architectural drift check
If the PR modifies `mvp_site/world_logic.py`, `mvp_site/agents.py`, or `mvp_site/rewards_engine.py`:
- Verify changes respect the file-responsibility table in `zfc-leveling-roadmap/SKILL.md` (or the relevant domain skill)
- Flag any change that adds logic to a "MUST NOT DO" column
- Flag any change that creates a second canonicalization path

---

## Step 1.5: API Pre-flight (MANDATORY — run EVERY TIME you state or repeat a /green claim)

**RECURRING FAILURE (4x+):** False 7-green declarations on PRs with CONFLICTING merge state and no CR APPROVAL. Most recent instance (2026-07-10, PR #8268): verified `mergeable=MERGEABLE` at T, an unrelated same-author PR merged to main at T+2h17m editing the exact same lines, PR #8268 silently flipped to CONFLICTING, and the stale "ready to merge" claim was repeated ~9 hours later before anyone re-checked. This pre-flight prevents all of these.

```bash
gh pr view <PR> --json headRefOid,mergeable,mergeStateStatus,reviewDecision | python3 -m json.tool
```

| Field | Required value | If wrong → |
|-------|---------------|-----------|
| `mergeable` | `MERGEABLE` | STOP: branch has a conflict. Gate 2 FAIL. Do not proceed, do not call it green. |
| `mergeStateStatus` | `CLEAN` (not `DIRTY`/`CONFLICTING`/`UNSTABLE` while CI is pending) | Same as above — this is the authoritative live signal, not a cached memory of an earlier check. |
| `reviewDecision` | `APPROVED` | STOP: CR has not approved (unless CodeRabbit check is success). Gate 3 FAIL. Do not proceed. EXCEPTION (2026-07-11 slow-bot policy): if ONE once-per-head review request has gone >2h with total CR silence, Gate 3 may be satisfied by a substitute gate (Bugbot approval or a codex/cross-model adversarial pass logged in the PR); CHANGES_REQUESTED always still blocks, and late CR feedback must be fixed post-hoc. |

**A merge conflict is an automatic, non-negotiable FAIL of Gate 2. No other gate compensates for it** — all-green CI + CR APPROVED + resolved comments + evidence PASS does NOT make a CONFLICTING PR green. State the gate result as `mergeable=<value> as of <SHA> @ <UTC timestamp>` — it is a live snapshot, not a fact that persists across time.

**⚠️ MUST RE-RUN before EVERY point you state a /green verdict, not just once per session:**
1. Before starting gate checks — initial pre-flight.
2. Immediately before any verbal "/green" or "ready to merge" report.
3. Immediately before any merge action (`gh pr merge`).
4. **Before repeating a prior /green claim after ANY elapsed time gap, new session, or new conversation turn** — mergeability is base-branch-dependent and recomputed asynchronously by GitHub; it can flip hours after your last check with zero action on the PR's own branch. Treat every prior "/green" statement as expired the moment you're about to act on or repeat it — re-fetch, don't recall.

This check takes 3 seconds. Skip it and you will produce false 7-green claims.

**When you find a conflict, resolve it — don't stop and ask.** Per `~/.claude/CLAUDE.md` "Merge conflicts are routine, not an escalation event": rebase, take the correct/newer side of a mechanical collision (e.g. two independent fixes to the same CI-infra lines), reapply your own changes, push, and report the resolution afterward. Only escalate if the conflict is genuinely ambiguous business logic.

---

## Step 2: 7-Green Checks

Only run these AFTER Steps 0, 1, and 1.5 all pass.

| # | Gate | Command / Check |
|---|------|----------------|
| 1 | CI green | All core check runs pass (`Staging Canary Gate`, `find-openclaw-json`, `Full canary (6/6)`) |
| 2 | No conflicts | `mergeable=MERGEABLE`, `mergeStateStatus=CLEAN` (re-verified fresh in Step 1.5 — never trust a cached/prior-turn value; ANY conflict = automatic FAIL regardless of gates 1/3-7) |
| 3 | CR APPROVED | `reviewDecision=APPROVED` or CodeRabbit check is success |
| 4 | Bugbot clean | `cursor[bot]` check-run conclusion is not `failure` |
| 5 | Comments resolved | Zero unresolved non-nit inline review comments |
| 6 | Evidence pass | Evidence review verdict is `PASS`, OR `evidence-gate.yml` CI passed |
| 7 | Skeptic PASS | `github-actions[bot]` posted `VERDICT: PASS` on the PR — SHA must match `headRefOid` |

For detailed command syntax for each gate, see `7green.md` in `~/.hermes/procedures/` or run `gh pr checks --repo <owner/repo> <pr>`.

---

## Stop Conditions

**STOP and do not proceed to 7-green when:**
- Design Decision section is missing or linked artifact does not exist
- Diff violates stated design boundaries
- Evidence section contains fabrication
- A grep gate in `design-doc-gate.yml` would fail

**STOP and escalate (do not keep iterating) when:**
- You have made 3+ commits attempting to fix the same failing check
- You are uncertain whether the fix creates a new architectural violation
- The PR description's design doc says X but the code does Y and you cannot reconcile them

Escalation is a success, not a failure. Report what you found, what you're uncertain about, and what decision is needed.

---

## Related

- `.claude/skills/zfc-leveling-roadmap/SKILL.md` — file-responsibility table for level-up/XP work
- `.claude/skills/field-ownership-contracts.md` — field writer registry for shared dicts
- `design-doc-gate.yml` — automated grep gates for architectural boundaries
- `skeptic-cron.yml` — LLM-based skeptic gate (condition 7)
