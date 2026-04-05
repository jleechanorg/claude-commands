# /up — Update All Agent Instruction Files

Update `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, `~/.gemini/GEMINI.md`, and `~/.cursor/rules/` with a new rule or preference stated in the argument.

## EXECUTION INSTRUCTIONS

When invoked as `/up <instruction>`, you (Claude) must immediately:

### Step 1 — Determine what to add
Parse the argument as a plain-English instruction describing a preference or rule.
For each target file, synthesize the appropriate addition:
- Keep it concise (1–4 lines)
- Use the existing style of that file
- Place it in the most relevant existing section, or append under `## Node / Runtime` if no section fits

### Step 2 — Target files (user-global scope)

| File | Tool |
|------|------|
| `~/.claude/CLAUDE.md` | Edit |
| `~/.codex/AGENTS.md` | Edit |
| `~/.gemini/GEMINI.md` | Edit |
| `~/.cursor/rules/env-preferences.mdc` | Write (create if missing) |

### Step 3 — Apply updates

For each file:
1. Read the file first
2. Identify the right section (or append)
3. Add the rule — do NOT rewrite unrelated content
4. Confirm with one line: `✓ updated <file>`

### Step 4 — Summary

Print a single table showing what was added to each file.

## Example

`/up prefer Node 22 via nvm, never Homebrew node`

Expected additions:
- CLAUDE.md: Under `## Repository-aligned engineering defaults` — "Node version: always use nvm Node 22 (`~/.nvm/versions/node/v22.22.0`). Never use Homebrew node — it is Node 24 and causes native module ABI mismatches with the openclaw gateway."
- AGENTS.md: Similar rule in the relevant section
- GEMINI.md: Same
- cursor rule: `env-preferences.mdc` with the Node preference
