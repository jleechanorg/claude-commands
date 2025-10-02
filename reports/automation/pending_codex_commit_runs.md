# Pending Codex Commit Automation Check

## Overview
This document doubles as the long-form pull-request description for the "Fix Codex pending commit detection prefix handling" work. It explains what the automation change does, how the guard behaves at runtime, and the exact steps required to validate the behaviour locally without reaching out to the GitHub API.

The `JleechanorgPRMonitor` now defers posting Codex instructions when it detects that the latest PR commit already came from Codex automation. To regression-test that flow, I executed the monitor against representative pull requests using a mocked `gh` CLI. The mock returns deterministic metadata so we can exercise both the success path and the skip condition introduced by the latest changes.

## Pending Commit Guard Logic
1. The monitor fetches the PR head SHA and recent comments via `gh pr view --json headRefOid,comments`.
2. Each comment authored by a Codex-like bot (`codex` substring, case-insensitive) is scanned with three regexes that understand blob links, commit links, and prose references (e.g., "commit abc1234").
3. When a referenced SHA is found, the monitor normalizes both the summary hash and the PR head SHA to lowercase.
4. The guard compares the two hashes, allowing either an exact match or a prefix relationship where the summary SHA is a shortened form of the full head SHA.
5. If a match is found, the monitor records the PR as processed and skips posting any further Codex instructions for that commit, preventing duplicate automation loops.

Because the guard records the processed state even when it skips, rerunning the monitor on the same commit remains idempotent. Only new commits that are not referenced in a Codex summary will trigger a fresh automation pass.

## Mocked Execution Flow
To validate the guard end-to-end without hitting GitHub rate limits, the repository now includes a lightweight CLI shim at `automation/testing_util/mock_gh_cli.py`. When copied or symlinked to `gh` and placed at the front of `$PATH`, it intercepts the exact `gh pr view` and `gh pr comment` calls the monitor performs.

The shim exposes three synthetic pull requests:

| PR | Scenario | Key Fixture Data |
| --- | --- | --- |
| `#101` | Eligible path | No Codex summary comment references the head SHA (`abc1234…`). |
| `#102` | Pending-commit skip | A Codex bot comment references the short SHA `ffeeddbc`, which matches the head commit `ffeeddbc…`. |
| `#103` | Historical marker | Contains an old Codex marker for a different commit so the run proceeds normally. |

Running the monitor with the shim exercises the new logic while keeping stdout logs and exit codes identical to a real run.

## Environment
- Command runner: `python -m automation.jleechanorg_pr_automation.jleechanorg_pr_monitor`
- Mock GitHub CLI (`automation/testing_util/mock_gh_cli.py`) copied to `gh` and inserted via `PATH` to supply fixture PR data.

## Validation Steps
Follow these commands (with the mock CLI named `gh` and available on `$PATH`) to reproduce the scenarios that informed this PR:

1. **Eligible PR (simulated #101)**
   1. Run `python -m automation.jleechanorg_pr_automation.jleechanorg_pr_monitor --target-pr 101 --target-repo worldarchitect.ai`.
   2. Observe the monitor emit a `✅ Posted Codex instruction comment…` log line. The mock CLI prints `Comment posted`, confirming the comment body would have been sent in production.
   3. The monitor writes the processed state to disk, so reruns on #101 will now skip unless a new commit arrives.

2. **Pending Codex commit (simulated #102)**
   1. Run `python -m automation.jleechanorg_pr_automation.jleechanorg_pr_monitor --target-pr 102 --target-repo worldarchitect.ai`.
   2. The monitor logs `⏳ Pending Codex automation commit … detected…` and exits with a non-zero status to signal that no comment was posted.
   3. Despite the skip, the processed state file is updated, demonstrating that the guard is idempotent.

3. **Historical Codex marker (simulated #103)**
   1. Run `python -m automation.jleechanorg_pr_automation.jleechanorg_pr_monitor --target-pr 103 --target-repo worldarchitect.ai`.
   2. The guard sees that the Codex marker references a different commit and proceeds to post a fresh instruction comment, mirroring the behaviour on a real PR where Codex previously ran on an older commit.

Each command echoes the behaviour captured in CI, making this document a self-contained audit trail of what was run, why it was run, and the expected outcomes.

## Notes
- The mock responses allow reproducible verification of the gating logic without relying on live GitHub data. Re-run the commands with the `mock_gh_cli.py` helper on the `PATH` (renamed to `gh`) to reproduce these results.
