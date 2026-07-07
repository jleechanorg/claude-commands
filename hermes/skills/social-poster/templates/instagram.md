# Instagram Caption Template

**Character limits:**
- Caption: **2,200 chars max** (hard limit; truncation at ~125 chars before "...more")
- Hashtags: **30 max** total per post
- Alt text: optional, **100 chars max** for the alt field per image

**Voice:** Visual-first. Caption supports the image, doesn't replace it.

**Hashtag strategy:**
- 8-15 hashtags is the sweet spot (2026 data; >30 hurts reach)
- Mix: 3-5 niche (<50K posts), 3-5 mid (50K-500K), 2-3 broad (>500K)
- Place hashtags in first comment OR after a line-break-dots separator in the caption

## Template

```
{{HOOK_LINE}} ({{1-2_EMOJI}})

{{STORY_OR_CONTEXT_2-3_SENTENCES}}.

{{CTA_LINE}}.

.
.
.
#{{TAG_NICHE_1}} #{{TAG_NICHE_2}} #{{TAG_NICHE_3}} #{{TAG_MID_1}} #{{TAG_MID_2}} #{{TAG_MID_3}} #{{TAG_BROAD_1}} #{{TAG_BROAD_2}}
```

## Alt text (for image)

```
{{CONCRETE_DESCRIPTION_OF_IMAGE_FOR_SCREEN_READERS}}
```

## Anti-patterns

- ❌ >30 hashtags (penalized)
- ❌ Hashtags only in caption (no body — wastes the first 125 chars)
- ❌ Engagement bait ("Tag a friend who…", "Save this for later")
- ❌ No image / no visual (Instagram without a visual gets buried)

## Web compose reality

Instagram has **no web compose flow** (as of 2026-07-05). `scripts/post_approved.py` will print the caption + alt-text and surface mobile-app instructions instead of clicking submit.