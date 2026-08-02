---
title: Prompt-contract PR-fix — broaden static test scope to match CR review's demanded forbidden list + lockdown-test pattern
date: 2026-07-21
verified-on: $GITHUB_REPOSITORY PR #8488 V3.21 (CodeRabbit re-review head f9f269a685)
---

## Why this reference exists

When a CodeRabbit review flags static-content blockers (forbidden entities,
formula/example mismatches, hidden-state leaks, malformed placeholders,
contradictory clause pairs) that the existing static tests in the repo
**do NOT enforce** at the wider scope CR is asking for, the canonical
recipe is:

1. **Broaden the existing static test's forbidden list** so the wider
   CR-mandated scope becomes a hard regression.
2. **Run that test locally before editing the prompt** to know exactly
   which entities are still leaking. The test becomes your scope
   checklist.
3. **Add a `LockdownTests` class** to the same test file with
   contract-pinning assertions for the OTHER fixes (exact formula
   string present, exact phrasing present, exact no-leakage of
   malformed artifacts).
4. **All patches land in the same commit** with the broadened test +
   prompt edits, then push as one PR ref. The static test is the
   "no regression" insurance; the lockdown test is the "this exact
   fix stays fixed" insurance.

This pattern showed up on PR #8488 V3.21 (fixing V3.20's five-blocker
review) and is reusable for any prompt-edit / doc-edit / static-content
PR fix where CodeRabbit demands more than the existing static checks
enforce.

## The five blocker shape

Verified on PR #8488 V3.21 head f9f269a685. CR's review of V3.20 listed
five distinct blocker classes. The first class ("default text still
setting-specific") was the WRAPPER around the others — the static test
needed broadening before any of the prompt edits could pass:

| # | Blocker class | Where it lives | Test shape |
|---|---|---|---|
| 1 | Setting-specific leakage in default text (named entities: Forgotten Realms, D&D, cross-setting franchises like Bleach / Naruto / 5e-specific) | Prompt body §V3, §V3.X body + cross-refs footers | Negative-list assertion split on `default_text = text.split(APPENDIX_MARKER, 1)[0]` |
| 2 | Stat formula vs worked-example mismatch (canonical formula exists but worked example uses a simpler/abbreviated form) | V3-style prompts with formula + worked-example blocks | Exact substring assertion of canonical formula text + worked-example arithmetic-pass |
| 3 | Hidden-state leakage into player-visible examples + reset-rule conflict (F, PS exact, RP shown where §V3.0 says HIDDEN; DPP arithmetic contradicts §V3.6 no-carry rule) | Worked example blocks where the LLM "demo" surface unintentionally re-leaks internal math | Negative-list assertion that the visible-vs-internal split is labeled + cross-check the math against the §V3.X reset rule |
| 4 | "X growth only" header contradicts cross-ref body (e.g. "Clean Kill, no penalty" header but +50% D for all gods including the killer listed in another section) | Section header AND a cross-referenced section's body | Two assertions: header says actor-no-penalty AND cross-ref body says "+X% for ALL OTHER gods (not ALL gods)" |
| 5 | Cleanup left malformed default text (half-applied regex replacements like "Aizen's the the Lawbringer (replace per setting)ant (replace per setting) kill", "the Lawbringer (replace per setting)ant" archetype row) | Anywhere `replace_per_setting` style placeholders are scaffolded | Banned-artifact list: explicit banned strings that must NOT appear |

## The recipe

### Step 0 — Confirm CR's wider scope (before any patch)

Read the PR comment carefully. CR often lists each blocker with line
numbers. Confirm:

- Which file(s) CR names
- What literal substring CR wants gone
- Whether CR explicitly references an existing test or just complains

If CR's complaint list is wider than the existing test's forbidden list,
proceed with broadening.

### Step 1 — Broaden the existing test FIRST

```python
# BEFORE
def test_no_dnd_default_entities(self):
    forbidden = [
        "Mystra", "Helm", "Oghma", ...  # narrow FR list
    ]
```

```python
# AFTER
def test_no_dnd_default_entities(self):
    """No D&D / Forgotten Realms / cross-setting named-entity may appear in default text.

    Covers the broader CR-style forbidden list (added 2026-07-21 to fix
    CodeRabbit blocker #1 on PR #8488 V3.21): the static test originally
    only forbade a narrower Forgotten Realms name list; Loki/Vecna/...
    were leaking through.
    """
    forbidden = [
        # Forgotten Realms narrow list (pre-existing)
        "Mystra", "Helm", "Oghma", ...,
        # Broader cross-setting names — must appear only in Appendix A
        "Loki", "Vecna", "Chauntea", "Demeter", "Hoder", "Osiris",
        "Iuz", "Nocturne", "Aizen", "Sōsuke", "Drow", "Arachne",
    ]
```

### Step 2 — Run the test to learn the leak surface

Before editing the prompt, run the test:

```bash
python3 -m unittest mvp_site.tests.test_divine_prompts_setting_agnostic -v
```

The leaked list tells you exactly which lines need fixing. This is
cheaper than a 30-minute string-grep sweep across the file.

### Step 3 — Add a `LockdownTests` class for the OTHER four blockers

```python
class V321ContractualFixesTests(unittest.TestCase):
    """Lockdown tests pinning V3.21 contractual fixes (PR #8488)."""

    @classmethod
    def setUpClass(cls):
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "prompts", "divine", "divine_leverage_system.md",
        )
        with open(path) as f:
            cls.text = f.read()
        cls.default_text = cls.text.split(APPENDIX_MARKER, 1)[0] if APPENDIX_MARKER in cls.text else cls.text

    def test_section_phrase_present(self):
        """The §V3.X section must contain specific phrasing per the contract."""
        m = re.search(
            r"## V3\.X[^\n]*\n(.*?)(?=\n## |\Z)",
            self.default_text, re.DOTALL,
        )
        self.assertIsNotNone(m, "Could not find §V3.X")
        body = m.group(1)
        self.assertIn("specific phrasing", body)

    def test_no_malformed_artifacts(self):
        """Banned artifact strings must not appear in default text."""
        banned = [
            "the the Lawbringer (replace per setting)ant",
            "Aizen's the the",
        ]
        leaked = [a for a in banned if a in self.default_text]
        self.assertEqual(leaked, [], f"Malformed artifacts leaked: {leaked}")
```

### Step 3a — The section-extraction regex gotcha

When extracting a §V3.X section from a markdown document for
regex-assertion testing, naive `[^#]*?` fails when the section ends in
a delimiter line (`---`) followed by another `## ` heading. Use:

```python
r"## V3\.X[^\n]*\n(.*?)(?=\n## |\Z)"
```

NOT:

```python
r"## V3\.X[^#]*?(?=\n## |\n# Appendix|\Z)"  # wrong: matches "---\n\n## V3 → V2 changelog" boundary
```

The `[^\n]*\n` form captures the heading line itself, then the lazy
`.*?(?=\n## |\Z)` captures everything up to the next `## ` heading or
EOF. Verified on PR #8488 — the original regex returned None for
§V3.20 because the prior pattern's `[^#]*?` couldn't bridge a `---`
delimiter.

### Step 4 — Edit the prompt

Patch each blocker in turn. Pattern:

- **Blocker 1** (named-entity leakage): replace with generic
  placeholders using `replace_per_setting`-style anchors; keep
  Appendix A as the canonical D&D reference. Appendix A contains
  the named entities the test allows.
- **Blocker 2** (formula/example mismatch): prefer the canonical
  formula. Add a short bridging paragraph in the worked example
  noting "§V3.1's ×5.4 is the stat-block floor; V3.2's
  ×1.8 ×5.4 with follower/Repr bonuses is the working stat. V3.2 is
  authoritative."
- **Blocker 3** (hidden-state leak + reset-rule conflict): relabel
  worked-example blocks as "LLM-internal stat sheet (player sees
  only L, Repr, DPP, AT-remaining, D-bands, narrative PS)" with
  explicit `(LLM-only)` markers on F and PS rows. Cross-check the
  visible §V3.6 reset cadence against the example arithmetic (the
  "310 / 410" worked numbers must match `(L − 19) × 10 + 100` for
  L36 / L42; if not, the §V3.6 formula has a stale example
  arithmetic too).
