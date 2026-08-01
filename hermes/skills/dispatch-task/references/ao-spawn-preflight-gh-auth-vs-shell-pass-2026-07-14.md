# `ao spawn` preflight `gh auth status` fails when shell auth works

**Symptom (verified 2026-07-14 on AO Node CLI at `$HOME/bin/ao`):**
`ao spawn -p worldarchitect --claim-pr 8389 "..."` exits with:
```
✗ GitHub CLI is not authenticated. Run: gh auth login
```
…even though `gh auth status` succeeds in the SAME shell with the same `PATH`, same `HOME`, same `~/.config/gh/hosts.yml`. Reproduction: `node -e "const {preflight} = require('$HOME/project_agento/agent-orchestrator/packages/cli/dist/lib/preflight.js'); preflight.checkGhAuth()"` returns PASS in isolation; the real CLI fails. The Node CLI's `shell.js` uses `execFile` (not shell `exec`), and the child-process env propagation of the resolved `gh` binary is the variable — even with identical PATH.

**Workaround (when this fires):**
Stop debugging the preflight. Drive the work inline using an existing worktree:
```bash
WT=$HOME/.worktrees/worldarchitect/wa-NNNN   # any existing worktree for the PR
cd "$WT" && git fetch origin <branch>
# do the work (cherry-pick / compact / amend) directly on the branch
git add -A && git commit -m "fix: ..."
git pull --rebase origin <branch> 2>&1 || git fetch && git rebase origin/<branch>
git push origin <branch>
gh workflow run <id> --ref <branch>   # or curl POST /actions/workflows/{id}/dispatches
```
This bypasses the spawn layer entirely. The `dispatch-task` skill's `dispatch_on_install` and `pr-green-dispatch` COMMITs still apply — but if the spawn path itself is blocked, inline is the safe subset.

**Why this happens (root-cause class):**
The Node CLI spawns a child process for `gh` preflight. That child's environment reads from the parent's `process.env`, but macOS `launchd`-managed daemons (and some shell wrappers) compose env differently than interactive shells. The `gh` binary resolves to `$HOME/.local/bin/gh` (a bash wrapper that delegates to the real `gh`), and the wrapper's internal `command -v gh` re-resolution in the child context can land on a different binary than the parent shell sees. Both `$HOME/.local/bin/gh` (wrapper script) and `/opt/homebrew/bin/gh` (real binary) pass `auth status` independently, but the CLI's preflight somehow binds to one that doesn't. The two-hour debug loop is: re-source `~/.bashrc`, re-set `GH_TOKEN`, restart daemon, none of which fix it — because the bug is in the CLI's child-process composition, not auth state.

**Don't burn time on:**
- `unset GITHUB_TOKEN; env -i PATH=... gh auth status` (works, doesn't fix spawn)
- `launchctl setenv GITHUB_TOKEN ...` (works for daemon children, doesn't fix spawn's preflight)
- Editing the LaunchAgent plist's `EnvironmentVariables` block (same — propagates to daemon, not to the preflight child of the CLI itself)
- Adding `GITHUB_TOKEN` to `launchd-env-wrapper.sh` `_extract_bashrc_var` list (improves OTHER problems, not this one)

**Bead / provenance:**
- Session 2026-07-14 22:00 PT, dispatch-task → drive #8389 to green
- 6+ tool calls debugging before pivoting to inline drive
- Inline drive succeeded: pushed commit `0f95a61242`, re-triggered CI runs `29372342985` and `29372332368`

**Related v1.5.0 dispatch-task recipe additions worth pairing:**
- `AO_MAX_CONCURRENT_SESSIONS=50` env override for the 20-cap zombie pool
- `ao session restore <id>` to rebind an existing worktree without recreating it
- Branch-reset + cherry-pick + `ao send --file` steer pattern (still applies when spawn DOES succeed)

**Decision rule (updated for v1.6.0):**
If `ao spawn` fails with `gh auth` AND you've confirmed `gh auth status` works in your shell, abandon spawn and drive inline. The cost of one more debug attempt (~5-10 tool calls) exceeds the cost of just doing the work directly (~3-5 tool calls).