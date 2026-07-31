---
name: pr-green-definition
description: Use when checking whether a pull request is merge-ready or before executing an authorized merge.
type: policy
---

# PR Green Definition

A PR is `/green` only when exactly two gates pass at the same current HEAD SHA:

| Gate | Pass condition |
|---|---|
| CI | Every required non-advisory check is terminal with a successful conclusion |
| Conflicts | GitHub reports `mergeable == MERGEABLE` |

CodeRabbit and Bugbot are advisory reviewers. Evidence, `/advice`, and
review-thread cleanup are draft-phase quality work, not extra `/green` gates.

## Verification

1. Resolve the PR and capture its full URL and `headRefOid`.
2. Inspect `statusCheckRollup`. A `CheckRun` uses `.status` and `.conclusion`;
   a `StatusContext` uses `.state`.
3. Exclude the exact advisory contexts `CodeRabbit` and `Cursor Bugbot` from
   the CI gate.
4. Require every remaining check to be terminal and one of
   `SUCCESS`, `NEUTRAL`, or `SKIPPED`.
5. Require `mergeable == MERGEABLE`; retry only while it is `UNKNOWN`.
6. Re-read `headRefOid`. If it changed, discard the verdict and start again.

The following query shape was verified against a live PR:

```bash
gh pr view N --repo OWNER/REPO \
  --json url,headRefOid,mergeable,statusCheckRollup \
  --jq '
    def check_label: (.name // .context // "");
    def advisory:
      (check_label | test("^(CodeRabbit|Cursor Bugbot)$"; "i"));
    {
      url: .url,
      head: .headRefOid,
      mergeable: .mergeable,
      pending: [
        .statusCheckRollup[]
        | select(
            (advisory | not)
            and (
              (.__typename == "CheckRun" and .status != "COMPLETED")
              or
              (.__typename == "StatusContext"
               and (.state == "PENDING" or .state == "EXPECTED"))
            )
          )
        | check_label
      ],
      failed: [
        .statusCheckRollup[]
        | select(
            (advisory | not)
            and (
              (.__typename == "CheckRun"
               and .status == "COMPLETED"
               and ((.conclusion == "SUCCESS"
                     or .conclusion == "NEUTRAL"
                     or .conclusion == "SKIPPED") | not))
              or
              (.__typename == "StatusContext" and .state != "SUCCESS")
            )
          )
        | check_label
      ]
    }'
```

Gate 1 passes when `pending` and `failed` are empty. Gate 2 passes only when
`mergeable` is `MERGEABLE`.

## Merge Boundary

`/green` verifies; it does not merge. Before any merge, satisfy the target
repository's live authorization rule. A new commit invalidates `/green` and
every SHA-bound draft verdict.
