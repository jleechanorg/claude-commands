---
name: validation-gate
description: Pre-report gate — verifies all planned evidence artifacts exist before writing comparison/validation reports
---

# Validation Gate Skill

## When to use

Before writing ANY evidence report, comparison report, or validation summary that makes quantitative claims.

## Protocol

### Step 0: Intent alignment and compromise disclosure (MANDATORY)

Before executing ANY validation plan, the agent MUST present this to the user and wait for approval:

```
## Validation Intent Check

**What you asked**: <restate the user's actual question in plain language>
**What this plan measures**: <what the experiment will actually test>
**Gap**: <if these differ, say so explicitly>

### Ideal test (100% real, no compromises)
<describe what a perfect test would look like — real PRs, real CI, real review cycles, real merge, real cleanup>

### What this plan actually does
<describe what the plan will do, with all constraints visible>

### Compromises vs ideal
| Compromise | Why | Impact on validity |
|---|---|---|
| <e.g., dead sessions instead of real PRs> | <e.g., faster, no CI wait> | <e.g., measures cleanup overhead, not active PR work> |
| <e.g., N=1 measurement> | <e.g., time constraint> | <e.g., no statistical confidence> |
| <e.g., shared rate-limit pool> | <e.g., single GH token> | <e.g., sequential measurements may have cross-contamination> |

### What the results CAN prove
<honest list>

### What the results CANNOT prove
<honest list — this is the most important section>
```

If the user sees the "CANNOT prove" list and says "that's not good enough", redesign the experiment before executing. Do not execute a plan the user hasn't explicitly approved after seeing the compromises.

### Step 1: Find the plan

Locate the validation/test plan that specifies what artifacts should be produced. Common locations:
- `roadmap/*.md` (validation plans)
- `/tmp/*/` (evidence directories)
- Conversation context (agreed-upon steps)

### Step 2: Extract required artifacts

Parse the plan for every file path listed under "Evidence artifacts", "Output", or "Artifacts" sections. Build a checklist.

### Step 3: Verify each artifact exists and has substance

For each required artifact:

```bash
# Check exists and has content
for f in <artifact_list>; do
  if [ ! -f "$f" ]; then
    echo "MISSING: $f"
  elif [ $(wc -c < "$f") -lt 50 ]; then
    echo "EMPTY/TRIVIAL: $f ($(wc -c < "$f") bytes)"
  else
    echo "OK: $f ($(wc -c < "$f") bytes)"
  fi
done
```

### Step 4: Verify artifact content matches claim class

| Claim class | Artifact must contain |
|---|---|
| Runtime measurement | Timestamps, process output, actual command invocations |
| Code analysis | Source file references, line numbers, function names |
| Integration test | Real I/O logs, API call evidence, timing data |
| Projection | Stated assumptions, formula, sensitivity analysis |

If an artifact contains code analysis but the claim is "runtime measurement", flag it as **MISMATCH**.

### Step 5: Gate decision

- **All artifacts present + content matches claim class** → Proceed with report
- **Any artifact MISSING** → STOP. List missing artifacts. Either produce them or downgrade the claim class.
- **Content mismatch** → STOP. Re-label the claim class to match what was actually measured.

### Step 6: Consistency check

Before finalizing any report:
- Grep for all numeric assumptions (poll intervals, TTLs, session counts)
- Verify the same value is used consistently across all artifacts
- If values differ between artifacts, reconcile before publishing

## Anti-patterns this skill prevents

1. Writing a plan with runtime steps, then substituting code analysis
2. Capturing rate-limit deltas from test suite runs and attributing them to lifecycle-worker behavior
3. Using different poll interval assumptions in different artifacts
4. Claiming "integration test" when only code was read
5. Presenting projections as findings
