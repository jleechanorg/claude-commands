#!/usr/bin/env bash
# Git header generator script (ENHANCED VERSION WITH GIT STATUS)
# Usage: ./git-header.sh or git header (if aliased)
# Works from any directory within a git repository or worktree

# Source cross-platform timeout utilities
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
if [ -r "$SCRIPT_DIR/timeout-utils.sh" ]; then
    # shellcheck source=/dev/null
    source "$SCRIPT_DIR/timeout-utils.sh"
else
    gh_with_timeout() {
        local _timeout="$1"
        shift
        gh "$@"
    }
fi

# Find the git directory (works in worktrees and submodules)
git_dir=$(git rev-parse --git-dir 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "[Not in a git repository]"
    exit 0
fi

# Get the common git directory (for worktrees, refs are stored in the shared directory)
# In a normal repo, this equals git_dir. In a worktree, it points to the main repo's .git
git_common_dir=$(git rev-parse --git-common-dir 2>/dev/null || echo "$git_dir")

# Get the root of the working tree
git_root=$(git rev-parse --show-toplevel 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "[Unable to find git root]"
    exit 0
fi

# Find the git root and change to it
script_dir="$git_root"
cd "$git_root" || { echo "[Unable to change to git root]"; exit 0; }

# Get working directory for context
working_dir="$(basename "$git_root")"

local_branch=$(git branch --show-current)
remote=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || echo "no upstream")

# Get sync status and unpushed changes
local_status=""

# Check for uncommitted changes (always check, regardless of remote)
# Check both modified tracked files AND untracked files
# Handle fresh repos without HEAD gracefully
if git rev-parse --verify HEAD >/dev/null 2>&1; then
    # Normal repo with commits: check diff-index and untracked files
    if ! git diff-index --quiet HEAD -- 2>/dev/null || [ -n "$(git ls-files --others --exclude-standard 2>/dev/null)" ]; then
        uncommitted=" +uncommitted"
    else
        uncommitted=""
    fi
else
    # Fresh repo without commits: only check for any files
    if [ -n "$(git ls-files --others --exclude-standard 2>/dev/null)" ]; then
        uncommitted=" +uncommitted"
    else
        uncommitted=""
    fi
fi

if [ "$remote" != "no upstream" ]; then
    # Count commits ahead and behind
    ahead_count=$(git rev-list --count "$remote"..HEAD 2>/dev/null || echo "0")
    behind_count=$(git rev-list --count HEAD.."$remote" 2>/dev/null || echo "0")

    if [ "$ahead_count" -eq 0 ] && [ "$behind_count" -eq 0 ]; then
        local_status=" (synced$uncommitted)"
    elif [ "$ahead_count" -gt 0 ] && [ "$behind_count" -eq 0 ]; then
        local_status=" (ahead $ahead_count$uncommitted)"
    elif [ "$ahead_count" -eq 0 ] && [ "$behind_count" -gt 0 ]; then
        local_status=" (behind $behind_count$uncommitted)"
    else
        local_status=" (diverged +$ahead_count -$behind_count$uncommitted)"
    fi
else
    local_status=" (no remote$uncommitted)"
fi

# Smart PR detection with fast-first fallback strategy
# 1. Branch name patterns (instant)
# 2. Cached network lookup (fast)
# 3. Real-time network lookup with timeout (fallback)

# Fast detection from branch naming patterns
pr_text="none"
if [[ "$local_branch" =~ pr-([0-9]+) ]]; then
    pr_text="#${BASH_REMATCH[1]} (inferred)"
elif [[ "$local_branch" =~ /pr-([0-9]+) ]]; then
    pr_text="#${BASH_REMATCH[1]} (inferred)"
else
    # Enhanced PR cache with smart invalidation
    # - "none" results cached for CACHE_TTL_NONE seconds (PRs may be created soon after push)
    # - Real PR numbers cached for CACHE_TTL_PR seconds (stable)
    # - Bypass cache entirely if last push was < RECENT_PUSH_WINDOW seconds ago
    readonly CACHE_TTL_NONE=30      # 30 seconds for "none" results
    readonly CACHE_TTL_PR=300       # 5 minutes for PR numbers
    readonly RECENT_PUSH_WINDOW=60  # 60 seconds for recent push detection
    current_commit=$(git rev-parse HEAD 2>/dev/null)
    cache_file="/tmp/git-header-pr-${current_commit:0:8}"
    cache_valid=false

    # Helper function to get file mtime (POSIX-compatible)
    get_mtime() {
        local file="$1"
        if command -v perl >/dev/null 2>&1; then
            perl -e 'print((stat($ARGV[0]))[9])' "$file" 2>/dev/null || echo "0"
        else
            stat -f%m "$file" 2>/dev/null || stat -c%Y "$file" 2>/dev/null || echo "0"
        fi
    }

    current_time=$(date +%s)

    # Check if there was a recent push (within RECENT_PUSH_WINDOW seconds)
    # Detect by checking mtime of remote tracking ref (updated on push)
    recent_push=false
    if [ "$remote" != "no upstream" ]; then
        # Parse remote name and branch from upstream ref (e.g., "origin/main" or "upstream/feature")
        # Handle any remote name, not just "origin"
        remote_name="${remote%%/*}"
        remote_branch="${remote#*/}"
        ref_file="$git_common_dir/refs/remotes/$remote_name/$remote_branch"

        # Check unpacked ref file first
        if [ -f "$ref_file" ]; then
            remote_ref_mtime=$(get_mtime "$ref_file")
            if [ -n "$remote_ref_mtime" ]; then
                push_age=$((current_time - remote_ref_mtime))
                if [ "$push_age" -lt "$RECENT_PUSH_WINDOW" ]; then
                    recent_push=true
                fi
            fi
        fi

        # Fallback: check packed-refs if unpacked ref not found or mtime extraction failed
        # Modern git may pack refs into .git/packed-refs without updating individual file mtimes
        if [ "$recent_push" = false ]; then
            packed_refs_file="$git_common_dir/packed-refs"
            if [ -f "$packed_refs_file" ]; then
                packed_refs_mtime=$(get_mtime "$packed_refs_file")
                if [ -n "$packed_refs_mtime" ]; then
                    packed_push_age=$((current_time - packed_refs_mtime))
                    if [ "$packed_push_age" -lt "$RECENT_PUSH_WINDOW" ]; then
                        recent_push=true
                    fi
                fi
            fi
        fi
    fi

    # Check if cache exists and is valid
    # Skip cache check entirely if recent push detected (user likely just created PR)
    if [ -f "$cache_file" ] && [ -n "$current_commit" ] && [ "$recent_push" = false ]; then
        cache_mtime=$(get_mtime "$cache_file")
        cache_age=$((current_time - cache_mtime))
        cached_value=$(cat "$cache_file" 2>/dev/null || echo "none")

        # Different TTL based on cached value:
        # - "none" = CACHE_TTL_NONE seconds (PRs may be created soon)
        # - Real PR numbers = CACHE_TTL_PR seconds (stable, unlikely to change)
        if [ "$cached_value" = "none" ]; then
            max_cache_age="$CACHE_TTL_NONE"
        else
            max_cache_age="$CACHE_TTL_PR"
        fi

        if [ "$cache_age" -lt "$max_cache_age" ]; then
            cache_valid=true
            pr_text="$cached_value"
        fi
    fi

    # If no valid cache, perform network lookup with timeout
    if [ "$cache_valid" = false ] && [ -n "$current_commit" ]; then
        pr_text="none"
        if command -v gh >/dev/null 2>&1; then
            pr_info=""

            # First try to look up by branch name (works for local branches tied to PRs)
            if [ -n "$local_branch" ]; then
                pr_info=$(gh_with_timeout 5 pr view --json number,url --template '{{.number}} {{.url}}' "$local_branch" 2>/dev/null)
            fi

            # If branch lookup failed, fall back to searching by commit SHA (covers detached HEADs, renamed branches, etc.)
            if [ -z "$pr_info" ] && [ -n "$current_commit" ]; then
                pr_info=$(gh_with_timeout 5 pr list --state all --json number,url --search "sha:$current_commit" --limit 1 --template '{{- range $i, $pr := . -}}{{- if eq $i 0 -}}{{printf "%v %v" $pr.number $pr.url}}{{- end -}}{{- end -}}' 2>/dev/null)
            fi

            if [ -n "$pr_info" ]; then
                # Split the PR info into number and URL (preserve $1)
                pr_number="${pr_info%% *}"
                pr_url="${pr_info#* }"
                # Handle case where there's no URL (only number)
                if [ "$pr_number" = "$pr_url" ]; then
                    pr_url=""
                fi
                if [ -n "$pr_number" ]; then
                    if [ -n "$pr_url" ]; then
                        pr_text="#$pr_number $pr_url"
                    else
                        pr_text="#$pr_number"
                    fi
                fi
            fi
        fi

        # Cache the result (even if none to avoid repeated lookups)
        echo "$pr_text" > "$cache_file" 2>/dev/null
    fi
fi





# Skip git status output for statusline mode
if [ "$1" != "--status-only" ]; then
    echo "=== Git Status ==="
    git status
    echo
fi



# Simple output - just the essential info
echo -e "\033[1;36m[Dir: $working_dir | Local: $local_branch$local_status | Remote: $remote | PR: $pr_text]\033[0m"
