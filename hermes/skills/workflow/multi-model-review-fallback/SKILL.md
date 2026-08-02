---
name: multi-model-review-fallback
version: 1.0.0
description: "Use when multi-model reviewers are auth-walled."
tags: ["multi-model", "review", "fallback", "auth-wall", "local-evidence"]
category: workflow
---

# Multi-Model Review Fallback — recipes when primary reviewers are unreachable

When a multi-model review path is unavailable (web LLMs behind browser auth, CodeRabbit/Bugbot rate-limited, Codex connector exhausted, `/advice` subagent chain exhausted), the agent must produce a verdict on local-evidence-only grounds. This skill captures the fallback protocol for that situation.

## When this skill fires

**Trigger phrases** (any one):
- "0-of-3 web LLM coverage", "auth wall", "browser cookies unreachable"
- "CodeRabbit rate-limited AND Bugbot rate-limited AND Codex connector exhausted"
- "fall back to local-evidence review", "synthesize without multi-model coverage"
- "the leaf subagent cannot supply credentials"
- "no 3rd-party reviewer is available, give me your best local assessment"

**Pre-flight signature** (must verify before falling back):

| Service | Verify with | Failure signature |
|---|---|---|
| ChatGPT web | `browser_navigate` + `browser_snapshot` | "Just a moment..." title + empty body + `bot_detection_warning` (Cloudflare challenge) |
| Gemini web | `browser_navigate` + `browser_snapshot` | "Sign in" button visible; "Meet Gemini, your personal AI assistant" hero on landing |
| Grok web | `browser_navigate` + `browser_type` + `browser_click` on submit | Redirects to "Continue your conversation · Sign up for free" |
| CodeRabbit GH App | `gh api repos/<O>/<R>/pulls/<N>/reviews` | No review entries; rate-limit ack comments in issue API |
| Cursor Bugbot | `gh pr checks <N>` | `skipping context="usage limit reached"` |
| Codex connector | `gh pr checks <N>` | `skipped context="Codex usage limits"` |

If 2-of-3 or 3-of-3 are unavailable, the standard `/advice` Gate-3 substitute recipe (in `~/.hermes/skills/advice/SKILL.md` v1.5.0 §"Verified 2026-07-21") applies — subagent fan-out to `delegate_task` reaches models those services would have used.

**If the subagent fan-out ALSO fails or is unavailable** (e.g. this agent IS a leaf subagent with no `delegate_task`, OR the available subagents are not on different model families), this skill is the next fallback.

## The fundamental distinction: `/advice` vs `/web-advice` fallback

| Path | Primary reviewers | Fallback when all unavailable |
|---|---|---|
| `/advice` (in-session) | `delegate_task` subagents (Hermes `MiniMax-M3` mid-tier by default) | `delegate_task` to a different model family (`claude -p`, `codex`, `agy`); see `~/.hermes/skills/advice/SKILL.md` "Hermes-adapted Reviewer A fallback chain" |
| `/web-advice` (browser) | Web LLMs authenticated against the operator's browser cookies (ChatGPT, Gemini, Grok) | **Local-evidence-only review** — there is no subagent-equivalent because web LLM auth is browser-cookie-bound |

**The `/web-advice` fallback is the harder case** and the reason this skill exists. A leaf subagent cannot supply browser cookies, cannot OAuth into ChatGPT/Gemini/Grok, and cannot complete a Cloudflare challenge interactively. The fallback is NOT a subagent fan-out — it's a **local-evidence-only synthesis**.

## Local-evidence-only review protocol (the fallback)

When multi-model coverage is 0-of-3 or 1-of-3 and the agent must produce a verdict:

### Step 1 — Inventory the load-bearing files

```bash
# From the PR's worktree (or read-only clone)
git -C <worktree> diff --name-only origin/<base>...HEAD
# OR for a fresh export review:
git -C <worktree> ls-files | head -50
```

Build a list of files that bear claims under review. For each, decide whether it's a load-bearer or boilerplate.

### Step 2 — Run targeted scans

| Scan type | Tool | Purpose |
|---|---|---|
| Sentinel leak | `grep -nE '<sentinel-regex>' <files>` | Detect personal identifiers (usernames, hostnames, emails, project paths) that survived export filter SUBS regexes |
| Test pass | `python3 -m pytest <test_file> -x --tb=line` | Verify the test suite passes locally on the export's HEAD |
| Lint / format | `plutil -lint <plist>` / `ruff check <py>` / `prettier --check <md>` | Verify structural validity |
| Provider neutrality | `grep -nE 'api\.anthropic\.com\|api\.openai\.com' <daemon_files>` | Confirm no direct HTTP calls to provider APIs |
| SUBS regex trace | `grep -nE "'s\|" <exportcommands.sh>` | Identify the filter rules the export applied; predict what should/would survive |
| Cross-reference | `git grep` for sentinel patterns across the entire repo | Catch leaks beyond the skill scope |

