# `launchd-env-wrapper.sh` missing `GITHUB_TOKEN` extraction

**Symptom (verified 2026-07-14):**
The `ao` daemon, running under LaunchAgent `ai.agento.ao-go-daemon` via `~/.hermes/scripts/launchd-env-wrapper.sh`, has no `GITHUB_TOKEN` in its environment. Children spawned by the daemon that need `gh` auth fail with `not authenticated`. The wrapper's `_extract_bashrc_var` list explicitly enumerates the vars it pulls from `~/.bashrc`:
- `MINIMAX_*`, `ANTHROPIC_*`, `SLACK_USER_TOKEN`, `SLACK_MCP_XOXP_TOKEN`, `MCP_*`, `HERMES_*` — present
- `GITHUB_TOKEN`, `AO_BOT_GH_TOKEN` — **MISSING**

**Why this matters:**
The `gh` CLI resolves auth from `~/.config/gh/hosts.yml` (Keychain-backed via `gh auth login`), so most user-level shells work fine. But the spawn CLI's `preflight.checkGhAuth` calls `gh auth status` in a child process whose env differs from the parent's — and any direct `curl -H "Authorization: token $GITHUB_TOKEN"` invocation inside a LaunchAgent-spawned worker fails silently because the env var is empty.

**Fix (harness-level):**
Patch `~/.hermes/scripts/launchd-env-wrapper.sh` to add `GITHUB_TOKEN` and `AO_BOT_GH_TOKEN` to the `_extract_bashrc_var` call. After the patch, `launchctl kickstart -k gui/501/ai.agento.ao-go-daemon` re-loads the daemon with the new env. `ps -ww -p $(pgrep -f 'ao-go daemon') -o command | xargs -I{} bash -c 'echo {}'` confirms via `psutil`.

```bash
# In launchd-env-wrapper.sh, add to the _extract_bashrc_var list:
_extract_bashrc_var GITHUB_TOKEN
_extract_bashrc_var AO_BOT_GH_TOKEN
```

**When to apply this fix:**
- When `ao spawn` workers need to invoke `gh pr view` / `gh api` directly via curl + `$GITHUB_TOKEN`
- When the AO daemon's `running.json` shows workers failing with auth errors not present in user-shell auth
- When `launchctl getenv GITHUB_TOKEN` returns empty but `bash -c 'source ~/.bashrc; echo $GITHUB_TOKEN'` shows it set

**What this fix does NOT solve:**
- The `ao spawn` Node CLI preflight `gh auth status` failure (separate issue — see `references/ao-spawn-preflight-gh-auth-vs-shell-pass-2026-07-14.md`). That bug is in the CLI's child-process composition, not auth state.

**Workaround (without patching the wrapper):**
```bash
# Manually inject via launchctl setenv before restarting the daemon:
GH=$(bash -c 'source ~/.bashrc; echo "$GITHUB_TOKEN"')
launchctl setenv GITHUB_TOKEN "$GH"
launchctl setenv AO_BOT_GH_TOKEN "$GH"
launchctl kickstart -k gui/501/ai.agento.ao-go-daemon
```
This persists across the daemon's current lifetime but not after a reboot. The wrapper patch is the durable fix.

**Bead / provenance:**
- Session 2026-07-14 22:00 PT, dispatch-task → drive PR #8389 to green
- Verified via `psutil.Process(pid).environ()` after restart — `GITHUB_TOKEN: YES`
- Did NOT solve the `ao spawn` preflight issue (separate child-process composition bug)

**Pair with:**
- `commit-self-serve-before-asking` — fix auth gaps instead of asking the user to re-login
- `commit-harness-engineering` — wrappers and LaunchAgent plists are harness-level infrastructure, not task-level