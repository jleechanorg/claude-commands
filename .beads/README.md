# Beads data in this repository

This repository tracks Beads state as JSONL under `.beads/issues.jsonl`.
The SQLite database file (`.beads/beads.db`) is intentionally excluded from
Git and should be rebuilt locally when needed.

## Local validation

```bash
# Rebuild/update local SQLite DB from tracked JSONL
br import --jsonl .beads/issues.jsonl --db .beads/beads.db

# Verify local DB content
br list --db .beads/beads.db --json --limit 1
```