### Step 3 — Synthesize verdict with explicit coverage downgrade

The synthesis MUST include:

```markdown
| Model | Verdict | Confidence | Key finding |
|---|---|---|---|
| ChatGPT | UNAVAILABLE | n/a | <failure mode> |
| Gemini Pro | UNAVAILABLE | n/a | <failure mode> |
| Grok | UNAVAILABLE | n/a | <failure mode> |
| **Local evidence** | **<verdict>** | **<confidence>** | <key finding> |

**Multi-model coverage:** <N>-of-3 (explicit fraction)
**Coverage downgrade:** <one sentence on what the missing adversarial diversity costs>
**Recommended action:** <APPROVE / approve with conditions / change requests>
```

**Confidence calibration when 0-of-3 multi-model:**
- CHANGES REQUESTED on code-correctness or filter-safety: **high** confidence is acceptable (local evidence is strong; the bugs are reproducible).
- APPROVED-as-is on a security-sensitive change: **low** confidence — escalation recommended.
- APPROVED with notes: **medium** confidence — local evidence is strong for the noted items but adversarial review would catch unknown-unknowns.

### Step 4 — Cite file:line for every claim

Local-evidence compensation for missing adversarial review is **maximal citation density**. Every finding must include `file:line` evidence on BOTH sides (the claim AND the source it cites, if applicable). No "looks good" or "seems fine" without a specific anchor.

### Step 5 — Post as PR comment

The synthesis is posted as a `gh pr comment` so the verdict is recorded on the PR thread (per `green.md` Step 3.4 "independent adversarial review recorded on the PR" requirement). Tag the comment header with the explicit coverage fraction:

```bash
gh pr comment <N> --repo <OWNER>/<REPO> --body-file /tmp/synthesis.md
# Header should include: "Multi-model coverage: 0-of-3 (auth wall on ChatGPT/Gemini/Grok)"
```

## Anti-patterns (do NOT do these)

- **Do NOT try to log in.** Per `~/.claude/skills/web-advice/SKILL.md`: "If any model is not logged in, stop and ask the user to log in — do NOT try to log in for them (no credentials, no auth cookies, no OAuth flow)." A leaf subagent cannot supply credentials.
- **Do NOT pretend multi-model coverage.** A "synthesis" that lists 3 verdicts when only 1 model answered is fabrication. State the actual coverage fraction.
- **Do NOT skip the verdict because "I couldn't reach the LLMs".** The user needs a verdict. The whole point of this skill is to produce one from local evidence, with explicit caveats.
- **Do NOT inflate confidence to compensate for missing coverage.** Lower confidence honestly is the right move; the user can decide whether to escalate.
- **Do NOT generalize beyond the file scope.** Multi-model review of a 1162-file export PR is impossible from local evidence alone; the right move is to scope the verdict to the 8 load-bearing files.

## Worked example: PR #346 (cmux-resume-watchdog skill export, 2026-08-01)

**Subject:** jleechanorg/claude-commands PR #346 — bulk content export from your-project.com → claude-commands, focused on `.claude/skills/cmux-resume-watchdog/` (7 files) + `.claude/skills/cmux-resume-watchdog.md` (single-file mirror).

**Multi-model coverage achieved:** 0-of-3 (Gemini: Sign-in wall; ChatGPT: Cloudflare "Just a moment..." challenge; Grok: submit redirects to "Sign up for free").

**Local-evidence method:** read all 8 files + `exportcommands.sh` SUBS regex pipeline + `test_cmux_resume_watchdog.py` pytest output (227/227 passed) + sentinel leak scan.

**Findings (with file:line citations):**
1. **Sentinel leak** — `test_cmux_resume_watchdog.py:306` literal `"$USER@jeffreys-macbook-pro: ~/projects/cold-reviewer"` survived the export's `\bjleechan\b` SUBS regex. Since `@` is a non-word character in Perl regex, `\bjleechan\b` SHOULD match `$USER@` — the surviving leak implies either (a) the SUBS pass did not run on test files, or (b) the file was added post-export (a re-sync from user_scope per the commit log `3f5f1e92 fix(skills/cmux-resume-watchdog): re-sync script + tests from user_scope post-PR-#38`). **Fix:** replace with `"user@host: ~/projects/repo"`.
2. **Filter drift** — `.claude/skills/cmux-resume-watchdog.md` lines 8/29/40 still reference `com.$USER.cmux-resume-watchdog` but the installer hardcodes `LABEL="com.localhost.cmux-resume-watchdog"`. Users following the single-file SKILL's install command will fail at `launchctl print`. **Fix:** rewrite all 3 references to use `com.localhost.cmux-resume-watchdog`.
3. **Nice-to-have** — `cmux_resume_watchdog.py:493-496` hardcodes "codex"/"claude"/"bypass permissions" substring detection; non-Codex/Claude sessions return `None` instead of `"unknown"`. Non-blocking (provider field is metadata-only; resume decision is screen-content-driven). **Fix:** add generic fallback returning `"unknown"`.

