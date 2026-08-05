#!/usr/bin/env bash

set -euo pipefail

SCRIPT_PATH="$HOME/.claude/scripts/tree-worktree.sh"
RUN_TREE_OUTPUT=""

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

assert_eq() {
  local actual="$1"
  local expected="$2"
  local label="$3"
  if [[ "$actual" != "$expected" ]]; then
    fail "$label: expected '$expected', got '$actual'"
  fi
}

assert_ne() {
  local actual="$1"
  local expected="$2"
  local label="$3"
  if [[ "$actual" == "$expected" ]]; then
    fail "$label: expected different value"
  fi
}

assert_not_exists() {
  local path="$1"
  local label="$2"
  if [[ -e "$path" ]]; then
    fail "$label: path exists unexpectedly '$path'"
  fi
}

assert_file_exists() {
  local path="$1"
  local label="$2"
  if [[ ! -f "$path" ]]; then
    fail "$label: expected file '$path'"
  fi
}

run_tree() {
  local cwd="$1"
  local name="$2"
  set +e
  RUN_TREE_OUTPUT="$(bash -lc "cd '$cwd'; source '$SCRIPT_PATH' '$name'; script_status=\$?; printf '__PWD__=%s\\n' \"\$PWD\"; exit \"\$script_status\"")"
  local status=$?
  set -e
  RUN_TREE_STATUS="$status"
  return "$RUN_TREE_STATUS"
}

run_tree_pwd() {
  local cwd="$1"
  local name="$2"
  if ! run_tree "$cwd" "$name"; then
    fail "tree-worktree call failed: $RUN_TREE_OUTPUT"
  fi
  printf '%s\n' "$RUN_TREE_OUTPUT" | awk -F= '/^__PWD__=/{print $2}' | tail -n 1
}

if [[ ! -f "$SCRIPT_PATH" ]]; then
  echo "Expected red-phase failure: script missing at $SCRIPT_PATH"
  exit 1
fi

