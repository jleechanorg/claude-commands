# Reddit Post Template

**Character limits:**
- Title: **300 chars max**
- Body (text post): **40,000 chars max**
- Comments: **10,000 chars max**

**Critical rules (verified via Aside probe 2026-07-05):**

| Sub | Spam rule | Format preference |
|-----|-----------|-------------------|
| r/LocalLLaMA | 1/10 rule (<10% self-promo), disclose affiliation, no LLM-generated copy | Text post + details, "I built this because..." framing |
| r/Rag | Reddit 10/90, must cite sources | Text post + comparison/benchmark numbers |
| r/OpenAI | 1/10 rule, no direct-link self-promo posts, must be text post + context | **Text post ONLY for project self-promo**; link posts allowed for non-self content |
| r/ClaudeAI | Claude-specific only | Text post |
| r/ChatGPT | "Self Advertising" rule, ChatGPT-specific | Discussion-first, plug only if relevant |
| r/singularity | **No Self-Promotion / Advertising** | DO NOT POST SELF-PROMO |
| r/MachineLearning | Research-grade content only | Pre-prints, papers — not tool launches |
| r/AGI / r/Futurism | Discussion only | Skip for project launches |

**Universal Reddit rules:**
- 10/90 rule: <10% of your content on this account should be self-promo.
- Disclose affiliation if you have one ("I'm the maintainer of…").
- No engagement-farming ("I found this…", "what do you think?", survey-style).
- Title must NOT contain clickbait: "You won't believe", "This X will blow your mind", "The future of", "Revolutionary".

## Template — r/LocalLLaMA (text post)

**Title (≤80 chars, descriptive, no clickbait):**
```
{{PROJECT}}: {{ONE_LINE_DESCRIPTION_WITH_CONCRETE_DETAIL}}
```

**Body:**
```
I built {{PROJECT}} — a {{ONE_LINE_PITCH}} — because {{PROBLEM_STATEMENT}}.

## What it does

{{2-3_PARAGRAPHS_WITH_BULLETS}}

## How it compares

| {{METRIC}} | {{PROJECT}} | {{BASELINE_1}} | {{BASELINE_2}} |
|---|---|---|---|
| {{ROW_1}} | ... | ... | ... |
| {{ROW_2}} | ... | ... | ... |

## What's missing (would love feedback on)

- {{GAP_1}}
- {{GAP_2}}
- {{GAP_3}}

Repo: {{URL}}
License: {{LICENSE}}
Discord / discussion: {{OPTIONAL}}

---

Disclosure: I'm the maintainer.
```

## Template — r/OpenAI (text post, NOT link post)

**Title:**
```
{{PROJECT}}: {{WHAT_IT_DOES}} ({{CONTEXT_FOR_OPENAI_SUB}})
```

**Body:**
```
I built this for the {{USE_CASE}} workflow.

## Context (why this matters here)

{{2-3_SENTENCES_RELEVANT_TO_OPENAI_USERS}}

## What it does

{{3_BULLETS}}

## What it doesn't do

- {{LIMITATION_1}}
- {{LIMITATION_2}}

## Why I'm posting in r/OpenAI

{{RELEVANCE_TO_OPENAI_TOOLS_OR_APIS}}

Repo: {{URL}}

Happy to answer technical questions, especially about {{TECHNICAL_DETAIL}}.
```

## Template — r/Rag (text post)

**Title:**
```
{{PROJECT}}: {{RAG_SPECIFIC_VALUE_PROP}}
```

**Body:**
```
Built this for {{RAG_USE_CASE}}.

## Comparison vs. {{BASELINE}}

| Metric | {{PROJECT}} | {{BASELINE}} |
|---|---|---|
| Latency | {{N}}ms | {{N}}ms |
| Recall@10 | {{N}} | {{N}} |
| Tokens / query | {{N}} | {{N}} |

## Stack

- Vector DB: {{VECTOR_DB}}
- Embeddings: {{MODEL}}
- Reranker: {{MODEL}}
- Orchestration: {{FRAMEWORK}}

## Reproduce

```
git clone {{REPO}}
cd {{REPO}}
docker compose up
# see benchmarks/ for the eval harness
```

Repo: {{URL}}

## Citation

If you use this in a paper / eval, here's the bibtex:

```bibtex
@software{{{KEY}},
  author = {{{AUTHOR}}},
  title = {{{TITLE}}},
  url = {{{URL}}},
  year = {{{YEAR}}}
}}
```
```

## Anti-patterns (Reddit-wide)

- ❌ Clickbait titles ("You won't believe what this LLM did")
- ❌ Link-only post to r/OpenAI / r/Rag (downranked)
- ❌ Posting same exact body to multiple subs (each sub needs a tailored draft)
- ❌ "I found this cool project..." without affiliation disclosure when you ARE the maintainer
- ❌ Engagement-bait ("What do you think?", "Upvote if useful")
- ❌ Asking for upvotes / stars / engagement