# /consensus Command - Multi-Agent Agreement Code Review

**Purpose**: Run a consensus-building review loop that uses the subagents defined under [`.claude/agents`](../agents/) to validate the current work-in-progress. The command inspects the active Git state (latest commit, local unstaged/staged changes) and the currently checked-out PR on GitHub, then drives iterative fixes until all agents agree no major issues remain or the maximum of three review rounds is reached.

## Usage
```
/consensus [<scope>]
/cons [<scope>]          # Alias
```
- **Default scope**: Current PR (if tracking a GitHub pull request) plus any local unmerged files.
- **Optional scope**: Specific file(s), folder(s), or PR number to narrow the review focus.

## Context Acquisition (Always Performed First)
1. **Detect active PR** using `gh pr status` or `git config branch.<name>.merge` to extract the PR number and remote.
2. **Record latest commit** with `git log -1 --stat`.
3. **Capture local changes**:
   - `git status --short` for staged/unstaged files.
   - `git diff --stat` and targeted `git diff` snippets for modified files.
4. **Verify synchronization with GitHub**:
   - Fetch PR files: `gh pr view <pr> --json files,headRefName,baseRefName`.
   - Confirm branch alignment (`git rev-parse HEAD` vs PR head SHA).
5. **Assemble review bundle** containing: PR description, latest commit message, diff summaries, and local-only edits.

## Agent Line-Up (All Agents Participate Every Round)
Run the same context bundle through the following `.claude/agents` profiles every round:

- `code-review`
- `codex-consultant`
- `gemini-consultant`
- `grok-consultant`

They do **not** get special roles. Everyone checks for serious correctness, security, performance, or stability problems. When any agent finds a major or critical problem they should literally say `LOL SERIOUS ISSUE:` before their explanation so the whole group snaps to it. All feedback should be tagged with severity (`critical`, `major`, `minor`, `nit`).

## Iterative Consensus Loop
The `/consensus` workflow is strictly limited to **three rounds**. Each round executes the following phases via `/execute` or `/orch`:

1. **Consultation Phase (Parallel)**
   - Run `/guidelines`.
   - Use `/execute` (or any orchestrator you prefer) to fan out the same brief to `code-review`, `codex-consultant`, `gemini-consultant`, and `grok-consultant` in parallel.
   - Remind each agent to call out serious problems with the `LOL SERIOUS ISSUE:` prefix and to keep the rest of their notes short.
   - Collect structured feedback (issue lists, severity, recommended fixes).
   - Use `/think` or `/thinku` as needed for synthesis.

2. **Synthesis & Priority Mapping**
   - Aggregate all findings into a single matrix keyed by file and issue type.
   - Highlight disagreements where any agent flags a `critical` or `major` issue that others do not.
   - Determine "consensus status" for the round:
    - **PASS**: No agent reports `critical` or `major` issues.
    - **REWORK**: Any `critical`/`major` items remain or agents disagree on fix completeness.

3. **Remediation Planning (If REWORK)**
   - Generate a fix plan referencing offending files/lines.
   - Prioritize fixes by severity and cross-agent agreement.
   - Decide required validations (tests, linters) before next round.

4. **Fix Application**
   - Apply code changes using natural language edits (`apply_patch`, file rewrites, or existing fix commands like `/fix`, `/execute` operations).
   - After **every individual change**, immediately run the relevant local automated tests (unit, integration, lint, type checks) and repair any failing tests before proceeding.
   - Update or create tests as required by agent feedback.
   - Document all modifications in an interim change log, including which tests were executed.

5. **Revalidation**
   - Re-run any quick sanity checks (e.g., `git diff`, `pytest`, build commands) to ensure fixes pass locally.
   - Proceed to the next round only after local validation succeeds and there are no outstanding failing tests.

6. **Round Retrospective**
   - Summarize the primary conversation highlights in the main thread so future readers can follow the resolution path.
   - Provide a per-agent recap that captures each consultant's stance, especially any `LOL SERIOUS ISSUE` flags and how they were addressed.
   - Store these notes with the interim change log for traceability before launching the next loop.

The loop stops immediately when a round achieves PASS status or after three rounds (whichever occurs first).

## Consensus Rule Set
- **Hard stop** on deployment/merge suggestions; output remains advisory.
- **Major issue definition**: Anything labeled `critical` or `major` by any agent, including security vulnerabilities, correctness bugs, significant architectural flaws, or blocking test failures.
- **Minor disagreements** (nitpicks, stylistic suggestions) do not prevent consensus but are documented for follow-up.
- **Second opinions**: When agents disagree on severity, automatically trigger a focused re-review of the disputed section (e.g., ping the specific agent that said `LOL SERIOUS ISSUE:` and one other peer) within the same round before deciding.

## Output Format
```
# Consensus Review Report

## Summary
- Round count: <1-3>
- Final status: PASS | REWORK_LIMIT_REACHED
- Key validated areas

## Major Findings
| Round | Source Agent | File/Section | Severity | Resolution |
|-------|--------------|--------------|----------|------------|

## Implemented Fixes
- <bullet list of code/test updates per round>

## Round-by-Round Summaries
- Round <n>: <main conversation highlights>
  - code-review: <key takeaways>
  - codex-consultant: <key takeaways>
  - gemini-consultant: <key takeaways>
  - grok-consultant: <key takeaways>

## Remaining Follow-Ups
- <nitpicks or deferred improvements>
```
Include references to executed test commands and link to generated guideline docs if applicable.

## Post-Run Clean Up
1. Ensure working tree cleanliness (`git status --short`).
2. If changes were made, restate next steps (commit, push, or request manual review).
3. Update memory systems with any new learnings or architectural decisions discovered during the run.
