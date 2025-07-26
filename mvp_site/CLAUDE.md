# CLAUDE.md - mvp_site Directory Reference

**PRIMARY RULE SOURCE**: The main operating protocol is in `/CLAUDE.md` at the project root.

This file exists for backward compatibility and directory-specific notes for the mvp_site directory.

## Directory-Specific Notes

### Test File Placement
- **ALL test files** must be placed in the `mvp_site/tests/` directory
- **NO test files** should be created in the root `mvp_site/` directory
- **Test naming**: All test files must follow the pattern `test_*.py`

### Running Tests
```bash
# From project root (preferred):
TESTING=true vpython mvp_site/tests/test_integration.py

# If in mvp_site directory:
cd .. && TESTING=true vpython mvp_site/tests/test_integration.py
```

### Claude Code Navigation Best Practices
- **ALWAYS run Python commands from project root** to avoid import errors
- **Use absolute paths** when referencing files in Claude Code
- **Navigation patterns**:
  - `pwd` to check current directory before any Python execution
  - `cd /path/to/project/root` if not at root
  - Use full paths: `vpython mvp_site/test_file.py` ✓
  - Never: `cd mvp_site && vpython test_file.py` ✗

### Key Files in mvp_site
- **main.py**: Flask application entry point
- **game_state.py**: Campaign state management
- **gemini_service.py**: AI integration
- **firestore_service.py**: Database operations
- **prompts/**: AI system instructions

## Important Reminders
- Always refer to `/CLAUDE.md` for the complete operating protocol
- Technical lessons are in `.cursor/rules/lessons.mdc`
- Cursor-specific configuration is in `.cursor/rules/rules.mdc`

## File Addition Protocol

- The AI must not create or propose new files unless strictly necessary for production, CI, or core test coverage.
- Any new file must be:
  - Essential for the main application, CI, or test infrastructure, **and**
  - Justified with a clear reason in the PR or commit message.
- Reference, demo, or exploratory files must be placed in `testing_ui/archive/` or a similar archive directory.
- The AI must always suggest moving non-essential files to archive or deleting them, not adding them to the main repo.
