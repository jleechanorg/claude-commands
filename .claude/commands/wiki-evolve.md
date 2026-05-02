# /wiki-evolve — Wiki Pattern Evolution Loop

## Purpose

Self-improving loop that validates llm-wiki against Karpathy pattern, identifies gaps, fixes issues via re-ingest, and verifies compliance. Runs via `/loop 5m /wiki-evolve`.

## Reference
- Karpathy gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Skill: /karpathy-wiki

## Loop Body (executed every 5 minutes)

### Phase 1: OBSERVE — Wiki State Snapshot

```bash
# Check wiki structure
WIKI_DIR="$HOME/llm_wiki/wiki"
echo "=== WIKI STRUCTURE CHECK ==="
ls -la $WIKI_DIR/

# Count pages
echo "Sources: $(ls $WIKI_DIR/sources/*.md 2>/dev/null | wc -l)"
echo "Entities: $(ls $WIKI_DIR/entities/*.md 2>/dev/null | wc -l)"
echo "Concepts: $(ls $WIKI_DIR/concepts/*.md 2>/dev/null | wc -l)"

# Check for root wiki files (should NOT exist)
echo "=== ROOT DUPLICATES CHECK ==="
ls $HOME/llm_wiki/*.md 2>/dev/null || echo "No root .md files (good)"
```

### Phase 2: MEASURE — Pattern Compliance

```bash
# Entity/concept ratio
SOURCES=$(ls $HOME/llm_wiki/wiki/sources/*.md 2>/dev/null | wc -l)
ENTITIES=$(ls $HOME/llm_wiki/wiki/entities/*.md 2>/dev/null | wc -l)
CONCEPTS=$(ls $HOME/llm_wiki/wiki/concepts/*.md 2>/dev/null | wc -l)

echo "=== RATIO CHECK ==="
echo "Sources: $SOURCES, Entities: $ENTITIES, Concepts: $CONCEPTS"
echo "Entity ratio: $(echo "scale=2; $ENTITIES * 100 / $SOURCES" | bc)%"
echo "Concept ratio: $(echo "scale=2; $CONCEPTS * 100 / $SOURCES" | bc)%"

# Index quality check
echo "=== INDEX QUALITY ==="
head -30 $HOME/llm_wiki/wiki/index.md
```

### Phase 3: DIAGNOSE — Identify Gaps

Compare against Karpathy pattern:
1. **Structure**: Only `wiki/` subdirectory, no root duplicates
2. **Ratio**: Entity + Concept should be ~10-20% of sources minimum
3. **Index**: Curated summaries, not raw email subjects
4. **Frontmatter**: All pages have YAML frontmatter with type field

### Phase 4: FIX — Implement Corrections

For each gap found:
1. **Structure gap**: Move content to wiki/, delete root duplicates
2. **Ratio gap**: Re-ingest key sources with mandatory entity/concept extraction
3. **Index gap**: Edit index entries to be curated summaries
4. **Frontmatter gap**: Add missing frontmatter to pages

### Phase 5: VERIFY — Confirm Pattern Compliance

```bash
# Run /wiki-lint
python3 $HOME/llm_wiki/lint.py

# Verify no broken wikilinks
grep -r '\[\[' $HOME/llm_wiki/wiki/sources/*.md | head -20
```

### Phase 6: RECORD — Log Findings

```bash
# Append to wiki evolution log
echo "## $(date '+%Y-%m-%d %H:%M')" >> $HOME/llm_wiki/wiki/evolution-log.md
echo "Sources: $SOURCES, Entities: $ENTITIES, Concepts: $CONCEPTS" >> $HOME/llm_wiki/wiki/evolution-log.md
echo "Issues: [list]" >> $HOME/llm_wiki/wiki/evolution-log.md
```

### Phase 7: RECAP — Cycle Summary

```
## Wiki Evolve Cycle — $(date '+%H:%M')
- Structure: ✅/❌
- Entity ratio: X% (target: >5%)
- Concept ratio: X% (target: >5%)
- Index quality: ✅/❌
- Fixes: [list]
```

## Invocation

```bash
# Start the loop
/loop 5m /wiki-evolve

# Or run one cycle manually
/wiki-evolve
```

## Termination Conditions

1. User says "stop" or "pause"
2. All pattern checks pass for 3 consecutive cycles
3. 2 hours elapsed (wiki doesn't need constant monitoring)