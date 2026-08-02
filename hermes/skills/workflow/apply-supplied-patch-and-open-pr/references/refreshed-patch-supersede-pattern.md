# Refreshed-patch supersede pattern (Pitfall P7)

When the user re-sends a patch they sent yesterday/last week for the SAME
feature, with the instructions file saying "REFRESHED ... supersedes the
<prior-date> patch" — this is a recurring shape, not a one-off.

## Detection

Step 1 pre-flight catches it via any of:

- `gh api .../pulls?state=all&head=<OWNER>:<branch>` returns a prior PR
  on the same branch name (or with the same/similar title)
- The instructions file's first paragraph contains "REFRESHED" or "supersedes"
- `gh api .../compare/<new-base-sha>...<prior-PR-head-sha>` returns
  `status: diverged` or `behind_by > 0`

## What to do (no user confirmation)

1. Branch from CURRENT `origin/main`, NOT from the prior PR's branch head.
   Use a new branch name — `<branch>-v2`, `<branch>-refreshed-<date>`, or
   whatever the user named in the new instructions.
2. Apply the new patch on the fresh branch.
3. Open the new PR. In the body, lead with:
   > **Note:** this PR **supersedes** [PR #N](url) — the <prior-date> patch
   > against base `<prior-base-sha>`. PR #N is now <N> commits behind main;
   > this refreshed patch (against base `<new-base-sha>`) is the new source
   > of truth. PR #N should be closed once this one lands.
4. Close the prior PR with `gh pr close <N> --repo <OWNER>/<REPO> --comment "..."`
   where the comment quotes the user's supersede directive and links to the
   new PR. The `supersede` framing is intentional — it is NOT a rejection,
   it's a version bump.
5. Do NOT delete the prior branch — leave it for diff inspection. Future
   agents may want to verify what changed between v1 and v2.

## Verified case

2026-07-16, `jleechanorg/disk_magician` PR #21 (superseded PR #17). Full
session details in SKILL.md "Verified case" section 2.

## Why this is durable

The shape will recur because:
- The user's pattern is "iteratively refresh a patch over multiple days
  until ready to merge"
- They explicitly keep the prior PR open while iterating, so a single
  PR for the topic can be in "superseded" state for weeks
- Multiple repos on `jleechanorg/*` (disk_magician, jleechanclaw,
  your-project.com) use this iterative-patch style

A future agent running this skill will hit P7 within ~2 sessions of disk_magician
work, and likely on the other iterative-patch repos too. The decision matrix
row + P7 pitfall + verified case together give them enough context to
handle it without re-deriving.