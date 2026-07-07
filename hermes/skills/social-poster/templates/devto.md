# Dev.to Article Template

**Character limits:**
- Title: **80 chars max** (recommended for SEO)
- Description: **140 chars max** (for OG card)
- Body: **100,000 chars max**
- Tags: **4 tags max** (the 5th gets ignored)

**Voice:** Technical tutorial / deep-dive. Dev.to is where engineers publish long-form; shorter than a Medium post, more code-heavy than a blog.

**Required:**
- Cover image (1000x420 recommended, hosted on Dev.to)
- 2-4 tags (e.g., `ai`, `opensource`, `python`, `tutorial`)
- Canonical URL field if cross-posting (otherwise Dev.to is canonical)

## Template

```
---
title: '{{TITLE_UNDER_80_CHARS}}'
published: {{true_or_false}}
description: '{{DESCRIPTION_UNDER_140_CHARS}}'
tags: {{tag1, tag2, tag3, tag4}}
cover_image: '{{COVER_IMAGE_URL}}'
canonical_url: ''
---

## {{SECTION_HEADER_1}}

{{2-3_PARAGRAPHS}}

## {{SECTION_HEADER_2}}

```{{LANGUAGE}}
{{CODE_BLOCK}}
```

{{EXPLANATION_PARAGRAPH}}

## {{SECTION_HEADER_3}}

{{CONTENT}}

## {{WRAP_UP}}

{{2-3_SENTENCES_CTA}}

Repo: {{URL}}
```

## Anti-patterns

- ❌ Marketing-style headers ("Unlock the Power of AI!")
- ❌ <500 words (Dev.to rewards depth)
- ❌ >4 tags (5th is ignored)
- ❌ No code blocks / all-prose (Dev.to is for engineers)
- ❌ Wall of text without `##` section headers