# /wiki-search — Search the LLM Wiki

## Usage
```
/wiki-search <query>
```

Search the wiki for pages matching a query. Searches titles, content, and tags.

## Execution

### Phase 1: Resolve wiki path
Use `~/llm_wiki/wiki` as the default wiki.

### Phase 2: Grep search
```bash
QUERY="<user query>"
WIKI="$HOME/llm_wiki/wiki"

# Search titles and content
results=$(grep -rl "$QUERY" "$WIKI"/**/*.md 2>/dev/null | head -20)

# Also search frontmatter titles
title_results=$(grep -rl "title:" "$WIKI"/**/*.md 2>/dev/null | xargs grep -l -i "$QUERY" 2>/dev/null | head -10)

# Combine and deduplicate
combined=$(echo "$results"$'\n'"$title_results" | sort -u | head -20)
```

### Phase 3: Extract context
For each result, extract:
- File path (relative to wiki/)
- Title from frontmatter
- First matching line snippet (50 chars context around match)

### Phase 4: Output
```
## Wiki Search: "<query>"

Found N results:

1. **[Page Title](path/to/page.md)**
   ~path/to/page.md~
   > ...snippet of matching content...

2. **[Page Title](path/to/page.md)**
   ...
```

If no results: `No wiki pages match "<query>".`
