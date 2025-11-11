---
description: /arch Command (Alias)
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### Phase 1: Execute Documented Workflow

**Action Steps:**
1. Review the reference documentation below and execute the detailed steps sequentially.

## 📋 REFERENCE DOCUMENTATION

# /arch Command (Alias)

**Alias for**: `/archreview`

**Purpose**: MVP-focused architecture review for solo developers - prioritizes shipping speed over perfection.

## Solo MVP Context

**Target**: Solo developer working on MVP project
- **No team concerns** (velocity, skills, coordination)
- **No backward compatibility** (breaking changes allowed)
- **Speed over polish** (ship fast, iterate)
- **Pragmatic decisions** ("good enough" that works)

## Usage

```
/arch [scope]
```

**Identical behavior to `/archreview`** - see [archreview.md](./archreview.md) for full documentation.

## MVP-Focused Examples

```bash
/arch                    # Review current changes for shipping readiness
/arch codebase          # Solo maintainability health check
/arch api               # Simple, shippable API design
/arch security          # MVP security basics (not enterprise)
```

Executes dual-perspective review optimized for MVP shipping priorities and solo developer constraints.
