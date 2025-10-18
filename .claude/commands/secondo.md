---
description: Get multi-model second opinion on design, code review, or bugs
aliases: [secondopinion]
---

# Second Opinion Command

Get comprehensive multi-model AI feedback on your code, design decisions, or bug analysis.

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
3. Returns comprehensive synthesis from 5+ AI models (Cerebras, Gemini, Perplexity, OpenAI, Grok)
4. Provides actionable recommendations with industry sources

## Authentication

Set an `XAI_API_KEY` (or fallback `GROK_API_KEY`) environment variable before running the command to authenticate with the multi-model service. Tokens are provisioned through the AI Universe portal—contact your workspace administrator if you need access.

## Rate Limits

- **Authenticated**: 60 requests/hour
- **Multi-model synthesis**: 1 per hour
- Token expires after 1 hour

## Output Format

Display results in markdown with:
- 📊 Summary (models used, tokens, cost)
- 🎯 Primary Opinion (Cerebras)
- 💡 Secondary Perspectives (Gemini, Perplexity, OpenAI, Grok)
- ✨ Final Synthesis (consensus with sources)
- 🔗 Industry Sources (clickable links)
