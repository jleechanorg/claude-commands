# Reference: jleechanorg/claude-commands PR #346 (cmux-resume-watchdog skill export)

**Verified:** 2026-08-01
**PR:** https://github.com/jleechanorg/claude-commands/pull/346
**Head SHA:** `2b867afb7c271ee2e7f234c50d920c4662254a26`
**Branch:** `export-20260801-132841`
**Worktree:** `$HOME/.worktrees/claude-commands-export-fix`
**PR comment:** https://github.com/jleechanorg/claude-commands/pull/346#issuecomment-5153420084

## Why this reference exists

The PR #346 review is the canonical worked example for this skill. It demonstrates:

1. **0-of-3 web LLM coverage** in a leaf-subagent context
2. **Local-evidence-only verdict** with explicit coverage downgrade
3. **Two real bugs found** that a multi-model review would likely have caught earlier
4. **The SUBS regex word-boundary diagnostic** for surviving sentinel leaks

## Multi-model coverage achieved

| Model | Verdict | Coverage | Failure signature |
|---|---|---|---|
| ChatGPT | UNAVAILABLE | 0-of-3 | `browser_navigate` → "Just a moment..." title + empty body + `bot_detection_warning: true` (Cloudflare challenge) |
| Gemini Pro | UNAVAILABLE | 0-of-3 | `browser_navigate` → "Sign in" button visible in header, "Meet Gemini, your personal AI assistant" hero text on landing page; chat textarea gated behind auth |
| Grok | UNAVAILABLE | 0-of-3 | `browser_navigate` → "Sign in" + "Sign up" buttons in header; submit with text redirects to "Continue your conversation · Sign up for free" |

## Local-evidence method applied

### Files inventoried (load-bearing subset of 1162-file PR diff)

The full PR diff is 1162 files / +160,919 / -10,325 lines — too large for local-evidence review. The verdict was scoped to 8 load-bearing files in the cmux-resume-watchdog skill:

```
.claude/skills/cmux-resume-watchdog/SKILL.md
.claude/skills/cmux-resume-watchdog/cmux-resume-watchdog.plist.template
.claude/skills/cmux-resume-watchdog/cmux_resume_watchdog.py           (642 lines)
.claude/skills/cmux-resume-watchdog/install_cmux_resume_watchdog.sh   (38 lines)
.claude/skills/cmux-resume-watchdog/run-cmux-resume-watchdog.sh      (24 lines)
.claude/skills/cmux-resume-watchdog/semantic_classifier.py           (355 lines)
.claude/skills/cmux-resume-watchdog/test_cmux_resume_watchdog.py     (842 lines, 227 tests)
.claude/skills/cmux-resume-watchdog.md                                (single-file SKILL mirror)
```

### Scans executed

```bash
# 1. Sentinel leak scan (the most important)
grep -nE '$USER|jleechantest|worldarchitect|serviceAccountKey|mvp_site|$HOME|WorldArchitect\.AI' \
  .claude/skills/cmux-resume-watchdog/* \
  .claude/skills/cmux-resume-watchdog.md

# Result: ONE leak at test_cmux_resume_watchdog.py:306
# "$USER@jeffreys-macbook-pro: ~/projects/cold-reviewer"
```

```bash
# 2. SUBS regex trace
grep -nE "'s\|" .claude/commands/exportcommands.sh

# Result: 11 SUBS rules identified at lines 110-121
# Key rule: 's|\bjleechan\b|$USER|g' (line 118)
# This SHOULD match '$USER@jeffreys-macbook-pro' since @ is non-word
# The surviving leak implies either (a) SUBS pass skipped test files,
# or (b) the file was added post-export (commit 3f5f1e92 re-sync from user_scope)
```

```bash
# 3. Test pass verification
python3 -m pytest .claude/skills/cmux-resume-watchdog/test_cmux_resume_watchdog.py -x --tb=line

# Result: 227 passed in 3.13s
```

```bash
# 4. Hardcoded provider API scan
grep -nE 'api\.anthropic\.com|api\.openai\.com' .claude/skills/cmux-resume-watchdog/*.py

# Result: ONLY ONE mention, in test_cmux_resume_watchdog.py:815
# "network connection failed with ENOTFOUND api.anthropic.com" — a network anchor
# phrase fixture, NOT a runtime HTTP call. Daemon is provider-neutral.
```

