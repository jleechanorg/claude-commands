---
name: skillify
version: 2.1.0
description: "Turn any feature, script, or workflow into a properly-skilled, tested, auditable Hermes skill. Runs the gbrain-derived 11-item Skillify Completeness Contract against the target and creates all missing artifacts."
when_to_use: "Use when the user says: skillify this, is this a skill?, make this proper, add tests and evals for this, check skill completeness, turn this into a skill, capture this workflow. Also use proactively after building any new feature without the full skill infrastructure."
triggers:
  - skillify this
  - skillify
  - is this a skill?
  - make this proper
  - add tests and evals for this
  - check skill completeness
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
context: inline
---

# Skillify — The 11-Item Skill Completeness Contract

> **v2.0.0 — backport of Garry Tan's [gbrain skillify v1.1.0](https://github.com/garrytan/gbrain/blob/master/skills/skillify/SKILL.md) 11-item contract.** The previous v1.x of this skill was a 10-item checklist with no tests, no scripts, and no resolver eval — we discovered during a gap audit (2026-07-02) that the most important pieces (the *routing* contract) had never been built. This rewrite ships the missing pieces with the test suite, scripts, and resolver eval that lock the contract in place.

## The 11-Item Contract

A feature is "properly skilled" when all applicable items are present. Six are always required; five are conditional.

| # | Item | Required? | What it looks like in this repo |
|---|------|-----------|---------------------------------|
| 1 | **SKILL.md** | Always | YAML frontmatter + `## Contract` + `## Phases` + `## Output Format`. This file. |
| 2 | **Deterministic code** | Always (if not pure LLM) | `scripts/<verb>.py` next to SKILL.md. See `scripts/skillify_check.py`. |
| 3 | **Cross-modal eval** | Deferrable | 3 frontier models from 3 different providers; mean ≥ 7 per dim; floor ≥ 5. **DEFERRED in Hermes** — see [references/gbrain-skillify-v1.1.0-port.md](references/gbrain-skillify-v1.1.0-port.md). |
| 4 | **Unit tests** | Always (if deterministic code) | `tests/test_<verb>.py` — every branch of deterministic logic, mocks only at external API boundaries. |
| 5 | **Integration tests** | Always (if deterministic code) | `tests/test_<verb>.py` runs the shipped script on the **live** skill tree — not a mocked stub. |
| 6 | **LLM evals** | Conditional | `evals/{rubric.json, cases.jsonl, run_eval.py}`. Only required if the feature calls an LLM. |
| 7 | **Resolver trigger entry** | Always | A row in `~/.hermes/skills/RESOLVER.md` whose **heading line** contains the trigger phrases a user types. |
| 8 | **Resolver trigger eval** | Always | `tests/test_trigger_eval.py` + `routing-eval.jsonl` fixture (format `{intent, expected_skill, ambiguous_with?}`). |
| 9 | **check-resolvable** | Always | `scripts/check_resolvable.py` reads the live RESOLVER.md, asserts every trigger line maps to a SKILL.md, asserts no orphan or ambiguous routes. |
| 10 | **E2E smoke test** | Always (if used in production) | `tests/test_e2e.py` exercises the full pipeline from user phrase to side effect. |
| 11 | **Brain filing** | Conditional | If the skill writes to a brain/RESOLVER.md system, the skill's SKILL.md describes the filing rules. **N/A** for skillify itself. |

## Phases

### Phase 0 — Should this be a skill?

