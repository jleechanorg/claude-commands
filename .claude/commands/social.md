---
description: Draft social-media posts for 9 platforms (LinkedIn, HN, Twitter, Reddit, Threads, Facebook, Instagram, Mastodon, Dev.to). Stages in Aside browser + screenshots. Posts only after "POST APPROVED" token.
type: execution
execution_mode: deferred
---

# /social — Draft + Stage Social Posts

Loads `~/.hermes/skills/social-poster/SKILL.md` and runs the draft + stage pipeline.

## Usage

```
/social <intent> [--platforms=...] [--reddit-subs=...] [--link=...] [--image=...]
```

## Examples

```
/social announce jleechanclaw open-source release
/social draft a Show HN for jleechanclaw
/social draft a tweet thread about jleechanclaw's deploy pipeline
```

## Behavior

1. Runs `python3 ~/.hermes/skills/social-poster/scripts/draft_social_post.py` with the intent + flags.
2. Runs `python3 ~/.hermes/skills/social-poster/scripts/stage_in_aside.py` to open Aside tabs + screenshots.
3. Surfaces screenshots via Slack `MEDIA:` + draft text.
4. **WAITS** for user to type `POST APPROVED` (optionally `POST APPROVED <platforms>`).
5. On approval, runs `python3 ~/.hermes/skills/social-poster/scripts/post_approved.py`.

## Safety

- Without `POST APPROVED` token, `post_approved.py` exits code 2. No bypass.
- Instagram has no web compose — draft surfaces caption + mobile-app instructions.
- Default mode is pure templating — no LLM call. Pass `--use-llm` to enable LLM refinement.