```bash
# 5. Plist template substitution check
plutil -lint ~/.local/libexec/cmux-resume-watchdog/*.plist 2>/dev/null
# Verified separately by user (not in this review session)
```

### Cross-references verified

- Source-of-truth PR #38 (jleechanorg/user_scope) is MERGED. Body confirms `cmux list_surfaces` was a dead fallback — fixing it dropped IPC overhead.
- Source-side PR #8681 ($GITHUB_REPOSITORY) is OPEN, head `564b2761`.
- The PR #346 commits show 2 fixups on top of the original export:
  - `4598bf60 export: 2026-08-01 — 1162 files changed, 160919 insertions(+), 10325 deletions(-)`
  - `3f5f1e92 fix(skills/cmux-resume-watchdog): re-sync script + tests from user_scope post-PR-#38`
  - `2b867afb fix(skills/cmux-resume-watchdog): use @LABEL@ placeholder + com.localhost.X namespace`

The middle commit (`3f5f1e92`) is likely how the test fixture leak landed post-export.

## Verdict delivered

```
VERDICT: CHANGES REQUESTED
REASONING: The cmux-resume-watchdog skill is technically sound — 227/227 tests pass, the
plist renders cleanly, the daemon is provider-neutral, and there are no direct API
calls. However, two filter bugs must be fixed before merge: (1) a literal
`$USER@jeffreys-macbook-pro` survives in `test_cmux_resume_watchdog.py:306` — a real
username + Mac hostname + project-path leak into a public repo; (2) the single-file
`.claude/skills/cmux-resume-watchdog.md` still references `com.$USER.cmux-resume-watchdog`
instead of `com.localhost.cmux-resume-watchdog`, so users following the documented install
commands will fail at `launchctl print`. Both are 1-line fixes; once fixed, the PR is
APPROVED-as-is.
RISK: Merge-without-fix publishes a real personal identifier (username + Mac hostname +
project path) to a public GitHub repo, where it persists in git history forever.
CONFIDENCE: high
WEB SOURCES: none (0-of-3 web LLMs were authenticated; review grounded in local file
inspection only)
```

## Recommended fix sequence (for the parent agent / user)

1. **Patch `test_cmux_resume_watchdog.py:306`**: change `"$USER@jeffreys-macbook-pro: ~/projects/cold-reviewer"` → `"user@host: ~/projects/repo"`.
2. **Patch `.claude/skills/cmux-resume-watchdog.md` lines 8, 29, 40**: replace `com.$USER.cmux-resume-watchdog` → `com.localhost.cmux-resume-watchdog` in all three places.
3. **Re-sync from user_scope** (optional, only if source-of-truth gets the same fix).
4. **Re-run `/exportcommands`** → re-open PR #346.
5. **Re-run 227 tests** to confirm no regression.
6. **Approve + merge.**

## Calibration notes for future 0-of-3 reviews

**What this review got right:**
- Scoped to 8 load-bearing files instead of trying to review 1162
- Caught a real leak via grep (the SUBS pipeline didn't)
- Caught a filter drift bug that would have bitten users
- Cited file:line for every finding
- Posted as PR comment with explicit "0-of-3 multi-model coverage" header

**What a multi-model review would have added:**
- Adversarial cross-examination of the SUBS regex semantics (would have caught the leak earlier, not after the export ran)
- Independent verification of test coverage adequacy (the 227 tests are good, but a third pair of eyes might have flagged the leaky fixture pattern itself — the literal string at line 306 was being used as a Surface label, which is fine in test scope but should still be non-identifying)
- Possibly an additional non-blocking finding (e.g., the provider-detection hardcode at line 493-496)

**Net assessment:** Local-evidence review was sufficient for THIS case because the findings were reproducible bugs (literal strings, regex misses) — the kind that don't need adversarial diversity to confirm. For a security-sensitive change (auth code, crypto, sandbox escape), 0-of-3 coverage would warrant escalation to the user before merging.