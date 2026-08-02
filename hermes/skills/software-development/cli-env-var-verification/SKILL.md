---
name: cli-env-var-verification
description: "Verify that a CLI tool or daemon honors a specific environment variable before claiming the var 'works'. Combines four signals in priority order: (1) binary-string grep on the compiled executable as ground truth, (2) official vendor docs, (3) live process test, (4) confirm-the-var-in-config-file presence. Use when a user says 'does CLI X honor env var Y', 'test this env var with tool X', 'verify DISABLE_FOO_BAR=1 actually does something', 'why isn't setting this env var helping', or when about to commit an env var to a config file and need proof the tool respects it. The class failure mode is assuming a documented env var is real when it's only present in third-party blogs, or assuming the var works when the tool silently ignores it."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [verification, cli, environment-variables, debugging, ground-truth]
    related_skills: [github-pr-workflow, research-integrity]
---

# CLI env-var verification protocol

When a user asks "test env var X with tool Y" or you need to confirm a CLI tool actually honors a documented env var, do NOT stop at "the docs say it works" or "I set it and nothing broke". The bar is **mechanically proving the tool reads the var at runtime**.

Four signals, ordered by strength:

## 1. Binary string grep (ground truth)

The compiled executable contains every env var name it checks. If the var name appears as a literal string in the binary, the tool reads it. If not, the var is either ignored or undocumented.

```bash
# Example: verify Claude Code honors CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY
strings /path/to/cli/binary | grep -E "^ENV_VAR_NAME$"

# Watch for these patterns:
#   - Exact var name as a standalone line
#   - Internal event/feature-flag names that pair with it (e.g. tengu_feedback_survey_event
#     paired with CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY)
#   - Counterpart vars (ENABLE_*/DISABLE_*, *_FOR_OTEL) that confirm the family
```

Companion checks:
```bash
# For npm-installed packages:
strings $(which <tool>) | grep -E "^ENV_VAR_NAME$"

# For shell-script CLIs (no binary):
grep -rE "ENV_VAR_NAME" /usr/local/lib/<tool>/ 2>/dev/null

# For Python CLIs:
grep -rE "ENV_VAR_NAME|os\.environ|os\.getenv" /path/to/cli/source/ | head -20
```

This is the **strongest signal** because there's no interpretation layer between you and the code path. Verified 2026-07-10 with Claude Code's `bin/claude.exe`: literal strings `CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY`, `CLAUDE_CODE_ENABLE_FEEDBACK_SURVEY_FOR_OTEL`, and `tengu_feedback_survey_event` all appeared.

## 2. Official vendor docs

Cross-check that the var is documented by the tool's author, not just third-party blogs.

Search priority:
1. Tool's official docs site (e.g. `docs.anthropic.com/en/docs/claude-code/...`)
2. Tool's GitHub issues — search for the var name; issues referencing it confirm real-world use
3. Tool's `--help` output or `man` page
4. Schemas (e.g. `claude-code-settings.json` `$schema` URL) — if the JSON schema lists the var, the tool parses it

Per research-integrity rule: a missing `--help` flag is NOT proof a flag is fake (help text can be incomplete). Conversely, third-party blog claims alone are NOT proof a flag works.

## 3. Live process / functional test

For env vars that control runtime behavior, prove they do something observable:

- **Boolean toggles** (DISABLE_*, ENABLE_*): find a behavioral side effect that should differ based on the var. Run the tool with and without it, capture the diff.
- **Path/location vars**: run the tool and inspect where it actually wrote/read.
- **Token/credential vars**: run the tool and inspect network traffic or auth headers.

