---
name: code-review
description: Guidelines for performing thorough code reviews with security and quality focus
---

# Code Review Skill

Use this skill when reviewing code changes, pull requests, or auditing existing code.

## Review Checklist

### 1. Security First
- [ ] No hardcoded secrets, API keys, or credentials
- [ ] Input validation on all user-provided data
- [ ] SQL queries use parameterized statements (no string concatenation)
- [ ] File operations validate paths (no path traversal)
- [ ] Authentication/authorization checks present where needed

### 2. Error Handling
- [ ] All external calls (API, DB, file) have try/catch
- [ ] Errors are logged with context (but no sensitive data)
- [ ] User-facing errors are helpful but don't leak internals
- [ ] Resources are cleaned up in finally blocks or context managers

### 3. Code Quality
- [ ] Functions do one thing and are reasonably sized (<50 lines ideal)
- [ ] Variable names are descriptive (no single letters except loops)
- [ ] No commented-out code left behind
- [ ] Complex logic has explanatory comments
- [ ] No duplicate code (DRY principle)

### 4. Testing Considerations
- [ ] Edge cases handled (empty inputs, nulls, boundaries)
- [ ] Happy path and error paths both work
- [ ] New code has corresponding tests (if test suite exists)

## Review Response Format

When providing review feedback, structure it as:

```
## Summary
[1-2 sentence overall assessment]

## Critical Issues (Must Fix)
- Issue 1: [description + suggested fix]
- Issue 2: ...

## Suggestions (Nice to Have)
- Suggestion 1: [description]

## Questions
- [Any clarifying questions about intent]
```

## Common Patterns to Flag

### Python
```python
# Bad: SQL injection risk
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# Good: Parameterized query
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

### JavaScript
```javascript
// Bad: XSS risk
element.innerHTML = userInput;

// Good: Safe text content
element.textContent = userInput;
```

## Tone Guidelines

- Be constructive, not critical
- Explain *why* something is an issue, not just *what*
- Offer solutions, not just problems
- Acknowledge good patterns you see

## Reviewing a PR whose head has advanced past prior reviews

When asked to "review PR #N" and the PR has prior review comments, **the head SHA in your context is stale the moment you start reading**. PRs are typically green-lit only after several fix-up commits land — and the new head may have introduced *new* findings, re-introduced *old* ones, or even fixed them silently. Re-derive state from the live remote every time:

```bash
# 1. Get current head and the FULL commit list
gh pr view N --repo OWNER/REPO --json headRefName,headRefOid,commits,statusCheckRollup

# 2. Read the diff against origin/main (NOT against the previously-reviewed head)
gh pr diff N --repo OWNER/REPO

# 3. Pull every review-thread state (resolved/outdated/inline path:line)
gh api -H "Accept: application/vnd.github+json" graphql -f query='
  query {
    repository(owner:"OWNER", name:"REPO") {
      pullRequest(number: N) {
        reviewThreads(last: 50) {
          nodes { isResolved isOutdated
                  comments(first:1) { nodes { author { login } path line body createdAt } } }
        }
        comments(last: 30) { nodes { author { login } createdAt body } }
      }
    }
  }
