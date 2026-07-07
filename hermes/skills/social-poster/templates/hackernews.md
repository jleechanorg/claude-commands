# Hacker News — Show HN Template

**Character limits:**
- Title: **80 chars max** (hard limit; HN truncates)
- Text body: **~10,000 chars** but first ~400 chars are what readers see before "展开"
- URL field: separate from title

**Voice:** Engineer-to-engineer. No marketing. Concrete numbers. Open about limitations.

**Show HN conventions (when self-promo):**
- Title MUST start with `Show HN:`
- URL field points to repo / live demo
- First-comment text post should answer: "what is it, why does it exist, what tech stack, what's missing, what feedback you want"

## Template — Title

```
Show HN: {{PROJECT_NAME}} – {{ONE_LINE_PITCH_UNDER_60_CHARS}}
```

## Template — First comment (text post body)

```
Hi HN — I built {{PROJECT}} because {{PROBLEM}}.

{{WHAT_IT_DOES}} ({{CONCRETE_DETAIL}})

Tech stack: {{STACK}}
License: {{LICENSE}}

What's already there:
- {{FEATURE_1}}
- {{FEATURE_2}}
- {{FEATURE_3}}

What's still missing (and I'd love feedback on):
- {{GAP_1}}
- {{GAP_2}}

Repo: {{URL}}
Demo: {{DEMO_URL_IF_ANY}}

Happy to answer anything — especially if you've hit {{ADJACENT_PROBLEM}}.
```

## Anti-patterns

- ❌ Title with "🚀" / "🔥" / emoji
- ❌ Title with "AI-Powered", "Revolutionary", "Next-Gen", "Game-Changing"
- ❌ Link-only post without text body (HN downranks these)
- ❌ Title >80 chars (truncates)
- ❌ Asking for upvotes / "please star"
- ❌ Burying the technical detail in marketing fluff

## Non-Show-HN post (Ask HN / general)

Use `Ask HN: {{QUESTION}}` for genuine questions, no project plug.