TMP_ROOT="$(mktemp -d)"
TMP_ROOT_REAL="$(cd "$TMP_ROOT" && pwd -P)"
PRIMARY_BARE="$TMP_ROOT/origin.git"
PRIMARY="$TMP_ROOT/main"
ADVANCER="$TMP_ROOT/advancer"
MAIN_PARENT="$TMP_ROOT"
MAIN_PARENT_REAL="$(cd "$MAIN_PARENT" && pwd -P)"
case "$MAIN_PARENT_REAL" in
  "$TMP_ROOT_REAL"|"$TMP_ROOT_REAL"/*) ;;
  *) fail "temporary parent escaped TMP_ROOT: $MAIN_PARENT_REAL" ;;
esac

# Seed primary remote + main repo.
git init --bare "$PRIMARY_BARE" >/dev/null
git clone "$PRIMARY_BARE" "$PRIMARY" >/dev/null
git -C "$PRIMARY" config user.name "tree-worktree-tester"
git -C "$PRIMARY" config user.email "jleechan2015@users.noreply.github.com"
git -C "$PRIMARY" checkout -b main

echo "seed" >"$PRIMARY/seed.txt"
git -C "$PRIMARY" add seed.txt
git -C "$PRIMARY" commit -m "seed"
git -C "$PRIMARY" push origin main >/dev/null

mkdir -p "$PRIMARY/.beads"
echo "../.beads" >"$PRIMARY/.beads/redirect"
printf "ignored-build/\n" >"$PRIMARY/.gitignore"
git -C "$PRIMARY" add .beads/redirect .gitignore
git -C "$PRIMARY" commit -m "beads redirect + ignore"
git -C "$PRIMARY" push origin main >/dev/null

LOCAL_ORIGIN_MAIN="$(git -C "$PRIMARY" rev-parse refs/remotes/origin/main)"

# Make origin/main advance elsewhere so fetch is required.
git clone "$PRIMARY_BARE" "$ADVANCER" >/dev/null
git -C "$ADVANCER" config user.name "tree-worktree-tester"
git -C "$ADVANCER" config user.email "jleechan2015@users.noreply.github.com"
git -C "$ADVANCER" checkout main >/dev/null
echo "advanced" >>"$ADVANCER/seed.txt"
git -C "$ADVANCER" add seed.txt
git -C "$ADVANCER" commit -m "advance origin main"
git -C "$ADVANCER" push origin main >/dev/null

ADVANCED_ORIGIN_MAIN="$(git -C "$ADVANCER" rev-parse HEAD)"
STILL_STALE="$(git -C "$PRIMARY" rev-parse refs/remotes/origin/main)"
assert_ne "$STILL_STALE" "$ADVANCED_ORIGIN_MAIN" "origin/main stale before fetch"

# Create linked worktree and run stale->fresh fetch+create.
LINKED="$TMP_ROOT/linked"
git -C "$PRIMARY" worktree add "$LINKED" "$LOCAL_ORIGIN_MAIN"

# Reject invalid input before any target mutation.
INVALID_SNAPSHOT="$(find "$TMP_ROOT" -mindepth 1 -maxdepth 2 -print | sort)"
if run_tree "$LINKED" ".."; then
  fail "dotdot was accepted unexpectedly"
fi
assert_not_exists "$MAIN_PARENT_REAL/worktree_.." "dotdot path untouched"
assert_eq "$(find "$TMP_ROOT" -mindepth 1 -maxdepth 2 -print | sort)" "$INVALID_SNAPSHOT" "dotdot has no filesystem side effects"

ALPHA_PATH="$(run_tree_pwd "$LINKED" "alpha")"
assert_eq "$ALPHA_PATH" "$MAIN_PARENT_REAL/worktree_alpha" "alpha path"
assert_eq "$(git -C "$ALPHA_PATH" rev-parse HEAD)" "$ADVANCED_ORIGIN_MAIN" "alpha from fetched origin/main"
assert_file_exists "$ALPHA_PATH/.beads/redirect" "alpha redirect file"

# Existing target reset + clean while preserving ignored.
UNRELATED="$MAIN_PARENT_REAL/worktree_keep"
git -C "$PRIMARY" worktree add "$UNRELATED" -b worktree_keep "$LOCAL_ORIGIN_MAIN"
echo "keep" >"$UNRELATED/keep.txt"
git -C "$UNRELATED" add keep.txt
git -C "$UNRELATED" commit -m "keep data" >/dev/null
KEEP_HASH_BEFORE="$(sha256sum "$UNRELATED/keep.txt" | awk '{print $1}')"
KEEP_HEAD_BEFORE="$(git -C "$UNRELATED" rev-parse HEAD)"
KEEP_STATUS_BEFORE="$(git -C "$UNRELATED" status --porcelain=v1)"
MAIN_HEAD_BEFORE="$(git -C "$PRIMARY" rev-parse HEAD)"
MAIN_STATUS_BEFORE="$(git -C "$PRIMARY" status --porcelain=v1)"

TARGET_BETA="$MAIN_PARENT_REAL/worktree_beta"
git -C "$PRIMARY" worktree add "$TARGET_BETA" -b worktree_beta "$LOCAL_ORIGIN_MAIN"
echo "stale-change" >"$TARGET_BETA/seed.txt"
echo "junk" >"$TARGET_BETA/untracked.txt"
mkdir -p "$TARGET_BETA/ignored-build"
echo "ignoreme" >"$TARGET_BETA/ignored-build/cache.bin"

BETA_PATH="$(run_tree_pwd "$LINKED" "beta")"
assert_eq "$BETA_PATH" "$MAIN_PARENT_REAL/worktree_beta" "beta path"
assert_eq "$(git -C "$BETA_PATH" rev-parse HEAD)" "$ADVANCED_ORIGIN_MAIN" "beta reset commit"
assert_not_exists "$TARGET_BETA/untracked.txt" "beta untracked cleaned"
assert_file_exists "$TARGET_BETA/ignored-build/cache.bin" "beta ignored preserved"
if [[ -n "$(git -C "$BETA_PATH" status --porcelain=v1)" ]]; then
  fail "beta not clean"
fi
assert_eq "$(sha256sum "$UNRELATED/keep.txt" | awk '{print $1}')" "$KEEP_HASH_BEFORE" "unrelated worktree file unchanged"
assert_eq "$(git -C "$UNRELATED" rev-parse HEAD)" "$KEEP_HEAD_BEFORE" "unrelated worktree HEAD unchanged"
assert_eq "$(git -C "$UNRELATED" status --porcelain=v1)" "$KEEP_STATUS_BEFORE" "unrelated worktree status unchanged"
assert_eq "$(git -C "$PRIMARY" rev-parse HEAD)" "$MAIN_HEAD_BEFORE" "primary worktree HEAD unchanged"
assert_eq "$(git -C "$PRIMARY" status --porcelain=v1)" "$MAIN_STATUS_BEFORE" "primary worktree status unchanged"

# Remaining failure modes with no mutation.
if run_tree "$TMP_ROOT" "outside"; then
  fail "outside-git argument was accepted unexpectedly"
fi

NO_MAIN_BARE="$TMP_ROOT/no-main-origin.git"
NO_MAIN="$TMP_ROOT/no-main"
git init --bare "$NO_MAIN_BARE" >/dev/null
git -C "$TMP_ROOT" -c color.ui=never init "$NO_MAIN" >/dev/null
git -C "$NO_MAIN" config user.name "tree-worktree-tester"
git -C "$NO_MAIN" config user.email "jleechan2015@users.noreply.github.com"
git -C "$NO_MAIN" remote add origin "$NO_MAIN_BARE"
git -C "$NO_MAIN" checkout -b dev
echo "dev-only" >"$NO_MAIN/dev.txt"
git -C "$NO_MAIN" add dev.txt
git -C "$NO_MAIN" commit -m "dev branch"
git -C "$NO_MAIN" push origin dev >/dev/null
if run_tree "$NO_MAIN" "x"; then
  fail "missing origin/main call was accepted unexpectedly"
fi
assert_not_exists "$NO_MAIN/../worktree_x" "missing branch no target"

mkdir -p "$MAIN_PARENT_REAL/worktree_unreg"
echo "stale" >"$MAIN_PARENT_REAL/worktree_unreg/file.txt"
if run_tree "$LINKED" "unreg"; then
  fail "unregistered target was accepted unexpectedly"
fi
assert_file_exists "$MAIN_PARENT_REAL/worktree_unreg/file.txt" "unregistered untouched"

git -C "$PRIMARY" worktree add "$MAIN_PARENT_REAL/worktree_omega_alt" -b worktree_omega "$LOCAL_ORIGIN_MAIN"
if run_tree "$LINKED" "omega"; then
  fail "branch conflict was accepted unexpectedly"
fi
assert_not_exists "$MAIN_PARENT_REAL/worktree_omega" "omega target not created"

echo "All tree-worktree tests passed."
