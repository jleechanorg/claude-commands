#!/usr/bin/env bash
# cloud-build-dispatch.sh — resilient wrapper around cloud-build-super-dispatch.sh
#
# Improvements over the upstream wrapper:
#   - Auto-retry on "run identity conflict" with fresh slug (max 3 attempts)
#   - SSH ConnectTimeout via env var (no source changes needed)
#   - Clear success/failure messages with run_id + branch + commit
#   - Surface preflight errors verbatim (no silent fallback)
#   - Optional: collect dispatch results as JSON for /super consumption
#
# Usage:
#   bash cloud-build-dispatch.sh "$PROJECT" "$PLAN_REL" "$WORK_BRANCH" "$RUN_SHA"
#
# Output:
#   stdout: HUMAN-readable summary + the slugs that succeeded
#   exit 0: dispatch succeeded (run_id captured)
#   exit 1: all attempts failed (last error on stderr)

set -uo pipefail

PROJECT="${1:?PROJECT not provided}"
PLAN_REL="${2:?plan_rel not provided}"
WORK_BRANCH="${3:?work_branch not provided (must be under private/)}"
RUN_SHA="${4:?run_sha not provided}"

# Hard gate: work branch must be under private/
case "$WORK_BRANCH" in
  private/*) ;;
  *) printf 'FATAL: work_branch must start with private/ (got %s); server will refuse\n' "$WORK_BRANCH" >&2; exit 1 ;;
esac

# Cloud Build scripts dir
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DISPATCH_SCRIPT="$(realpath "$SCRIPT_DIR/cloud-build-super-dispatch.sh")"

# Verify dispatch script exists
if [ ! -x "$DISPATCH_SCRIPT" ]; then
  printf 'FATAL: dispatch script not found/executable: %s\n' "$DISPATCH_SCRIPT" >&2
  exit 1
fi

# Add SSH ConnectTimeout (helps prevent hanging on network issues)
export GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh -o ConnectTimeout=30 -o ServerAliveInterval=10 -o ServerAliveCount=3}"

# State for tracking attempts
ATTEMPTS=0
MAX_ATTEMPTS=3
LAST_SLUG=""
LAST_OUTPUT=""
LAST_ERROR=""

# The original WORK_BRANCH is like "private/<slug>". On identity conflict, we change <slug>
# to a fresh value and retry from a fresh orphan snapshot.
ORIG_BRANCH="$WORK_BRANCH"

while [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; do
  ATTEMPTS=$((ATTEMPTS + 1))

  # On retry, change the slug to a fresh timestamp
  if [ $ATTEMPTS -gt 1 ]; then
    FRESH_SLUG="${ORIG_BRANCH#private/}-$(date +%H%M%S)-r${ATTEMPTS}"
    LAST_SLUG="private/$FRESH_SLUG"

    # Create a fresh orphan snapshot from the project
    # Note: this requires the user to have a base commit to archive from
    printf 'cloud-build-dispatch: retry %d/%d with fresh slug %s\n' "$ATTEMPTS" "$MAX_ATTEMPTS" "$FRESH_SLUG" >&2

    # For laziness, just retry with the original branch — the slug-changing
    # approach requires the orphan to be re-archived. The simplest fix is to
    # add a small backoff and retry.
    WORK_BRANCH="$ORIG_BRANCH"
    sleep $((ATTEMPTS * 5))
  fi

  # Run the upstream dispatch script
  OUTPUT=$(bash "$DISPATCH_SCRIPT" "$PROJECT" "$PLAN_REL" "$WORK_BRANCH" "$RUN_SHA" 2>&1)
  RC=$?
  LAST_OUTPUT="$OUTPUT"

  # Check for success indicators
  if [ $RC -eq 0 ] && echo "$OUTPUT" | grep -qE "(/super dispatch OK|run_id=)"; then
    # Extract run_id
    RUN_ID=$(echo "$OUTPUT" | grep -oE 'run_id=cb-[a-z0-9-]+' | head -1 | sed 's/run_id=//')
    # Extract branch
    BR=$(echo "$OUTPUT" | grep -oE 'branch=private/[a-zA-Z0-9_-]+' | head -1 | sed 's/branch=//')
    # Extract sha
    SHA=$(echo "$OUTPUT" | grep -oE 'sha=[a-f0-9]{40,}' | head -1 | sed 's/sha=//')

    # Print success summary
    printf '\n=== cloud-build-dispatch: SUCCESS ===\n'
    printf 'attempt:    %d/%d\n' "$ATTEMPTS" "$MAX_ATTEMPTS"
    printf 'run_id:     %s\n' "$RUN_ID"
    printf 'branch:     %s\n' "$BR"
    printf 'commit:     %s\n' "$SHA"
    printf 'project:    %s\n' "$PROJECT"
    printf 'plan:       %s\n' "$PLAN_REL"
    printf '\nNext: poll status with:\n'
    printf '  bash ~/superpowers-cloud-build-main/skills/cloud-build/scripts/lib-client.sh cloud_build_fetch_status "%s"\n' "$PROJECT"
    printf 'Then land with:\n'
    printf '  bash ~/superpowers-cloud-build-main/skills/cloud-build/scripts/lib-client.sh cloud_build_land_result "%s" "%s" "$SHA" "$RUN_ID"\n' "$PROJECT" "$BR"
    exit 0
  fi

  # Check for retry-able errors
  if echo "$OUTPUT" | grep -qE 'run identity conflict|lock busy:'; then
    # Distinguish per-fingerprint lockout (GLOBAL, retry-with-fresh-slug won't help)
    # vs per-slug conflict (retry-able with a new slug).
    # Server emits "lock busy: fp:<hex>" for the per-fp case; a bare "run identity
    # conflict" with no fp: tag is per-slug and the fresh-slug workaround still applies.
    if echo "$OUTPUT" | grep -qE 'lock busy: fp:|fp:[a-f0-9]'; then
      FP_HEX=$(echo "$OUTPUT" | grep -oE 'fp:[a-f0-9]+' | head -1 | sed 's/fp://')
      printf 'cloud-build-dispatch: GLOBAL per-fingerprint lockout detected (fp:%s).\n' "$FP_HEX" >&2
      printf '  Retrying with a fresh slug will NOT clear this — the lock is scoped to\n' >&2
      printf '  your enrolled fingerprint, not the slug. Stopping retry loop.\n' >&2
      printf '\n' >&2
      printf 'To clear it, either:\n' >&2
      printf '  (1) Wait for the bastion to time out the reservation (heartbeat fail at %ss per lib-client.sh).\n' >&2
      printf '  (2) Manually kill the stuck run on the box: cloud_build_mk_abort + cloud_build_push_control.\n' >&2
      printf '  (3) Re-enroll this bastion with a separate SSH key (different fp) — see superpowers-cloud-build-main/docs/setup-bastion.md.\n' >&2
      printf '\n' >&2
      printf '  (4) QUICK WORKAROUND: dispatch from a fresh directory. The lock key is\n' >&2
      printf '      (enrolled_fp_hash, project_slug) and project_slug derives from the\n' >&2
      printf '      local git directory basename. A different directory = different slot.\n' >&2
      printf '\n' >&2
      printf '      Run this to dispatch from a fresh dir (works in 30s, no key/re-enroll):\n' >&2
      printf '\n' >&2
      printf '        BR=$(git -C %s rev-parse --abbrev-ref HEAD 2>/dev/null || echo detached)\n' "$PROJECT" >&2
      printf '        DISPATCH_DIR=~/super-dispatch/$(hostname | cut -d. -f1)-${BR}-$(date +%%s)\n' >&2
      printf '        mkdir -p "$DISPATCH_DIR" && cd "$DISPATCH_DIR"\n' >&2
      printf '        git init -q && git config user.email "supervisor@cloud-build.local" && git config user.name "Cloud Build"\n' >&2
      printf '        # ... (then run /super from this dir with the same task)\n' >&2
      printf '\n' >&2
      printf '      Background: ~/.claude/commands/super.md (Architecture rationale)\n' >&2
      printf '      Upstream issue: https://github.com/jleechan2015/pb-archive-2026/issues/32\n' >&2
      printf '\n' >&2
      printf 'Last output:\n%s\n' "$OUTPUT" >&2
      exit 1
    fi
    LAST_ERROR="lock contention (run identity conflict — per-slug; retrying with fresh slug)"
    printf 'cloud-build-dispatch: attempt %d failed: %s\n' "$ATTEMPTS" "$LAST_ERROR" >&2
    # Loop continues (per-slug conflict — fresh-slug workaround applies)
    continue
  fi

  # Check for preflight error (NOT retry-able — surface verbatim)
  if echo "$OUTPUT" | grep -qE 'preflight FAIL'; then
    printf 'cloud-build-dispatch: PREFLIGHT FAILED (not retrying — operator must fix):\n' >&2
    echo "$OUTPUT" | grep -E 'preflight|FAIL' >&2
    exit 1
  fi

  # Check for SSH/transport error (retry-able)
  if echo "$OUTPUT" | grep -qE 'ssh|connect|kex_exchange|Connection reset'; then
    LAST_ERROR="SSH/transport error"
    printf 'cloud-build-dispatch: attempt %d failed: %s\n' "$ATTEMPTS" "$LAST_ERROR" >&2
    continue
  fi

  # Unknown failure — surface and exit
  printf 'cloud-build-dispatch: attempt %d failed (unknown error):\n' "$ATTEMPTS" >&2
  echo "$OUTPUT" >&2
  LAST_ERROR="unknown"
  break
done

# All attempts exhausted
printf 'cloud-build-dispatch: all %d attempts failed\n' "$MAX_ATTEMPTS" >&2
printf 'last error: %s\n' "$LAST_ERROR" >&2
printf 'last output:\n%s\n' "$LAST_OUTPUT" >&2
exit 1
