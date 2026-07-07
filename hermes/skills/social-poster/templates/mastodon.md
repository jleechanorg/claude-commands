# Mastodon Post Template

**Character limits:**
- Default: **500 chars** (configurable per instance; some allow 5,000)
- CW (content warning): optional, **255 chars max** for the spoiler text
- Polls: 4 options max, 1,400 chars total

**Voice:** Federated, community-aware. Less algorithmic than Twitter. Higher text density is OK.

**Federation etiquette:**
- Don't @-mention users on instances that don't federate with yours
- Use CW for content that might trigger folks
- Boost (reblog) > self-promotion

## Template

```
{{HOOK_LINE}}

{{2-4_SENTENCES_WITH_CONTEXT}}

{{LINK}}
```

## Template — Long form (5,000-char instance)

```
{{HEADLINE}}

{{PARAGRAPH_1}}

{{PARAGRAPH_2}}

## {{SECTION_HEADER}}

{{LIST_OR_PARAGRAPH}}

{{LINK}}
```

## Anti-patterns

- ❌ Cross-posting the Twitter thread verbatim
- ❌ Hashtag spam (Mastodon treats them as inline text; 1-3 max)
- ❌ No content warnings for spicy / political content
- ❌ Tagging users from non-federated instances