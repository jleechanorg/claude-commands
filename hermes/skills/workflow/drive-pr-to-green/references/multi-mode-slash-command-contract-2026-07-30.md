# Multi-mode slash-command skill contract (added 2026-07-30, PR jleechanorg/claude-commands#343)

When the user asks for a behavioral split on a slash command — e.g. *"make /nextsteps only do beads and ~/roadmap and /nextsteps --full does everything"* — the change is small in lines but high in drift risk. Without an executable contract, the LLM will silently fall back to running the side-effecting phases by default. Verified on `/nextsteps` against `jleechanorg/claude-commands` PR #343 (4 files, +565/−17, 13 new contract tests, all green).

This is **NOT** a layering change (see `slash-command-layering` for that) and **NOT** an authoring change (see `hermes-agent-skill-authoring`). It's a *behavioral contract* change: the skill's prose AND the test suite jointly pin which phases run in default vs `--full`. Future agents that touch the SKILL.md or `commands/<name>.md` will fail CI if they drop the mode split.

## When this recipe applies

Trigger on any of:

- "make /X only do Y and Z; /X --full does everything"
- "split /X into default vs --full"
- "by default /X should skip <side-effecting phase>, opt-in via flag"
- "gate the memory-write / issue-create / mem0 phases behind a flag"
- The user explicitly lists what to KEEP vs GATE — that's a multi-mode split

Don't use for:

- Single-mode commands (no flag, no default-vs-opt-in split)
- Layering changes (user-scope vs repo-local pointer — see `slash-command-layering`)
- Adding a new sub-flag to an already-flag-driven command without changing the default

## The four files that must change together

