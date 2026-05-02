---
name: evidence-review
description: Enforcement rules for reviewing evidence artifacts against the evidence-standards skill. Invoked by /er. Produces PASS / PARTIAL / FAIL verdicts.
---

# Evidence Review Skill

**Purpose**: Review evidence for a claim, a path, or a PR. Produce a PASS / PARTIAL / FAIL verdict with specific artifact-level citations. This skill is the enforcement layer for the `evidence-standards` skill (the "what to produce") — this file is the "how to judge it".

**Invoked by**: `/er [subject or path]`

**Standards source**: `evidence-standards` skill (`/es`). When in doubt about a requirement, read the standards first.

---

## Verdict Rubric

| Verdict | Meaning |
|---------|---------|
| **PASS** | Every claim has a matching artifact of STRONG quality and every mandatory check below passes. |
| **PARTIAL** | Claims are supported but one or more mandatory checks fail or soft-warn (e.g., WARN in verification_report.json, missing downloadable MP4). A PR at PARTIAL is not merge-ready. |
| **FAIL** | A claim is contradicted by an artifact, or integrity is broken (sha256 mismatch, dirty capture producing the claim, scope exclusion). |
| **INCONCLUSIVE** | Not enough artifact data exists to decide. Request more. |

---

## Mandatory Pre-PASS Checks (all must pass)

### 1. Bundle integrity

Evidence bundles use one of two checksum modes (declared in `metadata.json` → `checksum_mode`):

- **`bundle_checksum`**: a single top-level `checksums.sha256` file lists every tracked artifact
- **`per_file_checksums`**: each artifact has its own sibling `<file>.sha256`

Detect the mode, then verify accordingly. If `metadata.json` is absent or silent, infer: top-level `checksums.sha256` → `bundle_checksum`; otherwise fall back to per-file.

```bash
cd <bundle_dir>
if [ -f checksums.sha256 ]; then
  sha256sum -c checksums.sha256
else
  # per_file_checksums mode — verify each sibling .sha256
  find . -name '*.sha256' -exec sh -c 'd=$(dirname "$1") && b=$(basename "$1") && (cd "$d" && sha256sum -c "$b")' _ {} \;
fi
```

- Any mismatch → **FAIL** (the bundle is tampered or stale; treat as a hard integrity failure, not just PARTIAL)
- Also verify the manifest or per-file checksums cover every file referenced by the claim map — a missing entry is a **FAIL**
- The `INVALID` label may be used per-artifact in the claim map (Phase 2 below) to mark contradicted or corrupted individual artifacts, but the **overall verdict vocabulary stays `PASS | PARTIAL | FAIL | INCONCLUSIVE`**

### 2. Verification report ceiling (when applicable)

`verification_report.json` is **optional** — it is produced by bundles that went through an explicit verifier pass, but is not required by `evidence-standards`. Treat its presence as a ceiling constraint, not a prerequisite:

```bash
[ -f verification_report.json ] && jq -r '.overall_verdict' verification_report.json
```

- File absent → **not applicable**, continue with the other checks (do NOT downgrade to PARTIAL on this alone)
- File present, `PASS` → proceed
- File present, `WARN` → verdict ceiling is **PARTIAL** (never promote WARN to PASS without resolving each recorded violation)
- File present, other value → note the value and treat as PARTIAL pending clarification

### 3. Scope note consistency

```bash
grep -A10 "Scope note" README.md
```

- If the scope note explicitly excludes a domain the PR claim covers (e.g. "browser layer out of scope") → narrow verdict to in-scope claims only
- If the scope note has been updated to include a domain, verify the matching artifact exists

### 4. Video artifacts — BOTH types required for non-trivial PRs

**Tmux / Terminal video** (required for any code change, test run, deploy):
- [ ] **GIF** embedded inline in PR description (renders on GitHub without clicking)
- [ ] **MP4** linked and directly downloadable from PR description
- [ ] **Caption** naming: test name, pass/fail result, key assertion

**Browser UI video** (required when PR adds or modifies any `testing_ui/test_*.py` file):
- [ ] **GIF** embedded inline in PR description
- [ ] **MP4** linked and directly downloadable
- [ ] **Caption** naming: URL, user actions, before/after behavior

If ANY of the above is missing → verdict is **PARTIAL** (not PASS), regardless of other evidence quality.

### 5. Public-URL hosting check

GIFs and MP4s must be on a **public** repository — private repo release assets return 404 for anonymous viewers and do NOT render as inline images in PR descriptions.

