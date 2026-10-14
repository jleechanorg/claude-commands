---
name: human-review-brief
description: Standardized end-of-turn human review brief (## What Was Done and ## What to Review as a Human) grounded in empirical Mac and Linux agent blind spots. Use when finishing PR updates, code reviews, or merge-readiness handoffs, or when invoked via /what-to-review or /pr-summary.
---

# Human Review Brief (`human-review-brief` / `/what-to-review`)

## When to Apply
- **Full Brief (`## What Was Done` + `## What to Review as a Human`)**: Required when finishing a PR update, code/evidence review, multi-step feature implementation, or merge-readiness report, and inside `/pr-summary` breakdowns.
- **Compact Inline Form**: On small local coding turns that do not update a PR or claim merge readiness, emit a 2–3 bullet inline summary of what changed, what was verified, and the one human check that matters most. Skip on trivial Q&A or read-only lookups.

---

## Section 1: `## What Was Done` (Objective Facts & Provenance)

Provide a scannable 4-bullet summary of verified facts:
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
   - Confirm zero conflict markers, zero files reverted relative to `origin/main` (`git diff origin/main "$TREE"` matches only intended branch changes), and zero smuggled multi-file formatter edits (e.g., `ruff --fix` stripping re-exported underscore imports).
4. **SHA-Bound Gate & Evidence Matrix (`@ <short-sha>`)**:
   - State the exact status and attested SHA for CI / local equivalents (`/green`), `/es`, `/er`, independent review (`advice`), `/cs`, and `/wa` (with sanitized gist URLs where applicable). Never claim a prior-SHA receipt covers a new head without explicit delta-based applicability analysis.

---

## Section 2: `## What to Review as a Human` (Empirical Blind-Spot Checklist)

Agents routinely pass unit tests and static checks while missing visual/runtime layout defects, domain-constant drift, ZFC violations, or cross-host/systemd side effects. Select **3 to 6 concrete bullets** from the 10 empirical Mac + Linux blind-spot categories below that match the surfaces touched by the change, **plus** the two mandatory closing bullets (`What Current Evidence Does NOT Prove` and `Exact Human Decision Needed`).

### The 10 Empirical Mac + Linux Blind-Spot Categories (Select Only Applicable Surfaces)

1. **`Visual / UX / Hidden-State Verification`** *(when UI, CSS, templates, or mobile views change)*:
   - Link exact before/after frames across `1440x900` desktop, the `700–1024px` narrow/windowed-desktop band, and `375x812` mobile (or native simulator) plus walkthrough video timestamps.
   - Call out whether any rendered element sits inside a `display: none` / collapsed parent container, overlaps HUD/banner controls, drops theme contrast, or gets trapped behind a modal lock (`jsdom` and mocked e2e suites miss these).
2. **`Main-Merge Smuggling, Stale Base Diffs & Silent Reverts`** *(when rebasing, resolving conflicts, or merging `origin/main`)*:
   - List every conflict resolution or file where `git diff origin/main "$TREE"` differs from `git diff origin/main...HEAD`, confirming no recent `origin/main` commits were silently overwritten.
3. **`Partial, Stale-SHA, or Substitute-Provider Gates`** *(when reporting `/ready` or gate status)*:
   - Highlight any gate (`UI`, `MCP`, `/er`, independent `advice` review, CI shards) that was attested on an earlier SHA, ran via a fallback/substitute provider, or remains `PENDING`/`UNAVAILABLE`.
4. **`Product Constants, Cooldowns & Prompt Compression`** *(when prompts, docstrings, configs, or gameplay/business constants change)*:
   - Name every changed numeric constant, timeout, cooldown, model slug, or compressed/deleted system-instruction clause (`/ds`) so the human can verify no domain invariant or user-facing behavior was silently altered.
5. **`Zero-Framework Cognition (ZFC) & Scope-Blind Backend Guards`** *(when backend state, reducers, clamps, sanitizers, or security/migration paths change)*:
   - Cite exact `file:line` for any new backend guard, clamp, fallback, reducer normalization, auth/credential boundary, or destructive data migration.
   - Explain why it cannot clobber valid nested aliases, strip release flags, block legitimate empty-list clearing on sibling state scopes, or expose secrets/credentials.
6. **`Cross-PR Stack & Shared Token/Budget Ratchets`** *(when working on stacked PRs or shared system prompts)*:
   - State whether the PR depends on parent/sibling PRs landing first and whether combined prompt/schema changes stay within shared token or latency ratchets.
7. **`Provider-Boundary & Structured-Output Schema Complexity`** *(when JSON schemas, tool definitions, or model catalogs change)*:
   - Confirm whether `response_json_schema` / structured-output changes were live-probed against the production model provider (local `jsonschema` and proxy providers do not enforce union/nesting/property-ordering state-machine limits).
8. **`Cross-Host (macOS vs Linux) & Viewport Parity`** *(when shell scripts, Rust/Python tooling, skills, or hooks change)*:
   - Verify portability across macOS (Bash 3.2 without `mapfile`/`declare -A`, BSD `sed`, `vm_stat`, `cmux`/`aside`, `#[cfg(any(target_os = "linux", test))]` Clippy guards) and Linux (`tmux`, `/proc/meminfo`, GNU userland, headless Xvfb/Playwright).
9. **`Linux Systemd / Cgroup Live State & Runner Side Effects`** *(when Linux services, runner fleets, or container limits change)*:
   - Confirm verification used live cgroup and unit state (`systemctl show`, `/etc/systemd/system.control/` runtime overrides, ancestor `automation.slice/pids.current` vs `pids.max`, `memory.pressure` PSI), not just `free -h` or static unit files on disk.
10. **`Delivery vs Execution, Subprocess Stdin & Hook Hygiene`** *(when automation scripts, background jobs, or agent orchestration change)*:
    - Confirm backgrounded CLI invocations close stdin (`< /dev/null`), hooks bound timeouts in `settings.json`, ephemeral review worktrees use isolated object stores (`git clone --no-local`), and queued messages/timers are distinguished from completed execution.

### Mandatory Closing Bullets (Always Include in `## What to Review as a Human`)
- **`What Current Evidence Does NOT Prove`**: Explicitly state what remains unexercised (e.g., unit-only proof without live server/provider capture, untested viewport/OS, or pending CI check).
- **`Exact Human Decision Needed`**: State the single concrete action or decision requested from the human (e.g., `MERGE APPROVED` on PR `#NNNN`, or a product choice between Option A and Option B).