| File | Required change |
|------|----------------|
| `.claude/commands/<name>.md` | Add YAML frontmatter (often MISSING — see Pitfall #1). Document the `--full` flag explicitly with a usage table. |
| `.claude/skills/<name>/SKILL.md` | Add a `## Modes` section at the top with a default-vs-`--full` table. Tag side-effecting phases (memory, mem0, GH Issues) with `(--full only)` in their headings. Phase 8 must have per-mode `[x]`/`[ ]` checklists. |
| `.claude/skills/<name>.md` (user-scope loose fallback) | Mirror the lean/`--full` split so the command works in repos that haven't pulled the latest canonical. |
| `tests/test_<name>_modes_contract.py` (NEW) | 8-15 contract tests that fail-fast if any of the above regress. See the test recipe below. |

If you skip any one of these, the contract is incomplete: the SKILL.md tells future agents the rule, but only the test enforces it; or the command file lacks the frontmatter and Claude Code can't even classify it as executable.

## Pitfalls hit on this session — encode these, don't repeat them

### Pitfall #1 — `commands/CLAUDE.md` requires YAML frontmatter, and most commands in the wild don't have it

`<repo>/.claude/commands/CLAUDE.md` (look in every repo with `.claude/commands/`) explicitly states: *"Commands without this header are considered invalid and should be updated before use."* When adding or splitting a command's behavior, **the YAML header is part of the contract**, not cosmetic. Minimum required shape (matches sibling commands):

```markdown
---
description: <one-line summary>
type: execution|planning|testing|git|orchestration|quality|ai|research|review
execution_mode: immediate|deferred|manual
---

# /<name>

<your command body>
```

Verified by reading `swarm.md`, `sidekick.md`, `team-claude.md`, `advice.md`, `secondo.md` — all carry the frontmatter; legacy `nextsteps.md` did not. Adding it on `nextsteps.md` during the multi-mode split was required, not optional.

### Pitfall #2 — The "verbatim user request" must survive

Future maintainers should be able to find the user's exact phrasing in the repo so they understand *why* the split exists. Embed it as an HTML comment in the canonical SKILL.md and as a `USER_REQUEST = "..."` constant in the test file:

```markdown
<!-- USER REQUEST (verbatim, preserved per task brief): "Make /nextsteps only do beads and ~/roadmap and /nextsteps --full does everything" -->
```

```python
USER_REQUEST = "Make /nextsteps only do beads and ~/roadmap and /nextsteps --full does everything"
```

The test asserts the verbatim prefix appears in the combined file contents. A later maintainer who rephrases the contract will fail the test and have to consciously decide whether to keep the contract intact.

### Pitfall #3 — "Skipped by default" must be EXPLICIT in each side-effecting phase

It's not enough to say "default mode skips memory/mem0/GH Issues" once. Each phase heading must be self-labeled so a future agent reading only that section knows:

```markdown
### Phase 4 — Write to Claude auto-memory  (`--full` only)

**Skipped by default mode.** Run only when the invocation includes `--full`.
```

Then the test asserts the regex:

```python
pattern = rf"###\s+{re.escape(phase_num)}[^#\n]*{phase_name}[^#\n]*`--full`\s*only"
```

This catches both "removed the `(--full only)` tag" and "removed the skip note entirely" regressions. Phase 4, Phase 5, Phase 7b each need their own assertion.

### Pitfall #4 — Per-mode checklists in Phase 8, not one combined list

A single `[x]` list doesn't distinguish "default mode did this" from "would have done in `--full` mode." Use TWO checklists, one per mode, and the contract test asserts the `[x]` (done) bullets specifically:

```python
# Only the [x] (done) bullets count as claimed work; the [ ] bullet
# is an explicit non-claim.
done_bullets = "\n".join(
    line for line in body.split("\n") if re.search(r"\[x\]", line)
)
self.assertNotIn("Claude memory", done_bullets)  # default mode can't claim it
```

The `[- [ ] (intentionally blank — Claude memory + mem0 + GH Issues are owned by --full)]` bullet is allowed to MENTION the forbidden tokens as a meta-comment — only the `[x]` bullets are assertions.

### Pitfall #5 — Flag-parsing rules must be spelled out

Don't leave the flag parsing as an exercise for the LLM. Spell it out in the skill:

```markdown
### How to parse the flag

1. Look at the literal text right after `/nextsteps`.
2. If the first non-whitespace token is exactly `--full`, run in `--full` mode and strip it from the brief.
3. Otherwise (no `--full` anywhere on the line), run in default mode and treat the rest as the user-provided brief.
4. `--full` is the only recognized flag. Any other token (`--help`, `-h`, etc.) is treated as part of the brief.
```

And add a test that asserts the parsing rule (the literal phrases "first non-whitespace token", "exactly `--full`", "strip it from the brief") and the `Mode:` report-line examples (`Mode: default`, `Mode: --full`) are present. Without these, the agent's parsing can drift between runs and the report may misidentify the mode.

### Pitfall #6 — `npm run lint` is the wrong linter for this change

The repo's `package.json` declares `eslint --ext .js,.mjs` and runs it on Node.js sources. A multi-mode slash-command contract change touches Python (the test file) and Markdown (the skill + command files). `eslint` lints neither.

**Don't waste time installing eslint** for a Python+Markdown change. Run:

```bash
ruff check tests/test_<name>_modes_contract.py       # Python lint
ruff format --check tests/                           # Python format
python3 -m unittest discover tests                   # Run tests
python3 -m py_compile tests/test_<name>_modes_contract.py  # Syntax check
```

If `ruff format --check` flags your new test file, run `ruff format <file>` on JUST that file (per `<repo>/CLAUDE.md` "format strictly the specific files modified in your task" — never whole-repo during feature work). Commit the format fix as a separate `style:` follow-up so the diff is clean.

If the system insists on `npm run lint`, the concrete blocker is `eslint: command not found` because the repo has no `node_modules/`. State that as the blocker — don't fabricate a result.

## The contract test recipe (13 tests, all green)

Structure the test file as four test classes against the three files:

```python
class NextstepsCommandContractTest(unittest.TestCase):
    # 3 tests on .claude/commands/nextsteps.md
    test_has_yaml_frontmatter          # commands/CLAUDE.md mandate
    test_declares_default_and_full_modes  # both modes named in command file
    test_preserves_user_request_verbatim  # USER_REQUEST prefix found somewhere

class NextstepsSkillContractTest(unittest.TestCase):
    # 7 tests on .claude/skills/nextsteps/SKILL.md
    test_modes_section_exists          # ## Modes (or ## Modes (...)) present
    test_default_mode_only_uses_beads_and_roadmap  # sentence or table-row
    test_full_mode_does_everything     # sentence or table-row
    test_side_effecting_phases_marked_full_only  # per-phase regex
    test_default_mode_checklist_present  # Phase 8 default checklist
    test_full_mode_checklist_present     # Phase 8 --full checklist

class NextstepsLooseSkillContractTest(unittest.TestCase):
    # 2 tests on .claude/skills/nextsteps.md (skipTest if absent)
    test_loose_skill_names_both_modes
    test_loose_skill_marks_side_effecting_phases_default_skip

class NextstepsModeParsingTest(unittest.TestCase):
    # 2 tests on the parsing-rules + report examples
    test_skill_documents_flag_parsing_rules
    test_mode_report_examples_present
```

Two helpers worth keeping:

```python
def _extract_checklist_body(text: str, header_regex: str):
    """Find `**...:**` checklist header, return the bullet body up to the
    next bold-header or `---` separator. Accepts bullets wrapped in
    backticks (``- `[x]` ...``) and bare (`- [x] ...`)."""
    # See full implementation in test_nextsteps_modes_contract.py
```

```python
# Use a small set of regex patterns to assert both sentence-form AND
# table-form expression of the contract — different repos / skills use
# either, and the test should be tolerant of both.
sentence_patterns = [
    r"default.*only.*beads.*~/roadmap",
    r"only does? beads.*~/roadmap",
]
table_pattern = r"\|.*\*\*default\*\*.*\|.*\bbr\b.*~/roadmap"
```

## What this PR actually committed (jleechanorg/claude-commands#343)

```
5ea486fb9 feat(nextsteps): make --full opt-in; default does only beads + ~/roadmap
c189c7391 style(nextsteps tests): ruff format the new contract test
```

Authored as `jleechan2015 <jleechan2015@users.noreply.github.com>` (matches the pattern of recent `origin/main` commits in this repo — the repo's existing commits are all under this identity). PR opened via `gh pr create --base main --head feature/nextsteps-beads-roadmap-default`.

Branch name pattern: `feature/<verb>-<scope>` (matches `feature/sidekick-5min-checkpoint`, `feat/cross-cli-ratelimit-stop-hook` siblings in the repo).

## Verification checklist (post-push)

```bash
# 1. Tests
python3 -m unittest discover tests
# Expected: Ran N tests in ~0.01s, OK

# 2. Python lint (ruff)
ruff check tests/
ruff format --check tests/
# Expected: All checks passed! / N files already formatted

# 3. GitHub PR
gh pr view <N> --json state,url,number,baseRefName,headRefName,commits
# Expected: state=OPEN, baseRefName=main, commits >= 1

# 4. (Optional) GitHub Actions if the repo has CI
gh api repos/<OWNER>/<REPO>/commits/<HEAD_SHA>/check-runs \
  --jq '.check_runs[] | {name, status, conclusion}'
```

If any of these fail, see the matching pitfall above before attempting a fix.