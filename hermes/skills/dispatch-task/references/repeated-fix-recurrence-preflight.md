# Repeated-fix-recurrence preflight — when a prior dispatch vanished

**Symptom (verified 2026-07-20, slack thread `C09GRLXF9GR/1784563243.076849`, daily-bug-hunt silent-failure #4 in the same month):**

Session starts with a "clean sweep" / "0 bugs / 0/3 failures" message. The per-agent `.err` files all show the same `hermes: error: argument command: invalid choice: 'agent'` style failure. A prior session (or this same agent on a prior day) clearly diagnosed the same root cause and filed a fix-issue (e.g. `jleechanorg/jleechanclaw#782`), but no PR ever landed. Running the same `ao spawn` recipe a second time will hit the same fate.

This is the failure mode the harness keeps missing. Here is the recipe to NOT miss it.

## Pre-flight check (run before spawning)

```bash
# 1. The diagnostic question: did the prior fix-dispatch actually push?
ISSUE=782
gh issue view "$ISSUE" --repo OWNER/REPO --json state,title 2>&1
# If the issue is OPEN and was filed >1 day ago AND no closing PR exists,
# the previous dispatch vanished. Do NOT re-dispatch via the same recipe.

# 2. Find the prior-fix branch — there should be one if the worker pushed
gh pr list --repo OWNER/REPO --state all \
  --json number,title,headRefName,createdAt,mergedAt,closedAt \
  --jq '.[] | select(.title | test("<topic keywords>")) | "\(.number) \(.headRefName) \(.state) merged=\(.mergedAt)"'
# If empty -> prior dispatch did not push. Do NOT re-spawn; pivot to inline.

# 3. Verify the script/artifact on disk is what the prior session thought
git -C /path/to/repo log origin/main..origin/"$BRANCH" --oneline 2>&1 | head -5
# If empty -> branch was never pushed. Confirms the vanish.
```

## Decision tree

| Prior state                                            | What is wrong                            | Right action                                                                                          |
|--------------------------------------------------------|------------------------------------------|-------------------------------------------------------------------------------------------------------|
| Issue OPEN, no PR exists, no `headRefName` on origin  | Prior dispatch never pushed              | Inline-edit + push yourself (<=10-line fix per SOUL.md "apply now")                                  |
| Branch exists on origin but no PR was created          | Worker forgot `gh pr create`             | Open the PR yourself: `gh pr create --head fix/<name>`                                                |
| Branch + PR exist but PR is closed without merge       | CR declined / no auto-merge              | Read the CR feedback; if scope-acceptable, fix-forward in a NEW clean branch from origin/main         |
| Branch + PR exist AND merged                           | Done                                     | Just close the loop — ack in the original thread, no new work                                         |

## Inline-pivot recipe when prior dispatch vanished

The right shape per SOUL.md "diagnosis-requires-followthrough-or-handoff" is "apply now" — single-file, <=10-line fixes do NOT need an AO worker. The full sequence:

```bash
# 1. Clean worktree from origin/main, fresh branch
git worktree add -b fix/<descriptive-name> /tmp/<repo>-<phenotype> origin/main
cd /tmp/<repo>-<phenotype>

# 2. Apply the fix + test updates (mirror the prior-dispatch recipe)
#    ...edit, edit, edit...

# 3. Run the affected test suite locally BEFORE pushing
python3 -m pytest tests/<relevant>.py -v
# OR the shell-level equivalent for .sh scripts: `bash -n script.sh`

# 4. Commit + push + open PR
git add <files>
git commit -m "[<tag>] <subject> (closes #<issue>)"
git push -u origin fix/<descriptive-name>
gh pr create --repo OWNER/REPO --base main --head fix/<descriptive-name> --title "..." --body "..."

# 5. Verify the PR round-trip
gh pr view N --repo OWNER/REPO --json number,state,url,mergeable,headRefOid
```

## Why this matters (why "just re-dispatch" was wrong)

If the prior dispatch vanished, the same recipe path will vanish again. The vanish could be:
- AO worker died ungracefully (session timeout, network blip, OOM)
- AO worker completed but the auto-derived branch never reached `origin`
- AO worker pushed but the PR was never opened (script-side omission)
- The push landed but to the wrong org / repo

In all of these, "re-spawn via `ao spawn`" is just "re-run the same flaking pipeline." Inline-push avoids the pipeline entirely. This is also why SOUL.md `push-pr-donot-stop-halfway` makes push (not "agent spawned") the deliverable.

## "Test still asserts the broken string" sub-pattern

When the prior dispatch vanished, also check that the test fixtures were NOT asserting the broken behavior. Verified 2026-07-20: `test_bug_hunt_uses_one_shot_hermes_not_fire_and_forget_ao` was passing on `origin/main` because it asserted `assert "hermes agent --agent" in text` — i.e., the test was *locking in* the broken CLI form. Any prior dispatch that did not touch this test would have had to "lie" to pass CI.

When patching broken code, grep for tests that assert "the broken string is present" and update them in the same commit. A test that cannot distinguish broken from fixed is worse than no test.

## Checklist before considering the inline pivot done

- [ ] `git status --short --branch` shows clean, branch tracks `origin/<branch>`
- [ ] `git diff --stat origin/main` matches the PR's stated scope (no orphan commits, no merge commits carrying unrelated history)
- [ ] `git log origin/main..HEAD --oneline` shows only commits that belong to this fix
- [ ] `git push` returned `branch ... set up to track origin/...` and exit 0
- [ ] `gh pr view N --json state,url,mergeable` shows OPEN, MERGEABLE
- [ ] CI started — `gh pr checks N` lists the same checks that gate merges on this repo
- [ ] Reply posted in the originating thread with the PR URL + commit SHA

## When the AO CLI itself is broken

Today (2026-07-20), `~/bin/ao` failed with `Cannot find package 'commander'` because the symlink target `~/project_agento/agent-orchestrator/packages/cli/dist/index.js` has no `node_modules/` (the npm install ran against `agent-orchestrator-ts/` instead). The `ao` CLI cannot be repaired inline from this session.

The recovery is exactly the inline pivot above — skip AO entirely. If you must use AO for a multi-file fix that exceeds the "apply now" bar, the recipe is:

```bash
# 1. Repair the symlink target first (BEFORE relying on ao)
ls -la ~/bin/ao
# If it points to $HOME/project_agento/agent-orchestrator/packages/cli/dist/index.js
# but node_modules is missing:
cd ~/project_agento/agent-orchestrator && npm install 2>&1 | tail -5
# OR repoint the symlink to a working directory if you find one.

# 2. Verify ao is callable
~/bin/ao status 2>&1 | head -5
# Should NOT contain "Cannot find package 'commander'".

# 3. THEN resume normal dispatch.
```

If `npm install` is too heavy (10+ minutes, sometimes hangs on wheels), the inline-pivot recipe above is still the right fallback for <=10-line fixes. Do NOT block on AO for a small surgical fix.