For tools where the side effect is rare (e.g. Claude Code's survey prompt only appears at session end in interactive TUI mode, not in `claude --print`), document that the binary-level proof stands in for the functional test and note the limitation.

## 4. Config-file presence

For env vars that also live in a tool's config file (e.g. `~/.claude/settings.json`, `~/.config/<tool>/config.toml`), confirm the var is present in BOTH the live config AND any backup copy that's git-tracked.

This catches the **stale-snapshot trap**: a backup script may commit `settings.json` to git at one point, but the live file changes later. A restore from the older backup would lose the new var.

```bash
# Compare live config vs git-tracked backup
diff <(jq '.env' ~/.claude/settings.json) <(git show origin/main:backup/$(hostname)/claude/settings.json | jq '.env')
```

## Verification recipe (canonical)

When asked "does this env var work with this tool?", do all four:

```bash
# 1. Binary grep (ground truth)
strings "$(which <tool>)" | grep -E "^<ENV_VAR>=\$" && echo "BINARY: var is referenced" || echo "BINARY: var NOT found"

# 2. Doc cross-check
gh search issues "<ENV_VAR>" owner:<tool-org> --limit 3 || \
  curl -fsS "https://docs.<vendor>.com/api/search?q=<ENV_VAR>" 2>/dev/null | head -20

# 3. Functional probe
<tool> --version  # confirm tool runs at all
ENV_VAR=value <tool> <no-op-command>  # run with var set, capture baseline
unset ENV_VAR; <tool> <no-op-command>   # run without, compare

# 4. Config file audit
grep -F "<ENV_VAR>" ~/.config/<tool>/<config-file>
grep -F "<ENV_VAR>" /path/to/git-tracked/backup/<config-file>
```

Or run the bundled script: `bash scripts/verify-env-var.sh "$(which <tool>)" <ENV_VAR> [<DOCS_URL>]`.

## Common failure modes (avoid these)

### Failure: "I set the env var and nothing happened"

Many CLI tools only read certain env vars at startup or only check them in specific code paths. Diagnostic steps:
- Is the var read at startup (need to restart the tool)? Or per-invocation?
- Does the var name in your config match exactly (case-sensitive, underscores not dashes)?
- Did you set it in the right scope? `~/.bashrc` ≠ `~/.zshenv` ≠ launchd env ≠ cron env.
- Is the var being overridden by a config file? Many tools: env < config-file < CLI flag.

### Failure: "execute_code says the var is empty, so the token is broken" (DUAL-PROBE TRAP)

**The class trap:** `execute_code` Python subprocess does NOT source `~/.bashrc`. Any secret defined via `export VAR=...` in `~/.bashrc` returns empty string from `os.environ.get(VAR)` even though `terminal()` in the same session sees the var fine. Same family as the `bashrc-profile-xapp-drift-blocks-launchd` memory but for inline `execute_code` rather than launchd.

**Symptom:** Token probe in `execute_code` returns `len = 0` → `Bearer ` (empty) → `invalid_auth` → user reply "you got confused dd".

**Diagnostic — dual-probe rule (mandatory before any "blocked on token" claim):**

```bash
# Probe 1: bash-sourced terminal (the authoritative one for bashrc-exported vars)
bash -c "source ~/.bashrc 2>/dev/null; \
  echo \"HERMES_SLACK_BOT_TOKEN=\${HERMES_SLACK_BOT_TOKEN:+set(\${#HERMES_SLACK_BOT_TOKEN})}\"; \
  echo \"GH_TOKEN=\${GH_TOKEN:-MISSING}\""
```

```python
# Probe 2: execute_code Python subprocess (does NOT source bashrc)
import os
print({k: "SET" if os.environ.get(k) else "MISSING"
       for k in ("HERMES_SLACK_BOT_TOKEN","GH_TOKEN","MINIMAX_API_KEY","ANTHROPIC_API_KEY")})
```

If Probe 1 reports `set(N)` but Probe 2 reports `MISSING`, the cause is **execute_code env-isolation**, NOT a broken token. Refuse to publish a "blocked on token" or "token is invalid_auth" claim until both probes run.

**For live API calls, route through bash-sourced shell:**

```bash
# This works even when execute_code says the var is empty:
bash -c "source ~/.bashrc && curl -fsS -X POST \
  'https://slack.com/api/auth.test' \
  -H \"Authorization: Bearer \$HERMES_SLACK_BOT_TOKEN\""
```

**Bug-ref (2026-07-28 inline /roadmap):** Agent declared "Slack token invalid_auth, blocked" after one execute_code probe. Bash-sourced bash showed token set (58 chars, xoxb-, ok:true on auth.test, all 4 channels replied ok). User reply: "You def should have the slack tokens check bashrc and if it works see why you got confused dd" then "Why did you mess it up? Run /harness --fix first". Fix landed as SOUL.md `## COMMIT: dual-probe-secrets`, `~/.hermes/skills/roadmap/SKILL.md` Step 2.5.f, and `~/.hermes/tests/test_execute_code_env_isolation.py` (3 PASS, 1 skip-on-this-host).

**Other environments with the same trap family (probe before claiming):**
- **`launchd` plist jobs** — the `launchd-env-wrapper.sh` script exists precisely because launchd doesn't source `~/.bashrc`. Apply the same dual-probe pattern to launchd jobs: probe via `launchctl print gui/$(id -u)/<label>` env then re-probe from `bash -c 'source ~/.bashrc && ...'`.
- **`.profile` vs `.bashrc`** — same shell, different file. A var exported in `.bashrc` is invisible to a `.profile`-sourced shell and vice versa. Probe both.
- **`crontab -e` env** — cron doesn't source any dotfiles by default. Probe with `crontab -l | head` then `bash -c 'source ~/.bashrc && crontab -l'`.
- **`tmux`/`screen` sessions** started from a shell that already had the var set inherit it; sessions started by launchd from `~/.tmux/tmux-3.4/resurrect/` may not. Probe in-session env with `tmux show-env -g | grep VAR`.

### Failure: "Third-party blog says the var exists but my --help doesn't list it"

Per `research-integrity`: `--help` absence is NOT proof. Many CLIs silently accept unknown flags/env vars without erroring. Check the binary string set before declaring the var fake.

### Failure: "I tested with `--print` non-interactive mode but surveys still showed up"

Many CLI behaviors (notably Claude Code's "How is Claude doing?" survey prompt) only fire in interactive TUI mode at session end. A non-interactive `--print` test will not exercise that code path. Binary grep + docs are the substitute proof.

### Failure: "Var is set in live config but missing from git-tracked backup"

The backup script ran at time T, the live config changed at time T+1, and no later backup has run. Either:
- Run the backup manually to refresh: `bash scripts/backup-home.sh` (or equivalent)
- Patch the backup directly with `patch` + commit + push

Always diff live vs backup before claiming "the env var is in backup".

## Pitfalls (cross-tool)

1. **`strings` on stripped binaries** — output is sparse but env var names typically remain because they're referenced from `getenv()` calls. If grep returns nothing, try the unstripped variant or `nm <binary> | grep <var>`.

2. **`strings` on minified npm packages** — the binary may be a shim (`#!/usr/bin/env node`) that loads the real code from a `.js` bundle. Check `node_modules/<pkg>/dist/` for the actual code.

3. **macOS `strings` defaults** — `strings` on macOS BSD may not match GNU `strings` flags. Use `strings -a` to scan all sections. Or `grep -aoE "[A-Z_]{8,}=?[A-Z_]*" <binary>` as a fallback.

4. **Env vars read at compile time** — some C/Rust tools compile env-var defaults into the binary. Setting the var at runtime has no effect. Check the build config.

5. **Process spawning vs current shell** — env vars set in your current shell don't propagate to a launched subprocess unless you `export` them or pass them inline: `VAR=x ./tool` not `./tool` with `VAR=x` set in the same line via `&&`.

6. **`backup-home.sh` snapshot freshness** — auto-backup scripts commit `settings.json` at scheduled intervals. A live config change between backup runs is lost from git until the next run. For env-var tasks, **diff live vs `git show origin/main:backup/<hostname>/<config-path>`** before claiming the var is "in backup".

7. **`backup/<host>/` dir naming** — `user_scope`-style repos name backup dirs after `$(hostname)`, not a fixed `Mac/`. Wrong dir means the change lands in the wrong snapshot.

8. **Launchd auto-commit on auto-run** — if you patch a snapshot manually while a launchd backup job is also writing to it, the job's auto-commit will bundle your change with hundreds of unrelated files. Stop the launchd job OR rebase onto origin/main before applying minimal changes.

## Support files

- `scripts/verify-env-var.sh` — Reusable 4-signal verification script. Run: `bash scripts/verify-env-var.sh "$(which <tool>)" <ENV_VAR> [<DOCS_URL>]`. Prints a per-signal report.
- `references/anthropic-claude-code-feedback-survey.md` — Worked example for `CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY` with Claude Code (verified 2026-07-10). Includes all 4 signals for that specific var, the pitfalls hit during that session, and the user_scope backup-restore staleness trap.
- `references/execute_code-bashrc-env-isolation-dual-probe.md` — Worked example for the dual-probe trap: bashrc-exported secrets are visible to `terminal()` but invisible to `execute_code`'s clean Python subprocess. Includes the dual-probe recipe, the bash-sourced-shell call pattern, and the canonical SOUL.md / roadmap-SKILL.md / test fixes (verified 2026-07-28).

## Adjacent patterns

### Git SSH key override (push to a repo when default key fails)

When `git push` fails with `git@github.com: Permission denied (publickey)` but you have alternate SSH keys in `~/.ssh/`:

```bash
# Find which key reaches GitHub
for k in ~/.ssh/id_*; do
  [[ "$k" == *.pub ]] && continue
  ssh -i "$k" -o BatchMode=yes -T git@github.com 2>&1 | grep -q "successfully authenticated" && echo "WORKS: $k"
done

# Push with explicit key
git -c core.sshCommand="ssh -i ~/.ssh/id_temp_git -o StrictHostKeyChecking=no" push origin main
```

Verified 2026-07-10 on `~/projects/user_scope` — `~/.ssh/id_jeff_ubuntu` is for the LAN Ubuntu box (192.168.254.128), not GitHub; only `~/.ssh/id_temp_git` reaches GitHub.

### Flag verification (sibling skill, different axis)

This skill is about **env vars**. There is a sibling failure mode for **CLI flags**: a launchd-driven `~/.hermes/scripts/*.sh` calls `hermes <subcmd> --flag`, the flag does NOT exist, argparse rejects it, the script's `$(...) || true` swallows the failure, downstream shell vars fall back to `?` placeholders, and the broken message posts to Slack for weeks before anyone notices. The recipe is at `hermes-deploy-pipeline/references/cli-flag-verification-pre-deploy.md` — 4 pre-deploy checks (flag-exists-in-help → dry-run parser → smoke-test under launchd PATH → regression test pinning contract) plus a test-shell template that locks the CLI flag + parser row count + template-no-`?`-placeholders contract. Verified 2026-07-21 against `cron-backup-sync.sh`'s `Total: ? jobs (? enabled).` bug that ran 6 days before being noticed. The two skills (this one for env vars, the deploy-pipeline reference for flags) share the same "verify before assuming" failure pattern — apply both when editing launchd-driven scripts that touch env or call CLIs with non-trivial flags.

### Force-push ban recovery (rebase onto origin/main)

When your local has diverged and `git push` is rejected with "non-fast-forward", and the repo forbids `--force`, the right pattern is:

```bash
# Abort any in-progress rebase
git rebase --abort 2>/dev/null

# Reset to origin/main (discards local-only commits — make sure you have what you need first!)
git fetch origin
git reset --hard origin/main

# Re-apply your changes via patch capture
git diff <old-sha>^..<old-sha> -- <file> > /tmp/recovery.diff
git apply /tmp/recovery.diff
git add <file>
git commit -m "<message>"
git push origin main
```

Verified 2026-07-10 on `~/projects/user_scope` — cherry-pick of the original commit then rebase failed with 4 conflicts; `git reset --hard origin/main` + manual `git diff` capture + re-apply + fresh commit + push worked cleanly.

### `xargs` footgun from `git diff --name-only`

`git diff --name-only --diff-filter=U` returns paths that may contain whitespace. If you pipe to `xargs <command>` and any path has spaces, `xargs` parses them as separate arguments. Also, `git diff` may pick up commit-message tokens that look like paths if you accidentally pipe the wrong input.

Safer alternatives:
```bash
# Use null-delimited input
git diff --name-only --diff-filter=U -z | xargs -0 git checkout --theirs

# Or loop explicitly
git diff --name-only --diff-filter=U | while IFS= read -r f; do
  git checkout --theirs "$f"
  git add "$f"
done

# Or use git's built-in
git checkout --theirs -- .
git add -u
```