```bash
# For each <owner>/<repo> hosting a video asset:
gh api repos/<owner>/<repo> --jq '.private'
# Must be: false
```

```bash
# And verify the asset itself is uploaded and accessible:
gh api repos/<owner>/<repo>/releases/tags/<tag> \
  --jq '.assets[] | {name: .name, state: .state}'
# All states must be "uploaded"
```

Private repo assets = **PARTIAL / FAIL** for inline rendering.

### 6. Self-contained / clean-computer reproducibility

A PASS verdict requires the PR to meet the "clean computer" standard from `evidence-standards`:

- [ ] PR description links a **gist** with reproduction instructions
- [ ] Gist contains `git clone <url>` + `git checkout <branch>`
- [ ] Gist lists dependencies (Python version, pip requirements, service account needs)
- [ ] Gist has exact test invocation commands (copy-pasteable into a terminal)
- [ ] Gist documents expected output (pass counts, scenario names)
- [ ] Gist embeds or links the GIF + downloadable MP4

**Failure mode**: if the only instructions are "see the repo" or "run the tests" without exact commands → PARTIAL.

---

## Review Procedure

### Phase 1 — Inventory

1. Enumerate all artifacts referenced by the subject (bundle dir, PR description, run.json, metadata.json, gist, release assets)
2. Enumerate all claims (from PR description, commit messages, or user-provided claim list)

### Phase 2 — Claim-to-Artifact Mapping

For each claim, identify the single primary artifact that proves it. Rate quality:

| Quality | Meaning |
|---------|---------|
| **STRONG** | Claim directly observable in a raw artifact (log line, screenshot frame, test output, sha256-verified file) |
| **WEAK** | Claim is indirect — derived from self-reporting (evidence.md, summary.md) without raw backing |
| **MISSING** | No artifact supports the claim |
| **INVALID** | An artifact exists but contradicts the claim, or fails integrity check |

### Phase 3 — Mandatory Checks

Run all six checks in the "Mandatory Pre-PASS Checks" section above. Record the result of each.

### Phase 4 — Verdict Table

Produce output in this format:

```
## Evidence Review Verdict

**Subject**: <what was reviewed>
**Bundle**: <path>
**Overall**: PASS | PARTIAL | FAIL | INCONCLUSIVE
**Confidence**: HIGH | MEDIUM | LOW

### Claim Map
| # | Claim | Artifact | Quality | Notes |
|---|-------|----------|---------|-------|
| 1 | ...   | run.json | STRONG  | Line 42 shows ...|
| 2 | ...   | (none)   | MISSING | No artifact found |

### Mandatory Checks
- [x] sha256sum -c → 38/38 OK
- [x] verification_report.json overall_verdict = PASS
- [x] Scope note matches claimed domain
- [x] Terminal GIF + MP4 + caption present
- [ ] Browser UI GIF: 404 — private repo hosting (→ PARTIAL)
- [x] Gist has clone + test commands

### Violations
1. <specific evidence item that fails>

### Accepted Exceptions
1. <with rationale from verification_report.json>

### Recommendations
1. <non-blocking suggestions for future bundles>
```

---

## Anti-Patterns to Reject

- **Self-referencing claims**: `evidence.md` cites itself instead of raw artifacts → WEAK
- **Circular provenance**: the bypass gate reads the reference file it's supposed to match against → INVALID
- **Evidence committed but not linked**: bundle in `evidence/` but PR description has no gist/release link → PR fails "clean computer" check
- **Private repo release as inline image**: GitHub won't proxy it → broken GIF → PARTIAL
- **"Native video attachment"** (drag & drop into PR comment): not directly downloadable via URL → PARTIAL
- **Screenshot instead of GIF for a flow claim**: cannot show before/action/after → FAIL
- **`echo "PASS"` in terminal video instead of real test runner output**: hard block → FAIL
- **Pre/post git SHA mismatch** in terminal video: test was run against a different commit than claimed → FAIL

---

## Historical Lessons (keep the bar high)

- **2026-04-11 PR #6161**: GIFs hosted on private `worldarchitect.ai` release returned 404. Moved to public `agent-orchestrator` release. → Added mandatory check 5.
- **Pre-existing**: dirty GREEN captures (working tree dirty during the run that produced the artifact) require explicit exception in `verification_report.json` with rationale.
- **Pre-existing**: WARN verdict in `verification_report.json` is a ceiling — never promote to PASS without resolving each recorded violation.
