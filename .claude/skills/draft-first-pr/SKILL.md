---
name: draft-first-pr
description: "Lifecycle contract for opening PRs, driving them green, and fixing CI. Triggers on: opening a PR, driving a PR to green, fixing CI on a PR, /green, /es, /er, /advice on a PR."
metadata:
  type: policy
---

# Draft-First PR Policy

## Retained review integrations

The shared catalog preserves host-installed `/advice` and `/web-advice` integrations instead of installing them. Before invoking either, resolve its `../advice/SKILL.md` or `../web-advice/SKILL.md` relative to this package and read the existing skill. For a remote invocation, check the corresponding skill on the target host. If absent, report that integration as `UNAVAILABLE` and identify the missing package; do not invent a replacement runner, claim an approval, or treat a required gate as passed. Continue independent authorized work, but leave any dependent readiness or plan-approval gate unmet. Existing review quorum, external-disclosure authorization, and optional-review rules still apply.


**Every new PR is opened as DRAFT** (`gh pr create --draft`) and stays draft until quality is proven. Flipping to ready-for-review is a deliberate, gated action — not a side effect of pushing code.

## Canonical lifecycle

This is the full state machine — every other file (`pr-green-definition`, `/green`, `CLAUDE.md`, `AGENTS.md`) points here rather than restating it:

```
DRAFT
  → /es PASS @ SHA
  → /er PASS @ SHA (unless the narrow /er documentation allowlist or a repo-exempted class applies)
  → /advice APPROVED @ SHA when required by Advice applicability below
  → mark ready-for-review (gh pr ready <N>)
  → /ready work: /green, comments, conflicts, and regression checks
  → final /er PASS @ current HEAD when applicable
  → final /advice APPROVED @ current HEAD when required
  → READY
  → separate merge authorization: explicit human "MERGE APPROVED" (case-insensitive)
    in the most recent live user message
```

Each arrow is a gate, not a formality — do not skip ahead, and do not treat an earlier gate's pass as still valid once HEAD has moved (see "SHA-binding rule" below).

## Advice applicability

`/advice` is optional for every PR under 50 changed lines, at both the draft and
final ready-review phases. A PR with 50 or more changed lines requires `/advice`
at both phases. A specifically requested review still runs. This size rule
supersedes broader docs/test/non-production `/advice` exemptions; it does not
waive independent safety/code review, security, evidence, CI, or merge authorization.
High-risk changes retain their required independent coverage even when `/advice`
itself is optional. Initial gate applicability and later re-review depth are
separate decisions.

For a high-risk change with optional `/advice`, follow the repository's required
independent code/safety lane. If none is named, require a named independent
full-diff code/safety reviewer (not the author or orchestrator) to inspect the
risk controls and record exact SHA, complete coverage, findings, and verdict.
Evidence-only review does not satisfy this code-review gate. Preserve stricter
repository lanes and quorums; this fallback does not make `/advice` mandatory
for an under-50 PR.

Count additions + deletions in the complete PR diff at the live head against its
actual base, including all production and non-production files, not net lines or
production-only lines. Use complete GitHub PR totals or the equivalent verified
base...head Git diff; record both refs and the count. An unknown or incomplete
count does not qualify, nor may uncounted binary changes establish the exception.
Recompute after a head or base change; do not use only the latest commit's size.
Examples: +25/-24 = 49: optional; +25/-25 = 50: required;
+10/-0 code and +40/-0 docs = 50: required.

`/wa` (`/web-advice`) is optional, never an implicit lifecycle gate. Run it only
when requested or separately authorized; preserve its real verdict if it runs.
Neither optional review permits ignoring a known correctness or safety blocker.

## Coding lifecycle (pre-draft work) — scale layers to risk

Order: explore → outcome spec (no code) → code-level design when useful → TDD
(fresh failing test first) → unit + relevant integration tests → coder
correctness checkpoint → formal code/evidence review → narrow fixes until a
genuine human dependency. Batch findings, preserve passing lanes, and recheck
only the affected behavior.

| Change class | Layers |
|---|---|
| Wording-only / small low-risk (including a small code fix) | Skip standalone spec, plan, and plan-review cycle; focused tests, then the applicable gates below. Runtime change or file count alone does not make a change non-small. |
| Ordinary feature | Outcome spec, TDD, unit + relevant tests, correctness checkpoint, then formal review. |
| Cross-service boundary | Add an integration-layer test; a mocked unit test cannot prove it. |
| Large change | May pause at the correctness checkpoint for human direction before expensive review (optional, never a gate). |
| High-risk (security, data-integrity, permission, deployment, approval, merge, destructive, credential) | No layer skipping except the explicit Advice applicability rule; independent final coverage and all other required gates still apply. |

