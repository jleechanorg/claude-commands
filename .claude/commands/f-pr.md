---
description: "/f-pr — use LLM judgment to pick the right dark-factory pipeline for an existing PR (gates only, full validation, or PR iteration) and run it with evidence"
type: quality
execution_mode: immediate
aliases: [pr-f, f-on-pr, factory-pr]
---

# /f-pr — drive an existing PR to /green via dark-factory

Use the LLM to **read the PR's context and pick the right dark-factory
pipeline** to bring it to /green with evidence. The decision is the
LLM's, not a deterministic rule table — the model is told what each
pipeline is good for and reasons from the PR's actual content.

The LLM may decide /fs (`pipelines/slim/spec_gen.dot`) is needed first
and stop without running gates; that is a valid terminal state for this
skill.

## Action

1. **Resolve the PR number.**
   - If `$ARGUMENTS` contains a number, use it.
   - Else if the cwd is a git repo, `gh pr list --head
     "$(git rev-parse --abbrev-ref HEAD)" --json number --jq '.[0].number'`.
   - Else ask the user.

2. **Read PR context** (LLM uses these as facts, not as routing rules):
   ```bash
   gh pr view <N> --json number,title,state,isDraft,additions,deletions,changedFiles,baseRefName,headRefName,body,files,labels
   gh pr view <N> --json statusCheckRollup
   gh pr diff <N> --name-only
   # Optional context the LLM may pull:
   gh pr view <N> --comments
   ls specs/ 2>/dev/null          # in-PR specs (when present)
   ls road*/  docs/design/ 2>/dev/null
   ```

3. **Let the LLM reason.** The LLM should read the PR context and
   reason about:
   - **What kind of work is this?** New feature / bug fix / refactor /
     docs / test-only / infra. The diff stat + body + file list inform
     this. Do NOT pre-bucket by label; `documentation` is a label, not
     a contract.
   - **Is the spec already present?** If `specs/<feature>.md` or a
     `roadmap/*.md` link in the PR body covers the change, /fs is
     skippable. If the PR is "implement X per spec Y" with X,Y visible
     in the body, /fs is skippable. Otherwise the LLM may decide
     spec_gen is a prerequisite and stop here with a recommendation
     (this is a valid terminal state — do not force a run).
   - **Holdout eligibility.** If the PR's diff touches a feature that
     has a sealed holdout (`~/projects/dark-factory-holdouts/holdouts/<feature>/`),
     the LLM should pass `--feature <name>`. If the holdout directory
     does not exist for this feature, the LLM should not invent one.
   - **What evidence do we need?** /es + /er + /code_standards are
     the minimum; holdout_eval is the behavior-grade. The LLM picks
     the pipeline that delivers the right evidence mix without
     over-running.

4. **Pick the pipeline from this set** (LLM uses these as the menu,
   not as a rule table):

   | Pipeline | When the LLM might pick it |
   |----------|----------------------------|
   | `pipelines/factory/hello.dot` | Wiring smoke only — LLM is unsure of the graph; verify mechanics first with `--backend echo` |
   | `pipelines/factory/gates.dot` | Code is on the branch and the LLM wants holdout + the 3 evidence gates |
   | `pipelines/factory/pr_gates.dot` | Code is on the branch and the LLM wants the 3 evidence gates; the holdout is also run per the "Holdout-always policy" (the SKILL.md files at `.claude/skills/dark-factory/SKILL.md:40` and `.claude/skills/factory-spec/SKILL.md:280` say "bypasses holdouts" but the actual `.dot` does not — the LLM should trust the file). Requires `--feature <name>` for the holdout to resolve. |
   | `pipelines/slim/minimal_pr.dot` | The LLM thinks the PR needs more implement/test work, not just gates; pass `--state slim.test_command=...` to parameterize the test command. The SKILL.md also says "bypasses holdouts" but the .dot does include holdout — the LLM should trust the file and pass `--feature` if a sealed holdout exists. |
   | `pipelines/bug_fix.dot` | The PR is a TDD bug fix with red/green discipline |
   | `pipelines/slim/spec_gen.dot` | The LLM has decided /fs is needed first — STOP and recommend running it before any /f pipeline; this is a valid terminal state |

5. **Pick the backend.**
   - `--backend echo` for wiring smoke (no LLM cost).
   - `--backend claude` / `codex` / `agy` / `minimax` for real runs.
     The LLM should default to `claude` unless the PR's reviewer queue
     or the `gate_er` priority queue says otherwise.

6. **Construct the command**, **show the user**, and **run it.**

   ```bash
   export DARK_FACTORY_HOME="${DARK_FACTORY_HOME:-$HOME/projects/dark-factory}"
   export DARK_FACTORY_HOLDOUTS="${DARK_FACTORY_HOLDOUTS:-$HOME/projects/dark-factory-holdouts}"
   export PATH="$HOME/.local/bin:$PATH"
   cd <PR's target repo>   # the repo the PR is against, not dark-factory
   dark-factory \
     --pipeline <CHOSEN> \
     --goal "<PR#N + short title + 1-line LLM rationale>" \
     --backend <CHOSEN> \
     [--feature <holdout-feature-if-applicable>] \
     [--state <KEY>=<VALUE> if minimal_pr] \
     --cxdb ~/.dark-factory/cxdb.sqlite
   ```

7. **Report the verdict.** Quote the runner's final JSON line
   (`final_outcome`, `pipeline`, `steps`) and the per-node trace. If
   `final_outcome != "success"`, run `df-healer --cxdb <path>` and
   surface the report.

## Honesty rules (LLM, do not skip)

- Quote the **actual** `dark-factory` command you ran. No paraphrasing.
- If the LLM decided /fs is needed first, **say so and stop** — do not
  silently fall through to `gates.dot` and pretend the PR is green.
- If `--backend echo` was used, label the run as a wiring smoke, not a
  real validation. The 3-gate verdicts from echo are not real LLM
  verdicts.
- The `gate_er` priority queue is `codex > minimax > agy > claude-sonnet`
  by default. If the LLM passes `--backend claude` for a real run, the
  `gate_er` reviewer is still resolved via the priority queue (not
  clauded by default unless the queue falls all the way through).
- Do not invent `--feature` values. If you cannot find a holdout
  directory at `~/projects/dark-factory-holdouts/holdouts/<feature>/`,
  do not pass `--feature`.

## Why this is ZFC

The decision (pipeline choice, backend choice, --feature) is the LLM's
based on the PR's actual content. There is no `if is_draft then X`
branch, no `if labels contains 'bug' then bug_fix.dot` rule, no
keyword-routing. The model reads the PR and reasons about it. If the
LLM gets it wrong, the user corrects it and the LLM learns — there is
no code to maintain.
