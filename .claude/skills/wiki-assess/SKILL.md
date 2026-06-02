---
name: wiki-assess
description: Assess wiki structure and ratios against Karpathy pattern standards
---

# /wiki-assess — Wiki Quality Assessment

## Usage
```
/wiki-assess [<wiki_dir> | --wiki <wiki_dir>]
```

Assess any wiki directory against Karpathy pattern:
- Structure: sources/entities/concepts in wiki/ subdir
- Ratios: Entity and Concept should be >5% of sources
- Index: Curated summaries, not raw content
- Frontmatter: YAML frontmatter with type field

`--wiki <wiki_dir>` or a bare positional path both override the default (`~/llm_wiki/wiki`).

## Execution

### Phase 1: Resolve wiki path
```bash
# Check for local wiki default (project-level override)
if [ -f ".wiki-default" ]; then
  WIKI=$(cat .wiki-default)
elif [ -f "$HOME/.wiki-default" ]; then
  WIKI=$(cat "$HOME/.wiki-default")
else
  WIKI="$HOME/llm_wiki/wiki"
fi
# Accept either positional arg or --wiki flag (both override .wiki-default)
if first positional arg is a path (not a flag); then
  WIKI="<first positional arg>"
elif args contain "--wiki <path>"; then
  WIKI="<path>"
fi
```

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
- `/wiki-assess --wiki $HOME/agent-f/jleechan_llm_wiki/wiki` — assess agent-f wiki