**Mandatory regardless of class:** gates the user explicitly required;
high-risk, security, data-integrity, permission, deployment, approval, merge,
destructive, and credential gates; and real proof for any production-behavior claim. **Skippable by class:**
standalone spec/plan, plan-review cycle, history mining, and extra review lanes
for small low-risk changes, including small code fixes. A standalone plan review
applies only to high-risk or user-required cases, or an unresolved material
decision. Skill pipelines (`write-goal`, `ironclad`, `ready`) delegate
applicability and review timing here; none may apply universally.

Run a direct causal reproducer early; cheap real smoke may catch a wrong target.
Collect expensive final evidence once relevant code and checks have stabilized.
Do not wait for green to diagnose a failed test. Diagnose existing failures and
batch fixes before paid capture; apply the documented local-equivalent exception
for backlogged checks, never label a failed or unproven check as passed.

Freeze means a coordinated candidate SHA with the executing owners, not a branch
lock. It does not authorize resets, history rewrites, or discarded work. After a
necessary fix, agree the new candidate and revalidate the affected claims.

**Execution handoff invariant.** An accepted next step must have an executing
owner or started tool before reporting `Working`. With only an exact blocker plus
resumption trigger, report `Blocked` or `Waiting` — a blocker never makes it
`Working`. Creating a goal or checklist is not execution. Do not stop
at a completed design when implementation was authorized.

## Draft-phase final acceptance gates (in order)

Before this final sequence, run independent code-correctness reviews (including
/advice reviewers) and cheap focused checks in parallel when resources permit.
Resolve or explicitly defer their findings, batch fixes, and freeze the code
before expensive evidence. Reviewers may finish code inspection early; final
approval must account for the finished evidence and exact current SHA. Do not
run expensive evidence while known code-correctness work remains unfinished.

When multiple reviews are requested, use one frozen candidate/base and one
shared factual scope and defect inventory; shared inputs do not replace each
review's independent judgment. Run independent review groups concurrently
where transport and resource rules permit; each review covers the entire
declared change, while focus lanes supplement rather than replace approval.
Collect current findings in one batch. After repeated same-cause
findings, inspect the shared representation before another local patch. Do not
invent additional approval gates; existing approvals remain workflow-specific.
Final evidence stays last; when evidence is in the declared review scope, the
same independent reviewers must inspect it and reaffirm at the finished HEAD. A
same-HEAD finished code review can account for unchanged code without blindly
rereading it; the orchestrator cannot promote an earlier review alone.

While a PR is draft, accept these final gates, where applicable, in sequence — do not skip any applicable gate:

A repository's own instructions (for example its `AGENTS.md` coding lifecycle)
may exempt defined low-risk classes, such as docs-only, test-only, or small
non-production changes, from `/er`; when they do, follow that
classification and its exclusions. The narrow documentation allowlist below is
the default when the repo defines none. No `/er` exemption covers changes to approval,
merge, review, evidence, or security rules, or to security, permission,
credential, or merge-path code.

1. **`/es`** — evidence bundle passes (real evidence per `~/.claude/skills/evidence-standards/SKILL.md` + repo-specific extensions), verified at the PR's current HEAD SHA.
2. **`/er`** — for every PR except the documentation-only class below or a repo-exempted class, evidence review verdict is PASS (not PARTIAL/FAIL/INCONCLUSIVE), verified at the same current HEAD SHA — re-run if `/es` was earned at an older SHA.
3. **`/advice`** — second-opinion approval on the change itself (`APPROVED at <SHA>` / `NOT APPROVED at <SHA>` / `WITHHELD at <SHA>` — see `~/.claude/skills/advice/SKILL.md`), bound to the same current HEAD SHA, when required by Advice applicability. `WITHHELD` does not satisfy the draft gate.

Only after every applicable gate passes **at the same current SHA**: flip the PR from draft to ready-for-review (`gh pr ready <N>`).

### Documentation-only CI exception

Documentation-only changes, including instruction/skill documentation, do not require CI or waiting for runners. Apply `~/.claude/skills/pr-green-definition/SKILL.md` § Documentation-only CI exception for scope, proportionate local validation, and SHA-bound reporting. That exception is independent of the narrower `/er` allowlist below; it does not remove applicable draft-phase gates, conflict checks, or merge authorization.

### Documentation-only `/er` exception (narrow allowlist)

