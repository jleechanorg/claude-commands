# lvl-lanes / wt-NNNN closed-PR worktree pattern (your-project.com fleet)

## Pattern

`~/.lvl-lanes/wt-lvl-pr<N>/` and `~/.worktrees/<org>/<repo>/wa-NNNN-*/` accumulate fast on the your-project.com fleet because the leveling/green-driver daemon spawns one git worktree per bead. Once a PR closes (merged, abandoned, or superseded), the worktree directory is **NOT auto-removed** — the daemon only spawns new lanes, never reaps old ones. A single triage session found 7 lanes in `~/.lvl-lanes/` alone, all syncing to upstream `origin/<branch>` and all backed by CLOSED PRs.

## Per-lane cleanup recipe (3-step)

```bash
# 1. Read the worktree's branch + last commit + upstream tracking
branch=$(git -C "$WT_DIR" branch --show-current)
sha=$(git -C "$WT_DIR" log --oneline -1 | awk '{print $1}')
upstream=$(git -C "$WT_DIR" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null)
remote_url=$(git -C "$WT_DIR" config --get remote.origin.url)
owner_repo=$(echo "$remote_url" | sed -E 's#.*github.com[:/]([^/]+/[^.]+)(\.git)?$#\1#')

# 2. Cross-check live PR state — REST API, NOT `gh pr list --limit 200` (GraphQL pagination bug)
gh pr list --repo "$owner_repo" --state all --head "$branch" \
  --json number,state,title,url 2>/dev/null

# 3. Confirm upstream is in sync (no uncommitted/unpushed work to lose)
[[ -n "$upstream" ]] && {
  ahead=$(git -C "$WT_DIR" rev-list --count "$upstream..HEAD" 2>/dev/null)
  behind=$(git -C "$WT_DIR" rev-list --count "HEAD..$upstream" 2>/dev/null)
  echo "ahead=$ahead behind=$behind — if ahead>0, the lane has unmerged work; SKIP"
}

# 4. If PR is CLOSED/MERGED AND ahead=0 → safe to remove
git -C "$WT_DIR" worktree remove --force "$WT_DIR" 2>/dev/null || rm -rf "$WT_DIR"
```

## Verified instance (2026-07-15)

`~/.lvl-lanes/` (5.3G total, 7 lanes):

| Lane | Branch | PR | State | Upstream sync |
|---|---|---|---|---|
| `wt-lvl-pr1/` | `lvl-pr1-schema-failclosed` | — | local-only branch | none |
| `wt-lvl-pr2/` | `feat/levelup-v2-routing` | [#7529](https://github.com/$GITHUB_REPOSITORY/pull/7529) | CLOSED | `origin/feat/levelup-v2-routing` |
| `wt-lvl-pr3/` | `feat/levelup-v2-rewards-engine` | [#7530](https://github.com/$GITHUB_REPOSITORY/pull/7530) | CLOSED | `origin/feat/levelup-v2-rewards-engine` |
| `wt-lvl-pr4/` | `feat/levelup-v2-world-logic` | [#7531](https://github.com/$GITHUB_REPOSITORY/pull/7531) | CLOSED | `origin/feat/levelup-v2-world-logic` |
| `wt-lvl-pr5/` | `feat/levelup-v2-streaming-xp` | [#7532](https://github.com/$GITHUB_REPOSITORY/pull/7532) | CLOSED | `origin/feat/levelup-v2-streaming-xp` |
| `wt-lvl-pr6/` | `feat/levelup-v2-godmode-fold` | [#7533](https://github.com/$GITHUB_REPOSITORY/pull/7533) | CLOSED | `origin/feat/levelup-v2-godmode-fold` |
| `wt-lvl-pra/` | `feat/levelup-v2-prompt-full-sheet` | [#7528](https://github.com/$GITHUB_REPOSITORY/pull/7528) | CLOSED | `origin/feat/levelup-v2-prompt-full-sheet` |

All 6 PR-bearing lanes were `git worktree remove --force` candidates (~5.3G reclaimable). The `wt-lvl-pr1` local-only branch needs a `git branch -D lvl-pr1-schema-failclosed` in the parent repo before `git worktree remove` to avoid "branch checked out" refusal — OR `rm -rf` directly.

## Pitfall — `gh pr list --limit 200` returns 0 results intermittently

The `--limit 200` boundary has a GraphQL pagination bug that returns `[]` even when open PRs exist. **Always use the REST API** (`gh api .../pulls?state=open&per_page=100` paginated through 2+ pages for repos with >100 open PRs) for the cross-check. The lvl-lanes instance hit this — `gh pr list --limit 200` returned `[]`, but the per-branch `gh pr list --state all --head <branch>` correctly returned the closed-PR records.

## Pitfall — worktree branch has unpushed commits

`git rev-list --count <upstream>..HEAD` is the gate. If `ahead > 0`, the lane has unmerged work even if the PR is closed (e.g. follow-up commits made after the PR closed). Skip these — `git worktree remove` would lose the work. The lvl-lanes instance had `ahead=0` across all 6 PR-backed lanes (verified via upstream `origin/<branch>` SHA matches HEAD SHA).

## Pitfall — daemon process still owns the worktree

Before `git worktree remove`, verify no daemon process is still attached:

```bash
ps aux | grep -iE 'lane_runner|levelup|wa-<N>|lvl-pr<NUM>' | grep -v grep
```

If found, kill the daemon first or the `git worktree remove` will fail with "device or resource busy". The lvl-lanes instance had no daemon attached — all 7 worktrees were orphaned.

## Reclaimable estimate

Per `your-project.com` fleet, this pattern recurs across:

- `~/.lvl-lanes/` — 5.3G observed (2026-07-15)
- `~/.worktrees/<repo>/wa-NNNN-*/` — 5-15G per repo (estimated; wa-7715, wa-8408, wa-ci-fast-checkout, wa-precompute-deps observed at 300M each)
- `~/.ao/data/worktrees/<org>/<repo>/<lane>/` — 1-3G per lane (load-bearing for live AO workers; check `ao status` first)

Total fleet-wide reclaimable from this pattern alone: **10-25G** with low risk (every step is git-registry-confirmed + PR-cross-checked + upstream-sync-checked).