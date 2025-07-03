# CLAUDE.md - Claude Code Specific Configuration Only

⚠️ **DO NOT ADD GENERAL RULES HERE** ⚠️
- General operating protocols → `.cursor/rules/rules.mdc`
- Technical lessons → `.cursor/rules/lessons.mdc`
- This file → Claude Code tool-specific behavior ONLY

## What Belongs Here
✅ Claude Code specific tool usage
✅ Claude Code environment variables
✅ Claude Code file path handling
❌ General development rules
❌ Testing protocols
❌ Git workflows
❌ Code review processes
❌ Integration patterns

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WorldArchitect.AI is an AI-powered tabletop RPG platform that serves as a digital Game Master for D&D 5e experiences. The application uses Google's Gemini AI to generate dynamic narratives, manage game mechanics, and create interactive storytelling.

## Technology Stack

- **Backend**: Python 3.11 + Flask + Gunicorn
- **AI Service**: Google Gemini API (2.5-flash, 2.5-pro models) via `google-genai` SDK
- **Database**: Firebase Firestore for persistence and real-time sync
- **Frontend**: Vanilla JavaScript (ES6+) + Bootstrap 5.3.2
- **Deployment**: Docker + Google Cloud Run

## Development Commands

### Testing

**CRITICAL RULE: Test File Placement**
- **ALL test files** must be placed in the `mvp_site/tests/` directory
- **NO test files** should be created in the root `mvp_site/` directory
- **Test naming**: All test files must follow the pattern `test_*.py`
- **Organization**: Group related tests in the same file when possible
- **Migration**: Any existing test files in the root directory must be moved to `tests/`

```bash
# Run all tests (must be in mvp_site directory)
cd mvp_site && TESTING=true vpython -m unittest discover

# Run specific test file (note: now in tests/ directory)
cd mvp_site && TESTING=true vpython -m unittest tests.test_integration

# Run data integrity tests (catches corruption bugs)
cd mvp_site && TESTING=true vpython -m unittest tests.test_data_integrity

# Run combat integration tests (end-to-end combat flow)
cd mvp_site && TESTING=true vpython -m unittest tests.test_combat_integration

# Run specific test method
cd mvp_site && TESTING=true vpython -m unittest test_module.TestClass.test_method
```

### Running the Application
```bash
# Development (from mvp_site directory)
cd mvp_site && vpython main.py

# Production (Docker)
./deploy.sh                 # Deploy to dev environment
./deploy.sh stable          # Deploy to stable environment
```

### Environment Setup
- Always use the project virtual environment (`venv`)
- Set `TESTING=true` environment variable when running tests (uses faster AI models)
- Firebase service account configured via environment variables

## Architecture

### Core Components

- **`main.py`**: Flask application entry point with API routes
- **`game_state.py`**: Campaign state management, combat system, data migrations
- **`gemini_service.py`**: AI integration with context management and personality-driven responses
- **`firestore_service.py`**: Database operations and real-time synchronization
- **`document_generator.py`**: Export campaigns to PDF/DOCX/TXT formats

### AI System

The platform uses three specialized AI personas:
- **Narrative Flair**: Storytelling and character development
- **Mechanical Precision**: Rules and game mechanics  
- **Calibration Rigor**: Game balance and design

System instructions are stored in `prompts/` directory with MBTI personality definitions in `prompts/personalities/`.

### Data Architecture

- **Firestore Collections**: Campaigns, game states, user data
- **State Management**: Deep recursive merging for nested updates
- **Schema Evolution**: Defensive data access patterns for backward compatibility
- **Append-Only Patterns**: Game history preserved through append operations

## Important Development Patterns

### Gemini API Usage
```python
# Use modern google-genai SDK patterns
# CRITICAL: Always use google.genai (NOT google.generativeai)
from google import genai
from google.genai import types
client = genai.Client(api_key=api_key)
response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
```

### Data Handling
```python
# Defensive data access for schema evolution
campaign_data.get('last_played', 'N/A')  # Backend
campaign?.last_played || 'N/A'           # Frontend

# Type validation for dynamic data
if isinstance(item, dict):
    name = item.get('name', str(item))
```

### Testing Patterns
- Use `TESTING=true` environment variable for faster AI models
- Always use temporary directories for test file operations
- Case-insensitive field detection for AI-generated data
- Flexible assertions for AI content validation

## File Structure

```
mvp_site/                    # Main application
├── main.py                  # Flask routes and application factory
├── game_state.py           # Core state management
├── gemini_service.py       # AI service integration  
├── firestore_service.py    # Database layer
├── static/                 # Frontend assets (app.js, auth.js, style.css)
├── prompts/                # AI system instructions
├── test_*.py              # Comprehensive test suite
└── requirements.txt        # Python dependencies
```

## Key Constraints

