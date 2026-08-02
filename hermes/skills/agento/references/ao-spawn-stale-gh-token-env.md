# ao spawn: STALE `GH_TOKEN` / `GITHUB_TOKEN` produces false "not authenticated" (verified 2026-07-23)

## Failure class

`ao spawn` returns:

```
✗ GitHub CLI is not authenticated. Run: gh auth login
```

…even when `gh auth status` works fine in the gateway shell (keychain `~/.config/gh/hosts.yml` returns `✓ Logged in to github.com account jleechan2015`).

## Root cause

The CLI preflight at `packages/cli/dist/lib/preflight.js:checkGhAuth` runs `gh auth status` via `child_process.execFile` and inherits the gateway env. If a stale `GH_TOKEN` / `GITHUB_TOKEN` is set in the gateway shell (common: prior `gh auth login --with-token` from another machine, leftover `AO_BOT_GH_TOKEN=jleechanao` while active account is `jleechan2015`, or `GH_TOKEN_AGENTF=$USER-af` pointing at a user that is NOT a member of `jleechanorg`), `gh` exits non-zero on `auth status` and the preflight rejects with the misleading "not authenticated" message.

This is the **opposite** of the empty-token pitfall already covered in `SKILL.md §⚠️ ALWAYS WRAP SPAWN IN env -i`: that one bites when you pass `GH_TOKEN=""` (empty literal); this one bites when you pass `GH_TOKEN=ghp_<stale>` (wrong-account literal).

## Why `env -i … GH_TOKEN="$GH_TOKEN_VAL" …` does NOT fix it

If you compute the literal from `gh auth token` *without stripping the stale env first*, you copy the same stale token back into the wrapper. The preflight then sees the same bad token and rejects.

## Fix

Strip the env vars BEFORE invoking `ao`, and let `gh` fall back to `~/.config/gh/hosts.yml`:

```bash
unset GH_TOKEN GITHUB_TOKEN
AO=$HOME/.nvm/versions/node/v22.22.0/bin/ao
env -u GH_TOKEN -u GITHUB_TOKEN \
    PATH="/tmp/ao-gh-probe:$PATH" \
    "$AO" spawn -p <project> --claim-pr <N> --agent codex
```

The `-u GH_TOKEN -u GITHUB_TOKEN` MUST come BEFORE the spawn call. For the cron-friendly `ao send` variant: same prefix.

## Diagnostic recipe (when spawn returns "not authenticated" with no obvious token-missing cause)

Write a `/tmp/ao-gh-probe/gh` shim that logs the env + args then `exec`s the real binary:

```bash
#!/bin/bash
{
  echo "ARGS:$*"
  echo "GH_TOKEN_SET:$([ -n "${GH_TOKEN:-}" ] && echo yes || echo no)"
  echo "GITHUB_TOKEN_SET:$([ -n "${GITHUB_TOKEN:-}" ] && echo yes || echo no)"
} >> /tmp/ao-gh-probe.log
exec $HOME/.local/bin/gh.real "$@"
```

chmod +x, prepend `/tmp/ao-gh-probe` to PATH, run spawn, then inspect `/tmp/ao-gh-probe.log`. First 2 entries reveal:
1. Whether `GH_TOKEN`/`GITHUB_TOKEN` were set when the preflight ran (if `yes`, this is your bug).
2. Whether the failing command was `gh auth status` (preflight) or `gh api repos/...` (subsequent, different bug — check token scopes).

## Quick re-check recipe after fix

```bash
unset GH_TOKEN GITHUB_TOKEN
env -u GH_TOKEN -u GITHUB_TOKEN gh api user --jq .login
# → jleechan2015
env -u GH_TOKEN -u GITHUB_TOKEN gh auth status
# → ✓ Logged in to github.com account jleechan2015
```

If both return cleanly, the `ao spawn` preflight will pass. Clean up the shim (`rm -f /tmp/ao-gh-probe/gh`) when done so it doesn't pollute future spawns.

## Related

- `feedback_2026-07-18_gh_token_env_override_stale_unset_before_gh_or_push.md` (memory) — covers the `git push` failure mode; same root cause.
- `SKILL.md §⚠️ ALWAYS WRAP SPAWN IN env -i` — the empty-token twin pitfall.
- `references/ao-spawn-ts-cli-auth-and-20-slot-cliff-2026-07-22.md` — TS CLI auth quirks, complementary.
