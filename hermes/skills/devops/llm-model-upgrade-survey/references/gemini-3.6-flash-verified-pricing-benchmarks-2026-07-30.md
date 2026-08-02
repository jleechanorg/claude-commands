# Gemini 3.6 Flash — verified pricing + benchmark data (2026-07-30)

Source: `https://deepmind.google/models/gemini/flash/` (the canonical comparison page) + `https://openrouter.ai/google/gemini-3.6-flash` (cross-vendor pricing) + `https://ai.google.dev/gemini-api/docs/models/gemini-3.6-flash` (developer docs). Launch date 2026-07-21 per [9to5google](https://9to5google.com/2026/07/21/gemini-3-6-flash-launch/).

## Pricing (verified, list price per 1M tokens)

| Field | Value | Source |
|---|---|---|
| Input | $1.50 / 1M | OpenRouter JSON-LD `1.5e-6` per token |
| Output | $7.50 / 1M | OpenRouter JSON-LD `7.5e-6` per token |
| Cache read | $0.15 / 1M | OpenRouter |
| Cache write | $0.08333 / 1M | OpenRouter |
| Image input | $1.50 / 1M | OpenRouter |
| Audio input | $1.50 / 1M | OpenRouter |
| Context window | 1,048,576 tokens | DeepMind + OpenRouter |
| Max output | 65,536 tokens | DeepMind + OpenRouter |
| Status | General availability | DeepMind model card |
| Modalities | text + image + video + audio + PDF (in); text (out) | DeepMind |

OpenRouter surfaces a per-token price; the vendor list price is the same since OpenRouter's 5% markup is on the FULL routing cost (multiple providers). For raw vendor-API pricing, the OpenRouter JSON-LD is the canonical source.

## Same-vendor benchmark comparison (DeepMind Flash page table)

All numbers from `https://deepmind.google/models/gemini/flash/` comparison table, scraped 2026-07-30. Higher = better. **Bold = leader on that row.**

| Benchmark | Gemini 3.6 Flash | Gemini 3.5 Flash | Gemini 3.1 Pro | GPT-5.6 Luna | Grok 4.5 | Claude Sonnet 5 |
|---|---|---|---|---|---|---|
| Price in / out ($/1M) | $1.50 / $7.50 | $1.50 / $9.00 | $2.00 / $12.00 | $1.00 / $6.00 | $2.00 / $6.00 | $3.00 / $15.00 |
| MLE-Bench (ML eng) | 63.9 % | 49.7 % | 42.6 % | 47.6 % | 43.2 % | **66.9 %** |
| Terminal-Bench 2.1 | 78.0 % | 76.2 % | 73.8 % | **83.3 %** | 80.4 % | n/a |
| CharXiv Reasoning (no tools) | **85.2 %** | 84.2 % | 83.3 % | 82.7 % | 81.6 % | 77.0 % |
| CharXiv Reasoning (with tools) | **89.4 %** | 84.9 % | 83.2 % | — | — | 88.3 % |
| MRCR v2 (128k avg, long-context) | **91.8 %** | 77.3 % | 84.9 % | 74.8 % | 81.4 % | 71.6 % |
| MRCR v2 (1M pointwise) | **54.0 %** | 26.6 % | 26.3 % | — | — | — |
| OSWorld-Verified (agentic) | **83.0 %** | 78.4 % | 76.2 % | — | 72.6 % | 81.2 % |
| GDPVal-AA Elo (knowledge work) | 1421 | 1349 | 965 | **1584** | 1535 | 1607 |

## How to read this when answering "is it worth upgrading"

- **Long-context is the headline win.** 3.6 Flash's 91.8 % on 128k MRCR is +14.5 points over 3.5 Flash and +20 points over Sonnet 5. The 1M pointwise score of 54 % is the **only** model that scores at all on that bucket — every other model is ~26 % or "—" (didn't run). If the user's workload includes long-context retrieval or 1M-context fan-out, 3.6 Flash is the only budget option.
- **Agentic score at half the price of Sonnet 5.** 83.0 % OSWorld at $1.50/$7.50 vs 81.2 % at $3/$15. If the project runs agentic tool-use loops, the cost-per-task score-trade is favorable.
- **Sonnet 5 still leads on raw engineering.** 66.9 % MLE-Bench vs 63.9 % — but the absolute gap is 3 points and the cost is 2×. For a primary synthesis slot (where Sonnet 5 already drives the synthesizing model), the upgrade is not 1:1 worth.
- **GPT-5.6 Luna is the cheapest top-tier alternative** at $1.00/$6.00 with 47.6 % MLE-Bench. Strength: Terminal-Bench 2.1 (83.3 %) and GDPVal-AA Elo (1584). Weakness: long-context (74.8 % on 128k MRCR). For low-context high-throughput workloads, this is the cheapest viable non-Flash option.
- **Grok 4.5 is competitive on agentic + knowledge work** at $2.00/$6.00 with 80.4 % Terminal-Bench and 1535 GDPVal-AA Elo. The web-search citations are stronger than OpenAI's defaults.

## When 3.6 Flash is the wrong upgrade

- **High-volume batch with no long-context need.** If the workload is sub-32k context and runs millions of requests per day, the existing `gpt-5-nano` ($0.05/$0.40) is 13× cheaper on input and 18× cheaper on output. The 3.6 Flash at $1.50/$7.50 is 30× more expensive on input.
- **When the model's voice/tone matters more than scores.** The DeepMind comparison table doesn't measure style — if the user complains about the existing Gemini output feel, 3.6 Flash may inherit whatever caused the complaint. There's no benchmark for tone.
- **When the user is already on Sonnet 5 for the same slot.** Sonnet 5 wins on MLE-Bench (66.9 % vs 63.9 %) at 2× the cost. If quality on engineering tasks is the deciding metric, Sonnet 5 is the right slot.

## Cache pricing reminder

For second-opinion workloads (same prompt sent to N models, prompt cached), the cache_read rate ($0.15/1M) is the dominant cost when the prompt is reused across many calls. 3.6 Flash's cache_read is 10× cheaper than its input rate — a feature that the predecessor `gemini-3-flash-preview` did not have. Surface this in the cost-vs-quality matrix when the user runs high-volume secondary queries (e.g. `agent-second-opinion` MCP tool).