- **AI Models**: Current models are `DEFAULT_MODEL = 'gemini-2.5-flash'`, `LARGE_CONTEXT_MODEL = 'gemini-2.5-pro'`, `TEST_MODEL = 'gemini-1.5-flash'` - never change without explicit user authorization
- **Model Usage**: Use TEST_MODEL (1.5-flash) for general tests to save costs, but use DEFAULT_MODEL (2.5-flash) when testing production features like entity tracking
- **SDK**: Must use modern `google.genai` SDK patterns (NOT `google.generativeai`) - Always import with `from google import genai`
- **Virtual Environment**: Always activate `venv` before running Python commands
- **Test Isolation**: Use temporary directories to avoid overwriting application files
- **Data Integrity**: Implement defensive programming for external data sources

## Code Review and Integration Validation

### Critical Review Process
When reviewing code changes or merges, ALWAYS follow this validation process:

1. **Validate AI Instructions Have Implementation**: Always verify that documented AI capabilities (especially in `prompts/` directory) have corresponding code implementation
2. **Trace Data Flow End-to-End**: For any AI-driven feature, trace the complete pipeline: AI instruction → parsing → state updates → storage
3. **Integration Testing Over Syntax**: Treat reviews as functional integration tests, not just code quality checks
4. **Search for Missing Implementations**: Before approving merges, search codebase for referenced tokens/features (e.g., `__DELETE__`, special syntax, documented functions)

### Common Pitfalls to Avoid
- **Never assume documentation equals working implementation** - Always verify
- Focusing on code structure without validating complete data pipelines
- Treating AI instructions as truth rather than specifications to verify
- Missing gaps between what AI is instructed to do vs what code actually processes

### Validation Commands
```bash
# Search for documented features in prompts
grep -r "__DELETE__" prompts/
grep -r "special_token" prompts/

# Verify implementation exists
grep -r "__DELETE__" *.py
grep -r "process.*special_token" *.py
```

**Critical Lesson**: A bug was missed where AI was instructed to use `__DELETE__` tokens for defeated enemies, but no code existed to process these tokens, causing combat state inconsistencies. This type of documentation-implementation gap must be caught during review.

### Automatic Rule Updates
**MANDATORY**: Whenever I make a mistake, encounter a bug I should have caught, or receive correction from the user, I MUST immediately update both CLAUDE.md and .cursor/rules/rules.mdc with the lesson learned. I will not wait for the user to remind me - this is an automatic responsibility that happens every time I fail or am corrected.

### Code Review Blind Spots - Empty String Handling
**CRITICAL RULE**: When refactoring code that checks for truthiness, ALWAYS verify empty string handling:
- ❌ BAD: `if value:` - This skips empty strings which may be valid
- ✅ GOOD: `if value is not None:` - This preserves empty strings
- **Common locations**: JSON parsing, form validation, data extraction
- **Why missed**: Automated refactoring focuses on structural changes, not semantic differences
- **Prevention**: Add specific tests for empty string cases when refactoring conditionals

**Lesson**: Missed empty string handling bugs in JSON parser refactoring because the extraction focused on structural duplication, not behavioral differences. The `if narrative:` check was copied verbatim without considering that empty strings are valid JSON values.

### Temporary Fix Protocol - NEVER GLOSS OVER
**CRITICAL RULE**: When implementing ANY temporary fix or workaround:
1. **IMMEDIATELY flag it** - "⚠️ TEMPORARY FIX: This will break when [specific scenario]"
2. **PROPOSE permanent solution in same message** - Don't wait to be asked
3. **Run the checklist**:
   - [ ] Will this work from a fresh clone?
   - [ ] Will this work in CI/CD?
   - [ ] Will this work for other developers?
   - [ ] Will this work next week/month?
   - [ ] What are ALL the failure scenarios?
4. **Create the permanent fix NOW** - Not "we could fix it" but actually implement it
5. **Document assumptions** - "This assumes [X] which will fail if [Y]"

**Example**: When copying files manually for deployment:
- ❌ BAD: "I copied the files, deployment works now"
- ✅ GOOD: "⚠️ TEMPORARY FIX: I manually copied world/ to fix deployment. This WILL BREAK on next deploy from fresh clone. Creating permanent fix to deploy.sh now..."

**Lesson**: Manually copied world directory for deployment without immediately fixing deploy.sh, causing future deployment failures. Always think about sustainability, not just immediate success.

### Data Corruption Pattern Analysis
**CRITICAL RULE**: When encountering ANY data corruption bug, treat it as a systemic issue requiring comprehensive pattern analysis:
- Search for ALL similar corruption patterns across the codebase (e.g., `str()` conversions, type changes)
- Identify ALL code paths that process the same data structures
- Apply the principle: "If there's one bug of this type, there are likely others"
- Create data integrity audit checklists for similar data structures

**Lesson**: Missed NPC data corruption because I focused on isolated `__DELETE__` bug without auditing all `str()` conversions that could corrupt structured data.

