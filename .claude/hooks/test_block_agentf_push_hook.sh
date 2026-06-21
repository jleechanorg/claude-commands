#!/usr/bin/env bash
# test_block_agentf_push_hook.sh — regression tests for
# block-agentf-push-to-jleechanorg.sh.
#
# Covers the two false-positive root causes fixed on 2026-06-20:
#   1. The bare "agentf" substring matched unrelated camelCase / hyphenated
#      identifiers (AgentFactory, TestGetAgentForInput, task-agentfoo,
#      agent-framework). Telltales now require a hyphen boundary.
#   2. The existing-branch range "<remote>/<branch>..HEAD" re-flagged content a
#      merge commit drags in from the remote's main. The range now uses
#      `--not --remotes`, which excludes anything already on the remote.
#
# Plus the still-required true positives (real Agnt-F telltales must block) and
# the self-exemption.
#
# The hook never touches the network: it reads remote.origin.url from git config
# and inspects local history. So `origin` points at a local bare repo, and we
# override its url to a jleechanorg URL to trip the org check.
set -uo pipefail

HOOK="$(cd "$(dirname "$0")" && pwd)/block-agentf-push-to-jleechanorg.sh"
JLEE_URL="https://github.com/jleechanorg/test.git"
PASS=0; FAIL=0
tmproot="$(mktemp -d)"
trap 'rm -rf "$tmproot"' EXIT

# run_hook <cwd> <command> -> echoes exit code
run_hook() {
  local cwd="$1" cmd="$2"
  printf '{"tool_input":{"command":%s},"cwd":%s}' \
    "$(printf '%s' "$cmd" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')" \
    "$(printf '%s' "$cwd" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')" \
    | bash "$HOOK" >/dev/null 2>&1
  echo $?
}

check() { # <desc> <expected_exit> <actual_exit>
  if [ "$2" = "$3" ]; then PASS=$((PASS+1)); echo "  PASS: $1"
  else FAIL=$((FAIL+1)); echo "  FAIL: $1 (expected exit $2, got $3)"; fi
}

# Build a repo with a jleechanorg origin and a feature branch that merges main.
setup_repo() {
  local d="$1"; shift
  local bare="$tmproot/bare-$RANDOM.git"
  git init -q --bare "$bare"
  git init -q "$d"
  git -C "$d" config user.email t@t.t; git -C "$d" config user.name t
  git -C "$d" remote add origin "$bare"
  echo "init" > "$d/README"
  git -C "$d" add -A && git -C "$d" commit -q -m "init"
  git -C "$d" push -q origin HEAD:main
  git -C "$d" branch -q -m main 2>/dev/null || true
}

echo "=== FP1: camelCase / hyphenated identifiers in a new commit must NOT block ==="
d="$tmproot/fp1"; setup_repo "$d"
git -C "$d" checkout -q -b feat/x
mkdir -p "$d/.beads"
printf '%s\n' 'class AgentFactory: pass' 'def TestGetAgentForInput(): pass' \
  'task-agentfoo' 'see the agent-framework docs' > "$d/.beads/issues.jsonl"
git -C "$d" add -A && git -C "$d" commit -q -m "benign camelcase content"
# Override to jleechanorg so the org gate fires and the telltale grep is exercised
# (the bare-repo url would otherwise skip the whole hook for the wrong reason).
git -C "$d" config remote.origin.url "$JLEE_URL"
check "camelCase content allowed" 0 "$(run_hook "$d" "git push origin feat/x")"

echo "=== FP2: content merged in from origin/main must NOT block (merge drag-in) ==="
d="$tmproot/fp2"; setup_repo "$d"
# Branch exists on remote first.
git -C "$d" checkout -q -b feat/y
echo "feature work" > "$d/work.txt"
git -C "$d" add -A && git -C "$d" commit -q -m "feature commit"
git -C "$d" push -q origin feat/y
# main advances with camelCase .beads content, then we merge main into the branch.
git -C "$d" checkout -q main
mkdir -p "$d/.beads"
printf '%s\n' 'AgentFactory TestGetAgentForInput task-agentfoo' > "$d/.beads/issues.jsonl"
git -C "$d" add -A && git -C "$d" commit -q -m "main: beads update"
git -C "$d" push -q origin main
git -C "$d" checkout -q feat/y
git -C "$d" merge -q --no-edit main
# All real pushes (to the bare repo) are done; now flip origin to jleechanorg.
# The naive range feat/y..HEAD now contains main's camelCase content via the merge;
# --not --remotes=origin must exclude it.
git -C "$d" config remote.origin.url "$JLEE_URL"
check "merge-from-main content allowed" 0 "$(run_hook "$d" "git push origin feat/y")"

echo "=== TP1: a real agent-f telltale in a NEW commit must still block ==="
d="$tmproot/tp1"; setup_repo "$d"
git -C "$d" checkout -q -b feat/z
echo "contact jeffrey@agent-f.com about the agf-api repo" > "$d/notes.txt"
git -C "$d" add -A && git -C "$d" commit -q -m "real agentf reference"
# Override origin url to jleechanorg so the org gate fires (bare repo path won't).
git -C "$d" config remote.origin.url "$JLEE_URL"
check "real telltale blocked" 2 "$(run_hook "$d" "git push origin feat/z")"

echo "=== TP2: Agnt-F org string in a new commit must still block ==="
d="$tmproot/tp2"; setup_repo "$d"
git -C "$d" checkout -q -b feat/w
echo "moved to github.com/Agnt-F/widget" > "$d/notes.txt"
git -C "$d" add -A && git -C "$d" commit -q -m "org reference"
git -C "$d" config remote.origin.url "$JLEE_URL"
check "Agnt-F org blocked" 2 "$(run_hook "$d" "git push origin feat/w")"

echo "=== NEG: non-jleechanorg remote is never inspected ==="
d="$tmproot/neg"; setup_repo "$d"
git -C "$d" checkout -q -b feat/n
echo "jeffrey@agent-f.com" > "$d/notes.txt"
git -C "$d" add -A && git -C "$d" commit -q -m "telltale but wrong org"
git -C "$d" config remote.origin.url "https://github.com/someoneelse/test.git"
check "non-jleechanorg allowed" 0 "$(run_hook "$d" "git push origin feat/n")"

echo
echo "RESULT: $PASS passed, $FAIL failed"
[ "$FAIL" = "0" ]
