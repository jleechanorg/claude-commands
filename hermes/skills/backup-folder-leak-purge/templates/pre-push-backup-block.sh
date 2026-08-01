#!/usr/bin/env bash
# pre-push backup-block.sh — INSTALL AT <repo>/.git/hooks/pre-push (chmod 755)
# Refuses any push to refs/heads/main whose commit tree contains forbidden paths
# (default: ^backup/, ^snapshot/, ^home-config/, ^private/, ^secrets/).
#
# Stdin format per git/githooks.adoc:
#   <local-ref> SP <local-sha> SP <remote-ref> SP <remote-sha> LF
#
# Bug-ref 2026-07-15: jleechanorg/claude-commands leaked 491 MiB of home-dir
# snapshots because the existing gitleaks pre-push hook only checked secret
# patterns, not path prefixes. This hook is the path-prefix check; install it
# ALONGSIDE the secret scan, not as a replacement.
#
# Verification: see scripts/verify-hook-blocks-backup-push.sh in this skill.

set -euo pipefail

REMOTE="${1:-}"
URL="${2:-}"

# Forbidden path prefixes (regex; matched against `git ls-tree -r` output).
# Override with FORBIDDEN_PATTERNS="^a/|^b/" ./pre-push ...
FORBIDDEN_PATTERNS="${FORBIDDEN_PATTERNS:-^backup/|^snapshot/|^home-config/|^private/|^secrets/}"

# Only enforce on protected branches. Override with PROTECTED_BRANCHES="refs/heads/main refs/heads/release".
PROTECTED_BRANCHES="${PROTECTED_BRANCHES:-refs/heads/main}"

main_sha=""
while read -r local_ref local_sha remote_ref remote_sha; do
    [[ -z "$local_ref" ]] && continue

    # Skip delete operations (local_sha is all-zeroes)
    [[ "$local_sha" == "0000000000000000000000000000000000000000" ]] && continue

    # Skip if local sha already matches remote sha (nothing to push)
    [[ "$local_sha" == "$remote_sha" ]] && continue

    # Is this a protected branch?
    is_protected=0
    for ref in $PROTECTED_BRANCHES; do
        if [[ "$local_ref" == "$ref" ]]; then
            is_protected=1
            break
        fi
    done
    [[ "$is_protected" -eq 0 ]] && continue

    # Check the local sha's tree for forbidden paths
    bad=$(git ls-tree -r --name-only "$local_sha" 2>/dev/null \
        | grep -E "$FORBIDDEN_PATTERNS" || true)

    if [[ -n "$bad" ]]; then
        echo "" >&2
        echo "🛑 PRE-PUSH BLOCKED: forbidden path detected in outgoing $local_ref commits" >&2
        echo "   remote: $REMOTE ($URL)" >&2
        echo "   branch: $local_ref" >&2
        echo "   local sha: $local_sha" >&2
        echo "   forbidden patterns: $FORBIDDEN_PATTERNS" >&2
        echo "   sample of offending files:" >&2
        echo "$bad" | head -10 | sed 's/^/     /' >&2
        echo "" >&2
        echo "   These paths contain personal home-directory snapshots, secrets, or other" >&2
        echo "   content that must NEVER reach the public repo." >&2
        echo "" >&2
        echo "   To fix:" >&2
        echo "     1. git rm -r --cached <forbidden-path>/  && git commit" >&2
        echo "     2. Verify .gitignore contains the forbidden path" >&2
        echo "     3. Push with --no-verify ONLY for intentional one-off scrubs" >&2
        echo "" >&2
        exit 1
    fi
done

exit 0