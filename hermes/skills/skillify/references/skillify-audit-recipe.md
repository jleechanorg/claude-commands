# Skillify Audit Recipe — Remote-Tree First (added 2026-07-14)

A class-level playbook for any agent running `skillify_check.py`,
`check_resolvable.py`, or `trigger_eval.py`. Companion to the Phase 1
"Pre-audit verification" block in SKILL.md.

## Why this recipe exists

Two failure modes recurred in the 2026-07-02 and 2026-07-14 audits of
the `skillify` skill itself:

1. **Stale-local-worktree audit.** The local checkout was 58 commits
   behind `origin/main`. Auditing it produced `score=2/10` — looked
   like everything was broken. Cause: SKILL.md on disk, but the
   scripts/tests/routing-eval.jsonl landed on a later PR that wasn't
   pulled yet. Investigation of a non-existent regression wastes a
   cycle.
2. **Stranded side-branch absorption.** A fix commit
   (`92b6acfc67 fix(skillify): address CodeRabbit and skeptic review`)
   was reachable from `git log --all` but NOT an ancestor of
   `origin/main`. Counting that commit toward "skillify is fully
   landed" was a hallucination — the public tree doesn't have it.

Both are now codified as anti-patterns in the SKILL.md and as the
recipe below.

## The recipe (canonical)

```bash
# Step 1 — orient: where is local vs remote?
git status --short --branch
git rev-parse HEAD origin/main

# Step 2 — archive the remote tree (the source of truth)
REPO=$HOME/jleechanclaw   # adjust
rm -rf /tmp/skillify_audit && mkdir -p /tmp/skillify_audit
git -C "$REPO" archive origin/main | tar -x -C /tmp/skillify_audit
cd /tmp/skillify_audit

# Step 3 — run the audit trio against the archived tree
python3 skills/skillify/scripts/skillify_check.py     skills/skillify/ --repo-root .
python3 skills/skillify/scripts/check_resolvable.py  --resolver skills/RESOLVER.md --skills skills/
python3 skills/skillify/scripts/trigger_eval.py      --fixture skills/skillify/routing-eval.jsonl --repo-root .

# Step 4 — run the test suite against the archived tree
PYTHONPATH=skills/skillify/scripts pytest skills/skillify/tests/ -v
```

Record the score, pytest pass/fail, and trigger_eval total/passed.

## Surface stranded fixes (post-audit)

After the audit returns a clean score, check whether topic-relevant
fix commits are sitting on side branches:

```bash
git -C "$REPO" log --all     --oneline --grep="<topic>" -i > /tmp/all_topic.txt
git -C "$REPO" log origin/main --oneline --grep="<topic>" -i > /tmp/main_topic.txt
comm -23 <(sort -u /tmp/all_topic.txt) <(sort -u /tmp/main_topic.txt)
```

Each row of `comm -23` is a commit that exists somewhere but is NOT
in origin/main. Treat each as a follow-up PR. Do NOT silently fold
them into the audit verdict.

Real example (2026-07-14):

```
$ git log origin/main --grep="skillify" -i --oneline | wc -l
16
$ git log --all --grep="skillify" -i --oneline | wc -l
21
$ comm -23 <(...all... ) <(...origin/main...) | wc -l
5
```

Five stranded skillify-related commits on side branches at the time
of the audit. None counted in the 10/11 PASS.

## When local worktree IS current

If `git status --short --branch` shows `Your branch is up to date
with 'origin/main'` (or equivalently `git rev-parse HEAD ==
git rev-parse origin/main`), the local tree is authoritative and the
`/tmp/skillify_audit` archive step is unnecessary overhead — run the
audit inline. The recipe above is the safe default for an unknown
state; fall through to it whenever uncertain.

## Output

The audit report should always include:

1. **Tree audited:** `origin/main@<sha>` (preferred) or `<local ref>`
2. **`skillify_check` score:** e.g. `10/11 (1 defer, 0 fail)`
3. **`check_resolvable` summary:** `valid=N orphans=N dups=0 ambiguous=0`
4. **`trigger_eval` summary:** `passed=N total=N ambiguous_rows=N`
5. **pytest result:** `N passed, 0 failed`
6. **Stranded commits:** list with SHA + topic, OR `none — local tree matches origin/main`

This shape makes the answer verifiable by a downstream reviewer
without re-running the audit.
