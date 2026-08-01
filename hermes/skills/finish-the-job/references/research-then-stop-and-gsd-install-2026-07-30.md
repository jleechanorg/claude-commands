# Research-then-stop pitfall + GSD Core install findings (2026-07-30)

> Companion reference for the `finish-the-job` umbrella. Linked from
> the skill's body via the "P_research_stop" cross-reference below.

---

## A. Pitfall: Research-report-then-stop

**Symptom (verified 2026-07-30, Slack C09GRLXF9GR):** A `/research` or
"how should we use X" deliverable ends with a `Next actions:` list
(e.g. *install GSD with `--profile=core`, then run `/gsd-onboard` in a
throwaway repo*) but the agent never executes any of those actions
before declaring done. User reply: `Ok will did you even finish the
work?`

**Why this happens:**
- The deliverable looks finished because the report is well-formatted
  (Healthy/Risky/Next sections, citations, clear action list).
- The agent treats the action list as for-the-user-to-do-later, not for
  the agent to do now.
- `proof-before-claim` and `finish-the-job` SOUL.md commits don't gate
  on "the report's own action items have been executed."

**Fix (5-point checklist before any "research is done" claim):**

1. **Every `Next action` line in your own reply MUST have been executed
   by YOU in this session** — not delegated, not deferred, not "queued
   for next turn."
2. **If an action is destructive/expensive/requires user approval**,
   name it explicitly in the reply ("NOT doing X because Y — here's
   the shell block if you want me to run it"). Per
   `diagnosis-requires-followthrough-or-handoff` SOUL.md commit: name
   WHICH of the three end-states (apply / dispatch / hand-off) applies.
3. **If the user typed a mid-turn steer (`do X, don't Y`)**, X must run
   before the session ends. The user's instruction is the new task; the
   prior report is no longer the deliverable.
4. **Install/eval actions are NOT deliverables — they're part of
   finishing the prior one.** A research report that lists
   `npx X --profile=Y` as a `Next action` is incomplete if
   `npx X --profile=Y` has not actually been run with output captured.
5. **Forbidden closing phrases** for any unfinished work: `Done.`,
   `Posted.`, `Here you go.`, `Let me know if you want me to X.` These
   all signal "stopped before the action list ran."

**Disambiguation vs `no-pick-one-menus` / `no-confirmation-gate`:**
THIS pitfall forbids declaring "done" when the report's own action list
has not been executed. Different failure mode, same fix shape: **do the
safe subset, then post a single concise status — never the other way
around.**

**Test:** When you catch yourself typing `Next actions:` — for EACH
bullet, ask: *did I run this in the session already?* If no, run it now
or convert it to a named, approved hand-off shell block.

---

## B. GSD Core install profile lessons (verified 2026-07-30)

The canonical repo is now `https://github.com/open-gsd/gsd-core`. The
older `gsd-build/get-shit-done` GitHub repo is archived and redirects
to it. npm packages: `@opengsd/gsd-core` (current) and
`get-shit-done-cc` (legacy alias).

**Non-interactive install:**
```bash
npx -y @opengsd/gsd-core@latest --claude --global [--profile=core]
```
- `--claude` selects the Claude Code runtime (other flags: `--opencode`,
  `--kilo`, `--codex`, `--kimi`, `--copilot`, `--antigravity`,
  `--cursor`, `--windsurf`, `--augment`, `--trae`, `--qwen`, `--hermes`,
  `--cline`, `--codebuddy`, `--zcode`, `--all`).
- `--global` writes to `~/.claude/`; `--local` writes to `./.claude/`.
- **`--profile=core` is the lean install** — ~700 tokens of eager
  skill-listing overhead. Default (`--profile=full`) loads all skills
  and adds ~10k tokens + 15 always-on hooks to `settings.json`.

**Always-on hooks added by default `--profile=full` install (verified on
this machine, 2026-07-30):**

| Event | Hook |
|-------|------|
| SessionStart | `gsd-check-update.js` |
| SessionStart | `gsd-session-state.sh` |
| Stop | `gsd-context-monitor.js` |
| PreToolUse | `gsd-prompt-guard.js`, `gsd-read-guard.js`, `gsd-workflow-guard.js`, `gsd-worktree-path-guard.js`, `gsd-validate-commit.sh` |
| PostToolUse | `gsd-context-monitor.js`, `gsd-read-injection-scanner.js`, `gsd-graphify-update.sh`, `gsd-phase-boundary.sh` |
| SubagentStop | `gsd-context-monitor.js` |
| PreCompact | `gsd-context-monitor.js` |
| FileChanged | `gsd-config-reload.js` |

`gsd-context-monitor` fires on Stop, PostToolUse, SubagentStop, AND
PreCompact — basically always running. Some listed hooks are `opt-in`
via config (workflow-guard, graphify-auto-update, phase-boundary,
session-state, commit-validation) — verify which are wired before
assuming they're active.

**Install marker files (verify presence):**
- `~/.claude/gsd-core/VERSION` (e.g. `1.9.0`)
- `~/.claude/gsd-core/.gsd-runtime` (`claude`)
- `~/.claude/gsd-file-manifest.json`

**Uninstall:**
```bash
npx -y @opengsd/gsd-core@latest --uninstall
```

**Matt Pocock skills install:**
```bash
npx -y skills@latest add mattpocock/skills --skill=grill-me -y -g
```
`-y` (yes-to-all-selections) is required to bypass the interactive
multi-select TUI when running from a non-TTY context. `-g` requests
global install, but **some skills error with `PromptScript does not
support global skill installation`** — these still install locally
to `~/.claude/skills/<name>/`. Verify by `ls ~/.claude/skills/ | grep
^grill-`.

**Grill-me family installed locally:**
- `grill-me` (front door, `disable-model-invocation: true` → opt-in
  only, agent never auto-fires it)
- `grilling` (interview primitive, callable by other skills)
- `grill-with-docs` (writes `CONTEXT.md` / ADRs)

**Three-way install recipe (Superpowers + GSD + Grill-me, all installed
but lean):**

```bash
# 1. Superpowers (already installed via plugin marketplace)
#    verify: ls ~/.claude/plugins/cache/superpowers-marketplace/superpowers/

# 2. GSD Core lean
npx -y @opengsd/gsd-core@latest --claude --global --profile=core

# 3. Grill-me
npx -y skills@latest add mattpocock/skills --skill=grill-me -y -g
```

This combo honors the user's "don't add default guidance" steer
because:
- Grill-me is `disable-model-invocation: true` — opt-in only.
- GSD `--profile=core` skips most auto-firing hooks.
- Superpowers already wired via plugin marketplace; no new enabled
  plugin needed.

---

## C. Cross-references in `finish-the-job` SKILL.md

When editing the umbrella, add a one-line pointer to this file in the
existing pitfalls section. Suggested placement: directly after the
"Two-way halt mid-Phase-2" pitfall, or as a new sub-section called
"P_research_stop — see references/research-then-stop-and-gsd-install-2026-07-30.md".