After `/es`, resolve the PR number (safe fallback `PR_NUMBER=$(gh pr view --json number --jq '.number')` if `<N>` is not known), query the supported pull-request API for the base branch and canonical repository URLs, require exactly one matching Git remote, fetch it, and classify the complete changed-path set against that base. Match the full host and repository path; an owner/repository suffix alone is ambiguous across hosts.

```bash
PR_NUMBER=${1:-$(gh pr view --json number --jq '.number')}
if ! BASE_DATA=$(gh api "repos/{owner}/{repo}/pulls/${PR_NUMBER}" \
  --jq '[.base.ref, .base.repo.clone_url, .base.repo.ssh_url] | @tsv'); then
  echo "Error: could not resolve PR base through the GitHub API" >&2
  exit 1
fi
IFS=$'\t' read -r BASE_BRANCH BASE_CLONE_URL BASE_SSH_URL <<<"$BASE_DATA"
EXPECTED_BASE_DATA="${BASE_BRANCH}"$'\t'"${BASE_CLONE_URL}"$'\t'"${BASE_SSH_URL}"
if [[ "$BASE_DATA" != "$EXPECTED_BASE_DATA" ||
      -z "$BASE_BRANCH" || -z "$BASE_CLONE_URL" || -z "$BASE_SSH_URL" ||
      "$BASE_CLONE_URL" == "null" || "$BASE_SSH_URL" == "null" ]]; then
  echo "Error: GitHub API returned an incomplete PR base" >&2
  exit 1
fi

normalize_repo_url() {
  python3 - "$1" <<'PY'
import re
import sys
from urllib.parse import urlsplit

raw = sys.argv[1].strip().rstrip("/")
scp = re.fullmatch(r"(?:[^@/]+@)?([^:]+):(.+)", raw)
if scp and "://" not in raw:
    normalized = f"{scp.group(1).lower()}/{scp.group(2)}"
elif "://" in raw:
    parsed = urlsplit(raw)
    if parsed.scheme == "file":
        normalized = parsed.path
    elif not parsed.hostname:
        raise SystemExit(1)
    else:
        normalized = f"{parsed.hostname.lower()}/{parsed.path.lstrip('/')}"
else:
    normalized = raw
print(re.sub(r"\.git$", "", normalized.rstrip("/")))
PY
}

if ! BASE_CLONE_ID=$(normalize_repo_url "$BASE_CLONE_URL") ||
   ! BASE_SSH_ID=$(normalize_repo_url "$BASE_SSH_URL"); then
  echo "Error: could not normalize canonical base repository URLs" >&2
  exit 1
fi

MATCHING_REMOTES=()
while IFS= read -r remote; do
  url=$(git config --get "remote.${remote}.url") || continue
  remote_id=$(normalize_repo_url "$url") || continue
  if [[ "$remote_id" == "$BASE_CLONE_ID" || "$remote_id" == "$BASE_SSH_ID" ]]; then
    MATCHING_REMOTES+=("$remote")
  fi
done < <(git remote)

if [[ ${#MATCHING_REMOTES[@]} -ne 1 ]]; then
  echo "Error: expected exactly one remote for '$BASE_CLONE_URL'; found ${#MATCHING_REMOTES[@]}" >&2
  exit 1
fi
BASE_REMOTE=${MATCHING_REMOTES[0]}

git fetch "$BASE_REMOTE" "$BASE_BRANCH"
git diff --name-only "${BASE_REMOTE}/${BASE_BRANCH}...HEAD"
```

For this `/er` exemption, every changed path must be one of:

- `README.md`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `docs/**`

For that class, do not run `/er`. Record
`/er: NOT REQUIRED — documentation-only (<changed paths>)` on the PR, then
continue to `/advice` where Advice applicability requires it. Documentation-only
PRs still require applicable `/es` and current-SHA verdicts, followed by the ready
phase using the documentation-only CI exception and separate merge authorization.

This `/er` exemption is an exact allowlist, not a file-extension heuristic. Changes under
`.claude/**`, `.codex/**`, `.github/**`, prompts, tests, scripts, configuration,
schemas, or source code do not qualify even when the file is Markdown. Any
mixed diff uses the normal `/er` gate.

## Change-impact review and test depth

Initial gate applicability follows the rules above. For a later delta, read the
full change and identify which claims, contracts, assertions, or drivers it can
invalidate before choosing full re-review versus focused reaffirmation. Use
`~/.claude/skills/4layer/SKILL.md` (`/4layer`) and
`~/.claude/skills/testing-layers/SKILL.md`, plus the repository testing-layers
overlay, to select the lowest sufficient layer. Evidence classification (`/es`)
does not by itself require a paid model call or browser run.

