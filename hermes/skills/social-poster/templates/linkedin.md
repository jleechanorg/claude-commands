# LinkedIn Post Template (long-form)

**Character limits:**
- Post body: **3,000 chars max** (practical sweet spot 1,300-1,500)
- "See more" cutoff: ~210 chars (first 2 lines before fold)
- Comments: 1,250 chars each

**Voice:** Professional but personal. First-person. Concrete. No emojis in body (1 emoji max per post, never as the first character).

**Structure:**
1. **Hook (0-210 chars)** — punchy statement or contrarian take. MUST be visible before "see more".
2. **Context (210-800 chars)** — why this matters, the problem you hit, the gap you found.
3. **What you built / observed (800-1,500 chars)** — concrete details, numbers, a screenshot or link.
4. **Takeaway (final 200 chars)** — one sentence the reader can repeat.

**Required:**
- 3-5 hashtags at the very end (LinkedIn rewards 3-5, not 30).
- A link, image, or document (boosts reach 2-3x).
- Tag 1-3 people if relevant (optional).

**Anti-patterns:**
- ❌ "I'm excited to announce…" / "Thrilled to share…" (engagement-bait opener)
- ❌ Emoji as first character
- ❌ 30 hashtags
- ❌ Wall of text with no line breaks
- ❌ "Agree?" / "Thoughts?" / "Like if you…" engagement bait

## Template

```
{{HOOK_LINE}}

{{CONTEXT_PARAGRAPH}}

Here's what we built / learned / shipped:

{{DETAIL_PARAGRAPH_1}}

{{DETAIL_PARAGRAPH_2}}

{{TAKEAWAY_LINE}}

{{LINK_OR_IMAGE}}

#{{HASHTAG_1}} #{{HASHTAG_2}} #{{HASHTAG_3}} #{{HASHTAG_4}} #{{HASHTAG_5}}
```

## Example (filled)

```
Most "AI agent" repos are toys that break at the first CI flake.

We hit the same wall building {{PROJECT}}: skills that worked in one agent runtime
died in another, and a single failed test could silently wedge a cron for hours.

So we shipped a {{3_WORD_DESCRIPTION}}:
- {{FEATURE_1}} ({{CONCRETE_DETAIL}})
- {{FEATURE_2}} ({{CONCRETE_DETAIL}})
- {{FEATURE_3}} ({{CONCRETE_DETAIL}})

Open source, MIT, deployable in a single command:

{{LINK}}

#{{TAG_1}} #{{TAG_2}} #{{TAG_3}} #{{TAG_4}} #{{TAG_5}}
```