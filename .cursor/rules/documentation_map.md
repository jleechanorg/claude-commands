# Documentation Map

## Hierarchy Overview

```
┌─────────────────────────────────────────────────────┐
│                   rules.mdc                         │
│         (Primary Operating Protocol)                │
│                                                     │
│  • Meta-rules & file hierarchy                     │
│  • Core principles                                 │
│  • Development/Git workflows                       │
│  • Critical rules                                  │
│  • References to:                                  │
│    ├── project_overview.md                         │
│    ├── planning_protocols.md                       │
│    └── lessons.mdc                                │
└─────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
        ▼                                   ▼
┌──────────────────┐              ┌──────────────────┐
│project_overview.md│              │planning_protocols│
│                  │              │       .md        │
│ • Tech stack     │              │                  │
│ • Architecture   │              │ • Decision tree  │
│ • Commands       │              │ • All approaches │
│ • API docs       │              │ • Progress track │
└──────────────────┘              └──────────────────┘
                                            │
                                  References:
                                  • virtual_agents.md
                                  • milestone_planning_structure.md
        
┌──────────────────┐              ┌──────────────────┐
│   lessons.mdc    │              │    CLAUDE.md     │
│                  │              │                  │
│ • Recent only    │              │ • Claude Code    │
│ • Actionable     │              │   specific only  │
│ • Links to rules │              │ • Minimal        │
│                  │              │                  │
│ Archives:        │              └──────────────────┘
│ lessons_archive_ │
│    2024.mdc      │
└──────────────────┘
```

## Quick Navigation

### "Where do I find...?"

| Looking for | Go to |
|------------|-------|
| How to run tests | `project_overview.md` → Development Commands |
| Git workflow | `rules.mdc` → Git & Repository Workflow |
| Planning approach | `planning_protocols.md` → Decision Tree |
| Recent bugs/fixes | `lessons.mdc` |
| Tech stack details | `project_overview.md` → Technology Stack |
| Core principles | `rules.mdc` → Core Principles |
| Old incidents | `lessons_archive_2024.mdc` |

### "Where do I add...?"

| Adding | Put in |
|--------|--------|
| New rule/protocol | `rules.mdc` |
| Lesson from bug | `lessons.mdc` |
| API endpoint doc | `project_overview.md` |
| Planning technique | Reference in `planning_protocols.md` |
| Claude Code specific | `CLAUDE.md` |

## File Purposes

1. **rules.mdc** - The constitution. All rules live here.
2. **project_overview.md** - The encyclopedia. Technical details.
3. **planning_protocols.md** - The playbook. How to approach tasks.
4. **lessons.mdc** - The journal. Recent learnings.
5. **CLAUDE.md** - The tool guide. Claude Code specifics only.

---
*Created: 2025-01-01*
*Purpose: Visual guide to documentation structure*