### AI Instruction Priority and Ordering
**CRITICAL RULE**: When AI systems have multiple competing instructions, instruction ORDER determines compliance:
- **Most critical instructions MUST be loaded first** (e.g., state management, core protocols)
- Later instructions can override or distract from earlier ones
- Long instruction sets suffer from "instruction fatigue" where later rules are ignored
- Always prioritize core functionality over stylistic preferences in prompt ordering

**Lesson**: AI was ignoring state update requirements because game state instructions were loaded LAST after lengthy narrative instructions. Moving them FIRST fixed the core state update failure.

### Codebase Exploration Protocol
**CRITICAL RULE**: When working with any codebase, ALWAYS follow this sequence:
1. **Run tests FIRST** - before reading any code, run the full test suite to establish baseline understanding of what works/breaks
2. **Read project documentation** - Review CLAUDE.md, README, and project instructions
3. **Investigate specific issues** - Only then dive into individual files and components

**Lesson**: Failed to catch multiple dependency and API inconsistency bugs because I explored code files individually instead of running tests first. The test suite immediately reveals: current state, expected behavior, dependency issues, and API changes. This systematic approach prevents iterative discovery of issues that should be obvious upfront.

## Deployment

- Multi-environment deployment via `./deploy.sh` script
- Docker containerization with health checks and 300s timeout
- Google Cloud Run with secret management for API keys
- Automatic context-aware deployment from any directory

---

**Remember**: For all general development rules, testing protocols, and operating procedures, see `.cursor/rules/rules.mdc`

## Work Progress Tracking

### Scratchpad Protocol
**MANDATORY**: The main WIP plan must be maintained in `roadmap/scratchpad_[remote_branch_name].md` (e.g., `scratchpad_state_sync_entity.md`). This file must contain:
- **Project Goal**: Clear statement of what the branch aims to achieve
- **Implementation Plan**: Step-by-step plan with milestones
- **Current State**: What's completed, in progress, or blocked
- **Next Steps**: Specific actionable items
- **Key Context**: Important decisions and findings
- **Branch Info**: Remote branch name, PR number, merge target

Update this file after every significant progress point for work continuity.

## Cursor Rules Integration

The complete cursor rules from `/home/jleechan/projects/worldarchitect.ai/.cursor/rules/rules.mdc` are integrated as the primary operating protocol for AI collaboration on this project. Key highlights include:

### Core Principles
- **Meta-Rule**: Check for `.cursor/rules/rules.mdc` file and treat as primary protocol
- **Deletion Prohibited**: Never delete without explicit confirmation
- **Preserve Working Code**: No modifications without permission
- **Focus on Primary Goal**: Don't get sidetracked by linters/cleanup

### Development Guidelines
- **String Constants**: Manage repeated strings as constants
- **Defensive Data Handling**: Validate types before operations
- **Use Modern Gemini SDK**: `google.genai` (NOT `google.generativeai`) - Always use `from google import genai` and `genai.Client()`
- **AI Model Lock**: Current models are `DEFAULT_MODEL = 'gemini-2.5-flash'`, `LARGE_CONTEXT_MODEL = 'gemini-2.5-pro'`, `TEST_MODEL = 'gemini-1.5-flash'` - never change without explicit user authorization
- **Temporary Files for Testing**: Use `tempfile.mkdtemp()`

### Testing Protocol
- **Use `vpython`**: Always run tests with `TESTING=true vpython`
- **Directory Navigation**: `cd mvp_site && TESTING=true vpython test_file.py`
- **Red-Green Testing**: Write failing tests first, then implement
- **Test Truth Verification**: ALWAYS verify tests are testing what they claim - check imports, dependencies, and actual behavior
- **Architecture Decision Tests**: Create separate tests that validate architectural decisions remain valid

### Critical Validation Rules
- **AI Instructions Must Have Implementation**: Verify documented capabilities exist in code
- **Data Flow Tracing**: Follow complete pipeline from AI → parsing → storage
- **Pattern Analysis**: Treat data corruption as systemic, not isolated
- **Automatic Rule Updates**: Update rules immediately when corrected

### Git Workflow
- **Main Branch Source of Truth**: Use `git show main:<file>` for originals
- **Working Code Only**: Never push unverified code
- **Confirm Before Push**: Ask permission before remote operations

### Dead Code Analysis
- **Run Tests First**: Always run tests before removing any code to establish baseline
- **Check Dynamic Usage**: Functions may be used as callbacks or default parameters (e.g., `json.dumps(data, default=func)`)
- **Remove Incrementally**: Remove one item at a time and test after each removal
- **See Full Protocol**: Detailed dead code analysis lessons in `.cursor/rules/lessons.mdc`

The full detailed rules are maintained in `.cursor/rules/rules.mdc` and should be consulted for complete protocol compliance.