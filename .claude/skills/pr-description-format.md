---
name: pr-description-format
description: Required PR description sections — Background, Goals, Tenets, High-level, Testing, Low-level details
type: policy
---

# PR Description Format

Every PR description must include the following sections in order:

## Background

What context led to this change? What problem or opportunity is being addressed? Include relevant links, tickets, or prior decisions.

## Goals

What outcomes should this PR achieve? State them as concrete, verifiable objectives.

## Tenets

Guiding principles that constrained design decisions (e.g., "prefer real tests over mocks", "no breaking API changes", "minimize scope").

## High-level description of changes

Summarize what was changed and how it accomplishes the goals. Focus on the "why" behind architectural choices, not just the "what".

## Testing

How was this tested? Include:
- Unit tests added/modified
- Integration or E2E tests run
- Manual verification steps performed
- Any CI results or evidence bundles

## Low-level details (up to 20 files)

For each changed file (pick top 20 most important if more than 20):
- **File path**: Justification for changing this file, what changed, why it was changed this way.