'
```

### Three pitfalls that fire specifically on re-review

**Pitfall A — Bugbot's `resolved=True` is not ground truth.** Bugbot's review-threads API exposes an `isResolved` flag that auto-flips to `true` when Bugbot re-runs against a new head without finding a *new* finding to attach. That does NOT mean the underlying issue was fixed — it can mean "Bugbot didn't have anything new to say". **Re-derive the operational behavior from the source** at every review. If a prior Hermes review said "this loop early-returns and skips command #2", grep for the early-return on the new head — don't trust the green thread.

**Pitfall B — "moved the bug down the stack" regression.** A common fix pattern is to replace a `return Ok(true)` short-circuit with a more thorough check (e.g. health-verify after success). The fix can accidentally preserve the *structural* bug — the early-return path now fires *one layer deeper*, where the new check returns false and the same short-circuit kicks in. Detection heuristic: for every Bugbot/P1 finding marked `resolved=True`, grep the new head for the *exact line* the prior review flagged and confirm the operational behavior is genuinely different. If the only change is "the early-return is now wrapped in `if !health_check { return Ok(false) }`", the bug is unchanged.

**Pitfall C — Findings posted in the same minute as the prior review.** If Bugbot posted new inline findings at `T-15s` and the prior Hermes review went up at `T+10s`, the review didn't see them. Always check timestamps of issue-level comments vs. review-thread `createdAt` before crediting "all known findings addressed". A common pattern is a multi-bot re-review storm at `T-2min..T+1min` against a freshly-pushed head; the prior human-visible review can lag the bot batch.

## Pitfalls

- **CodeRabbit "Review limit reached" auto-comment is noise.** The body is a generic fair-use policy template (`<!-- rate limited by coderabbit.ai -->`), not a finding. Skip it in the review-status table; only surface reviews with substantive bodies.
- **Don't recommend `gh pr merge` from inline review.** Per `~/.claude/CLAUDE.md` "Merge safety", merging a PR requires `MERGE APPROVED` in the *most recent live user message*. Code-review verdicts (`✅ approve`, `LGTM`) are NEVER merge authorization. Always end with "Pending — needs your PR review + merge to apply".
- **Don't post a duplicate review when one already exists.** Check the PR's issue-level comments for prior `Hermes Review —` posts. If a prior review exists at an older head, either: (a) post a *delta* review explicitly scoped to "what changed since `OLDHEAD`", or (b) ask the user "do you want me to repeat the full review against the new head, or just diff against the prior one?" before posting.
- **Don't count unit-only evidence as production-grade.** Per the env-preferences rule, claims backed only by mocked unit tests are insufficient for production paths that use real external services (LLM, network, docker). Always ask "is there an integration test, or a local-run command, that exercises the real callcall?" before accepting "tests pass" as proof.
- **Don't fabricate Bugbot's finding body.** When Bugbot posts a `<!-- BUGBOT_REVIEW -->` placeholder without inline diffs (e.g. dark-factory PR #248 cursor[bot] review at 01:10:51Z), the body is unreadable via GitHub API. Say so explicitly and recommend fetching via the Cursor IDE link in the placeholder — never paraphrase what Bugbot "probably meant".
- **Don't write a substring test for a multi-token contract — assert the full contract (added 2026-07-13, your-project.com PR #8381 CodeRabbit 1st review).** When a production probe / diagnostic / config string is a concatenation of N items (e.g. the 7-dep precompute probe `fastembed, numpy, google.cloud.storage, jsonschema, pydantic, cachetools, flask`), the test that pins the contract MUST assert ALL N items are present — not just the first 6, not a substring of the first item, not a regex on the bare prefix. The verified bug case: my v1 tests for `tests/test_precompute_deps_self_hosted.py::TestDeployShProbeNoMvpSiteAgentPrompts` asserted only that the substring `"fastembed+numpy+google-cloud-storage+jsonschema+pydantic+cachetools"` (6 deps) was present in the deploy.sh `_EMBED_PROBE` variable. They passed when the v2 fix introduced the new `_EMBED_PROBE='...6 deps...'` value via copy-paste (forgetting flask). CodeRabbit caught the real bug — deploy.sh `_EMBED_PROBE` was missing flask even though `action.yml`'s `install-deps` now installed it. The test gap let the copy-paste bug ship. **Two rules to apply:**

  1. **One assertion per item, every time.** Instead of `assertIn("a+b+c", contract)`, write `for item in [a, b, c]: assertIn(item, contract)`. The loop pattern costs 3 lines vs 1 but catches the missing-prefix bug class.
  2. **Pin the contract's exact dep-list at the test file's module level** (`EXPECTED_DEPS = ("fastembed", "numpy", "google.cloud.storage", "jsonschema", "pydantic", "cachetools", "flask")`). Loop over it. When a future dep is added, the test file changes in one obvious place — not three.

  Anti-pattern (the one that shipped): `assertIn("fastembed+numpy+google-cloud-storage+jsonschema+pydantic+cachetools", probe_value)` — passes whether the contract is the 6-dep version OR the 7-dep version. The assertion only proves "the 6-dep prefix is present," which is true for both. This is the same family as the same-name test dismissal anti-pattern — substring matches that survive contract changes are silently-permissive assertions.

  Companion: `~/.hermes/skills/qa-test-failure-dismissal-anti-pattern/SKILL.md` for the same-name dismissal rules (don't blanket-allow a test that survived a contract change without inspecting the new contract).
