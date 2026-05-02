---
name: wiki-assess
description: Assess wiki against Karpathy pattern standards
---

# /wiki-assess — Wiki Quality Assessment

## When invoked

Assess any wiki directory against Karpathy gist pattern:
- Structure: sources/entities/concepts in wiki/ subdir
- Ratios: Entity and Concept should be >5% of sources
- Index: Curated summaries, not raw content
- Frontmatter: YAML frontmatter with type field

## Execution

### Phase 1: Check wiki exists
Accept path argument or default to $HOME/llm_wiki/wiki

### Phase 2: Count pages
```bash
SOURCES=$(ls $WIKI/sources/*.md 2>/dev/null | wc -l)
ENTITIES=$(ls $WIKI/entities/*.md 2>/dev/null | wc -l)
CONCEPTS=$(ls $WIKI/concepts/*.md 2>/dev/null | wc -l)
```

### Phase 3: Calculate ratios
- Entity ratio = ENTITIES / SOURCES * 100
- Concept ratio = CONCEPTS / SOURCES * 100

### Phase 4: Check structure
- Verify wiki/ subdirectory exists
- Verify sources/, entities/, concepts/ subdirs exist
- Check for root duplicates

### Phase 5: Check oracle backlink density
```bash
ORACLE="$WIKI/syntheses/jeffrey-oracle.md"
OUTBOUND=$(grep -oE '\[\[[^]]+\]\]' "$ORACLE" 2>/dev/null | grep -v '|' | sort -u | wc -l)
INBOUND=$(grep -l 'jeffrey-oracle' "$WIKI"/**/*.md 2>/dev/null | wc -l)
```
Target: outbound ≥15, inbound ≥10.

### Phase 6: Output assessment

```
## Wiki Assessment: <wiki_path>

### Structure: ✅/❌
### Ratios:
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Sources | N | - | - |
| Entities | N | - | - |
| Concepts | N | - | - |
| Entity ratio | X% | >5% | ✅/❌ |
| Concept ratio | X% | >5% | ✅/❌ |

### Index Quality: ✅/❌
### Frontmatter: ✅/❌

### Oracle Backlink Density:
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Outbound wikilinks from oracle | N | ≥15 | ✅/❌ |
| Inbound links to oracle | N | ≥10 | ✅/❌ |

### Verdict: COMPLIANT / NON-COMPLIANT
```

## Example usage
- `/wiki-assess` — assess default llm_wiki
- `/wiki-assess ~/memory/wiki` — assess memory wiki