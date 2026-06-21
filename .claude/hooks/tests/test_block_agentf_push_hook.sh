#!/usr/bin/env bash
# Test the block-agentf-push-to-jleechanorg.sh hook against synthetic inputs.
# Each test feeds a JSON stdin like PreToolUse gives us, asserts the exit code.
set -u

HOOK="$HOME/.claude/hooks/block-agentf-push-to-jleechanorg.sh"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# Set up a tiny throwaway git repo that looks like a jleechanorg remote.
TEST_REPO="$TMP/jlco-test"
mkdir -p "$TEST_REPO"
cd "$TEST_REPO"
git init -q -b main
git config user.email test@example.com
git config user.name "Test User"
git remote add origin "https://github.com/jleechanorg/test-repo.git"
# Set up a fake tracking ref so `origin/<branch>` resolves.
git commit --allow-empty -q -m "base"
git update-ref refs/remotes/origin/main HEAD
git update-ref refs/remotes/origin/clean-branch HEAD

# Now create feature branches.
make_branch() {
  local name="$1"
  git branch -f "$name" main
  git checkout -q "$name"
}

run_case() {
  local label="$1" expect="$2" input_json="$3" workdir="$4"
  local got
  printf '%s' "$input_json" | bash -c "cd '$workdir' && bash '$HOOK'" >/dev/null 2>/tmp/agentf_test_stderr
  got=$?
  if [ "$got" = "$expect" ]; then
    printf "  ✅ %-55s expect=%s got=%s\n" "$label" "$expect" "$got"
  else
    printf "  ❌ %-55s expect=%s got=%s\n" "$label" "$expect" "$got"
    echo "     stderr: $(head -3 /tmp/agentf_test_stderr | tr '\n' '|')"
  fi
}

echo "=== TESTS ==="

# 1. clean commit on a branch with origin tracking → push to jleechanorg → pass.
make_branch clean-branch
echo "hello" > clean.txt
git add clean.txt
git commit -q -m "Clean commit"
git update-ref refs/remotes/origin/clean-branch HEAD~1
run_case "1. clean push to jleechanorg" 0 \
  '{"cwd":"'$TEST_REPO'","tool_input":{"command":"git push origin clean-branch:clean-branch"}}' \
  "$TEST_REPO"

# 2. non-push command → fast bail.
run_case "2. non-push command" 0 \
  '{"cwd":"'$TEST_REPO'","tool_input":{"command":"git status"}}' \
  "$TEST_REPO"

# 3. push to Agnt-F (different org) → pass.
git remote add agntf "https://github.com/Agnt-F/test-repo.git"
git update-ref refs/remotes/agntf/main main
run_case "3. push to Agnt-F (not jleechanorg)" 0 \
  '{"cwd":"'$TEST_REPO'","tool_input":{"command":"git push agntf main:main"}}' \
  "$TEST_REPO"

# 4. commit msg mentions Agnt-F → block.
make_branch msg-branch
echo "x" > x.txt
git add x.txt
git commit -q -m "Touch Agnt-F integration"
git update-ref refs/remotes/origin/msg-branch HEAD~1
run_case "4. commit msg mentions Agnt-F" 2 \
  '{"cwd":"'$TEST_REPO'","tool_input":{"command":"git push origin msg-branch:msg-branch"}}' \
  "$TEST_REPO"

# 5. commit body references agent-f.com → block.
make_branch body-branch
echo "y" > y.txt
git add y.txt
git commit -q -m "fix" -m "contact: jeffrey@agent-f.com"
git update-ref refs/remotes/origin/body-branch HEAD~1
run_case "5. commit body has agent-f.com" 2 \
  '{"cwd":"'$TEST_REPO'","tool_input":{"command":"git push origin body-branch:body-branch"}}' \
  "$TEST_REPO"

# 6. author is $USER-af → block.
make_branch author-branch
echo "z" > z.txt
git add z.txt
git -c user.email=288516065+$USER-af@users.noreply.github.com -c user.name="$USER-af" commit -q -m "regular"
git update-ref refs/remotes/origin/author-branch HEAD~1
run_case "6. author is $USER-af" 2 \
  '{"cwd":"'$TEST_REPO'","tool_input":{"command":"git push origin author-branch:author-branch"}}' \
  "$TEST_REPO"

# 7. code diff has 'agf-' (e.g. importing an agf-api module) → block.
make_branch diff-branch
mkdir -p src
cat > src/main.ts <<'EOF'
import { Foo } from 'agf-api/dist/foo';
console.log(Foo);
EOF
git add src/main.ts
git commit -q -m "use agf-api client"
git update-ref refs/remotes/origin/diff-branch HEAD~1
run_case "7. code diff contains agf-" 2 \
  '{"cwd":"'$TEST_REPO'","tool_input":{"command":"git push origin diff-branch:diff-branch"}}' \
  "$TEST_REPO"

# 8. --dry-run → pass.
run_case "8. git push --dry-run" 0 \
  '{"cwd":"'$TEST_REPO'","tool_input":{"command":"git push --dry-run origin author-branch:author-branch"}}' \
  "$TEST_REPO"

# 9. empty stdin → pass.
got=$(printf '' | bash "$HOOK" >/dev/null 2>&1; echo $?)
[ "$got" = "0" ] && echo "  ✅ 9. empty stdin                          expect=0 got=$got" \
                || echo "  ❌ 9. empty stdin                          expect=0 got=$got"

# 10. brand-new branch (no upstream yet) with clean commit → pass (HEAD~1 exists
# because main is its base).
make_branch new-branch
echo "fresh" > f.txt
git add f.txt
git commit -q -m "First commit on new branch"
# Note: no update-ref — origin/new-branch doesn't exist. Hook falls back to
# HEAD~1..HEAD which still works.
run_case "10. new branch (no upstream) — clean" 0 \
  '{"cwd":"'$TEST_REPO'","tool_input":{"command":"git push -u origin new-branch"}}' \
  "$TEST_REPO"

# 11. brand-new branch with Agnt-F content → still block (range = HEAD~1..HEAD).
make_branch new-dirty-branch
echo "h" > h.txt
git add h.txt
git commit -q -m "Hook into Agnt-F monitor"
run_case "11. new branch (no upstream) — Agnt-F content" 2 \
  '{"cwd":"'$TEST_REPO'","tool_input":{"command":"git push -u origin new-dirty-branch"}}' \
  "$TEST_REPO"

# 12. real-world test: simulate a "force push with lease" to jleechanorg →
# the existing author-branch is dirty; confirm still blocks.
make_branch force-test
git -c user.email=288516065+$USER-af@users.noreply.github.com -c user.name="$USER-af" commit -q --allow-empty -m "oops"
run_case "12. git push --force-with-lease with agentf" 2 \
  '{"cwd":"'$TEST_REPO'","tool_input":{"command":"git push --force-with-lease origin force-test"}}' \
  "$TEST_REPO"
