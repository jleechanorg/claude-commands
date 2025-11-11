---
description: Get multi-model second opinion (alias for /second_opinion)
aliases: [secondo, secondopinion]
type: ai
execution_mode: immediate
---

# /secondo - Second Opinion Command Alias

This is an alias for the `/second_opinion` command.

See [second_opinion.md](second_opinion.md) for complete documentation.

## Command Behavior Notes

- Invoke the same workflow described in `/second_opinion`.
- When calling the MCP tool, rely on default model selection—**do not** send `primaryModel`, `secondaryModels`, or `maxOpinions` arguments.
  - (`primaryModel` specifies the main model to use, `secondaryModels` lists additional models for comparison, and `maxOpinions` sets the number of model responses. For details, see [second_opinion.md](second_opinion.md).)
  - (`primaryModel` specifies the main model, `secondaryModels` lists comparison models, and `maxOpinions` sets the number of responses. For more detail, see [second_opinion.md](second_opinion.md).)
- Provide only the `feedback_type` and/or question context that the user supplied.

## Quick Usage

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

## Full Documentation

For complete documentation, authentication setup, and detailed usage instructions, see:
- [second_opinion.md](second_opinion.md)
- Skills: `test-credentials` for OAuth testing setup
