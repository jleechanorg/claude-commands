# Target Documentation Structure - Step 1.3

## Final Documentation Hierarchy

```
.cursor/rules/
├── rules.mdc                    # Primary operating protocol
├── lessons.mdc                  # Recent actionable lessons
├── lessons_archive_2024.mdc     # Historical incidents archive
└── project_overview.md          # Project architecture and tech stack

.cursor/
├── CLAUDE.md                    # Claude Code specific behavior

coding_prompts/
├── virtual_agents.md            # Perspective-taking framework
├── milestone_planning_structure.md # Planning methodology
└── planning_protocols.md        # Unified planning approach (NEW)

roadmap/
└── scratchpad_*.md             # Active work tracking
```

## File Specifications

### 1. rules.mdc (Primary Protocol)
**Target Size**: ~400 lines
**Purpose**: Single source of truth for all operating protocols
**Contents**:
- Meta-rules and file hierarchy (lines 1-50)
- Core principles & interaction (lines 51-150)
- Development, coding & architecture (lines 151-250)
- Git & repository workflow (lines 251-350)
- Critical rules and lessons (lines 351-400)
- References to other documents

**What Gets Removed**:
- Project overview section → project_overview.md
- Detailed examples → appropriate technique files
- Historical incidents → lessons.mdc

### 2. lessons.mdc (Recent Lessons)
**Target Size**: <300 lines (<5K words)
**Purpose**: Recent actionable lessons and incidents
**Contents**:
- Last 10 significant lessons
- Dated entries with clear headers
- Root cause analyses
- Links to rules they created
- NO protocols or rules

**What Gets Removed**:
- All mandatory protocols → rules.mdc
- Incidents older than 6 months → archive
- Duplicate content → consolidated

### 3. project_overview.md (NEW)
**Target Size**: ~200 lines
**Purpose**: Project-specific technical documentation
**Contents**:
```markdown
# WorldArchitect.AI Project Overview

## Technology Stack
- Backend: Python 3.11 + Flask + Gunicorn
- AI Service: Google Gemini API
- Database: Firebase Firestore
- Frontend: Vanilla JavaScript + Bootstrap
- Deployment: Docker + Google Cloud Run

## Architecture
### Core Components
- main.py: Flask application
- game_state.py: State management
- llm_service.py: AI integration
- firestore_service.py: Database layer

### AI System
- Three specialized personas
- Prompt structure
- Context management

## File Structure
[Directory tree with descriptions]

## Development Commands
### Testing
- Run all tests: ./run_tests.sh
- Specific tests: TESTING=true vpython mvp_site/test_*.py

### Running
- Development: vpython mvp_site/main.py
- Production: ./deploy.sh

## API Reference
[Endpoint documentation]
```

### 4. planning_protocols.md (NEW)
**Target Size**: ~300 lines
**Purpose**: Unified planning and development approaches
**Contents**:
```markdown
# Planning and Development Protocols

## Decision Tree
When to use which approach:
1. Simple bug fix (<30 min) → Direct implementation
2. Feature development (2-8 hours) → Scratchpad + milestones
3. Complex project (days) → Full milestone planning
4. Architecture decisions → Multi-perspective review

## Scratchpad Protocol
[Merged from rules.mdc]

## Milestone Planning
[Reference to milestone_planning_structure.md]

## Multi-Perspective Approach
[Reference to virtual_agents.md]

## Plan Review Protocol
[Moved from rules.mdc]
```

### 5. lessons_archive_2024.mdc (NEW)
**Target Size**: As needed
**Purpose**: Historical record of past incidents
**Contents**:
- All incidents before July 2024
- Superseded lessons
- Historical context
- Searchable archive

### 6. CLAUDE.md (Minimal)
**Target Size**: <50 lines
**Purpose**: Claude Code specific behavior
**Contents**:
```markdown
# CLAUDE.md

This file provides Claude Code specific guidance.

## Primary Protocol
All operating protocols are in `.cursor/rules/rules.mdc`.

## Claude Code Specific
1. Directory Context: Claude Code operates within the worktree shown
2. Tool Usage: File operations, bash commands, web tools available
3. Test Execution: Use `vpython` with TESTING=true
4. Path Conventions: Always use absolute paths
5. Gemini SDK: Use `from google import genai`
```

### 7. virtual_agents.md (Updated)
**Status**: Already updated to clarify perspective-taking
**Changes**: Removed CLI command references

### 8. milestone_planning_structure.md
**Status**: Keep as-is
**Purpose**: Detailed planning methodology

## Migration Checklist

### Phase 1: File Creation
- [ ] Create project_overview.md
- [ ] Create planning_protocols.md
- [ ] Create lessons_archive_2024.mdc

### Phase 2: Content Extraction
- [ ] Extract project info from rules.mdc
- [ ] Extract old lessons from lessons.mdc
- [ ] Extract planning protocols

### Phase 3: Content Movement
- [ ] Move protocols from lessons to rules
- [ ] Update all cross-references
- [ ] Remove redundant content

### Phase 4: Validation
- [ ] Verify file sizes meet targets
- [ ] Test documentation flow
- [ ] Confirm no lost information

## Cross-Reference Updates

### In rules.mdc:
```markdown
## Project Overview
WorldArchitect.AI is an AI-powered tabletop RPG platform.
See `.cursor/rules/project_overview.md` for full details.

## Planning Approaches
For planning methodologies, see `coding_prompts/planning_protocols.md`.
```

### In lessons.mdc:
```markdown
# Lessons Learned & Best Practices

**Meta-Rule:** This file contains recent lessons and incidents only.
For operating protocols, see `.cursor/rules/rules.mdc`.
For historical incidents, see `.cursor/rules/lessons_archive_2024.mdc`.
```

## Benefits of New Structure

1. **Clear Authority**: Each file has distinct purpose
2. **Manageable Sizes**: All files under reasonable limits
3. **Easy Navigation**: Clear where to find/add content
4. **No Redundancy**: Single location for each topic
5. **Maintainable**: Structure supports growth

## Implementation Timeline

1. **Hour 1**: Create new files with headers
2. **Hour 2-3**: Extract and move content
3. **Hour 4**: Update cross-references
4. **Hour 5**: Validate and test
5. **Hour 6**: Final cleanup

Total: ~6 hours of focused work

---
*Created: 2025-01-01*
*Purpose: Step 1.3 of Documentation Optimization*
*Status: Design Complete*
