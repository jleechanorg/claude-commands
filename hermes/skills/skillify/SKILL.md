---
name: skillify
version: 2.0.0
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

1. Add a `## <skill-name>` row to `~/.hermes/skills/RESOLVER.md`. **Triggers must appear on the same line as the `##` heading** so the `test_resolver_trigger` regex matches (gbrain's pitfall, ours too).
2. Drop a `routing-eval.jsonl` fixture next to SKILL.md (one row per expected trigger phrase).
3. `python3 -m trigger_eval --fixture <fixture>` runs the structural pass; `--llm` adds a semantic tie-break via Anthropic (Claude default).
4. `python3 -m check_resolvable --repo .` audits the whole resolver graph: orphans, dup-keys, ambiguous routes.

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

## Quality Gates

A skill is "properly skilled" only when:
- ✅ All always-required items (1, 2, 4, 5, 7, 8, 9, 10) pass or are explicitly deferred with rationale in `references/`.
- ✅ All pytest tests pass.
- ✅ `check_resolvable` reports 0 orphans, 0 dup-keys, 0 ambiguous.
- ✅ `trigger_eval` matches every intent in the fixture.
- ✅ `/er` verdict is **PARTIAL or PASS** on the resulting change.
