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