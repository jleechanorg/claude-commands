# Cross-Vendor Re-Sync Recipe (verified 2026-08-01)

The companion to SKILL.md Pitfall 11. This file captures the full three-bug
re-discovery cycle that happens when an exported skill bundles source from a
different upstream repo. The bugs (a) stale vendored copy, (b) broken REPO_ROOT
in vendored test, (c) fixture leak not caught by SUBS, all show up together;
agents often fix (a) then re-export, only to rediscover (b) and (c) on the
next review pass. This reference shows how to close all three in one pass.

## The three-PR pipeline

Every cross-vendor re-sync moves three PRs together. Missing any one = merge decouples.

```
Upstream fix lands:
  jleechanorg/user_scope  PR #N  (or as merged commit on origin/main)

Source-side re-sync (skill lives in source product repo):
  $GITHUB_REPOSITORY  PR #M     ← copies script + tests from upstream
                                                into .claude/skills/<skill>/

Downstream mirror (export bundle lands in claude-commands):
  jleechanorg/claude-commands  PR #K       ← mirrors the same files into the
                                                export branch created by
                                                /exportcommands
```

If you skip the source-side PR (PR #M), the next `/exportcommands` run sees
the stale file in your-project.com and re-vendors it backward.

If you skip the downstream mirror (PR #K), the published `claude-commands`
is one PR behind (and the next consumer's `git pull` lands the stale copy).

## Bug 1 — Vendored source is pre-fix (the obvious one)

**Symptom:** `/advice` Reviewer B diff output shows the vendored copy is missing
patterns that the upstream canonical has. Concrete example: vendored
`cmux_resume_watchdog.py` was 27 tests + 25647 bytes; upstream canonical has
29 tests + 25647 bytes + 3 quota regex anchors ("bugbot usage limit",
"overloaded", "output token maximum") + 10 network regex patterns ("stalled
mid-stream", "idle timeout", "econnrefused", "529", "2064", "connection
closed", etc.). Live state.json shows `attempt_count: 7` on one surface —
the daemon was missing enough patterns to mislabel it.

**Recipe:**
```bash
cp $HOME/projects/<upstream>/scripts/<script>.py \
   $HOME/.worktrees/<source-wt>/.claude/skills/<skill>/<script>.py
```

Verify with:
```bash
diff $HOME/projects/<upstream>/scripts/<script>.py \
     $HOME/.worktrees/<source-wt>/.claude/skills/<skill>/<script>.py
# Expected: empty diff.
```

## Bug 2 — Test file's REPO_ROOT resolves wrong in vendored location

**Symptom:** every test in the vendored copy fails on
`FileNotFoundError: '<...>/scripts/<script>.py'` at module load time, before
any test logic runs. The vendored test does `REPO_ROOT = Path(__file__).resolve().parents[1]`
because in upstream's tree the test lives at `tests/test_X.py` and the script
lives at `scripts/X.py` (one parent up + "scripts" subdir). In the vendored
location the script lives in the SAME directory as the test (the skill
directory IS the package), so `parents[1]` resolves to the wrong ancestor.

**Recipe:**
```bash
# Patch only the vendored test (do NOT patch the upstream test):
sed -i 's|REPO_ROOT = Path(__file__).resolve().parents\[1\]|REPO_ROOT = Path(__file__).resolve().parent|; s|REPO_ROOT / "scripts" / "cmux_resume_watchdog.py"|REPO_ROOT / "cmux_resume_watchdog.py"|' \
   $HOME/.worktrees/<source-wt>/.claude/skills/<skill>/test_<script>.py

cd $HOME/.worktrees/<source-wt>/.claude/skills/<skill>/
~/.local/orch-venv/bin/python3 -m pytest test_<script>.py -q
# Expect: same pass count as upstream's test run.
```

Why "same directory as the test" is the layout the skill assumes: the
`.claude/skills/<skill>/` directory is meant to be a self-contained bundle
that can be rsynced anywhere. The test reaching upward to `parents[1]` breaks
that bundle contract.

A common upstream-side fix is to write a small `conftest.py` next to the test
that does `sys.path.insert(0, str(Path(__file__).resolve().parent))`. If the
upstream test file has such a conftest, you may need to copy the conftest too.

## Bug 3 — Fixture leak that the SUBS regex doesn't catch

**Symptom:** a web-advice / CodeRabbit review finds a string in the bundled
skill like `"$USER@jeffreys-macbook-pro: ~/projects/cold-reviewer"` in a
test fixture. The export's SUBS regex `s|\bjleechan\b|$USER|g` rewrites
`$USER` to `$USER` (so the string becomes
`"$USER@jeffreys-macbook-pro: ~/projects/cold-reviewer"` in the published
file) — which means:
- The published file leaks this developer's hostname + project path verbatim.
- Even after the SUBS pass, the file still contains literal hostnames +
  project paths a downstream consumer can grep to identify the author.

**Why the SUBS regex misses this:** the regex replaces `$USER` only — it
has no rule for `@<hostname>` suffix or `~/projects/<path>` patterns. Those
patterns are not in the regex set the operator uses.

**Recipe (always run, in order, after every re-sync):**

```bash
# Phase 1 — keyword scan
rg -n '\bjleechan\b|jeffreys-macbook-pro|~/projects/[^/]+/' \
   $HOME/.worktrees/<source-wt>/.claude/skills/<skill>/
# Expected: empty (post-SUBS the \bjleechan\b regex catches $USER substitution)
# but the hostname + project-path patterns must be checked manually.

# Phase 2 — sentinel-occurrence scan after simulating the SUBS pass
python3 <<'PY'
import re, os, json
SUBS = [
    (r's|jleechanorg/worldarchitect\.ai|$GITHUB_REPOSITORY|g', '/jleechanorg/worldarchitect'),
    (r's|worldarchitect\.ai|your-project.com|g', '/worldarchitect'),
    (r's|jleechantest@gmail\.com|<your-email@gmail.com>|g', '/jleechantest@gmail'),
    (r's|WorldArchitect\.AI|Your Project|g', '/WorldArchitect'),
    (r's|$PROJECT_ROOT/|$PROJECT_ROOT/|g', '/mvp_site'),
    (r's|$HOME|$HOME|g', '$HOME'),
    (r's|\bjleechan\b|$USER|g', r'\bjleechan\b'),
]
src_dir = '$HOME/.worktrees/<source-wt>/.claude/skills/<skill>'
files = sorted(os.listdir(src_dir))
files = [os.path.join(src_dir, f) for f in files if os.path.isfile(os.path.join(src_dir, f))]
leaks_total = 0
for path in files:
    with open(path) as f:
        text = f.read()
    leaks = []
    for pat, _ in SUBS:
        hits = list(re.finditer(pat, text))
        for m in hits:
            leaks.append((pat, m.start(), m.group()))
    if leaks:
        print(f'\n{os.path.basename(path)}:')
        for pat, idx, hit in leaks:
            line_no = text[:idx].count('\n') + 1
            print(f'  L{line_no} pattern={pat!r} hit={hit!r}')
        leaks_total += len(leaks)
print(f'\nleaks_total={leaks_total}')
# Expect leaks_total = 0 BEFORE force-push.
```

If `leaks_total > 0`, fix the source files in the vendored copy (NOT in
upstream; upstream's test fixture is canonical and may be correct as-is).
Common fixes: replace literal hostnames with `localhost`, replace literal
project paths with `test-workspace`, replace literal usernames with
`$USER` or with a placeholder.

**Why grep misses the leak:** even after the upstream test passes, the
SURFACE object constructed by the test fixture is the leak source — the
fixture is a Python literal string used to build a `Surface()` constructor
call, and the upstream author's dev-machine hostname ends up encoded as
that literal string. Only the multi-regex sweep in Phase 2 catches it
because it's looking for the post-filter result, not the pre-filter
literal.

## The combined one-pass recipe (verified 2026-08-01)

Run Phases A-E in the source-side worktree, mirror to downstream, then
verify both PRs come back CLEAN on the next CI tick:

```bash
# Phase A — copy the new canonical files from upstream
SRC_UPSTREAM=$HOME/projects/user_scope
WT_SOURCE=$HOME/.worktrees/worldarchitect/cmux-resume-watchdog-export
WT_DOWNSTREAM=$HOME/.worktrees/claude-commands-export-fix

cp $SRC_UPSTREAM/scripts/cmux_resume_watchdog.py $WT_SOURCE/.claude/skills/cmux-resume-watchdog/
cp $SRC_UPSTREAM/tests/test_cmux_resume_watchdog.py $WT_SOURCE/.claude/skills/cmux-resume-watchdog/

# Phase B — fix REPO_ROOT in the vendored test
sed -i 's|REPO_ROOT = Path(__file__).resolve().parents\[1\]|REPO_ROOT = Path(__file__).resolve().parent|; s|REPO_ROOT / "scripts" / "cmux_resume_watchdog.py"|REPO_ROOT / "cmux_resume_watchdog.py"|' \
   $WT_SOURCE/.claude/skills/cmux-resume-watchdog/test_cmux_resume_watchdog.py

# Phase C — verify the SUBS pass produces zero leaks (use the Phase-2 script
# above with the cmux-resume-watchdog directory as src_dir).

# Phase D — run tests in the vendored location
cd $WT_SOURCE/.claude/skills/cmux-resume-watchdog/
~/.local/orch-venv/bin/python3 -m pytest test_cmux_resume_watchdog.py -q
# Expect: same pass count as upstream (227/227 in the 2026-08-01 case).

# Phase E — amend source-side PR, force-push, mirror to downstream
cd $WT_SOURCE
git add .claude/skills/cmux-resume-watchdog/*.py
git commit --amend --no-edit
git push --force-with-lease=<expected_old_sha> origin HEAD

cp $WT_SOURCE/.claude/skills/cmux-resume-watchdog/*.py $WT_DOWNSTREAM/.claude/skills/cmux-resume-watchdog/
cd $WT_DOWNSTREAM
git add .claude/skills/cmux-resume-watchdog/*.py
git commit -m "feat(skills/cmux-resume-watchdog): re-sync from user_scope PR #N"
git push origin HEAD

# Phase F — poll both PRs for CLEAN
for i in 1 2 3 4 5 6; do
    sleep 20
    CLEAN=$(gh pr view 8681 --repo $GITHUB_REPOSITORY --json mergeStateStatus --jq .mergeStateStatus)
    [ "$CLEAN" = "CLEAN" ] && break
done
gh pr view 8681 --repo $GITHUB_REPOSITORY --json mergeStateStatus
```

## Why the SUB pitfalls are subtle

The export SUBS regexes are designed for **forks that ship auth tokens,
hostnames, usernames, project paths in skill files**. They handle 95% of
leak surface but miss the test-fixture escape hatch: when a Python test
builds a `Surface()` object with a literal hostname + path as the
identifier, the regex only finds the username prefix. The downstream
consumer of the skill (anyone running `pip install cmux-resume-watchdog`
or copying it into their own project tree) ends up running a daemon that
tries to attach to literal `workspace:22`, `surface:44` — which is fine,
but the fixture leak means their `.claude/skills/cmux-resume-watchdog/test_cmux_resume_watchdog.py`
file contains a dev-author identifier pair. Not a credential leak, not
a security issue, but a tracing fingerprint.

**Two rules** for any new vendored skill:

1. **Always grep for `\b<githubuser>\b` AND `~/projects/<path>/` AND `<hostname>`**
   after every re-sync. The SUBS regex catches the first, misses the
   second and third.
2. **Always run the vendored test suite in the vendored directory, not
   upstream.** REPO_ROOT lookup is layout-dependent; the upstream layout
   cannot reproduce a vendored-layout failure.

## Cross-reference

- SKILL.md Pitfall 11 — high-level summary + recipe
- `pr-cleanup-replay` SKILL.md § Phase 5.5 (race-with-AO-worker guard) —
  when two agents re-sync the same skill in parallel, the local-HEAD-vs-remote-HEAD
  check is mandatory before force-push
- `always-pr-never-local-edit` SKILL.md § Worktree-silent-edit trap — when
  the venv lives in the main checkout and `pytest` runs from the worktree,
  REPO_ROOT resolution can land in the wrong tree
