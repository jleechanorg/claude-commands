# Memory Entity Design for jleechan2015's Patterns

## Entity Structure

### Core Entities

#### 1. Developer Entity
- **Name**: jleechan2015
- **Type**: developer
- **Observations**:
  - Primary developer of WorldArchitect.AI
  - Uses urgency indicators like 'urgent' to convey priority
  - Prefers focused, minimal changes when context is low
  - Values comprehensive testing and quality standards
  - Works systematically through test-driven development
  - Documents learnings and patterns for future reference

#### 2. Coding Patterns

**urgent_context_pattern**
- **Type**: coding_pattern
- **Observations**:
  - When jleechan2015 mentions 'urgent' or 'context', they want minimal, focused changes
  - Urgency indicators signal to avoid comprehensive refactoring
  - Context awareness is critical - check remaining context percentage
  - Preserve working code and make only essential modifications
  - Skip nice-to-haves and focus on primary objective

**focused_execution_mode**
- **Type**: execution_pattern
- **Observations**:
  - Activated by urgency indicators or low context warnings
  - Skip comprehensive analysis and go straight to solution
  - Make surgical edits only where necessary
  - Defer refactoring and improvements to future PRs
  - Prioritize task completion over code perfection
  - Document technical debt for later addressing

#### 3. Quality Standards

**code_quality_standards**
- **Type**: quality_standard
- **Observations**:
  - 100% test pass rate required - no partial successes accepted
  - Never skip failing tests or blame pre-existing issues
  - Use evidence-based debugging with exact error messages
  - Follow SOLID principles and DRY patterns
  - Constants over hardcoded strings for maintainability
  - All imports must be at module level - zero tolerance

**testing_methodology**
- **Type**: development_pattern
- **Observations**:
  - Red-green TDD methodology is standard practice
  - Write failing tests first, then minimal code to pass
  - Test behavior not implementation details
  - Browser tests use Puppeteer MCP by default in Claude Code
  - Integration tests verify real system behavior
  - Coverage analysis via run_tests.sh --coverage only

#### 4. Review and Communication

**review_preferences**
- **Type**: review_pattern
- **Observations**:
  - Always include branch header in responses
  - Be extremely self-critical - no false positivity
  - Show evidence before making claims
  - Document learnings immediately when corrected
  - Follow structured analysis format for complex tasks
  - Prefer editing existing files over creating new ones

**communication_style**
- **Type**: preference
- **Observations**:
  - Direct and concise responses preferred
  - No emojis unless explicitly requested
  - Evidence-based claims with specific line numbers
  - Bullet points for clarity in complex topics
  - Acknowledge uncertainties with warning markers
  - Self-critical tone without excessive celebration

#### 5. Workflow Patterns

**git_workflow**
- **Type**: workflow_pattern
- **Observations**:
  - All changes through PRs - never push to main directly
  - Branch header required in every response
  - Descriptive branch names like feature/task-description
  - Verify push success by checking remote commits
  - PR marked complete only when MERGED, not just OPEN
  - Use integrate.sh for fresh branches after merge

**error_handling_approach**
- **Type**: debugging_pattern
- **Observations**:
  - Extract exact error messages before analyzing
  - Trace data flow from backend to frontend systematically
  - Never assume - always verify with evidence
  - Check both .py and .js files for string origins
  - One bug often indicates systemic issues - search broadly
  - Document root cause analysis in lessons.mdc

#### 6. Project Context

**worldarchitect_ai_project**
- **Type**: project
- **Observations**:
  - AI-powered tabletop RPG platform (digital D&D 5e GM)
  - Stack: Python 3.11/Flask/Gunicorn, Gemini API, Firebase Firestore
  - Frontend: Vanilla JS/Bootstrap for simplicity
  - Deployment: Docker/Cloud Run architecture
  - Critical files: CLAUDE.md for AI rules, mvp_site/ for core code
  - Test infrastructure in testing_ui/ and testing_http/

## Relationships

### Primary Relationships

1. **jleechan2015** → "prefers" → **urgent_context_pattern**
   - The developer actively uses this pattern for efficient work

2. **jleechan2015** → "enforces" → **code_quality_standards**
   - Strict adherence to quality metrics

3. **jleechan2015** → "maintains" → **worldarchitect_ai_project**
   - Primary maintainer relationship

4. **urgent_context_pattern** → "triggers" → **focused_execution_mode**
   - Urgency indicators activate focused mode

5. **focused_execution_mode** → "defers" → **code_quality_standards**
   - Temporarily postpones refactoring for speed

6. **testing_methodology** → "supports" → **code_quality_standards**
   - TDD ensures quality standards are met

7. **review_preferences** → "implements" → **communication_style**
   - Review patterns reflect communication preferences

8. **git_workflow** → "enables" → **testing_methodology**
   - PR workflow ensures tests run before merge

9. **error_handling_approach** → "documents-in" → **worldarchitect_ai_project**
   - Debugging learnings stored in project files

10. **communication_style** → "reflects" → **urgent_context_pattern**
    - Concise communication aligns with focused execution

## Implementation Code

```python
# Once permissions are resolved, this code would create the entities:

# Create all entities
entities = [
    {
        "name": "jleechan2015",
        "entityType": "developer", 
        "observations": [...]  # As defined above
    },
    # ... all other entities
]

# Create all relationships
relations = [
    {
        "from": "jleechan2015",
        "to": "urgent_context_pattern",
        "relationType": "prefers"
    },
    {
        "from": "jleechan2015", 
        "to": "code_quality_standards",
        "relationType": "enforces"
    },
    # ... all other relationships
]

# Would be called via MCP functions:
# mcp__memory-server__create_entities(entities)
# mcp__memory-server__create_relations(relations)
```

## Usage Examples

### Querying Patterns
- Search: "urgent" → Returns urgent_context_pattern and focused_execution_mode
- Search: "test" → Returns testing_methodology and code_quality_standards
- Search: "review" → Returns review_preferences and communication_style

### Understanding Relationships
- Open node: "jleechan2015" → See all related patterns and preferences
- Open node: "urgent_context_pattern" → See what it triggers and who prefers it

### Adding New Observations
- As new patterns emerge, add observations to existing entities
- Create new entities for distinct pattern categories
- Establish relationships to show how patterns interact

This structure captures the key patterns and preferences discovered, making them queryable and maintainable through the memory server system.