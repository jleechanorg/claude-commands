# CLAUDE.md

This file provides Claude Code specific guidance when working with this repository.

## Primary Operating Protocol

All operating protocols, development guidelines, and project-specific rules are maintained in `.cursor/rules/rules.mdc`.

## Claude Code Specific Behavior

When using Claude Code (claude.ai/code):

1. **Directory Context**: Claude Code operates within the specific worktree directory shown in the environment information
2. **Tool Usage**: Claude Code has access to file operations, bash commands, and web tools  
3. **Test Execution**: Use `vpython` with the `TESTING=true` environment variable
4. **File Paths**: Always use absolute paths when referencing files
5. **Gemini SDK**: Always use `from google import genai` (NOT `google.generativeai`)
6. **Path Conventions**: `roadmap/` always means `/roadmap/` from project root

The complete operating protocol is in `.cursor/rules/rules.mdc` - refer to that file for all development guidelines.