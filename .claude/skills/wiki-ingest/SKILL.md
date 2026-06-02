---
name: wiki-ingest
description: Ingest a file into the local LLM wiki and update source/entity/concept pages.
---

# /wiki-ingest — Ingest a file into the LLM Wiki

## Usage
```
/wiki-ingest <file_or_path> [--wiki <wiki_dir>]
```

Ingest a source document into the wiki. Creates a source page, extracts entities and concepts, updates the index.

`--wiki <wiki_dir>` overrides the default wiki location (`~/llm_wiki/wiki`). The `raw/` directory is derived as the sibling of the wiki dir: `$(dirname <wiki_dir>)/raw`.

## Execution

### Phase 1: Resolve wiki path and source file
```bash
# Parse args: file is first positional; --wiki <path> overrides default
# Check for local wiki default (project-level override)
if [ -f ".wiki-default" ]; then
  WIKI=$(cat .wiki-default)
elif [ -f "$HOME/.wiki-default" ]; then
  WIKI=$(cat "$HOME/.wiki-default")
else
  WIKI="$HOME/llm_wiki/wiki"
fi
FILE_ARG="<first positional arg>"
# --wiki flag always wins over .wiki-default
if args contain "--wiki <path>"; then
  WIKI="<path>"
fi

WIKI_ROOT=$(dirname "$WIKI")
RAW_DIR="$WIKI_ROOT/raw"
SOURCE="$RAW_DIR/$(basename "$FILE_ARG")"

# Copy source to raw/ if not already there
mkdir -p "$RAW_DIR"
cp "$FILE_ARG" "$SOURCE" 2>/dev/null || cp "$(pwd)/$FILE_ARG" "$SOURCE"

# Determine slug from filename
SLUG=$(basename "$FILE_ARG" | sed 's/\.md$//' | sed 's/[^a-zA-Z0-9]/-/g' | tr '[:upper:]' '[:lower:]')
```

### Phase 2: Read source document
Read the file fully.

### Phase 3: Read wiki context
Read `wiki/index.md` and `wiki/overview.md` for current wiki state.

### Phase 4: Create source page
Write `wiki/sources/<slug>.md` using Source Page Format:

```markdown
---
title: "<title>"
type: source
tags: []
date: YYYY-MM-DD
source_file: <relative path>
---

## Summary
2–4 sentence summary.

## Key Claims
- Claim 1
- Claim 2

## Key Quotes
> "Quote here" — context

## Connections
- [[EntityName]] — how they relate
- [[ConceptName]] — how it connects
```

### Phase 5: Update index
Add entry to `wiki/index.md` under Sources section.

### Phase 6: Oracle impact check
Check if new content affects [[jeffrey-oracle]]. If so, append to `wiki/log.md`.

### Phase 7: Entity & concept extraction
Create entity pages for key people, companies, projects.
Create concept pages for key ideas, frameworks, methods.

### Phase 8: Log
Append to `wiki/log.md`: `## [YYYY-MM-DD] ingest | <Title>`