- **Blocker 4** (contradictory header + cross-ref): rename the
  header to make the actor-penalty rule explicit (e.g.
  "Deicide-cost: no actor penalty (Clean Kill — others pay)") and
  add a clarifying external-consequence blockquote. Update the
  cross-ref body to say "ALL OTHER gods (killer excluded)" with a
  cross-reference back.
- **Blocker 5** (malformed cleanup): replace each malformed
  artifact with a coherent single-token placeholder (Tribunal,
  Source-stitcher, "the canon reference god's first ascendant-kill
  was clean"). Test that no `(replace per setting)` strand collides
  with another `(replace per setting)` strand.

### Step 5 — Commit + push + ask for re-review

Single commit, single push. The commit message should list all five
blockers with fix-location + lockdown-test references:

```
fix(prompts): V3.21 — wider setting-agnostic contract

PR #8488 CodeRabbit review (link) flagged 5 blockers. This commit
closes all 5:

1. Wider setting-agnostic list — broadened test_no_dnd_default_entities
   to cover 12 cross-setting entities + test_v320_lockdown pin.
2. Stat formula vs example — added V3.2 worked-example block; V3.2 is
   authoritative. test_stat_formula_consistency pin.
3. Hidden-state leakage in V3.20 — relabel as "LLM-internal stat sheet"
   + explicit DPP carry rule. test_v320_stat_sheet_labels_hidden_fields.
4. Clean Kill contradicting cross-ref — V3.12 renamed "Clean Kill —
   others pay"; V3.14 says "ALL OTHER gods". test_v312 + test_v314 pins.
5. Malformed cleanup — Tribunal / Source-stitcher / "canon reference
   god's first ascendant-kill was clean". test_no_malformed_cleanup_artifacts.

All 25 tests pass locally.
```

Post a brief CR-reply summary on the PR mentioning each blocker with
fix-location + lockdown-test ref. Don't ask "are you happy?" — ask
"please confirm APPROVED on the new head <SHA>".

## Worked example — PR #8488 V3.21 (this session)

Initial state: CR review at https://github.com/$GITHUB_REPOSITORY/pull/8488#issuecomment-5030521131
lists 5 blockers. Local test `test_no_dnd_default_entities` only forbade
11 narrower FR names. Setting up the fresh worktree:
`git worktree add -b fix/prompts-v3-coderabbit-cleanup origin/feat/god-mechanics-v2`.

Sequence:

1. **Broaden test** — added 12 cross-setting entities (Loki/Vecna/
   Chauntea/Demeter/Hoder/Osiris/Iuz/Nocturne/Aizen/Sōsuke/Drow/
   Arachne) to the forbidden list.
2. **Run test** — `python3 -m unittest test_divine_prompts_setting_agnostic -v`.
   Initial result: FAIL with `[Forgotten Realms, the Weave, Nocturne]`.
   Each was a meta-reference pointing to Appendix A. Replaced with
   "setting-specific pantheon equivalents appear only in Appendix A" /
   "Source-stitcher" / "(V2 design doc — superseded by V3 + cross-refs)".
3. **Edit prompt** — applied per-blocker fixes per the recipe above;
   5 named-entity leaks + 4 orphaned sub-issues fixed.
4. **Add lockdown tests** — 6 new tests in `V321ContractualFixesTests`
   class. Hit the §V3.X section-extraction regex gotcha once (lazy
   match crossed a `---` delimiter) — fixed with `[^\n]*\n` opening.
5. **Run all tests** — `Ran 25 tests in 0.007s OK`.
6. **Validate contracts** — `python3 scripts/validate_prompt_tool_contracts.py`
   → "prompt/tool contracts validated".
7. **Commit + push** — `git push origin HEAD:refs/heads/feat/god-mechanics-v2`
   → `9b8d09ccb8..f9f269a685 HEAD -> feat/god-mechanics-v2`.
8. **Verify push landed** — `git rev-parse origin/feat/god-mechanics-v2`
   = `f9f269a685d2bc2d389604da0f71678c9c75f97a`.
9. **Post CR reply** — single message listing all 5 blockers with
   fix-location + test-ref per blocker.

Final state: 0 FAILED, 20 PASSED, 7 still running self-hosted directory
tests + Green Gate Precheck. `mergeable: MERGEABLE`.

## Pitfalls

- **Don't push a PR-body fix without a commit.** `gh pr edit --body-file`
  does not re-trigger Evidence Gate (per the existing Gate 6b reference).
  For prompt-fix PRs specifically, the prompt edit IS the commit; push
  the commit, the body edit then re-evaluates against the new SHA.
- **Don't expand scope beyond CR.** If CR lists 12 forbidden entities,
  add those 12. Adding 100 unrelated entries is over-reach and creates
  churn in tests that downstream agents must read.
- **Don't duplicate lockdown-test assertions.** If the existing static
  test already checks that "Mystra" doesn't appear in default text,
  don't add a `LockdownTests` variant of the same assertion. Lockdown
  tests are for the OTHER 4 blockers (exact formula, exact phrasing,
  exact no-leakage of artifacts). The static test is the scope
  envelope; the lockdown tests are the contract pins.
- **Don't write `[^\#]*?` against `## Section` boundaries.** Bridge
  `[^\n]*\n` then lazy-`.*?(?=\n## |\Z)`. The original regex returns
  None at `---` delimiters.
- **Don't claim push landed without verifying.** `git push` returning
  `9b8d09ccb8..f9f269a685 HEAD -> feat/god-mechanics-v2` is the
  transport-layer proof; `git rev-parse origin/<branch>` is the
  remote-ref proof. Both are required before posting "pushed" in the
  final reply.
- **Don't ask "want me to push?"** — `push-pr-donot-stop-halfway`
  from SOUL.md. Push in the same turn as the commit.
- **Don't ask "are you happy now, CR?"** — post the CR re-review
  request as a single blocker-closure summary listing fix + test ref
  per blocker. The reviewer either approves or surfaces new blockers;
  neither requires a follow-up question from the agent.

## Cross-references

- `references/pr-description-validator-gate6b-2026-07-15.md` — Gate 6b
  validator + Evidence Gate Check 7 freshness (companion CR/PR-fix
  reference, this repo only).
- `references/learn-skillify-harness-closeout-2026-07-14.md` — the
  full /learn + /skillify + /harness + /newb closeout loop (you may
  also run `/skillify` on the test-after-broadening pattern as a
  separate skillify pass after this fix lands).
- SOUL.md `## COMMIT: push-pr-donot-stop-halfway` — durable push
  contract.
- SOUL.md `## COMMIT: grep-before-constant-change` — analogous for
  numeric constants; the prompt-fix analog is "broaden test scope
  before editing prompt".
