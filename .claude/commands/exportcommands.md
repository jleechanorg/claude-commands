---
description: /exportcommands - Export Claude Commands to Reference Repository
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**

## 🚨 EXECUTION WORKFLOW

### Phase 1: Preparation & Validation

1. Validate GitHub token and permissions for target repository
2. Check if target repository exists and is accessible
3. Set $PROJECT_ROOT if not already set (use `git rev-parse --show-toplevel`)
4. Verify `~/.claude/commands/exportcommands.sh` exists

### Phase 2: Content Export (CODE AND MARKDOWN ONLY)

1. Execute the shell implementation:
```bash
bash ~/.claude/commands/exportcommands.sh
```

**Implementation Details**:
- **Automatic Filtering**: Only `.md`, `.py`, `.sh`, `.yml`, `.yaml`, and `.json` files are exported.
- **Asset Exclusion**: All binary/asset files (e.g., `.png`, `.jpg`, `.pdf`) are strictly excluded.
- **Content Masking**: Project-specific strings and paths are automatically replaced with placeholders.
- **Union Merge**: Intelligently merges global and project-specific Claude configurations.

### Phase 3: Verification

1. Ensure the export PR URL is printed as the final output.
2. Verify that NO asset files were included in the export.

## 📋 REFERENCE DOCUMENTATION

🚨 **CRITICAL SUCCESS REQUIREMENT**: This command MUST always print the export PR URL as the final output.

🚨 **REPOSITORY SAFETY RULE**: Export operations NEVER delete, move, or modify files in the current repository.

**Purpose**: Export your complete command composition system to https://github.com/jleechanorg/claude-commands for reference and sharing

**Implementation**: This command delegates all technical operations to `exportcommands.sh` while providing LLM-driven orchestration.

**Usage**: `/exportcommands` - Executes complete export pipeline with automated PR creation

## 🎯 COMMAND COMPOSITION ARCHITECTURE

At its core, `/exportcommands` is exporting a complete **command composition system** that transforms how you interact with Claude Code.

### Key Compositional Commands Being Exported

**Workflow Orchestrators**:
- `/pr` - Complete PR workflow (analyze → fix → test → create)
- `/copilot` - Autonomous PR analysis and fixing
- `/execute` - Auto-approval development with TodoWrite tracking
- `/orch` - Multi-agent task delegation system

**Building Blocks**:
- `/think` + `/arch` + `/debug` = Cognitive analysis chain
- `/test` + `/fix` + `/verify` = Quality assurance chain
- `/planexec` + `/implement` + `/validate` = Development chain

## ⚡ COMMAND COMBINATION SUPERPOWERS

Combine multiple commands in a single prompt to create sophisticated multi-step workflows:
`Give this PR a thorough code review with /archreview /thinkultra /fake`

1. `/archreview` - Architectural analysis
2. `/thinkultra` - Deep strategic thinking
3. `/fake` - Detection of placeholder or incomplete code
