# Codebase Analysis: Where Are The Lines?

## Current Codebase Size (Existing Lines)

### Total Core Code: ~81,045 lines in mvp_site/
- **Python**: 67,398 lines (83%)
  - Main app logic: ~45,000 lines
  - Tests: ~22,000 lines
- **JavaScript**: 8,534 lines (10.5%)
  - app.js: 1,152 lines
  - campaign-wizard.js: 1,024 lines
  - Other UI components: ~6,358 lines
- **CSS**: 3,819 lines (4.7%)
  - style.css: Main styles
  - interactive-features.css: 696 lines
- **HTML**: 1,294 lines (1.6%)

### Other Directories:
- **roadmap/**: 40,266 lines (documentation, planning)
- **testing_ui/**: 15,220 lines (browser tests)
- **prototype/**: 10,743 lines (early experiments)
- **scripts/**: 4,290 lines (automation tools)
- **testing_http/**: 3,683 lines (HTTP tests)
- **docs/**: ~2,000 lines (documentation)
- **analysis/**: 1,051 lines (data analysis)

### Total Project: ~166,070 lines of actual code/docs

## Where Did 570K Lines of Changes Go?

### Changes by Directory (404K added + 166K deleted = 570K total):

1. **mvp_site/**: 233,440 lines changed (41%)
   - Most changed files:
     - llm_service.py: 163 changes
     - main.py: 122 changes
     - static/app.js: 81 changes
   - Heavy refactoring of core services
   - Multiple format migrations (string → JSON)

2. **Other**: 217,769 lines changed (38%)
   - World files: ~100K lines
     - world/celestial_wars_alexiel_book.md
     - world/world_assiah.md variations
   - Test data files: ~40K lines
   - CLAUDE.md: 117 changes (5,596 lines churned)
   - Cursor rules: ~20K lines

3. **roadmap/**: 51,755 lines changed (9%)
   - Continuous documentation updates
   - Sprint planning files
   - Architecture documents

4. **testing_ui/**: 40,903 lines changed (7%)
   - New browser test infrastructure
   - Test framework iterations

5. **prototype/**: 13,263 lines changed (2%)
   - Early experiments moved/refactored

6. **scripts/**: 5,772 lines changed (1%)
   - Automation tools added

## Key Insights

### Why 570K lines for 81K codebase?

1. **High Churn Rate**: 7:1 ratio means each line changed ~7 times
   - String → Array → JSON migrations
   - Multiple CSS fixes for same features
   - Repeated optimization rounds

2. **Documentation Explosion**:
   - CLAUDE.md alone: 117 edits
   - World files: Multiple versions created/deleted
   - Roadmap files: Constant updates

3. **Test Coverage Growth**:
   - Tests grew from minimal to 22K lines
   - Multiple test framework changes
   - Browser tests added late

4. **Refactoring Patterns**:
   - llm_service.py: Changed 163 times
   - main.py: Changed 122 times
   - Core services rewritten multiple times

### Where Most Code Lives vs Where Most Changes Happen

**Lives** (existing):
- 83% Python (core logic)
- 10% JavaScript (UI)
- 5% CSS
- 2% HTML

**Changes** (activity):
- 41% mvp_site core
- 38% world/docs/config files
- 9% roadmap documentation
- 7% testing infrastructure
- 5% other

This shows heavy iteration on core services and constant documentation updates, supporting the "too fast" diagnosis from the productivity analysis.
