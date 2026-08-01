# Cleanup-Archetype Recipe — PR #327 case study

Case study from session 2026-07-13T22:57:00Z. The user said:
> "lets remove the archive from the PR and modify /exportcommands to stop exporting it"

The auto-opened PR #327 (`export-20260713-155353`, commit `25ad28ac`) had 66 files. 61 of them
were archive / history-keeping content the user did NOT want shipped. After Track A + Track B,
the PR shrank to exactly 5 incremental files. This is the full recipe with every pitfall I hit
along the way.

## The two-track atomic edit

### Track A — patch `~/.claude/commands/exportcommands.sh`

The script has three union-merge / rsync surfaces. Each needs its own exclude for `_archive/`:

| Surface | Line(s) | Patch |
|---|---|---|
| `union_dir()` global `find` | L129 | add `\( -not -path '*/_archive/*' \) \` to the `\( -not -path ... \)` block |
| `union_dir()` project `find` | L169 | same exclude, different anchor context |
| Root-dir `rsync` block | L272, L273 | add `--exclude='_archive/'` + `--exclude='*/_archive'` to the rsync flags |

**Pitfall I hit:** the first patch failed because the `--not -path '*/__pycache__/*' ... --not -path '*/canvas-fonts/*' ...` pattern matched in three different find invocations (both union_dir surfaces + maybe one more). The patch tool requires unique surrounding context. Use the `while IFS= read -r -d '' f; do ... global_src ...` opening lines for the global find, and the `local relpath="${f#$project_src/}"` opening for the project find. Don't rely on the `--not -path` patterns alone.

**Pitfall I hit (verification):** after patching, `bash -n ~/.claude/commands/exportcommands.sh` is necessary but NOT sufficient. The find-clauses might still parse OK while subtly changing semantics. Run a real `find` against a fixture with both `_archive/` and non-archive paths and confirm the file count is what you expect:

```bash
mkdir -p /tmp/exptest/proj/.claude/commands/_archive
echo "real" > /tmp/exptest/proj/.claude/commands/real.md
echo "arch" > /tmp/exptest/proj/.claude/commands/_archive/arch.md
find /tmp/exptest/proj/.claude -type f \
  \( -not -path '*/_archive/*' \) -print
# Expected: 1 file (real.md). Got more than 1 = exclude didn't land.
```

### Track B — amend the auto-opened PR to drop the unwanted content

In a fresh worktree of the PR branch:

```bash
git clone -b export-20260713-155353 --depth=10 \
  https://github.com/jleechanorg/claude-commands.git \
  ~/worktrees/jleechanorg-pr-327-cleanup
cd ~/worktrees/jleechanorg-pr-327-cleanup
git config user.email "cleaner@anthropic.com"
git config user.name "Claude Cleanup"

# Get the diff-list of what THIS PR added (vs main)
# The PR base is whatever main was at the time the export ran.
git fetch --unshallow origin main  # shallow clone only has 10 commits; need full history
MAIN_SHA=$(git rev-parse origin/main)  # = 337dc6d7085ae7c57f678af593f26273c2ca3a4e in this case

# Get the diff list of the PR's own commits
git diff --name-only --diff-filter=AM HEAD~1..HEAD > /tmp/all_files.txt

# Filter to just the unwanted category
grep '_archive' /tmp/all_files.txt > /tmp/rm_files.txt
# wc -l /tmp/rm_files.txt → 61 in this case

# git rm
git rm -rf $(cat /tmp/rm_files.txt)
# git status shows ~61 'D' entries
```

**Pitfall I hit:** I naively did `git rm` on EVERY file matching `_archive` — but 4 of those
files (the `automation-audit.{md,SKILL.md}` dupe paths) **already existed on main** (committed in
PR #310 from 2026-06-21). The export's content filters (`perl -pi -e` substitutions) had
modified them by ~30 bytes each. If I deleted them wholesale, my "cleanup" PR would make
those 4 files DISAPPEAR from main on merge — a regression.

**Recipe to keep main's version intact while still removing the unwanted category:**

For each file in the rm list, ask: "does `git cat-file -e <MAIN_SHA>:<path>` succeed?"
- If **yes** (file exists on main): the PR's version differs by ~content-filter bytes.
  Run `git restore --source=<MAIN_SHA> --staged --worktree -- <path>` to put main's exact
  bytes back. This will register as an `A` (added) in `git status` because we're restoring
  a file the export-PR had deleted via `git rm`. After committing, the file is in HEAD
  with main's exact content — zero net diff vs main.

- If **no** (file does NOT exist on main): the file was truly net-new in this PR. `git rm`
  is correct.

**Byte-identity verification** (mandatory before committing):

```bash
for f in <files-i-restored>; do
  main_sha=$(git show "<MAIN_SHA>:$f" 2>/dev/null | git hash-object --stdin)
  work_sha=$(cat "$f" | git hash-object --stdin)
  if [ "$main_sha" = "$work_sha" ]; then
    echo "OK $f"
  else
    echo "MISMATCH $f: main=${main_sha:0:8} work=${work_sha:0:8}"
  fi
