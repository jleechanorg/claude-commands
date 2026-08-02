# Git pre-push hook stdin format — field order pitfall

## Symptom

Your pre-push hook is supposed to refuse pushes containing forbidden paths
(e.g. `backup/`, `secrets/`, `*.env`). It runs, it `read`s stdin, it does the
check, but **the push goes through anyway**.

You trace with `bash -x .git/hooks/pre-push origin <url>` and see:

```
+ read -r local_sha local_ref remote_sha _
+ [[ <SHA> != refs/heads/main ]]
+ continue
+ exit 0
```

The hook silently passed because `local_ref` and `local_sha` were swapped.

## Root cause

Per `git/githooks.adoc` (verified 2026-07-15), the stdin format is:

```
<local-ref> SP <local-sha> SP <remote-ref> SP <remote-sha> LF
```

So the correct read is:

```bash
while read -r local_ref local_sha remote_ref remote_sha; do
    [[ -z "$local_ref" ]] && continue
    if [[ "$local_ref" == "refs/heads/main" ]]; then
        main_sha="$local_sha"
        break
    fi
done
```

The common bug is using `read -r local_sha local_ref remote_sha _` — that swaps
`local_sha` and `local_ref`, so the `[[ $local_ref == refs/heads/main ]]`
comparison never matches (it's comparing a SHA to a ref string), and the hook
either falls through to `exit 0` (no enforcement) or skips the block entirely.

## Why this is dangerous

The hook LOGIC is correct in your head — you wrote a clear `if [[ ref ==
refs/heads/main ]]; then check_for_forbidden_paths; fi`. The bug is invisible
in code review because the bash variables `local_sha` and `local_ref` look
plausible. The push succeeds; you believe the hook is doing its job; you
discover the leak hours later when the cron keeps re-pushing forbidden content.

## Verification recipe (TDD the hook before deploying)

```bash
# Test 1: forbidden path in commit, main push → MUST exit 1
TMP=$(mktemp -d)
git worktree add --detach "$TMP" <clean_base_sha>
cd "$TMP"
mkdir -p backup/Mac && echo secret > backup/Mac/test.txt
git add -f backup/ && git commit -m test --no-verify
BAD_SHA=$(git rev-parse HEAD)
echo "refs/heads/main $BAD_SHA refs/heads/main 0000000000000000000000000000000000000000" \
  | .git/hooks/pre-push origin https://github.com/.../repo.git
echo "Exit: $?"   # expect: 1

# Test 2: clean commit, main push → MUST exit 0
CLEAN_SHA=<a_clean_sha>
echo "refs/heads/main $CLEAN_SHA refs/heads/main 0000000000000000000000000000000000000000" \
  | .git/hooks/pre-push origin https://github.com/.../repo.git
echo "Exit: $?"   # expect: 0

# Test 3: feature branch push (any commit) → MUST exit 0
echo "refs/heads/feat/x $BAD_SHA refs/heads/feat/x 0000000000000000000000000000000000000000" \
  | .git/hooks/pre-push origin https://github.com/.../repo.git
echo "Exit: $?"   # expect: 0
```

**If Test 1 exits 0, your hook is silently broken — fix the field order immediately.**

## Field order across git hook types (don't confuse them)

| Hook | Stdin format |
|---|---|
| `pre-push` | `<local-ref> SP <local-sha> SP <remote-ref> SP <remote-sha>` |
| `pre-receive` | `<old-value> SP <new-value> SP <ref-name>` |
| `update` | `<ref-name> SP <old-value> SP <new-value>` (positional args, not stdin) |
| `post-receive` | `<old-value> SP <new-value> SP <ref-name>` |

Always check `git/githooks.adoc` in the upstream git source for the format
you're implementing. The hook scripts in your repo can drift; the docs are
the source of truth.

## Why gitleaks pre-push hooks don't catch this class of leak

The existing pre-push hooks in many repos run `gitleaks` on staged content or
commit history. They detect SECRET patterns (apiKey=..., tokens, etc.) but
NOT path-prefix patterns. A `backup/` folder containing your entire `~/`
home dir passes gitleaks cleanly because there's no regex that matches
"sensitive path prefix" — gitleaks only knows about secret shapes.

**Fix path:** Add a path-prefix check to your pre-push hook that runs BEFORE
the secret scan. Both checks belong in the same hook; the path check refuses
the push if forbidden paths are in the diff, the secret scan refuses the push
if any secrets are in the diff.

## Bug-ref

2026-07-15, jleechanorg/claude-commands. Hook written with wrong field order,
4 commits failed to detect the leak, 491 MiB pushed to public repo. Fixed by
rewriting hook with correct `<local-ref> SP <local-sha> ...` order and adding
the three-test verification harness above.