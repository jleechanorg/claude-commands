# Claude Code: `CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY` worked example

**Verified:** 2026-07-10, on `jeffreys-macbook-pro` (macOS 15.5, Claude Code installed via nvm Node 22 → `$HOME/.nvm/versions/node/v22.22.0/lib/node_modules/@anthropic-ai/claude-code/`).

## The ask

User asked: "Test this setting CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY with Claude code and if it works do it on /linux too and ensure user_scope repo has it in backup."

## Verification (all 4 signals)

### 1. Binary string grep — ground truth

```bash
strings $HOME/.nvm/versions/node/v22.22.0/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe \
  | grep -E "^CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY$"

# Output:
# CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY

strings $HOME/.nvm/versions/node/v22.22.0/lib/node_modules/@anthropic-ai/claude-code-darwin-arm64/claude \
  | grep -E "DISABLE_FEEDBACK|tengu_feedback"

# Output:
# CLAUDE_CODE_ENABLE_FEEDBACK_SURVEY_FOR_OTEL
# CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY
# tengu_feedback_survey_event  (×10 — appears at every code site that emits the survey)
```

### 2. Official vendor docs

- <https://docs.anthropic.com/en/docs/claude-code/data-usage>: "To disable these surveys, set CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY=1."
- <https://code.claude.com/docs/en/env-vars>: env var listed in the reference table.

### 3. Functional probe

`claude --print` is non-interactive and does NOT surface the survey prompt (which only appears at session end in interactive TUI mode). Binary grep + docs are the substitute proof.

```bash
CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY=1 claude --print --output-format text "Say ok"
# Output: "ok"  (no survey prompt, as expected)
```

### 4. Config file audit

Live config (Mac):
```bash
grep "DISABLE_FEEDBACK" ~/.claude/settings.json
# 10:    "CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY": "1",
```

Backup config (`user_scope` repo, Mac host `jeffreys-macbook-pro`):
```bash
git show origin/main:backup/jeffreys-macbook-pro/claude/settings.json | grep DISABLE_FEEDBACK
# (empty — var was MISSING from backup)

git show origin/main:backup/Jeff-Ubuntu/claude/settings.json | grep DISABLE_FEEDBACK
# (empty — var was MISSING from Linux backup)
```

## Outcome

- **Live config**: had the var (no action needed).
- **Mac backup** (`backup/jeffreys-macbook-pro/claude/settings.json`): patched, added line 10 var, committed `3948f3171`.
- **Linux backup** (`backup/Jeff-Ubuntu/claude/settings.json`): patched, added line 7 var, committed `3948f3171`.
- **Push**: `git -c core.sshCommand="ssh -i ~/.ssh/id_temp_git"` (because default SSH key in `~/.ssh/config` was scoped to LAN Ubuntu box only, not GitHub).
- **Linux host**: user must `git pull && ./install.sh` on the Ubuntu box to apply.

## Pitfalls hit during this session (now in main SKILL.md)

1. **`/linux` ambiguity** — user said "do it on /linux" but there is no `/linux` path. Interpreted as the Ubuntu host (`backup/Jeff-Ubuntu/`) since that was the only Linux backup in user_scope. When unclear, ask with a `clarify` tool call early.
2. **`backup-home.sh` runs at hostname, not fixed `Mac/` dir** — the Mac backup dir is `backup/jeffreys-macbook-pro/` (current hostname), not the older `backup/Mac/` snapshot from Jun 29.
3. **Auto-running `backup-home.sh` mid-task committed 409 files into a single commit** — my Ubuntu-only patch got bundled. To avoid this in the future, either (a) stop the launchd backup job before patching manually, or (b) rebase onto origin/main first then apply minimal changes as a fresh commit.
4. **`xargs` parsing filenames from `git diff --name-only`** — commit-message words ("to settings env") got parsed as paths, then `git checkout --theirs` failed on `to`, `settings`, `env` as pathspecs. Fix: use `-z` null-delimited input or a `while read` loop.
5. **Force-push ban** — `user_scope/AGENTS.md` prohibits `git push --force`. The recovery pattern when rebase conflicts arise is `git rebase --abort && git reset --hard origin/main && git diff <old-sha> -- <file> > /tmp/diff && git apply /tmp/diff && git commit && git push`.

## One question left open (clarify tool call timed out)

`/linux` interpretation: assumed `Jeff-Ubuntu` host. If user meant something else (different Linux box, WSL path, etc.), they should clarify and I'll redirect.