done
```

Mismatches mean the content-filter stripped a trailing newline somewhere. Investigate
with `wc -c` — main will report one more byte than your restore (the trailing `\n`).

**Anti-pattern (don't do this):** `git checkout HEAD~1 -- <file>`. That restores to the
export-PR's pre-cleanup version (which had the content-filter modifications), not main's
original. `git restore --source=<MAIN_SHA>` is the only path that ensures zero net diff.

**Pitfall I hit (amending):** I first did the `git rm` + commit, then realized the
already-on-main files shouldn't have been deleted. Used `git commit --amend --no-edit`
to fold the restorations into the original cleanup commit. The diff stats showed:
61 files changed, 7986 deletions(-). After amendment: 61 files changed, 8 insertions(+),
7317 deletions(-). The 8 insertions = 4 files × 2 (each main's automation-audit.md is
written back identically, but `git diff` counts a restore as +N -N). The diff still
shows the 4 files as `+0 / -N` entries — GitHub's UI may show them as "deleted" in the
PR even though the cumulative effect on main is zero.

**Pitfall I hit (force push):** the amended commit has a different SHA than what was
originally pushed (`964cdec` → `afe98ef`). Must use `--force-with-lease`:

```bash
git push --force-with-lease origin HEAD:refs/heads/<branch>
```

`--force-with-lease` (vs bare `--force`) refuses the push if the remote has been updated
by anyone else since your last fetch. With a personal branch like an export branch, this
safety net is free and good practice.

## Final shape verification

After the amend + force-push, verify via REST:

```bash
gh api 'repos/jleechanorg/claude-commands/pulls/<N>' \
  --jq '{headSha: .head.sha, changed_files: .changed_files, additions: .additions, deletions: .deletions}'

gh api 'repos/jleechanorg/claude-commands/pulls/<N>/files?per_page=20' \
  --jq '.[] | .filename'
```

Expected: 5 files, all in `.claude/commands/{harness,slackbots,social}.md` + the 2 backing
skills. If you see more, the byte-identity restoration didn't land on a file and it's still
showing as a deletion.

## Post-cleanup communication

**Always post a follow-up PR comment** summarizing the cleanup. Future sessions need to know:
1. What was removed (category + count)
2. Why (user's stated rationale)
3. What the script patch prevents (the durable fix)
4. The final file list (so audit trails can see the PR's actual scope)

CodeRabbit will most likely actually review the PR this time because the bot rate limit
window has shifted — the cleanup push is also your chance to retrigger a real review.

## Lessons encoded back into the parent SKILL.md

This case study is the basis for **Pitfall 10** in `SKILL.md`. The 5 pitfalls are:

1. Always re-check current state BEFORE planning (from session 2026-07-13)
2. `mergeable_state: dirty` on a stale-base PR means BASE != main
3. `~/.claude/commands/exportcommands.sh` is NOT the canonical version
4. Bot rate-limit faux-green on the auto-opened export PR
5. (Implicit, session-recap-only) `git secret guard` output IS the security pre-check
6. `localexportcommands.md` and `exportcommands.md` are DOCS, not scripts
7. The auto-opened PR has no `.github/workflows/`
8. Supersession comment template
9. `/exportcommands` from a non-main branch
10. **NEW: cleanup-PR + script-patch workflow (this case study)**

The class is distinct from `drive-pr-to-green` and `github-pr-workflow` because Pitfall 10
is the unique multi-PR-archetype handler (supersede + merge-as-is + cleanup + rebase) that
no other PR skill owns.

## Cross-references

- Parent: `../SKILL.md`
- Sessions recap: `sessions-recap.md`
- Export script contract: `exportcommands-sh-contract.md`