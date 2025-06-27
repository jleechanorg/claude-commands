# CLAUDE.md

**CRITICAL RULE SYNCHRONIZATION: When ANY rule is added, modified, or updated in .cursor/rules/rules.mdc, I MUST immediately update this CLAUDE.md file with the same rule to keep both files synchronized. Both files serve as the operating protocol and must remain consistent.**

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
```bash
# CRITICAL: When user says "run all tests", always use run_tests.sh script from project root
./run_tests.sh

# CRITICAL: When ANY test fails, either fix it immediately or explicitly ask user if it should be fixed

# Run specific test file
cd mvp_site && TESTING=true vpython test_integration.py

# Run data integrity tests (catches corruption bugs)
cd mvp_site && TESTING=true vpython test_data_integrity.py

# Run combat integration tests (end-to-end combat flow)
cd mvp_site && TESTING=true vpython test_combat_integration.py

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
import google.generativeai as genai
client = genai.Client()
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
- **SDK**: Must use modern `google-genai` SDK patterns (not legacy `google-generativeai`)
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

### Agent Approach Recommendation Protocol
**CRITICAL RULE**: Before starting any multi-step task or project, I MUST evaluate and explicitly recommend whether to use a single agent approach or virtual agents/Task tool approach:
- **Analysis Required**: Task complexity, coherence requirements, coordination needs, quality control considerations
- **Single Agent Preferred**: Content requiring consistent tone/style, unified decision-making, cross-referencing, editorial judgment
- **Virtual Agents/Task Tool Preferred**: Parallel research tasks, independent data gathering, multiple specialized perspectives needed
- **Timing**: This recommendation must be provided BEFORE beginning any work on the task

### Automatic Rule Updates
**MANDATORY**: Whenever I make a mistake, encounter a bug I should have caught, or receive correction from the user, I MUST immediately update both CLAUDE.md and .cursor/rules/rules.mdc with the lesson learned. I will not wait for the user to remind me - this is an automatic responsibility that happens every time I fail or am corrected.

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

### Data Structure Schema Enforcement 
**CRITICAL RULE**: When AI systems generate structured data, explicit schemas with mandatory data types must be enforced through prompt engineering:
- **Schema Definition**: Clearly define expected data structures (lists vs dictionaries, required fields)
- **Contradictory Instructions**: Remove any conflicting examples or deprecated patterns that confuse the AI
- **Type Validation**: Add explicit rules forbidding type changes (e.g., "active_missions MUST be a list, never a dictionary")
- **Example Clarity**: Provide concrete examples of correct vs incorrect formatting

**Lesson**: Fixed critical data corruption where AI was changing `active_missions` from list to dictionary and using incorrect `combat_state` schemas by adding explicit data type rules and removing contradictory dot notation examples.

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
- **Use Modern Gemini SDK**: `google-genai` patterns only
- **AI Model Lock**: Current models are `DEFAULT_MODEL = 'gemini-2.5-flash'`, `LARGE_CONTEXT_MODEL = 'gemini-2.5-pro'`, `TEST_MODEL = 'gemini-1.5-flash'` - never change without explicit user authorization
- **Temporary Files for Testing**: Use `tempfile.mkdtemp()`

### Testing Protocol
- **Use `vpython`**: Always run tests with `TESTING=true vpython`
- **Directory Navigation**: `cd mvp_site && TESTING=true vpython test_file.py`
- **Red-Green Testing**: Write failing tests first, then implement

### Critical Validation Rules
- **AI Instructions Must Have Implementation**: Verify documented capabilities exist in code
- **Data Flow Tracing**: Follow complete pipeline from AI → parsing → storage
- **Pattern Analysis**: Treat data corruption as systemic, not isolated
- **Automatic Rule Updates**: Update rules immediately when corrected

### Git Workflow & Merge Protocol
- **Main Branch Source of Truth**: Use `git show main:<file>` for originals
- **Working Code Only**: Never push unverified code
- **Confirm Before Push**: Ask permission before remote operations

### Merge Protocol (NEW)
- **Integrate Pattern**: Always use `git checkout main && git pull && git branch -D dev && git checkout -b dev`
- **Main Branch Protection**: Never work directly on main - use local dev branch
- **PR Creation Process**:
  1. Create feature branch from latest main using integrate pattern
  2. Make changes and commit with descriptive messages
  3. **MANDATORY**: Run `./run_tests.sh` and include test results in PR description
  4. Push branch and create PR with comprehensive description using `gh pr create`
  5. Provide clickable PR URL for user review
  6. After merge, immediately run integrate pattern before next PR
  7. **CRITICAL**: Never use 'dev' as a remote branch for PRs - always use descriptive feature branch names
- **PR Descriptions**: Must include Summary, Changes, Benefits, Usage, and Test Results
- **Post-Merge**: Always run integrate pattern immediately after each merge


### Additional Development Safety Rules

#### Event System Safety
- **Global Event Listeners**: Require explicit approval before using document-wide event listeners
- **Targeted Binding**: Always prefer specific element binding over broad delegation
- **Selector Safety**: Avoid CSS selectors that might match unintended elements

#### System Integration Analysis
- **Feature Categorization**: Classify changes as Surface Feature, Cross-Cutting Concern, or Infrastructure Change
- **Integration Analysis**: Mandatory analysis for cross-cutting concerns before implementation
- **Blast Radius Assessment**: Document all systems a change will affect

#### Core Functionality Protection
- **Workflow Identification**: Identify core user workflows before system modifications
- **Mandatory Testing**: Test all core workflows after any system change
- **Rollback Protocol**: Immediate rollback if core functionality breaks

#### General Principles Over Specific Details
- **Content Separation**: Both `.cursor/rules/rules.mdc` and `CLAUDE.md` must contain **general principles and protocols** only
- **Specific Details Location**: **Specific technical failures, code patterns, and detailed incident analysis** belong in `.cursor/rules/lessons.mdc`
- **File Purpose**: **Rules files** establish timeless operational principles; **lessons files** capture specific technical learning
- **Content Test**: When adding content, ask: "Is this a general principle or a specific technical detail?" and place accordingly

### GitHub CLI Preference for PR Operations
- **Primary Method**: Use `gh pr checkout <PR_NUMBER>` to apply PR changes locally for testing
- **Alternative Method**: If GitHub CLI unavailable, use `git fetch origin pull/<PR_NUMBER>/head:<branch_name>` followed by `git checkout <branch_name>`
- **Benefits**: More convenient and reliable workflow for PR testing, reduces manual errors in branch management

The full detailed rules are maintained in `.cursor/rules/rules.mdc` and should be consulted for complete protocol compliance.