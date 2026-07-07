---
name: llm-narration-format-clarifier
description: |
  Fix LLM narration drift (LLM improvises formatting because a prompt line is
  too terse) by adding a worked example in the prompt, NOT by adding backend
  enforcement. Use when the user reports the LLM is dropping fields, abbreviating
  formats, or substituting its own template for an underspecified one.

  Triggers: "the LLM dropped X", "show both/all Y", "the narrative is missing Z",
  "prompt is too vague", "LLM invents the format", "add a worked example",
  "make the LLM consistently format X", "narration drift", "format hint needed".

  Does NOT apply to: LLM judgment errors that need richer prompt context (use
  llm-prompt-engineering / root-cause-first), backend state bugs (use root-cause-first),
  or LLM compliance with explicit instructions it already has (use systematic-debugging).
version: 1.0.0
allowed-tools:
  - read_file
  - search_files
  - patch
  - write_file
  - terminal
  - send_message
context: |
  Repos where the LLM is the formatter of player-facing narrative text:
  your-project.com, $GITHUB_REPOSITORY, any RPG / game / story engine
  that surfaces dice rolls / currency / status lines to the user.
---

# llm-narration-format-clarifier

## The class of bug

The prompt has a one-line instruction like `**Advantage/Disadvantage:** Show both dice, indicate which was used.` The LLM reads it, decides "show both dice" is a soft hint, and narrates the roll with only the kept die. The user complains: "the LLM is dropping the second die."

The same shape recurs for currency, status lines, time deltas, name rendering, etc. The temptation is to add a backend formatter / regex / post-processor that scrubs the LLM output. **That is the wrong move** for two reasons:

1. **It violates root-cause-first.** The LLM is the canonical author of the narrative. A backend post-processor silently rewrites it; the user sees "corrected" prose with no signal that something was overridden.
2. **It drifts.** The post-processor handles the specific case the user complained about; the next case is a new post-processor; six months later the codebase has a forest of regex scrubbers, each handling a slightly different pattern, none of them tested together.

The correct fix is a **worked example** in the prompt — the same pattern the LLM already imitates successfully for the canonical case. Worked examples are what the LLM was trained on; they are the highest-fidelity format hint you can give it.

## The 4-step recipe (verified 2026-06-13, dice adv/disadv PR #7539)

### Step 1 — Confirm the LLM controls the formatting, not the server

Grep the prompt file for the format-relevant rule. Grep the server code for any
post-processing that scrubs the LLM output for this format. If the server does
post-process, you have a different bug (and a different skill).

For dice in your-project.com:
- Prompt: `$PROJECT_ROOT/prompts/dice_system_instruction.md:44` — single ambiguous line.
- Server: `$PROJECT_ROOT/dice.py` returns the raw server-rolled values via `tool_requests`; no post-processor scrubs the narrative.
- **Verdict: LLM is the formatter. Prompt is the right surface.**

### Step 2 — Find an existing worked example in the same prompt to mirror

The LLM reliably imitates the existing normal-roll format on line 42:
```
`Action: Stealth Check | Roll: 1d20+5 = [12]+5 = 17 | Result: Success`
```
The adv/disadv lines below it lacked a worked example — that's the gap. Find
the canonical line in your own prompt and mirror its structure. **Do not invent
a new format style**; the LLM imitates the dominant pattern, so the worked
example should be byte-similar to the line above it.

### Step 3 — Replace the vague line with the worked example(s)

Before:
```
**Advantage/Disadvantage:** Show both dice, indicate which was used.
```

After (one worked example per branch, plus a "never abbreviate" guard):
```
**Advantage/Disadvantage:** The server rolls 2d20 (one kept, one dropped). Display BOTH raw d20 values, label which die was kept, then apply the modifier once. Format examples:

- `Action: Stealth Check (Advantage) | Roll: 2d20+5 keep high = [8, 17]+5 = 22 | Kept: 17 | Result: Success`
- `Action: Perception Check (Disadvantage) | Roll: 2d20+3 keep low = [4, 11]+3 = 14 | Kept: 4 | Result: Fail`

The "kept" die is the one that determined the total; always show the dropped one too for transparency. Never abbreviate to a single d20.
```

Three structural pieces, all required:
1. The instruction (what to do).
2. A worked example per branch (concrete template).
3. A negative guard ("never abbreviate to X") — the LLM will paraphrase on edge cases; the durable rule is the negative guard.

### Step 4 — Add a string-presence unit test

The test guards the worked example so a future prompt revision cannot silently
regress to the vague line. Use string-presence assertions on the prompt file:

