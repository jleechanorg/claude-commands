---
name: credential-discipline
description: Example/seed/fixture files must use placeholders not real credentials. Pre-commit grep check + enforcement hooks.
---

## Rule: examples, seeds, and test fixtures must use placeholders, not real values.

### What counts as an example

Any file under: `examples/`, `seed/`, `seed_data/`, `test_data/`, `fixtures/`, `mocks/`
Or filename contains: `example`, `seed`, `fixture`, `mock`, or `sample`

### Required placeholder scheme

| Real | Placeholder |
|---|---|
| `AIzaSy...` (Firebase API key) | `<your-firebase-api-key>` |
| `cntvDfj7cGUhUFkxcmV3` (campaign ID) | `<your-campaign-id>` |
| `0wf6sCREyLcgynidU5LjyZEfm7D2` (Firebase UID) | `<your-firebase-uid>` |
| `<your-email@gmail.com>` (test email) | `<your-test-user>@example.com` |
| `worldarchitecture-ai` (GCP project) | `<your-firebase-project-id>` |
| Any other identifier | `<your-<descriptor>>` |

### Before-commit checklist

```bash
grep -rnE 'AIza[A-Za-z0-9_-]{35}|cntvDfj7cGUhUFkxcmV3|L5iB5eWq8TyzQW3qFDDv|z7eDk3NzY1mB6BTm23yu|Z2sEA1hQW3YJbyQHvvt6|XHWCpllzfKNgwf6o1Jvc|zheWLda5wsDVQTdXrRFm|0wf6sCREyLcgynidU5LjyZEfm7D2|<your-email@gmail.com>|worldarchitecture-ai|worldai-prod-c4977' examples/ 2>&1
```

### Enforcement

- **Pre-commit hook:** `~/.claude/hooks/pre-commit-git-identity-example-com-guard.sh` blocks commits by `@example.com`.
- **Per-repo test:** `tests/test_example_placeholder_discipline.sh` in CI for browserclaw and jleechanclaw.
- **Per-repo hook:** `.githooks/pre-commit` chains identity guard + discipline test on staged `examples/**`.

### Why

3 real production credential leaks landed in public repos between 2026-02 and 2026-04 (commits `3aac8fe8`, `45836c8`). `.gitleaksignore` is suppression, not a fix — rotate keys + rewrite history.

**If example needs real credential:** move to private repo, parameterize via env var, or use Firebase Emulator.
