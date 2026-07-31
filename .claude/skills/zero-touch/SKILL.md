---
name: zero-touch
description: Use when evaluating, reporting, or labeling whether a pull request completed without human or operator intervention.
---

# Zero-Touch by Operator

A PR is zero-touch when automation created or claimed it, completed its work,
earned draft-quality verdicts, passed `/green`, and merged without a human or
human-operated terminal changing PR state.

`/green` always means exactly:

1. required current-head CI is terminal and successful;
2. GitHub reports mergeable/no conflicts.

CodeRabbit and Bugbot are advisory. Evidence, `/er`, `/advice`, and
review-thread cleanup may be required by the draft lifecycle, but are not extra
`/green` gates.

## Operator Actions That Break Zero-Touch

- a human-operated terminal pushes a fix to the PR branch;
- a human posts an approval, dismissal, or merge action;
- a human manually re-runs CI to bypass an unresolved failure;
- a human resolves a conflict or required draft-quality blocker.

Observation, status questions, and bot-to-bot actions do not break zero-touch.

## Measurement

Audit commits, comments, reviews, workflow dispatches, and the merge actor.
Classify ambiguous actor ownership as `unknown`, not zero-touch.

```text
zero_touch_rate = zero_touch_merged_prs / all_merged_prs * 100
```

Bind every classification to the PR URL, merge SHA, actors, and measurement
window.
