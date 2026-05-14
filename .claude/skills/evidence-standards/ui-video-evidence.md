---
name: ui-video-evidence
description: Record captioned browser/UI evidence videos, upload to GitHub PR attachments, and link sanitized artifacts in a self-contained gist
---

# UI Video Evidence for Visual Verification

## Purpose

Prove user-visible behavior in a way reviewers and agents can verify quickly from the PR conversation.

## When UI Video Is Mandatory

UI/browser video is mandatory whenever work is user-facing, including:
- Visual/UI layout or styling changes
- Click flows, form submit flows, navigation, or modal behavior
- New/changed browser interactions
- Any claim of visual correctness or lack of visual regression

If a PR touches user-facing behavior, missing UI video is an evidence failure.

## Required Outputs

Each UI evidence run must provide:
- UI video (`.mp4` preferred)
- UI fallback media (`.gif` recommended for easy PR preview)
- Captions (burned-in preferred; `.vtt`/`.srt` acceptable)
- Git linkage (`git rev-parse HEAD` visible in recording context)
- GitHub-hosted URL(s) published by automation
- A browser-viewable artifact (`.gif`, raw URL, release asset, or native attachment)
- A downloadable high-fidelity artifact (`.mp4`, `.mp4.zip`, or release asset)
- Matching entry in a self-contained gist bundle

## Mandatory Frames

| # | Frame | Must show |
|---|-------|-----------|
| 1 | URL + Page Load | Full browser URL bar with route under test |
| 2 | Before State | Initial state before action |
| 3 | Action | Click/input/navigation action |
| 4 | After State | Resulting state after action |
| 5 | Git Linkage | Terminal split, devtools log, or on-page SHA marker |

## Recording Options

### Option 1: Claude-in-Chrome GIF/Video workflow
Use browser automation and record the full flow while keeping URL visible.

### Option 2: Kap (manual desktop capture)
```bash
brew install --cask kap
```
Record browser window including address bar.

### Option 3: ffmpeg (headless/CI)
```bash
ffmpeg -video_size 1280x720 -framerate 10 -f x11grab -i :99 -t 30 /tmp/<work_name>.mp4
```

## Caption Requirements (MANDATORY)

Both tmux and UI videos must always have captions.

Accepted forms:
1. Burned-in captions in the video (preferred)
2. Sidecar caption file (`.vtt`/`.srt`) linked in PR and included in gist

Use `~/.claude/skills/video-caption/SKILL.md` for reliable burned-in captions.

## GitHub Hosting (Required, Zero-Touch)

Preferred path:

```bash
zip -j /tmp/ui_flow.mp4.zip /abs/path/to/ui_flow.mp4
gh release create evidence-pr-<PR_NUMBER> --draft --title "PR #<PR_NUMBER> Evidence" --notes "" 2>/dev/null || true
gh release upload evidence-pr-<PR_NUMBER> /tmp/ui_flow.mp4.zip /abs/path/to/ui_flow.gif /abs/path/to/ui_flow.srt --clobber
gh release view evidence-pr-<PR_NUMBER> --json assets,url
gh pr edit <PR_NUMBER_OR_URL> --body-file /tmp/pr_body.md
```

Behavior:
- Keeps publication fully zero-touch via `gh`
- Publishes durable GitHub-hosted release URLs
- Avoids dependence on browser cookies

Optional path:
- `$HOME/.claude/scripts/github_pr_media_upload.py` may be used when native `user-attachments` URLs are specifically desired

## PR Snippet Template

```markdown
## UI Evidence

- GIF: `<asset url from gh release view --json assets>`
- MP4 ZIP: `<asset url from gh release view --json assets>`
- Captions: burned-in (or gist: https://gist.github.com/<id>#file-ui-video-vtt)
- Route: `/path/under/test`
- Commit: `<sha>`
- Claim: <what this proves>
```

## Anti-Patterns

Reject these:
- URL bar cropped out
- Success-only clip (no before/action)
- No git SHA linkage
- Missing captions
- Screenshot-only evidence for flow claims
- Manual drag-drop as the only publication path
- Non-GitHub-hosted media when GitHub hosting is available

## Reviewer Checklist

1. Video is linked in PR via GitHub-hosted URL
2. Automation path uses `gh` or the optional native-attachment helper instead of manual drag-drop
3. Captions are present
4. Before/action/after flow is visible
5. URL and route match claim
6. Git SHA linkage is visible
7. Gist contains matching metadata/caption artifacts
