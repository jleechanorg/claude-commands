# CLAUDE.md

This file provides Claude Code specific guidance when working with this repository.

## Primary Operating Protocol

All operating protocols, development guidelines, and project-specific rules are maintained in `.cursor/rules/rules.mdc`. 

**IMPORTANT**: Always read `.cursor/rules/rules.mdc` as the single source of truth for:
- Project overview and architecture
- Development commands and workflows
- Testing protocols
- Code review processes
- Git workflow and merge protocols
- Critical lessons and rules
- **Plan Review Protocol** (two-stage review process)

## Claude Code Specific Behavior

When using Claude Code (claude.ai/code):

1. **Directory Context**: Claude Code operates within the specific worktree directory shown in the environment information
2. **Tool Usage**: Claude Code has access to file operations, bash commands, and web tools
3. **Test Execution**: Use `vpython` with the `TESTING=true` environment variable as specified in rules.mdc
4. **File Paths**: Always use absolute paths when referencing files in responses
5. **Gemini SDK**: Always use `from google import genai` (NOT `google.generativeai`)
6. **Path Conventions**: 
   - `roadmap/` always means `/roadmap/` from project root
   - Never assume relative paths - always clarify from project root
   - See Directory and Path Conventions in rules.mdc

The complete operating protocol is in `.cursor/rules/rules.mdc` - refer to that file for all development guidelines.