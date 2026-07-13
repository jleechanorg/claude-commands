---
description: Draft social-media posts for 9 platforms (LinkedIn, HN, Twitter, Reddit, Threads, Facebook, Instagram, Mastodon, Dev.to). Stages in Aside browser + screenshots. Posts only after "POST APPROVED" token.
type: execution
execution_mode: deferred
---

# /social — Draft + Stage Social Posts

Loads `~/.claude/skills/social-poster/SKILL.md` first, which routes to the canonical Hermes social-poster skill.

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

1. Read and execute `~/.claude/skills/social-poster/SKILL.md`.
2. That skill should resolve to `~/.hermes/skills/social-poster/SKILL.md` as the canonical workflow.
3. Follow the skill-defined draft + Aside staging flow, including screenshot verification, direct-asset propagation, and platform-specific handling.
4. **WAITS** for user to type `POST APPROVED` (optionally `POST APPROVED <platforms>`).
5. On approval, follow the skill-defined posting flow.

## Safety

- Without `POST APPROVED` token, `post_approved.py` exits code 2. No bypass.
- Never treat a loaded compose form or login-wall screenshot as proof a draft was staged.
- Prefer canonical outbound links and explicit media assets over reposting LinkedIn shortlinks.
- Instagram may require a media-upload flow instead of text-only staging, especially when the intended creative is an image/screenshot plus an outbound video link. For those media posts, cross-share to Threads and Facebook by default unless the user opts out.
- Default mode is pure templating — no LLM call. Pass `--use-llm` to enable LLM refinement.