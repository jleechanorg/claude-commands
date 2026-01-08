# Fix-Comment Orchestration Workflow Design

## Goals
- Add `--fix-comment` mode to the PR monitor that targets the same actionable PRs as the current monitor.
- Replace the mega-comment posting with an orchestration prompt that instructs the chosen CLI model(s) to fix PR comments directly.
- Post a queued comment immediately and a final review-request comment after fixes, mentioning all bots and Greptile.
- Prevent repeat processing with a new hidden marker tied to the head SHA.

## Non-Goals
- Changing `/fixpr` orchestration behavior or safety limits.
- Reworking PR discovery or bot detection logic outside fix-comment needs.

## Behavior Overview
1. Discover actionable PRs using the existing monitor logic.
2. For each PR:
   - Fetch head SHA + comments.
   - Skip if a fix-comment marker already exists for the head SHA.
   - Dispatch an orchestration task (TaskDispatcher) using the CLI chain from `--fixpr-agent`.
   - Post a queued comment immediately (without marker to avoid blocking review requests).
   - Wait for `/tmp/orchestration_results/pr-{number}._results.json` (timeout default 1200s).
   - Post a final review-request comment that mentions all bots + Greptile and includes the marker.
3. Count fix-comment markers alongside Codex markers for safety limits.

## Prompt Requirements (Agent Side)
- Focus on addressing all PR comments; respond with DONE/NOT DONE for each.
- Fix failing tests and merge conflicts.
- Commit with `[{primary_cli}-automation-commit] ...`.
- Write a JSON summary to `/tmp/orchestration_results/pr-{number}._results.json`.
- Do **not** mention Greptile in the prompt.

## Markers
- New marker prefix/suffix: `<!-- fix-comment-automation-commit:SHA -->`.
- Used to skip repeat processing for the same head SHA.

## CLI + Targeting
- New `--fix-comment` flag (mutually exclusive with `--fixpr`).
- Reuse `--fixpr-agent` for CLI chain in fix-comment mode.
- `--target-pr/--target-repo` should work for fix-comment.

## Testing
- Marker extraction for fix-comment.
- Review-request comment includes Greptile + all bot mentions.
- Fix-comment path dispatches orchestration task.
