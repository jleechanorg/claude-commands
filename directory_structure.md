# WorldArchitect.AI Directory Structure

This document provides a comprehensive overview of the project's directory structure to help navigate the codebase efficiently.

## Root Directory (`/home/jleechan/projects/worldarchitect.ai/`)

### Core Application Directory
- **`mvp_site/`** - Main application directory containing all production code
- **`vpython`** - Virtual environment Python wrapper script
- **`run_tests.sh`** - Test runner script for the entire test suite
- **`deploy.sh`** - Deployment script for Google Cloud Run
- **`requirements.txt`** - Python dependencies (symlink to mvp_site/requirements.txt)

### Documentation & Planning
- **`roadmap/`** - Project planning and milestone documentation
  - `templates/` - Document templates
  - `scratchpad_*.md` - Work-in-progress documentation for branches
- **`world/`** - Game world lore and content
  - `banned_names.md` - List of reserved names
  - Various world-building documents

### Development Support
- **`.cursor/`** - Cursor IDE configuration
  - `rules/` - Development rules and guidelines
    - `rules.mdc` - Primary development rules
    - `lessons.mdc` - Learned lessons and patterns
- **`.github/`** - GitHub configuration
  - `workflows/` - GitHub Actions CI/CD pipelines
- **`analysis/`** - Code analysis and metrics
  - `test_results/` - Test execution results

### Legacy/Archive
- **`prototype/`** - Early prototype code (not in production)
- **`data/`** - Legacy data files
- **`scripts/`** - Utility scripts
- **`coding_prompts/`** - Development prompts and examples
- **`ajax-chat/`** - Legacy chat implementation

## Main Application (`mvp_site/`)

### Core Python Modules
- **`main.py`** - Flask application entry point and API routes
- **`gemini_service.py`** - Google Gemini AI integration
- **`game_state.py`** - Game state management and data structures
- **`firestore_service.py`** - Firebase database operations
- **`constants.py`** - Application-wide constants

### Entity Tracking System
- **`entity_tracking.py`** - Core entity tracking functionality
- **`entity_preloader.py`** - Pre-loads entities into prompts
- **`entity_validator.py`** - Validates entity presence in narratives
- **`entity_instructions.py`** - Generates entity-specific instructions
- **`dual_pass_generator.py`** - Two-pass narrative generation

### Support Modules
- **`document_generator.py`** - Export functionality (PDF/DOCX/TXT)
- **`world_loader.py`** - Loads world content for campaigns
- **`debug_mode_parser.py`** - Parses debug content from AI responses
- **`narrative_sync_validator.py`** - Validates narrative consistency
- **`narrative_response_schema.py`** - Structured response handling

### Frontend
- **`static/`** - Static web assets
  - `js/` - JavaScript files
    - `app.js` - Main application logic
    - `auth.js` - Authentication handling
    - `ui_*.js` - UI component modules
  - `styles/` - CSS stylesheets
  - `themes/` - Theme definitions
- **`templates/`** - HTML templates
  - `index.html` - Main application page

### Prompts & AI Instructions
- **`prompts/`** - AI system instructions
  - `narrative_system_instruction.md` - Storytelling guidelines
  - `mechanics_system_instruction.md` - Game mechanics rules
  - `calibration_instruction.md` - Balance and design guidelines
  - `destiny_ruleset.md` - Destiny attribute system rules
  - `game_state_instruction.md` - State management instructions
  - `entity_schema_instruction.md` - Entity tracking schema
  - `personalities/` - MBTI personality definitions

### Data Schemas
- **`schemas/`** - Data structure definitions
  - `entities_pydantic.py` - Pydantic entity models
  - `entities_simple.py` - Simple entity structures

### Testing
- **`tests/`** - Main test directory
  - `data/` - Test data files
    - `validation_results/` - Validation test outputs
    - `sariel_campaign_prompts.json` - Sariel campaign test data
  - `manual_tests/` - Tests requiring manual verification
  - `auth/` - Authentication tests
  - `timing/` - Performance and timing tests
  - `wizard/` - Campaign wizard tests
  - `integration_test_lib.py` - Integration test utilities
  - `test_*.py` - Individual test modules

- **`test_integration/`** - Integration tests (separate for CI/CD)
  - `integration_test_lib.py` - Original integration test library
  - `data/` - Integration test data

### Analysis & Tools
- **`analysis/`** - Analysis scripts and results
  - Scripts for capturing LLM responses
  - Sariel campaign analysis tools

### Configuration & Build
- **`mocks/`** - Mock data for testing
- **`assets/`** - Application assets
- **`bin/`** - Binary executables (e.g., ChromeDriver)
- **`world/`** - Symlink to root world directory
- **`CLAUDE.md`** - Claude Code specific instructions

## Key File Locations

### When Looking For:

**Test Files:**
- Unit tests: `mvp_site/tests/test_*.py`
- Integration tests: `mvp_site/test_integration/test_*.py`
- Manual tests: `mvp_site/tests/manual_tests/`

**AI Prompts:**
- System instructions: `mvp_site/prompts/*.md`
- Personality definitions: `mvp_site/prompts/personalities/*.md`

**Configuration:**
- Constants: `mvp_site/constants.py`
- Claude rules: `.cursor/rules/rules.mdc`
- Environment setup: `mvp_site/requirements.txt`

**Frontend Code:**
- JavaScript: `mvp_site/static/js/`
- CSS: `mvp_site/static/styles/`
- HTML: `mvp_site/templates/`

**World Content:**
- Lore documents: `world/` (root directory)
- Loaded by: `mvp_site/world_loader.py`

## Important Notes

1. **Working Directory**: Most operations should be run from `mvp_site/` directory
2. **Virtual Environment**: Use `vpython` script from project root for Python commands
3. **Test Data**: Shared between `tests/data/` and `test_integration/data/`
4. **Imports**: Python imports assume `mvp_site/` as the base directory
5. **Deployment**: Production code is only in `mvp_site/`, other directories are development support

## Common Mistakes to Avoid

1. Don't look for test files in the root directory - they're in `mvp_site/tests/`
2. Don't look for prompts in the root - they're in `mvp_site/prompts/`
3. Don't confuse `test_integration/` with `tests/` - they serve different purposes
4. Remember that `world/` content is in the root, not in `mvp_site/`
5. The main application entry point is `mvp_site/main.py`, not a file in the root