**Verdict:** CHANGES REQUESTED (high confidence, local-evidence-only).
**Risk if shipped as-is:** username + Mac hostname + project path leak into a public GitHub repo's git history forever.

## Diagnostic technique: SUBS regex word-boundary semantics

The cmux-resume-watchdog leak surfaced a subtle SUBS regex gotcha worth recording for future export reviews.

**The regex:** `'s|\bjleechan\b|$USER|g'` (Perl, in `exportcommands.sh`)

**Expected match:** `$USER@jeffreys-macbook-pro` — `\b` (word boundary) matches between a word char (`n`) and a non-word char (`@`), so `\bjleechan\b` SHOULD match the substring `$USER` even when followed by `@`.

**Why the leak survives anyway:** Two possible explanations:
1. **The SUBS pass did not run on test files.** Some export pipelines filter `.test.` patterns out of the SUBS scope (performance: tests don't ship to production). Check whether the export's file filter excludes test fixtures.
2. **The file was added AFTER the export ran.** A re-sync from user_scope (commit `3f5f1e92 fix(skills/cmux-resume-watchdog): re-sync script + tests from user_scope post-PR-#38`) re-introduced a test fixture from the canonical source — but the source's test fixture already contains the leak (the SUBS pass ran on the source-of-truth user_scope, not on this downstream export).

**Diagnostic recipe for future exports:**
```bash
# 1. Identify the SUBS rules
grep -nE "'s\|" <repo>/.claude/commands/exportcommands.sh

# 2. For each surviving sentinel, check the file's git history
git -C <worktree> log --oneline --all -- <file>

# 3. If the file was added in a "re-sync" or "fix" commit AFTER the export
#    commit, the SUBS pass never touched it. The fix belongs in the source
#    repo (user_scope), not in the export pipeline.

# 4. If the file was present at the export commit, the SUBS regex didn't
#    match — verify the regex's word-boundary semantics against the literal.
#    \b\w+\b matches \w+ surrounded by \W or string boundaries. @ is \W in
#    Perl regex, so $USER@host should match \bjleechan\b.
```

## When this skill does NOT apply

- **The standard `/advice` Gate-3 substitute** (CodeRabbit + Bugbot + Codex connector all unavailable) — use `~/.hermes/skills/advice/SKILL.md` v1.5.0 §"Verified 2026-07-21", which uses `delegate_task` subagent fan-out. This skill is the deeper fallback when subagents ALSO can't reach different model families.
- **In-session code review** without multi-model coverage expectation — use `code-review` skill directly.
- **Evidence bundle integrity** (checksum / SHA / real-service proof) — use `evidence-standards` skill.
- **Triage plan review** that needs external validation — escalate to user, don't fall back silently.

## Related

- `~/.claude/skills/web-advice/SKILL.md` — the canonical web-advice skill (user-owned); covers 1-of-3 and 2-of-3 graceful degradation, but does NOT explicitly cover 0-of-3.
- `~/.hermes/skills/advice/SKILL.md` — the canonical /advice skill (user-owned); has the `/advice` Gate-3 substitute recipe for when subagent fan-out works.
- `~/.hermes/skills/workflow/drive-pr-to-green/SKILL.md` v2.5.9 — the `/advice` Gate-3 substitute applied to drive-pr-to-green (verified PR #407).
- `~/.hermes/skills/software-development/code-review/SKILL.md` — code-review checklist for when an inline review is needed without multi-model fan-out.

## Changelog

- **1.0.0 (2026-08-01):** Initial authoring. Verified on jleechanorg/claude-commands PR #346 (cmux-resume-watchdog skill export, head `2b867afb`). Found 2 blocking bugs (sentinel leak at `test_cmux_resume_watchdog.py:306`, filter drift in single-file SKILL) via local-evidence review after 0-of-3 web LLM coverage failed. PR comment posted at https://github.com/jleechanorg/claude-commands/pull/346#issuecomment-5153420084.