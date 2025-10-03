# /cons Command Documentation

The `/cons` command aggregates consolidated summaries for large pull requests.

## Usage

```bash
/cons [--refresh] [filters]
```

## Behavior
- Fetches outstanding code review comments and status information.
- Produces a condensed summary for async stakeholders.
- Supports optional `--refresh` flag to force data reload.

## Related Commands
- `/con` for contextual conversation history.
- `/commentreply` to author follow-up responses.
