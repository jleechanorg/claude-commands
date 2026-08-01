# Installation Check (per methodology)

How to verify local install status before recommending changes.

## Superpowers

```bash
# Claude Code marketplace install
ls ~/.claude/plugins/cache/superpowers-marketplace/superpowers/<version>/    # expect: 6.2.0 or newer
ls ~/.claude/plugins/cache/claude-plugins-official/superpowers/<version>/    # alternative: official

# Skills mirror
ls ~/.claude/skills/superpowers-*.md        # expect ~13 files (brainstorming, writing-plans, …)
ls ~/.claude/skills/tessl__*/SKILL.md       # expect ~13 directories (obra's newer naming)

# Codex CLI mirror
ls ~/.codex/plugins/cache/superpowers-marketplace/superpowers/<version>/
ls ~/.codex/plugins/cache/openai-curated/superpowers/*/

# Active in current session?
rg -l "using-superpowers" ~/.claude/plugins/cache/superpowers-marketplace/superpowers/<version>/skills/
```

## GSD Core

```bash
# Local install (post-`npx @opengsd/gsd-core@latest`)
ls ~/.claude/commands/gsd/        # expect: /gsd-* commands
ls ~/.claude/commands/gsd-*/      # alternative kebab form
ls ~/.codex/commands/             # expect: $gsd-* commands

# Skills dropped directly under ~/.claude/skills/ (one dir per skill)
ls ~/.claude/skills/ | grep -c '^gsd-'   # expect: ~71 (profile=full) or ~8 (profile=core)

# Runtime marker + version
cat ~/.claude/gsd-core/.gsd-runtime       # expect: "claude" or other runtime name
cat ~/.claude/gsd-core/VERSION           # expect: "1.9.0" or current
ls ~/.claude/gsd-core/bin/gsd-tools.cjs   # expect: present

# What hooks GSD added (--profile=full installs ~15 always-on hooks)
python3 -c "import json; d=json.load(open('$HOME/.claude/settings.json')); \
  hooks = d.get('hooks',{}); \
  gsd_hooks = [(e, h.get('command','')) for e,arr in hooks.items() for ent in arr for h in ent.get('hooks',[]) if 'gsd' in h.get('command','').lower()]; \
  print(f'GSD-managed hooks: {len(gsd_hooks)}'); \
  [print(f'  {e:14} {cmd}') for e, cmd in gsd_hooks]"

# Active project state (if a project is GSD-onboarded)
ls .planning/                     # expect: PROJECT.md, ROADMAP.md, STATE.md, requirements.md

# What's NOT installed (before recommending)
find ~/.claude ~/.codex -name "*.md" -path "*gsd*" 2>/dev/null | head -5
```

## grill-me

```bash
# Local install (post-`npx skills@latest add mattpocock/skills --skill=grill-me -y -g`)
ls ~/.claude/skills/grill-me/SKILL.md
ls ~/.claude/skills/grilling/SKILL.md
ls ~/.claude/skills/grill-with-docs/SKILL.md      # optional

# The `npx skills` package manager installs 20+ Matt Pocock skills together —
# asking for any one selector pulls the related family (grilling, grill-with-docs,
# batch-grill-me, ask-matt, setup-matt-pocock-skills, to-spec, to-tickets, tdd,
# implement, handoff, teach, research, prototype, code-review, codebase-design,
# domain-modeling, diagnosing-bugs, improve-codebase-architecture,
# resolving-merge-conflicts, wayfinder). Verify all 21 if "installed".

# Or wherever the skills package manager installed it
find ~/.claude ~/.codex -name "SKILL.md" -path "*grill*" 2>/dev/null

# Pitfall: `npx skills add` is INTERACTIVE by default — needs a TTY for the
# multi-select UI. Add `-y` to bypass. The MCP-mail mirror error
# "PromptScript does not support global skill installation" can appear for
# skills that don't have a global-install mapping; they still install locally.
```

## OpenSpec / BMAD / Spec-Kit / Kiro / GSTACK

Same pattern: `find ~/.claude ~/.codex -name "*.md" -path "*<methodology>*"`.

## Quick all-methodology probe

```bash
# Single sweep that covers the most common install locations
find ~/.claude ~/.codex ~/.npm-global -type f \( -name "*.md" -o -name "*.toml" \) 2>/dev/null \
  | rg -i "superpowers|gsd|grill|openspec|bmad|spec-kit|kiro|gstack" \
  | rg -i "skill\.md|install|setup|readme" \
  | head -40
```

## Red flags (do NOT claim "installed" if any of these match)

- File path contains `_archive` or `_archived_loose_md` → historical copy, not active
- File path contains `.bak.` or `.disabled-` → disabled by user
- File path is in `node_modules/` of a project → project's vendored copy, not user-scope
- SKILL.md has `disable-model-invocation: true` → opt-in (grill-me default) — installed but won't auto-fire
- Plugin path is `Disabled=true` plist → installed but disabled