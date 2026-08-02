# Reference: `your-project.com` `.claude/worktrees/` leak (2026-07-14)

Session-specific case study. Captures the actual numbers from a live di[REDACTED_OPENAI_KEY] triage so future agents have a concrete baseline.

## Symptom
Slack alert at 2026-07-14T22:14:36Z: `disk-alert jeffreys-macbook-pro disk usage 879G (threshold 787G)`. Posted via `disk_usage_alert.sh` wrapper.

## Live state at triage start
```
df -h /System/Volumes/Data → 850G used / 926G total / 36G free / 96% capacity
df -h /                   → 17G used /  926G total / 45G free / 27% capacity (sealed system volume — misleading)
```

Note the **33-point gap** between the two `df` outputs. This is the sealed-system-volume trap; never trust `df /` alone on Apple Silicon.

## Top offenders (full `du` walk, ~5 min)
| Path | Size | Notes |
|---|---|---|
| `~/projects/your-project.com/.claude/worktrees/` | **46G** | 128 git-registered agent scratch dirs |
| `~/projects/` total | 142G | 338 subdirs; `.claude/worktrees/` dominates |
| `~/Pictures/Photos Library.photoslibrary` | 13G | User data — do NOT auto-touch |
| `~/Library/Developer/CoreSimulator/Caches/Devices/` | 7.3G | iOS simulator images |
| `~/Downloads/` | 5.7G | Includes 5× duplicate `AIE-Worlds-Fair-v4..v9.mp4` (~700MB) |
| `~/Library/Application Support/Aside/` | 2.6G | Browser cache (2 profiles) |
| `~/Library/Caches/Aside/` | 1.8G | Browser cache |
| `~/Library/Caches/claude-cli-nodejs` | 524M | Claude Code node cache |
| `~/Library/Application Support/CodexBar` | 214M | (cache) |

Per-worktree size distribution: most 300–400MB, the largest 1GB. Each worktree is a full repo checkout plus accumulated `docs/` (107M) and `evidence/` (105M) per worktree.

## Why the worktrees leaked

`git worktree list` from inside `~/projects/your-project.com` returned **394 entries**. Of those, 128 live in `.claude/worktrees/agent-*`. They were created by `delegate_task` subagents and never pruned after the subagent finished. The git worktree registration persisted, so subsequent sessions kept them alive in `git worktree list` even though no live process owned them.

Distribution by mtime at triage time:
- Modified in last 7 days: **52** (active/recent — DO NOT delete)
- Modified in last 8–30 days: **61** (probably safe to delete)
- Older than 30 days: **16** (definitely stale)
- Older than 90 days: **0**

## Open-PR cross-reference (REQUIRED before bulk delete)

Run before deleting:
```bash
cd ~/projects/your-project.com
gh pr list --state open --limit 200 --json headRefName,headRefOid \
  | jq -r '.[] | "\(.headRefName)\t\(.headRefOid)"' > /tmp/open_prs.tsv

# For each worktree, check if its branch matches an open PR headRefName
git worktree list | while read -r path sha branch; do
  if grep -q "$branch" /tmp/open_prs.tsv; then
    echo "KEEP $path (branch=$branch is open PR)"
  fi
done
```

At triage time this check returned ~10 worktrees tied to open PRs (e.g., `feat/cost-mock-previews-default`, `pr-7980`, `worktree-agent-a0a162c811f52d6ea`) — those MUST be preserved.

## Disk-alert script reference

- Script: `~/Library/Application Support/user-scope/bin/disk_usage_alert.sh`
- Threshold default: 90% of capacity in GB (`_cap_gb=$(df -kP "$CHECK_PATH" | awk 'NR==2{printf "%d", $2*0.9/1048576}')`)
- Silence flag: `--silence` writes `$HOME/.di[REDACTED_OPENAI_KEY]`
- Threshold override env: `DISK_ALERT_THRESHOLD_GB`
- Channel routing: depends on wrapper; on this machine posts to `#ai-general` (C0AJQ5M0A0Y)

## Open follow-ups (bead candidates)

1. **Hardcode `git worktree prune` on delegate_task exit** — `delegate_task` should call `git worktree remove` automatically when the subagent finishes. Currently they leak. Tracked as a Hermes harness improvement.
2. **Move `.claude/worktrees/` to a tmpfs/ramdisk** if possible — they're scratch state, no need to persist across reboots.
3. **Add a worktree-count watchdog** — alert when `<repo>/.claude/worktrees/` exceeds N=50 entries.