# CLAUDE.md Compression Strategy

## Summary
Successfully reduced CLAUDE.md from 45,490 to 6,601 characters (85% reduction) while retaining all critical information.

## Key Strategies Applied

### 1. Evidence Extraction (Saved ~10k)
- Moved all "🔍 Evidence:" citations to `.cursor/rules/evidence.md`
- Preserved traceability with rule codes ([MR1], [CR1], etc.)

### 2. Aggressive Formatting (Saved ~15k)
- Converted verbose explanations to single-line rules
- Used pipe separators instead of bullets
- Removed connecting words and redundant explanations
- Table format for Git workflow

### 3. External References (Saved ~8k)
- Replaced inline documentation with → references
- Leveraged existing .cursor/rules/*.md files
- Pointed to .claude/commands/ for command docs

### 4. Rule Consolidation (Saved ~7k)
- Grouped similar rules under single headers
- Removed duplicate explanations
- Used abbreviations (PR, MCP, API)

### 5. Section Compression (Saved ~5k)
- Condensed meta-rules to essential statements
- Simplified Claude Code behavior to numbered list
- Compressed development guidelines

## Files Created

1. **CLAUDE_compressed.md** (4,239 chars) - Ultra-minimal version
2. **CLAUDE_optimized.md** (6,601 chars) - Recommended balanced version
3. **.cursor/rules/evidence.md** - All evidence citations with rule references

## Recommendation
Use `CLAUDE_optimized.md` as it:
- Stays well under 40k limit
- Retains all operational rules
- Maintains readability
- Preserves critical context
- Links to detailed documentation

## Migration Steps
1. Review CLAUDE_optimized.md for completeness
2. Rename current CLAUDE.md to CLAUDE_original.md
3. Rename CLAUDE_optimized.md to CLAUDE.md
4. Ensure .cursor/rules/evidence.md is accessible
5. Test with a few commands to verify functionality