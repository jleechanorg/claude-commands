# Sanitization checklist for public examples

Drop this section at the bottom of any file you publish as a public
example derived from a working personal file. It makes the publishing
workflow reproducible — anyone forking your example can apply the same
recipe.

## What to keep

- [ ] Universal rules (zero-framework cognition, large-file read
      discipline, proactive issue creation, model routing, force-push
      safety, merge safety, time-boxing).
- [ ] File structure and section ordering.
- [ ] Voice and rule shape.
- [ ] A placeholder scheme (`<PLACEHOLDER>`) — keeps the example
      useful as a fill-in-the-blank template.

## What to remove

- [ ] Personal paths (`~/...`, machine names).
- [ ] User identifiers (real name, handles, machine hostnames).
- [ ] GitHub org names that imply private infrastructure.
- [ ] Internal tool / CLI names (`agento`, `ao spawn`, `vpython`,
      `mcp_mail`, custom bashrc wrappers like `claudem`/`claudeg`).
- [ ] Slack / Discord channel IDs (searchable on public archives).
- [ ] PR / issue / bead numbers pointing to private work.
- [ ] Memory / feedback file references with session-local evidence.
- [ ] OAuth token names, keychain service names, env var names that
      imply private credentials.

## What to verify

- [ ] Run `grep -niE '$USER|jeffrey|<your-org>|<your-cli>' <file>`
      against the sanitized file — must return 0 matches.
- [ ] Run `grep -cE '<[A-Z_0-9]+>' <file>` — must return >0 if you
      used the structure+placeholder flavor.
- [ ] Run `git diff --stat origin/main..HEAD` — must show only the
      files you intentionally added.
- [ ] Run `git log --oneline origin/main..HEAD` — must show only
      commits matching the PR's stated scope.
- [ ] The pre-push secret-guard hook will scan automatically when
      you push; do not bypass it.

## Pre-push command sequence

```bash
# Verify the file is leak-free
./scripts/verify-no-personal-leaks.sh <sanitized-file>

# Verify the diff is clean
git log --oneline origin/main..HEAD
git diff --stat origin/main..HEAD

# Push (secret-guard runs automatically)
git push -u origin <branch>
```

## See also

- `~/.claude/skills/sanitize-personal-content-for-public-publishing/SKILL.md`
  — full workflow (clarify upfront → leak inventory → write →
  verify → ship).