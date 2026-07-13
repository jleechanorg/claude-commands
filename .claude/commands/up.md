# /up — Update All Agent Instruction Files

Update `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, `~/.gemini/GEMINI.md`, `~/.cursor/rules/`, and Hermes user policy with a new rule or preference stated in the argument.

## EXECUTION INSTRUCTIONS

When invoked as `/up <instruction>`, you (Claude) must immediately:

### Step 1 — Determine what to add
Parse the argument as a plain-English instruction describing a preference or rule.
For each target file, synthesize the appropriate addition:
- Keep it concise (1–4 lines)
- Use the existing style of that file
- Place it in the most relevant existing section, or append under `## Node / Runtime` if no section fits
- If the instruction concerns localhost, browser UI, campaign pages, or user-visible web behavior, preserve the rule that verification must use Playwright MCP headless. Curl/HTTP checks can support server health, but they do not prove browser UI behavior; report redirects, console errors, screenshots, and whether the target page actually rendered.
- If the instruction concerns autonomous work, `/a`, `/fullrun`, `/finish`, `/auto`, hands-off mode, left/right-shift attention, or evidence cadence, update Hermes `SOUL.md` as well as every coding CLI instruction surface. The rule must say: front-load planning/setup, avoid mid-task interruption questions, make reversible judgment calls, and back-load verification/evidence before "done".
- **If the instruction creates or updates a slash command (any repo or user scope):** the command file must be a THIN dispatcher pointing at a skill — frontmatter + "Read `<skill>/SKILL.md` and execute with $ARGUMENTS" + usage examples, ≤ ~15 lines. All workflow substance lives in the SKILL.md (canonical pattern: /ms → memory-search; reference implementations: /ironclad, /cmux-goal). Never write a fat command file; if one exists, /skillify it (contract item 11).
- **If the instruction concerns auth / login / Keychain / OAuth / TTY / interactive prompts:** any rule about "do not recommend a fresh login / interactive re-auth before probing" must also be added to the rule below as a permanent guard. The recurring anti-pattern is an agent collapsing a narrow signal (`agy account list` TTY error, missing `oauth_creds.json`, sandbox HOME without token file) into "needs re-login" without probing the durable credential source first. The two-probe rule below is non-negotiable: every CLI policy surface gets it.

### Step 2 — Target files (user-global scope)

| File | Tool |
|------|------|
| `~/.claude/CLAUDE.md` | Edit |
| `~/.codex/AGENTS.md` | Edit |
| `~/.gemini/GEMINI.md` | Edit |
| `~/.cursor/rules/env-preferences.mdc` | Write (create if missing) |
| `~/.hermes/workspace/SOUL.md` (tracked source for `~/.hermes/SOUL.md`) | Edit when the rule affects Hermes behavior |
| `~/.hermes/skills/RESOLVER.md` | Edit only when adding/changing slash command or skill trigger routing |

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