```python
PROMPT_PATH = "$PROJECT_ROOT/prompts/dice_system_instruction.md"

def _load_prompt() -> str:
    with open(PROMPT_PATH, "r", encoding="utf-8") as fh:
        return fh.read()


class TestDicePromptAdvantageDisadvantage(unittest.TestCase):
    def test_prompt_has_advantage_keep_high_example(self):
        prompt = _load_prompt()
        self.assertIn("2d20+5 keep high", prompt)
        self.assertIn("[8, 17]", prompt)
        self.assertIn("Kept: 17", prompt)
        self.assertIn("Advantage", prompt)

    def test_prompt_has_disadvantage_keep_low_example(self):
        prompt = _load_prompt()
        self.assertIn("2d20+3 keep low", prompt)
        self.assertIn("[4, 11]", prompt)
        self.assertIn("Kept: 4", prompt)
        self.assertIn("Disadvantage", prompt)

    def test_prompt_drops_old_vague_line(self):
        prompt = _load_prompt()
        self.assertNotIn("Show both dice, indicate which was used.", prompt)

    def test_prompt_explicitly_forbids_single_d20_abbreviation(self):
        prompt = _load_prompt()
        self.assertIn("Never abbreviate to a single d20", prompt)
```

Three assertions per branch + one for the dropped-old-line + one for the
negative guard. The test file should live in `$PROJECT_ROOT/tests/` per AGENTS.md
"Test File Placement" rule (for your-project.com; adapt to your repo's test
dir convention).

## Evidence policy (what counts as proof the worked example works)

| Change scope | Evidence required | Why |
|---|---|---|
| `$PROJECT_ROOT/prompts/**` only, no LLM call site change, no schema change, no server change | **String-presence unit test is sufficient** | The prompt is a static string; the test guards that string. A real-LLM replay does not test the prompt — it tests the LLM, which is non-deterministic and not the unit under test. |
| Prompt change that coincides with a schema/tool/agent change | Real LLM full HTTP raw response evidence (`## Real LLM Evidence` section) | The change is no longer prompt-only; the schema is also a unit under test. |
| Prompt change that claims to fix a specific user-visible failure | Replay the original failure scenario (existing test, real LLM, real campaign) | The test must be RED before the prompt fix, GREEN after. The "Was the bug actually fixed?" question is the test's question. |

For the dice adv/disadv case (PR #7539), the change is prompt-only — string-presence test is the right evidence shape. The PR's `## Real LLM Evidence` is N/A + explains why, not skipped.

## Pitfalls

### Pitfall 1 — Stopping at "PR open" instead of driving to green

The prompt-only change takes 3 minutes to land. Watching the checks turn green
takes 15-30 minutes. The temptation is to declare done at PR-open. **Don't.**
Re-trigger failed checks, fix anything fixable in the PR, post the in-thread
update with the final state. PR-open is the *minimum* unit of done-ness; green
CI is the *complete* unit.

If a CI failure is **infra-class** (runner stale refs, missing env var, OOM),
ship the infra fix in the same turn — the work for the user is "PR is green",
not "PR exists with a known transient failure that I'll get to later." Verified
2026-06-13: a self-hosted runner had 6 stale broken local refs (deleted
branches); the same runner failed every job in 6 seconds with
`fatal: bad object refs/remotes/origin/<branch>`. Pruning the local refs
restored green. The PR diff was 0; the CI state went red→green.

### Pitfall 2 — Marking the change N/A on `## Real LLM Evidence` for a prompt-only change that touches user-visible behavior

The your-project.com PR template hard-requires `## Real LLM Evidence` whenever
`$PROJECT_ROOT/prompts/**` changed. For a pure prompt-text change with no schema /
agent / call-site change, N/A is correct — but the explanation must say *why*
N/A is correct ("the prompt is a static string; the test guards that string;
a real-LLM replay tests the LLM, not the unit under test"). N/A + reason
passes the gate; bare N/A does not.

### Pitfall 3 — Skipping the "test the test" step

The unit test guards the prompt. Run the test green in the worktree *before*
pushing the branch. A test that always passes is worse than no test — it
silences regressions.

```bash
cd <worktree>
$HOME/your-project.com/venv/bin/python3 -m unittest \
  mvp_site.tests.test_dice_prompt_advantage_disadvantage -v
# Expect: Ran 5 tests in 0.000s / OK
```

### Pitfall 4 — Inventing a new format style instead of mirroring the existing one

The LLM imitates the dominant pattern. If your worked example uses
`[d20_high, d20_low]+mod` but the surrounding prompt uses
`1d20+5 = [12]+5 = 17`, the LLM will produce inconsistent output. **Mirror the
existing line byte-similar.** Same delimiters, same modifier-once math, same
"Result: X" suffix.

## Cross-references

- `worldarchitect` skill — 7-green gate, evidence rules, design-decision heading requirement.
- `root-cause-first` skill — when the LLM is the wrong layer to fix (rare for narration drift; common for state bugs).
- `always-pr-never-local-edit` skill — worktree + GH issue + branch + PR + push, every time.
- `drive-pr-to-green` skill — full bring-to-green workflow for the next session.