| Actual change or claim | Proof and review depth |
|---|---|
| Unrelated prose delta | Read the delta, run relevant checks, and reaffirm unchanged claims; no automatic expensive replay. |
| Small single-file deterministic fix | Fresh causal unit RED/GREEN plus affected regressions can prove the deterministic claim when no external boundary is implicated; focused delta review may suffice. |
| A service boundary, auth, or persistence race | Integration proof crossing the implicated boundary; isolated unit mocks cannot establish the claim. |
| A prompt/schema or model-behavior change | Check assembled inputs deterministically first; run real LLM evidence when lower layers cannot prove the claim or an applicable risk-specific rule requires it. |
| New browser/UI behavior | Real browser proof for browser/UI claims, with required visual evidence. |
| CI config, agent policy, security, shared fixture, or weakened assertion | Review actual effects and rerun dependent proof; non-production labels and small file counts do not establish safety. |

Unit proof does not prove model compliance, auth, persistence races, or browser
behavior. Do not manufacture live proof from mocks or replays. Preserve strict
real-service-only rules inside `testing_mcp/` and `testing_ui/`; use deterministic
layers outside those directories. File count, path category, and line count
alone never decide evidence sufficiency or independent safety-review depth.

## SHA-binding rule (critical — applies to every gate in this chain)

`/es`, `/er`, `/advice`, and `/green` gate verdicts are each earned **at a specific commit SHA** — none of the production-gate verdicts carry forward across a HEAD move. If a new commit lands after a verdict (a nit fix, a rebase, a CI-requested change), that verdict is **STALE** and must be re-earned — or explicitly re-affirmed at the new SHA — before it counts toward the next gate in the chain.

**This is a verdict-binding rule, not an automatic evidence-capture rule.** Apply
the evidence-staleness tolerance in `evidence-standards`: a HEAD change whose
actual delta (not its path category) leaves every tested claim intact does not
require a fresh production-evidence run. The reviewer may re-affirm `/es` at
the new SHA after documenting that delta and the claims checked. A production behavior
change still requires fresh evidence, then fresh SHA-bound `/es`, `/er`, and
`/advice` verdicts.

**Classify by the actual delta and the claim it could invalidate, never by path
category.** Tests, evidence drivers and captures, prompts, contracts, schemas, and
executable skill instructions can change behavior or invalidate proof. Re-affirm only
after reading the delta and documenting why no tested claim, driver, or assertion is
affected; a changed assertion, driver, or behavioral instruction invalidates the
evidence that depends on it.

Preserve the original tested SHA in every artifact. Record current applicability
separately with the actual reviewed delta, affected claims, relevant tests and
results, reviewer, and new SHA; never relabel an old capture as a new run.
A base-only change also requires checking its effect on the diff, advice size,
mergeability, and claims; an unchanged head is not proof of unchanged context.

The verdict rule applies uniformly:

- A stale `/es` PASS does not justify running `/er` against it when `/er` is required.
- A stale `/er` PASS does not justify running `/advice` against it when `/er` is required.
- A stale `/advice` APPROVED does not justify marking the PR ready.
- A stale `/green` does not justify reporting merge-readiness.

Before trusting any prior verdict, compare the SHA it was stamped with against the PR's live head: `gh pr view <N> --json headRefOid --jq '.headRefOid'`. On mismatch, run the staleness-tolerance diff test (read `git diff <verdict-sha> HEAD` against the verdict's claims): a delta that leaves those claims intact lets the verdict be re-affirmed at the new SHA after documenting the diff; a material delta means re-earning the gate. Never carry a verdict forward on memory alone — and never trigger an expensive rerun per finding: batch all pending fixes into one new SHA first (see `evidence-standards` § Evidence Sequencing).

**Chain timing and quality.** The draft chain (`/es` → `/er` → `/advice`) is the FINAL pass: run it after code is complete and all known findings are resolved or deferred (`evidence-standards` § Evidence Sequencing) — not per push while fixes are still landing. Review findings remain subject to the required correctness gates: behavior-blocking findings must be fixed and reverified, while style/nit/doc feedback may be tracked as follow-ups. Batch pending behavioral fixes into one SHA before re-earning affected evidence.

## Ready phase — finish `/ready`, then final reviews

Undrafting starts `/ready`; it does not establish completed readiness. Invoke the
`ready` skill for current-head `/green`, comments, conflicts, and cross-thread
regression checks. Follow `pr-green-definition` for applicable CI, documented
exceptions, and fresh mergeability; do not duplicate those mechanics here.
Keep an already non-draft PR non-draft while completing its open gates.

