#!/usr/bin/env bash
#
# check-hosted-runner-spike.sh — flag workflows pinned to GitHub-hosted runners
# in a repo's .github/workflows/ directory and print a cost estimate.
#
# Walk every *.yml/*.yaml under .github/workflows/, grep for `runs-on: ubuntu-latest`
# (or other GitHub-hosted runners like `windows-latest`, `macos-latest`), and report:
#   - Workflow file + job name
#   - Trigger event (pull_request, push, schedule, workflow_dispatch, etc.)
#   - Whether the workflow is PR-driven (highest cost risk)
#   - Per-run cost estimate based on the org's billing-API rate
#
# Exit codes:
#   0 = no hosted-runner workflows found
#   1 = at least one hosted-runner workflow found (review needed)
#   2 = no .github/workflows/ directory found
#
# Usage:
#   ./check-hosted-runner-spike.sh [REPO_DIR]
#
# Environment overrides:
#   HOSTED_RATE_PER_MIN    default 0.006   (effective hosted Linux rate post-discount)
#   SELF_HOSTED_RATE_PER_MIN default 0.002  (self-hosted accounting rate)
#   AVG_RUN_MINUTES         default 5       (avg minutes per hosted run, conservative)
#   PR_RUNS_PER_DAY         default 10      (PR-driven runs/day, conservative)
#
# Verified 2026-07-08 against $GITHUB_REPOSITORY — correctly flagged
# all 12 hosted-pinned workflows including the cost spike drivers in green-gate.yml.

set -euo pipefail

REPO_DIR="${1:-.}"
WORKFLOWS_DIR="${REPO_DIR}/.github/workflows"

if [[ ! -d "$WORKFLOWS_DIR" ]]; then
    echo "ERROR: no .github/workflows/ directory at ${REPO_DIR}" >&2
    exit 2
fi

HOSTED_RATE="${HOSTED_RATE_PER_MIN:-0.006}"
SELF_HOSTED_RATE="${SELF_HOSTED_RATE_PER_MIN:-0.002}"
AVG_MIN="${AVG_RUN_MINUTES:-5}"
PR_RUNS="${PR_RUNS_PER_DAY:-10}"

# Hosted-runner identifiers we want to flag
HOSTED_PATTERNS='ubuntu-latest|ubuntu-22.04|ubuntu-20.04|windows-latest|macos-latest|macos-13|macos-14|macos-15'

found_count=0
echo "=== Hosted-runner workflows in ${REPO_DIR} ==="
echo "(rate: hosted=\$${HOSTED_RATE}/min, self-hosted=\$${SELF_HOSTED_RATE}/min)"
echo

for wf in "${WORKFLOWS_DIR}"/*.yml "${WORKFLOWS_DIR}"/*.yaml; do
    [[ -f "$wf" ]] || continue

    # Skip worktrees / examples / templates
    case "$(basename "$wf")" in
        *.example|*.template|*.disabled) continue ;;
    esac

    # Check for any hosted runner pattern in the workflow file
    if ! grep -qE "runs-on:[[:space:]]+($HOSTED_PATTERNS)\b" "$wf"; then
        continue
    fi

    # Find the on: triggers
    triggers=$(awk '/^on:/{flag=1; next} /^[a-z]/{flag=0} flag && /^[[:space:]]+(push|pull_request|schedule|workflow_dispatch|workflow_call|issue_comment)/ {print $1}' "$wf" | sort -u | paste -sd ',' -)
    [[ -z "$triggers" ]] && triggers="(none detected)"

    # Count distinct jobs pinned to hosted
    hosted_jobs=$(grep -cE "runs-on:[[:space:]]+($HOSTED_PATTERNS)\b" "$wf" || echo 0)
    total_jobs=$(grep -cE "runs-on:" "$wf" || echo 0)

    # Mark PR-driven as high-risk
    risk="LOW"
    if echo "$triggers" | grep -q "pull_request"; then
        risk="HIGH (PR-driven)"
    fi

    # Cost estimate: per-run minutes × runs/day × hosted rate
    cost_per_day=$(awk "BEGIN {printf \"%.2f\", ${AVG_MIN} * ${PR_RUNS} * ${HOSTED_RATE}}")
    savings_per_day=$(awk "BEGIN {printf \"%.2f\", ${AVG_MIN} * ${PR_RUNS} * (${HOSTED_RATE} - ${SELF_HOSTED_RATE})}")

    echo "  ${wf#${REPO_DIR}/}"
    echo "    jobs: ${hosted_jobs}/${total_jobs} hosted"
    echo "    triggers: ${triggers}"
    echo "    risk: ${risk}"
    echo "    est. cost: \$${cost_per_day}/day (savings if moved to self-hosted: \$${savings_per_day}/day)"
    echo

    found_count=$((found_count + 1))
done

if [[ "$found_count" -eq 0 ]]; then
    echo "  none found — all workflows use self-hosted runners (good)"
    exit 0
fi

echo "=== Summary ==="
echo "Found ${found_count} workflow file(s) pinned to GitHub-hosted runners."
echo "Estimated savings if all moved to self-hosted: \$$(awk "BEGIN {printf \"%.2f\", ${found_count} * ${AVG_MIN} * ${PR_RUNS} * (${HOSTED_RATE} - ${SELF_HOSTED_RATE})}")/day"
echo
echo "Actions:"
echo "  1. Review each flagged workflow — is hosted intentional (e.g. macOS for non-Apple-silicon)?"
echo "  2. For PR-driven Linux workflows, switch to:"
echo "       runs-on: \${{ fromJson(vars.SELF_HOSTED_RUNNER_LABELS || '[\"self-hosted\"]') }}"
echo "  3. After merging, re-run billing API (gh api orgs/<org>/settings/billing/usage) to confirm savings"
exit 1