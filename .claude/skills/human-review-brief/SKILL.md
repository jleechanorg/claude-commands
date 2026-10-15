---
name: human-review-brief
description: Standardized end-of-turn human review brief (## What Was Done and ## What to Review as a Human) grounded in empirical Mac and Linux agent blind spots. Enforces the LLM-verifiability gate (If the LLM Can Verify It, Do It Yourself) and requires Why the LLM cannot do this on every human review item.
---

# Human Review Brief (`human-review-brief` / `/what-to-review`)

## Core Gate: "If the LLM Can Verify It, Do It Yourself (Never Put It in `What to Review as a Human`)"

Before placing ANY bullet into `## What to Review as a Human`, ask:
> *"Can an LLM, unit test, headless browser, DOM measurement (`getBoundingClientRect` / `getComputedStyle`), `gh` CLI check, `git merge-tree`, `grep`, `shasum` / `SHA-256` check, or cross-model review (`advice`) verify this autonomously?"*

- **If YES -> DO IT NOW yourself** and record the verified proof under `## What Was Done`.
- **NEVER ask the human to confirm LLM-verifiable facts**, including:
  - `grep` / token counts (e.g., *"Confirm `scan.py` has 0 occurrences of `re.compile`"*),
  - `SHA-256` digest matches across hosts or files,
  - line-count (`LOC`) deltas or file counts,
  - unit/integration test pass rates or CI check statuses,
  - deterministic code or schema invariants that a test can assert.
- **Mandatory Sub-Bullet (`Why the LLM cannot do this:`)**:
  Every item listed under `## What to Review as a Human` MUST include an explicit sub-bullet:
  - `Why the LLM cannot do this: <exact structural reason why no LLM or automated tool can verify or authorize this>`
- **The 4 Valid Reasons Why an LLM Cannot Do the Work**:
  1. **Authority / Permission Boundary**: Action requires human authorization that agents are forbidden from self-approving (`MERGE APPROVED`, spending money / billing checkout, production deployment, credential/secret rotation, or destructive actions).
  2. **Subjective Product / UX Taste or Tradeoff Preference**: Multiple valid product or engineering tradeoffs exist (e.g., visual aesthetics, pacing/feel, threshold/budget preference like `10,000` vs `5,000` words per capture buffer) and only the human operator knows their personal preference.
  3. **Uninstrumented External / Physical Ground Truth**: Behavior lives outside any CLI/API/DOM/log the agent can reach (e.g., physical device ergonomics, 2FA-locked external portal, legal/tax representation sign-off).
  4. **Intent Alignment vs. Shared Assumption**: The agent implemented and verified interpretation `X` of an ambiguous request, and needs the human to confirm `X` matched their intended product goal (not merely that the code implements `X`).
- **Zero-Item Escape Hatch**:
  When all verification was completed autonomously by the LLM and no subjective product/UX tradeoff remains, `## What to Review as a Human` MUST state:
  > `None — all code, test, and sync checks were verified autonomously by the LLM. Only human authorization (MERGE APPROVED) is required because agents are forbidden from self-approving merges.`

---

## When to Apply
- **Full Brief (`## What Was Done` + `## What to Review as a Human`)**: Required when finishing a PR update, code/evidence review, multi-step feature implementation, or merge-readiness report, and inside `/pr-summary` breakdowns.
- **Compact Inline Form**: On small local coding turns that do not update a PR or claim merge readiness, emit a 2–3 bullet inline summary of what changed, what was verified autonomously, and any remaining human-only decision (with `Why the LLM cannot do this:`). Skip on trivial Q&A or read-only lookups.

---

## Section 1: `## What Was Done` (Objective Facts & Autonomous Verification Proof)

Provide a scannable 4-bullet summary of verified facts (including all checks the LLM ran itself instead of offloading to the human):
1. **Outcome & Full Links**: 1–2 sentences stating what actually changed, with full clickable GitHub PR (`https://github.com/<owner>/<repo>/pull/<N>`) and 40-char commit URLs (`https://github.com/<owner>/<repo>/commit/<40-char-sha>`).
2. **Production vs. Non-Production LOC Delta (`/ponytail` Check)**:
   - Format: `Production: +X / -Y (M files) | Non-production: +A / -B (N files) | Total: +(X+A) / -(Y+B)`
   - Explicitly flag if net production lines grew (`+X > -Y`) on a fix where simplification or deletion (`/ponytail`) was expected.
3. **Merge-Tree Cleanliness & Silent-Revert Check vs. `origin/main`**:
   - Do not rely on GitHub `mergeable: MERGEABLE` alone (which misses silent reverts of `origin/main` and smuggled formatter churn). Run:
     ```bash
     git fetch origin main
     TREE=$(git merge-tree --write-tree origin/main HEAD)
     comm -23 <(git diff --name-only origin/main "$TREE" | sort) <(git diff --name-only origin/main...HEAD | sort)
     ```
   - Confirm zero conflict markers, zero files reverted relative to `origin/main`, and zero smuggled multi-file formatter edits.
4. **SHA-Bound Gate & Evidence Matrix (`@ <short-sha>`)**:
   - State the exact status and attested SHA for CI / local equivalents (`/green`), `/es`, `/er`, independent review (`advice`), `/cs`, `/wa`, and cross-host `SHA-256` sync verification. Never claim a prior-SHA receipt covers a new head without explicit delta-based applicability analysis.

---

## Section 2: `## What to Review as a Human` (Human-Only Judgment & Blind-Spot Checklist)

First run the **Core Gate** above: execute every check the LLM can perform itself and move those results into `## What Was Done`. Then, if human judgment, visual taste, or unverified blind-spot risk remains across the 10 empirical Mac + Linux categories below, emit only those items that genuinely require a human — each with `Why the LLM cannot do this:` — or emit the **Zero-Item Escape Hatch**, followed by the two mandatory closing bullets (`What Current Evidence Does NOT Prove` and `Exact Human Decision Needed`).

### The 10 Empirical Mac + Linux Blind-Spot Categories (Verify Autonomously First; Surface Only What the LLM Cannot Decide/Prove)

1. **`Visual / UX / Hidden-State Verification`** *(when UI, CSS, templates, or mobile views change)*:
   - First measure DOM geometry (`getBoundingClientRect` / `getComputedStyle`) and check for `display: none` parents, modal locks, or HUD overlap yourself across `1440x900`, `700–1024px`, and `375x812`.
   - Surface to the human only subjective visual aesthetics/feel with linked before/after frames and video timestamps, plus `Why the LLM cannot do this: Subjective Product / UX Taste or Tradeoff Preference — automated DOM geometry passes, but only the human can judge visual polish and layout feel.`
2. **`Main-Merge Smuggling, Stale Base Diffs & Silent Reverts`** *(when rebasing, resolving conflicts, or merging `origin/main`)*:
   - Run `git merge-tree --write-tree` yourself; surface to the human only when a conflict resolution required a business-logic judgment call between competing intents, with `Why the LLM cannot do this: Intent Alignment vs. Shared Assumption — ...`
3. **`Partial, Stale-SHA, or Substitute-Provider Gates`** *(when reporting `/ready` or gate status)*:
   - Highlight any gate (`UI`, `MCP`, `/er`, independent `advice` review, CI shards) that remains `UNAVAILABLE` or ran via a fallback provider after exhausting automated retries, with `Why the LLM cannot do this: Authority / Permission Boundary — ...`
4. **`Product Constants, Cooldowns & Prompt Compression`** *(when prompts, docstrings, configs, or gameplay/business constants change)*:
   - Verify line counts and tests yourself; surface to the human only subjective product tuning constants (e.g., cooldown durations, word-cap budgets, model tier tradeoffs) or semantic policy shifts, with `Why the LLM cannot do this: Subjective Product / UX Taste or Tradeoff Preference — ...`
5. **`Zero-Framework Cognition (ZFC) & Scope-Blind Backend Guards`** *(when backend state, reducers, clamps, sanitizers, or security/migration paths change)*:
   - Write unit tests for deterministic guards and zero-regex compliance yourself; surface to the human only architectural boundary tradeoffs or unmockable destructive migration risks, with `Why the LLM cannot do this: ...`
6. **`Cross-PR Stack & Shared Token/Budget Ratchets`** *(when working on stacked PRs or shared system prompts)*:
   - Check `baseRefName` and token ratchets yourself; surface to the human only land-order or budget-allocation decisions across competing features, with `Why the LLM cannot do this: ...`
7. **`Provider-Boundary & Structured-Output Schema Complexity`** *(when JSON schemas, tool definitions, or model catalogs change)*:
   - Live-probe `response_json_schema` against the real provider yourself whenever credentials exist; surface to the human only when a production provider endpoint cannot be reached from the test environment, with `Why the LLM cannot do this: ...`
8. **`Cross-Host (macOS vs Linux) & Viewport Parity`** *(when shell scripts, Rust/Python tooling, skills, or hooks change)*:
   - Verify macOS (Bash 3.2, BSD userland, `cmux`/`aside`, Clippy target guards) and Linux (`tmux`, `/proc/meminfo`, GNU userland) plus `SHA-256` sync yourself; surface to the human only uninstrumented host-hardware/GUI behaviors, with `Why the LLM cannot do this: ...`
9. **`Linux Systemd / Cgroup Live State & Runner Side Effects`** *(when Linux services, runner fleets, or container limits change)*:
   - Query `systemctl show`, `/etc/systemd/system.control/`, `automation.slice/pids.current`, and PSI `memory.pressure` yourself; surface to the human only capacity/cost tradeoffs on shared runner hardware, with `Why the LLM cannot do this: ...`
10. **`Delivery vs Execution, Subprocess Stdin & Hook Hygiene`** *(when automation scripts, background jobs, or agent orchestration change)*:
    - Verify `< /dev/null` stdin closure, hook timeouts in `settings.json`, and `git clone --no-local` review worktree isolation yourself; surface to the human only workflow policy choices, with `Why the LLM cannot do this: ...`

### Mandatory Closing Bullets (Always Include in `## What to Review as a Human`)
- **`What Current Evidence Does NOT Prove`**: Explicitly state what remains unexercised (e.g., unit-only proof without live server/provider capture, untested viewport/OS, or pending CI check) and why the LLM could not run that layer in this turn.
- **`Exact Human Decision Needed`**: State the single concrete action or decision requested from the human (e.g., `MERGE APPROVED` on PR `#NNNN`, or a product choice between Option A and Option B) and `Why the LLM cannot do this: Authority / Permission Boundary — agents are forbidden from self-approving merges.`
