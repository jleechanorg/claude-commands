---
description: Get multi-model second opinion on design, code review, or bugs
aliases: [secondopinion]
---

# Second Opinion Command

Get comprehensive multi-model AI feedback on your code, design decisions, or bug analysis.

## ⚡ Execution Instructions for Claude

When `/second_opinion` (or its `/secondo` alias) is invoked, follow this protocol:

1. Call the AI Universe MCP tool `agent.second_opinion` (or run `scripts/secondo-cli.sh`) using only the necessary context arguments such as `feedback_type` and the end-user question.
2. **Do not** include optional tuning fields like `primaryModel`, `secondaryModels`, or `maxOpinions` in the request payload—allow the backend defaults to determine model selection and opinion counts.
3. If no question is provided, fall back to the built-in prompts from the CLI for the chosen `feedback_type`.

## Usage

```bash
# Get second opinion on current context
/secondo

# Specify feedback type
/secondo design
/secondo code-review
/secondo bugs

# With specific question
/secondo "Should I use Redis or in-memory caching for rate limiting?"
```

## How It Works

This command:
1. Analyzes your current context (open files, recent changes, or provided question)
2. Sends request to AI Universe MCP server for multi-model analysis
3. Returns comprehensive synthesis from 5 AI models (Cerebras, Gemini, Perplexity, OpenAI, Grok)
4. Provides actionable recommendations with industry sources

## Authentication

Requires authentication token from `node scripts/auth-cli.mjs login`

## Rate Limits

- **Authenticated**: 60 requests/hour (includes synthesis requests)
- **Multi-model synthesis**: 1 per hour per user (counts toward the 60/hr quota)
- Token expires after 30 days

## Output Format

Display results in markdown with:
- 📊 Summary (models used, tokens, cost)
- 🎯 Primary Opinion (Cerebras)
- 💡 Secondary Perspectives (Gemini, Perplexity, OpenAI, Grok)
- ✨ Final Synthesis (consensus with sources)
- 🔗 Industry Sources (clickable links)
