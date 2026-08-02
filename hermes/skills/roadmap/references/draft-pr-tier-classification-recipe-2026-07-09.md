# Draft-PR tier classification — verified Python recipe (2026-07-09 01:05Z)

**Problem:** the /roadmap § B "PR Auto-Merge Candidates" classification trap. Title keywords (`ci:`, `docs:`, `chore(`, `feat(observability)`) are NOT authoritative for tier. Verified n=51 on 2026-07-09 01:05Z: title-keyword "non-prod" guess → actual 14 strict-non-prod + 37 PROD after file-path audit.

**Authoritative classifier:** project's `PROD_PATH_PREFIXES` tuple — for $GITHUB_REPOSITORY this is:

```python
PROD_PATH_PREFIXES = (
    '$PROJECT_ROOT/',                     # backend + frontend v1/v2 + tests excluded below
    'testing_mcp/', 'testing_ui/',
    'prompts/',
    '$PROJECT_ROOT/frontend_v1/', '$PROJECT_ROOT/frontend_v2/',
)
# Exceptions (PROD path BUT non-production-only if ALL files match):
NON_PROD_TEST_PREFIXES = (
    '$PROJECT_ROOT/tests/', '$PROJECT_ROOT/test_integration/',
)
```

A PR is PROD if ANY file path starts with one of the `PROD_PATH_PREFIXES` AND that file is not under `NON_PROD_TEST_PREFIXES`. All other PRs (scripts/, docs/, .github/workflows/, roadmap/, .beads/, top-level tests/) are NON-PROD.

## Verified recipe (n=51, runtime ~30s, ghub REST via `gh api`)

```python
import json, subprocess

# 1. Get every open draft PR's number — REST pagination, NOT `gh pr list`
drafts = subprocess.run([
    'gh', 'api', 'repos/OWNER/REPO/pulls?state=open&per_page=100',
    '--jq', '.[] | select(.draft==true) | .number'
], capture_output=True, text=True).stdout
draft_nums = [int(x) for x in drafts.strip().split('\n') if x.strip()]

# 2. Per-PR file-path audit
results = []
for n in draft_nums:
    r = subprocess.run([
        'gh', 'pr', 'view', str(n), '--repo', 'OWNER/REPO',
        '--json', 'number,title,files,updatedAt,mergeable,isDraft'
    ], capture_output=True, text=True)
    d = json.loads(r.stdout)
    files = [f['path'] for f in d.get('files', [])]

    prod = False
    for fp in files:
        # Strip the test-subdir exception first
        if any(fp.startswith(p) for p in NON_PROD_TEST_PREFIXES):
            continue
        if any(fp.startswith(p) for p in PROD_PATH_PREFIXES):
            prod = True
            break

    results.append({
        'number': n, 'title': d['title'],
        'tier': 'PROD' if prod else 'NON-PROD',
        'files': files, 'file_count': len(files),
        'mergeable': d.get('mergeable', '?'),
        'updated': d.get('updatedAt', '')[:10],
    })

# 3. Bucket for the green-merge candidate list
green_ready   = [r for r in results if r['mergeable'] == 'MERGEABLE' and r['tier'] == 'NON-PROD']
conflicting   = [r for r in results if r['mergeable'] == 'CONFLICTING']
oversize      = [r for r in results if r['file_count'] >= 50]   # split candidates
needs_evidence = [r for r in results if r['mergeable'] == 'MERGEABLE' and r['tier'] == 'PROD']

print(f"PROD drafts: {sum(1 for r in results if r['tier']=='PROD')}")
print(f"NON-PROD drafts: {sum(1 for r in results if r['tier']=='NON-PROD')}")
print(f"Green-ready: {len(green_ready)} | Conflicting: {len(conflicting)} | Oversize: {len(oversize)}")
```

## Pitfalls (verified live)

- **REST > `gh pr list` for full draft count.** `gh pr list --state open --json number,isDraft --jq '[.[] | select(.isDraft==true)] | length'` truncated at 11 for n=51 on 2026-07-09 01:05Z; `gh api 'repos/OWNER/REPO/pulls?state=open&per_page=100' --jq '[.[] | select(.draft==true)] | length'` returned 51 (full). Always verify draft count via BOTH paths before posting; if they disagree, the higher is correct.

- **`gh pr view --json mergeable` may return `null`** when GitHub hasn't computed mergeability yet (cold state). Wait 30s and re-poll, or proceed with `unknown` and re-check before any green-merge call. Verified 2026-07-09 01:05Z: all 27 WA non-draft OPEN PRs returned `mergeable: null` on first poll; `mergeable: "MERGEABLE" | "CONFLICTING"` from the prior `gh pr list --json mergeable` was the authoritative state.

- **Test-file exception is critical.** Without `(fp not in $PROJECT_ROOT/tests/ AND fp not in $PROJECT_ROOT/test_integration/)` carve-out, EVERY PR that adds a test under `$PROJECT_ROOT/tests/` would be classified PROD and excluded from green-merge — false negative. WA has `$PROJECT_ROOT/tests/` and `$PROJECT_ROOT/test_integration/` as the canonical test subdirs; verify against the target repo's `AGENTS.md` "Project Structure" section before running.

- **Production-tier PRs still need full /es evidence.** A MERGEABLE+PROD draft is NOT a green-merge candidate — per AGENTS.md "Any non-test change under `$PROJECT_ROOT/` requires `/es` evidence before the work is complete." The recipe outputs `needs_evidence` so the report's § D can route them to `ao spawn` for 7-green drive, NOT batch-merge.

- **Oversize PRs (≥50 files) are split candidates.** Verified 2026-07-09 01:05Z: PR #7952 (96 files), #7979 (100 files), #7936 (100 files), #8004 (51 files). Close-as-split-then-reopen is the recommended action; verify with the operator before closing.

- **Tier classification must run BEFORE writing the Slack reply.** Don't post a count, then re-classify, then post a correction. Run the loop first, post the right numbers once.

## Related skill changes

- `pr-triage-and-next-steps` (sibling skill in `github/` category) carries the same recipe in its `## Tier classification` section. Both skills reference this file. Apply the recipe regardless of which skill surfaces the "triage the drafts" ask — `roadmap` covers the recurring sweep + report; `pr-triage-and-next-steps` covers on-demand cross-repo pulls.

- The 2026-07-07 trap (32-PR sweep) is the original observation; the 2026-07-09 verification at n=51 + the explicit single-PR counter-example (#8066) makes this durable: title-keyword tier classification is unreliable at every size.

## File path

`~/.hermes/skills/roadmap/references/draft-pr-tier-classification-recipe-2026-07-09.md` (canonical)
`~/.hermes_prod/skills/roadmap/references/draft-pr-tier-classification-recipe-2026-07-09.md` (after `deploy.sh`)