After ready-phase work stabilizes, perform the final `/er` when applicable, then
one final `/advice` when Advice applicability requires it. These are explicit
closing verdicts, not an automatic copy of draft approvals. At an unchanged
candidate, reviewers may inspect the completed work/receipts and reaffirm prior
coverage without repeating unchanged expensive captures. Required advice keeps
its canonical independent quorum; the orchestrator cannot approve itself.

If a final review requires a fix, batch fixes, rerun affected checks/evidence,
refresh `/green` at the new head, and repeat final `/er` then final `/advice`
where applicable until approved. No cycle-count limit substitutes for finishing;
stop only for a genuine blocker/decision or the governing autonomy deadline.
Report READY only after applicable closing verdicts and current readiness checks
pass. PARTIAL, FAIL, INCONCLUSIVE, WITHHELD, or an unavailable required reviewer
leaves its gate open. READY never supplies merge authorization.

## Review records in the PR description

For every review type that runs, including `/es`, `/er`, `/advice`, `/wa`, `/cs`,
other named lanes and native reviews, update the PR description with the exact
reviewed SHA, review type/phase, verdict or status, gist URL, timestamp, and
reviewer/coverage. Document reviews additionally retain document hashes; their
context SHA does not turn document approval into code approval.

For evidence-gate compatibility, keep one current marker in the PR body:
`**Evidence**: <gist-url> (head <sha>)`, pointing to the authorized sanitized
evidence-review receipt for current applicability. Update that index only;
preserve the historical ledger, receipt URLs, and original capture SHAs.
Underlying raw artifacts may remain private. Missing publication authority or
an inaccessible receipt leaves this marker incomplete; never fabricate its URL.

Publish each completed review's sanitized receipt as a gist only within the
approved disclosure scope. A gist is link-accessible, not private storage; omit
credentials, private source, personal communications, and sensitive artifacts
unless separately authorized. Verify the gist URL and intended reviewer access
before calling publication complete. If tools or permissions prevent publishing,
record `PUBLICATION BLOCKED` with the exact reason and local receipt location;
never invent a gist URL or passing verdict, and do not claim the record complete.

Keep `PENDING`, `UNAVAILABLE`, `FAILED`, and `SUPERSEDED` results visible as well
as approvals. Read the current body before updating it. Use the idempotency key
review type + phase + reviewed SHA + receipt identity; append a new record only
when that key or status is new. Retries with unchanged key and unchanged status
are a no-op. A status transition (including PENDING to PASS with the same receipt)
appends a dated superseding event identifying its prior record; an applicability
change likewise creates a new event without erasing history. Preserve prior rounds and visual
tables. For a moved head, add a current-applicability review and retain the
original tested SHA and capture link, instead of rewriting historical receipts.
Read back the PR body after each update; uncertain writes require readback before
retrying. Optional/skipped reviews are recorded honestly without fabricated gists.

## Slow CI — never block-wait

Documentation-only changes use the CI exception immediately; the ten-minute threshold below applies only to changes that require CI.

For checks queued/pending more than 10 minutes, follow the local-equivalent exception in `~/.claude/skills/pr-green-definition/SKILL.md`: run the workflow's actual command and post current-head proof. Passing local equivalents satisfy Gate 1 for backlogged checks; remote completion is not required for those checks. Failed checks, no-conflict verification, and merge authorization remain separate requirements.

## Rationale

Long-open PRs that skipped straight to chasing CI green (e.g. the level-up auto-PR class) were starved by CI contention — CI capacity is a shared resource, not a private queue. The `ci-value-audit-v2` findings (`green-gate` workflow: 341 hr/wk consumed, 50.7% cancel rate pre-[#8637](https://github.com/$GITHUB_REPOSITORY/pull/8637)) show that driving unproven work through full CI repeatedly is the dominant cost driver. Stabilizing correctness and applicable checks before final expensive capture avoids repeated evidence and review cost without delaying diagnosis of failing CI.

## CodeRabbit/Bugbot — optional advisory reviewers

Neither draft-phase gate above nor `/green` includes CodeRabbit or Bugbot approval. **CodeRabbit/Bugbot: optional advisory reviewers** — read their feedback, take what's useful; never a gate, never a wait, at any phase.

## Merge authorization — unchanged

Merge still requires the literal phrase `MERGE APPROVED` (case-insensitive) from the human in the most recent live message, scoped per-repo per existing policy (e.g. `$GITHUB_REPOSITORY`). Nothing in this skill changes that gate.
