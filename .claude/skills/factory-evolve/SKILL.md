---
name: factory-evolve
description: Analyze conversation and git history to find gaps where cold reviews (codex, Bugbot, CodeRabbit, /reviewdeep) caught issues that dark-factory in-pipeline reviewer nodes missed. Proposes targeted .dot and runner improvements ranked by G1–G9 gap taxonomy.
---

# /factory-evolve Skill

Compares what the dark-factory in-pipeline reviewer nodes actually caught against what a cold reviewer (codex, Bugbot, CodeRabbit, manual `/reviewdeep`) caught on the same work. Outputs a ranked proposal list of improvements to `.dot` graphs and `runner/` handlers.

## When to invoke

- Automatically from `/integrate` (post-branch cleanup pass)
- Manually after a dark-factory pipeline run to check if the reviewer nodes were adequate
- With `--pr N` to audit a specific PR's cold review vs factory run

## Inputs

```
/factory-evolve                  # scan last 7 days of history
/factory-evolve --days 14        # widen the lookback window
/factory-evolve --pr 26          # audit one PR (cold review vs factory wiring)
/factory-evolve --taxonomy       # skip history; just check current .dot files for G1+G2 violations
```

## Execution steps

### Phase 0 — Locate the dark-factory repo root

```bash
FACTORY_HOME="${DARK_FACTORY_HOME:-$(git rev-parse --show-toplevel 2>/dev/null)}"
```

### Phase 1 — History search (parallel)

Run two history searches concurrently.

**1a. Claude Code JSONL — find factory pipeline runs near cold reviews:**

```bash
# Find transcripts referencing dark-factory runs
rg --max-filesize 5M -l \
  'dark-factory --pipeline|gate_er|holdout_eval|_resolve_gate_backend' \
  ~/.claude/projects/ 2>/dev/null | head -20
```

For each matching file: `grep -n "gate_er\|cold review\|codex.*caught\|factory.*missed\|verdict.*fail" FILE | head -30` to locate the relevant lines; read only those ±30-line windows (Read with offset/limit).

**1b. Codex SQLite — threads where factory + review both appear:**

```python
import sqlite3, os
db = os.path.expanduser("~/.codex/state_5.sqlite")
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
rows = con.execute("""
  SELECT title, substr(first_user_message,1,400),
         datetime(created_at/1000,'unixepoch') as ts
  FROM threads
  WHERE (title LIKE '%dark-factory%' OR first_user_message LIKE '%gate_er%'
         OR first_user_message LIKE '%cold review%')
  ORDER BY created_at DESC LIMIT 15
""").fetchall()
```

### Phase 2 — Gap extraction

For each factory-run + cold-review pair found:

1. **Factory verdict** — what did the pipeline's reviewer nodes report? (pass/warn/fail, which node)
2. **Cold-review findings** — what did the independent reviewer catch?
3. **Gap category** — classify each missed finding using G1–G9 taxonomy (see below)

### Phase 3 — Structural audit of current .dot files (G1+G2)

```bash
cd "$FACTORY_HOME"
# Find all code-producing graphs
grep -rl 'codergen\|type=codergen\|backend=' pipelines/ | sort

# For each, check: does a path from start to exit pass through an independent reviewer?
# Reviewer-bearing nodes: type=codergen class=review, type=gate_er, type=gate_es,
#   type=gate_code_standards, or label containing "review" with prefer_adversarial

# G1 check: any graph with zero reviewer nodes on the code path
grep -rL 'gate_er\|gate_es\|class=review\|prefer_adversarial' pipelines/*.dot

# G2 check: reviewer fail edges routing to exit (not fix)
grep -A2 'outcome!=success' pipelines/**/*.dot | grep 'exit'
```

### Phase 4 — Ranked proposal output

Write a `specs/factory-evolve-research/proposals-YYYY-MM-DD.md` with:

```markdown
# Factory-Evolve Proposals — YYYY-MM-DD

## Evidence (N cold-review incidents, M structural G1/G2 violations)

## Proposals (ranked by impact × ease)

### [P1] Add cold-review node to gates.dot / pr_gates.dot (G1)
- Evidence: PRs #26, #28, #70 — factory gates not in CI; no cold-review node in these graphs
- Fix: insert `cold_review [type=codergen, class=review, prefer_adversarial=true,
        backend=codex, prompt="@prompts/slim/cold_review.md"]` after `plan`/`fix`,
        edge `cold_review -> fix [condition="outcome!=success", label="redo"]`
        `cold_review -> holdout_eval [condition="outcome=success"]`

### [P2] Route reviewer fail edges to fix loop, not exit (G2)
- Evidence: review_pr.dot, bug_fix.dot, gates.dot all route reviewer fail -> exit
- Fix: change `review -> exit [condition="outcome!=success"]` to
       `review -> fix [condition="outcome!=success"]` with max_visits guard

### [P3] Inject git diff into reviewer prompts (G4)
- Evidence: prompts/slim/review.md, prompts/catalog/review.md say "analyze workspace changes"
  but never embed the actual diff — reviewer may review wrong scope
- Fix: runner/handler_dispatch.py _build_codergen_prompt() to prepend
  `git diff ${base_sha}..HEAD` (base already in _resolve_base_sha) into reviewer prompts

### [P4] Make prefer_adversarial default-on for gate nodes (G7)
- Evidence: PR #26 — named gates (gate_er, gate_es, gate_code_standards) don't set
  prefer_adversarial; claude coder can get claude reviewer on same run
- Fix: handler_dispatch.py _resolve_gate_backend(): treat gates as prefer_adversarial=true
  unconditionally; log same_vendor_as_coder=true as CXDB metadata warning

### [P5] Treat warn/partial as blocking for code-producing graphs (G6)
- Evidence: handler_verdict.py maps warn->success; a "warn" with blockers passes
- Fix: add graph-level attribute gate_strict=true; handler reads it and maps warn->failure

...
```

## Gap taxonomy reference (G1–G9)

| Code | Name | Key files |
|------|------|-----------|
| G1 | reviewer-not-wired-in-graph | gates.dot, pr_gates.dot, minimal_research.dot |
| G2 | failed-review-routes-to-exit | review_pr.dot, bug_fix.dot, gates.dot |
| G3 | weak/templated reviewer prompt | handler_universal_prompts.py:111,146 |
| G4 | no-diff-injection | prompts/slim/review.md, prompts/catalog/review.md |
| G5 | scope-limited-to-diff-hunk | prompts/slim/review.md step 2 |
| G6 | verdict-parsing-swallows-nuance | handler_verdict.py:28-43, :135-138 |
| G7 | single-vendor-collapse | handler_dispatch.py:361, _execute_gate:423-425 |
| G8 | SHA-binding-not-freshness | handler_verdict.py:66-77 |
| G9 | unit-only/templated-evidence-accepted | prompts/slim/evidence_review.md |

## Output artifacts

- `specs/factory-evolve-research/proposals-YYYY-MM-DD.md` — ranked proposal list
- `specs/factory-evolve-research/convo-history-forensics.md` — updated incident log
- On-screen summary: top 3 proposals + counts

## Notes

- History search is read-only; do NOT modify `.dot` files or `runner/` without explicit user approval.
- If no factory pipeline runs are found in history, run Phase 3 (structural audit) only and note that history search found nothing.
- Proposals are advisory — the user drives which to implement. Never auto-apply.
- Source files for the gap taxonomy: `specs/factory-evolve-research/reviewer-gap-taxonomy.md` (canonical) and `specs/factory-evolve-research/git-pr-forensics.md`.