- Will it be invoked 2+ times? (One-off work ≠ skill.)
- Is there > 20 lines of logic? (Trivial helpers don't need full infrastructure.)
- Does it have a clear trigger phrase a user would actually type?

If "no" to all three, it's a script, not a skill. Move on.

### Phase 1 — Audit

Run `python3 -m skillify_check <skill_dir>` (i.e. `scripts/skillify_check.py`) to see which of the 11 items the target skill has. The script emits a JSON report; each item is `pass | fail | defer` with the evidence it found.

```bash
python3 skills/skillify/scripts/skillify_check.py skills/skillify/
# expect: 9 pass / 2 defer on this skill directory (item 3 + N/A item)
```

#### Pre-audit verification — read this first (added 2026-07-14)

**Default to auditing the remote tree, not the local worktree.** A `git status` showing "behind origin/main" is a trap: the local checkout may be N commits behind, missing scripts/tests/routing-eval.jsonl that a later PR landed. Auditing the stale local tree produces a phantom-regression report (score=2/10, "everything is broken") that wastes an investigation cycle. Recipe:

```bash
# 1. Confirm where local HEAD is vs remote
git status --short --branch
git rev-parse HEAD origin/main   # output two SHAs

# 2. If local is behind, archive origin/main and audit that tree
rm -rf /tmp/skillify_audit && mkdir -p /tmp/skillify_audit
git archive origin/main | tar -x -C /tmp/skillify_audit
cd /tmp/skillify_audit
python3 skills/skillify/scripts/skillify_check.py skills/skillify/ --repo-root .
python3 skills/skillify/scripts/check_resolvable.py --resolver skills/RESOLVER.md --skills skills/
python3 skills/skillify/scripts/trigger_eval.py --fixture skills/skillify/routing-eval.jsonl --repo-root .
PYTHONPATH=skills/skillify/scripts pytest skills/skillify/tests/ -v
```

**Surface stranded side-branch fixes.** A merged PR's follow-up commits can sit on a side branch and never reach `origin/main`. If they don't ship, they don't count. After the audit, grep for topic-relevant commits NOT reachable from `origin/main`:

```bash
# Example: skillify-related commits anywhere vs on origin/main
git log --all --oneline --grep="skillify" -i > /tmp/all_skillify_commits.txt
git log origin/main --oneline --grep="skillify" -i > /tmp/main_skillify_commits.txt
comm -23 <(sort -u /tmp/all_skillify_commits.txt) <(sort -u /tmp/main_skillify_commits.txt)
# Each row above is a fix that exists somewhere but is NOT in origin/main.
# Treat each as a follow-up PR; do NOT count it in the skill's score.
```

Real-world instance (2026-07-14): `92b6acfc67 fix(skillify): address CodeRabbit and skeptic agent review comments` (`scripts/deploy-tracked-file.sh` + 2 tests, 50 insertions) was reachable from `git log --all` but NOT an ancestor of `origin/main`. The audit on origin/main's tree produced a clean `10/11`; the side-branch content was reported honestly as a follow-up rather than silently absorbed into the score.

#### Pitfall — `skill_view` daemon wedge (added 2026-07-24)

The `skill_view` / `skills_list` / `session_search` tools share a daemon executor pool that occasionally returns `'DaemonThreadPoolExecutor' object has no attribute '_initializer'` for every call in a session (known py3.14 issue; the matching skill `py314-threadpoolexecutor-initializer-fix` documents the underlying root cause). When this fires, you cannot load any skill body via the canonical path. **Fallback path that always works** — read the SKILL.md directly off disk and run scripts in `terminal`:

```bash
SKILL=claude-code-claudem
sed -n '1,80p' ~/.hermes/skills/${SKILL}/SKILL.md
grep -n '^## ' ~/.hermes/skills/${SKILL}/SKILL.md
PYTHONPATH=~/.hermes/skills/${SKILL}/scripts python3 -m <entry-point> <args>
```

If a referenced skill script lives under `~/.hermes/skills/<name>/scripts/` and was never deployed (single-dir mode shares paths, so this is rare), fall back to `~/.hermes_prod/skills/<name>/scripts/` (it's a symlink to the same dir, but the literal path keeps the error message clear). Do NOT retry `skill_view` in a loop — the daemon needs a process restart, not another call. Document the wedged session in the closure summary so the user knows the skillify pass used file-direct verification rather than the canonical tool path. Verified 2026-07-24: produced `claude-code-claudem` SKILL.md + RESOLVER entry end-to-end with `skill_view` returning the daemon error on every call; file-direct path produced identical outcomes.

### Pitfall — memory at cap when persisting user preferences (added 2026-07-30, browserclaw v2 review)

When a session produces durable user preferences that should outlive the session, the default write target is `memory(target='user')`. If the store is at 95%+ capacity, single-op `add` calls reject with `Memory consolidation failed ... -- over the limit` and the tool loop warning fires after 3 retries. Two known failure modes:

1. **Retry loop**: calling `memory action=add` with shorter content 2-3 times in a row hits the same cap; the warning fires and forces a halt. The user preference is lost.
2. **Replace-still-overflow**: `memory action=replace` with a longer replacement text than the existing entry can also overflow because the *batch final-state* is checked against the cap, not the per-op delta.

**Correct behavior when memory is at cap:**

1. **Surface the blocker explicitly to the user.** Don't silently drop the preference. Tell them: "memory is at X/Y chars; both prefs are encoded in the [doc/skill] instead, which is the durable record."
2. **Pick the right durable store**: for *operational preferences* (how the user wants things done), embed them in the relevant SKILL.md body or `references/` file — those survive session restarts via the skill's own deploy pipeline. For *current-state facts*, write to a daily note (`memory/YYYY-MM-DD.md`) or a repo-local file. Memory is the wrong target when it's full.
3. **Avoid `replace` with longer text.** Replace can only *shorten* by enough characters to fit the new content + any queued adds. If your replacement is longer than the original entry, the operation will overflow. Either trim the original first (separate `remove` op) or write to the skill instead.

Verified 2026-07-30: memory at 97% (1,343/1,375 chars) on `~/.hermes/workspace/`. Tried to add two preferences totaling 470 chars → rejected 4× → embedded both in the browserclaw v2 design doc + a new `references/browserclaw-v2-design-2026-07-30.md` + the `browser-headless-default` SKILL.md "Automatic-auth default" section. The skill body is a stronger durable store anyway because it's loaded automatically by `skill_view` next time someone asks about browser automation.

### Phase 2 — Write SKILL.md + extract deterministic code

See the frontmatter template in the original v1.x content of this file (kept below in `## Frontmatter template`).

Extract deterministic logic into `scripts/<verb>.py`. Tests in Phase 4 will exercise it.

### Phase 3 — Cross-modal eval (DEFERRED in Hermes)

We do not yet wire 3-provider frontier eval into the Hermes gateway. The substitute is `/advice` adversarial review (the `advice` skill), which at the cost of one LLM turn (subagent) gives a single-hostile-reviewer second opinion. **Document the deferral in `references/gbrain-skillify-v1.1.0-port.md`** whenever this item is skipped.

### Phase 4 — Tests (items 4 + 5 + 6)

```bash
PYTHONPATH=skills/skillify/scripts pytest skills/skillify/tests/ -v
```

The test suite invokes the shipped scripts on the **live** RESOLVER.md + skill directory — no mocks at the boundary we care about. Unit-level coverage is a side effect, not the goal.

### Phase 5 — Resolver + check-resolvable (items 7 + 8 + 9)

1. Add a `## <skill-name> : <triggers...>` row to `~/.hermes/skills/RESOLVER.md`. **The oneline format MUST have a SPACE between `## <name>` and `:`** — `## name :` (note the trailing space before the colon). Verified pattern: `skillify_check.py` requires either `## <name>\n` (literal newline after) OR `## <name> ` followed by some non-newline content (a space-then-anything line). The compact `## name:` with NO space fails the heading marker regex (it matches `## <name> ` exactly, not `## <name>:`). Insert a space after the name: `## campaign-creation : create campaign, ...` not `## campaign-creation: create campaign, ...`. Verified 2026-07-20 (campaign-creation skillify pass).
2. Drop a `routing-eval.jsonl` fixture next to SKILL.md (one row per expected trigger phrase).
3. `python3 -m trigger_eval --fixture <fixture>` runs the structural pass; `--llm` adds a semantic tie-break via Anthropic (Claude default).
4. `python3 -m check_resolvable --repo .` audits the whole resolver graph: orphans, dup-keys, ambiguous routes.

### Pitfall — oneline RESOLVER heading needs SPACE between name and colon (added 2026-07-20)

The `skillify_check` regex for item 7 looks for `## <skill-name> ` (note the space) followed by a line that contains a comma. The compact form `## campaign-creation:` (no space) silently fails the heading-line check, even though the trigger CSV appears on the same line. The skillify audit will print `[MISS] 7. resolver_trigger_entry  no-##-campaign-creation-heading-in-RESOLVER.md` and `[MISS] 7. resolver_trigger_entry  triggers-not-on-heading-line`. Verified on `campaign-creation` 2026-07-20 — swapped `## campaign-creation:` to `## campaign-creation :` (with the space) and the score went from 7/9 to 8/9 with 0 fails.

Both formats are human-readable AND both make `tests/test_trigger_eval.py` pass (the test fixture accepts either via two regex branches). The `skillify_check` regex is the bottleneck.

**Canonical form (use this everywhere when adding to RESOLVER.md):**

```markdown
## campaign-creation : create campaign, design new campaign, campaign bible, …
```

NOT:

```markdown
## campaign-creation: create campaign, design new campaign, campaign bible, …   ← will fail skillify_check item 7
```

### Phase 6 — E2E + brain filing (items 10 + 11)

- E2E smoke: see `tests/test_e2e.py` for the resolver → audit pipeline.
- Brain filing: not applicable for this skill. skillify does not write brain pages; if a future skillify-derived skill does, that skill's SKILL.md describes the filing rule and we add a resolver entry pointing at the brain resolver.

### Phase 7 — Verify

```bash
python3 skills/skillify/scripts/skillify_check.py --target skills/skillify/ --json
python3 skills/skillify/scripts/check_resolvable.py --repo skills/
python3 skills/skillify/scripts/trigger_eval.py --fixture skills/skillify/routing-eval.jsonl
PYTHONPATH=skills/skillify/scripts pytest skills/skillify/tests/ -v
```

## Output Format

A skillify run produces:
- **`SKILL.md`** rewritten against the 11-item contract.
- **`scripts/<verb>.py`** — the deterministic audit / check / eval code.
- **`tests/test_<verb>.py`** — integration tests against the live skill tree.
- **`routing-eval.jsonl`** — `{intent, expected_skill, ambiguous_with?}` rows.
- **`evals/{rubric,cases,run_eval}.{json,jsonl,py}`** — LLM evals (conditional).
- **`references/gbrain-skillify-v1.1.0-port.md`** — deferral / N/A rationale when applicable.
- **`references/skillify-audit-recipe.md`** — remote-tree-first audit recipe (added v2.1.0, after a stale-local-worktree audit produced a phantom regression).

JSON output of `skillify_check.py`:
```json
{ "skill": "<name>", "items": [{"n": 1, "name": "SKILL.md", "status": "pass"}, ...], "score": "9/11", "deferred": [3], "na": [11] }
```

## Frontmatter template (copy-paste)

```yaml
---
name: my-skill
version: 1.0.0
description: |
  One paragraph. What it does, when to use it.
triggers:
  - "trigger phrase users actually say"
  - "another real trigger"
allowed-tools:
  - Read
  - Write
  - Bash
context: inline
---
```

## Anti-Patterns

- ❌ SKILL.md with no tests — contract regresses silently
- ❌ Tests that reimplement production — reimplementation bugs hide production bugs
- ❌ Resolver entry with internal jargon users never type
- ❌ JSONL fixture with fields named `phrase`/`skill` (gbrain uses `intent`/`expected_skill`; field-name mismatch breaks consumers)
- ❌ MECE/DRY overlap detection in `check_resolvable.py` — out of scope for this PR; defer to a separate bead
- ❌ Writing `scripts/check_resolvable.py` that only checks orphans (drop the MECE/DRY marketing claim or implement it)
- ❌ Unit-only evidence for `/er` — Layer 2 integration (real callstack output) is the bar for production changes
- ❌ **Auditing the local worktree when it's behind origin/main** — produces a phantom regression (score=2/10) that hides the real shipped state; archive the remote tree first (see `### Phase 1 — Pre-audit verification`)
- ❌ **Counting stranded side-branch fixes in the skill's score** — a commit reachable from `git log --all` but NOT an ancestor of `origin/main` is invisible to the public tree; report as follow-up, don't fold into the audit verdict

## Quality Gates

A skill is "properly skilled" only when:
- ✅ All always-required items (1, 2, 4, 5, 7, 8, 9, 10) pass or are explicitly deferred with rationale in `references/`.
- ✅ All pytest tests pass.
- ✅ `check_resolvable` reports 0 orphans, 0 dup-keys, 0 ambiguous.
- ✅ `trigger_eval` matches every intent in the fixture.
- ✅ `/er` verdict is **PARTIAL or PASS** on the resulting change.
