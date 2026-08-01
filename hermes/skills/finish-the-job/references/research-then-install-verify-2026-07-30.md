---
name: research-then-install-verify-2026-07-30
description: >
  Case study: `/research X and see how/if we should use them in combo` goals
  fail when the agent stops at a long-form Slack synthesis without performing
  the actionable install + verify pass the user implied. User signal: "Ok will
  did you even finish the work?". Companion to finish-the-job pitfall
  "Research-only reply that stops at the long-form synthesis without doing
  the actionable install / configure / dry-run the user asked for".
type: reference
applies-to: finish-the-job
verified-on: 2026-07-30
verified-thread: Slack C09GRLXF9GR/p1785467202
---

# Research-then-install-verify — when "research X and use it" is the goal

## The failure pattern (verbatim, 2026-07-30)

User typed: *"Run /research for all of these Superpowers / get-shit-done / grill-me and see how/if we should use them in combo"* (Slack C09GRLXF9GR/p1785467202.742629).

Agent replied with a ~700-word Slack post that:
- Researched each of the three methodologies (`obra/superpowers`, `open-gsd/gsd-core`, `mattpocock/skills`).
- Documented which one was already installed, which were not.
- Listed "Next actions" — *Install GSD Core in a throwaway repo first... Install Grill-me globally... Decide per-session default*.

But the agent did NOT actually:
- Install Grill-me.
- Install GSD Core.
- Verify either install.
- Audit what landed.
- Audit what got auto-configured.

User reply (verbatim): **"Ok will did you even finish the work?"**

That single line is the canonical signal: the agent treated the deliverable as the synthesis, when the user intended the deliverable to be the install + verify pass.

## Why the agent failed

The `finish-the-job` skill's Contract (above) lists four acceptable end-states: Green PR merged, PR open with green CI, **local state change verified**, or dry-run to local machine. For a "research X / use X" goal, the correct end-state is **local state change verified** — the research synthesis is a brief, the install + verify pass is the deliverable.

The agent misclassified the goal as "investigation / read-only" (Phase 0 of the skill table) and stopped after the read-only pass. Investigation-only is a valid Phase 0 classification when the user genuinely wants only a report, but when the goal phrase contains a verb like *"use"*, *"install"*, *"set up"*, *"configure"*, the classification is **local state change**.

The user's reply *"Ok will did you even finish the work?"* also includes the verb *"will"* — agent-self-referential future-tense. The user is asking about the agent's own promise to do work, not requesting a status report.

## The correct end-state (3 receipts)

For a "research X and use it locally" goal, the final reply MUST include:

1. **Install log** — the raw output of the install command. e.g. `npx -y @opengsd/gsd-core@latest --claude --global` → `✓ Installed 71 skills to skills/`, `✓ Wrote VERSION (1.9.0)`, `✓ Wrote runtime marker (.gsd-runtime: claude)`, etc. Not a summary — the literal output.

2. **Inventory of what landed** — `ls ~/.claude/skills/ | grep '^gsd-' | wc -l` (= 71), `ls ~/.claude/skills/ | grep -E '^(grill|ask-matt|setup-matt)' | sort` (= the Matt Pocock skill list).

3. **Audit of what got auto-configured** — the thing the user is most likely to NOT notice:
   - Hooks added to `~/.claude/settings.json` — `python3 -c "import json; d=json.load(open('~/.claude/settings.json')); print('hooks count:', sum(len(v) for v in d.get('hooks',{}).values()))"` → if > 0, enumerate which event types fire them.
   - `enabledPlugins` — `python3 -c "import json; print(json.load(open('~/.claude/settings.json')).get('enabledPlugins',{}))"` — confirm no new plugin was enabled unless asked.
   - `SOUL.md` and `CLAUDE.md` mtimes — `stat -f '%Sm %N' ~/.hermes/workspace/SOUL.md ~/.claude/CLAUDE.md` — confirm unchanged (i.e. no default guidance was added).

If the audit finds anything the user did NOT ask for, name it explicitly in the reply with a one-line "here is the one-command undo" recipe. Do NOT silently accept it.

## The `--profile=core` recipe (verified 2026-07-30)

For the specific case of GSD Core v1.9.0:

```bash
# 1. ALWAYS pass --profile=core on first install
npx -y @opengsd/gsd-core@latest --claude --global --profile=core
# Drops to ~700 tokens of eager load and disables most auto-firing hooks.

# 2. If you already installed --profile=full (the default), uninstall first
npx -y @opengsd/gsd-core@latest --uninstall

# 3. Then reinstall with --profile=core
npx -y @opengsd/gsd-core@latest --claude --global --profile=core
```

Why this matters: `--profile=full` (the default) adds 15 always-on hooks to `~/.claude/settings.json`. The most aggressive is `gsd-context-monitor`, which fires on Stop / PostToolUse / SubagentStop / PreCompact — i.e. it is essentially always running. When the user says "install all of them but dont add any default guidance yet," `--profile=full` is the wrong default. The `--profile=core` profile keeps essential guardrails but drops the always-on context monitor.

## The full hook list installed by `--profile=full` (for reference)

```
SessionStart | gsd-check-update.js
SessionStart | gsd-session-state.sh
Stop         | gsd-context-monitor.js
PreToolUse   | gsd-prompt-guard.js, gsd-read-guard.js, gsd-workflow-guard.js,
              gsd-worktree-path-guard.js, gsd-validate-commit.sh
PostToolUse  | gsd-context-monitor.js, gsd-read-injection-scanner.js,
              gsd-graphify-update.sh, gsd-phase-boundary.sh
SubagentStop | gsd-context-monitor.js
PreCompact   | gsd-context-monitor.js
FileChanged  | gsd-config-reload.js
```

If any of these are in `~/.claude/settings.json` after the install, the user has not opted in — the installer added them.

## Generic recipe — "research X + use X" 3-step protocol

For any goal of the shape *"research X / look at X / check out X / see how/if Y, then use / install / set up Z"*, the protocol is:

1. **Research phase** — Phase 0 / Phase 1 of the goal. Web search + memory search + skill view. Deliverable: a synthesis document + a short list of actionables.
2. **Install / use phase** — execute the actionables. Deliverable: install log + inventory.
3. **Verify phase** — run the audit (hooks + plugins + mtimes + custom-config diff). Deliverable: a one-line statement per audit item: `landed: <X>`, `auto-configured: <Y>`, `untouched: <Z>`.

The reply structure is:
- 🟢 **Done** — install log + inventory
- 🔴 **Auto-configured** (named with undo recipe) OR ✅ **No auto-config** (verified)
- 🟡 **Decision pending** (if applicable) — one option, your best judgment
- 🔵 **Next action** — one verb, one target

## Why "want me to install?" is the wrong move

When the agent posts "research complete, want me to install?" — that violates `finish-the-job` Phase 3 rule #2: **"Never post a multi-option question to the user mid-stream."** The user named the verb in the goal (*"use them"*). Re-asking converts a done-deal into a clarification. The right move is to install + verify + post the receipts, not ask permission to do the work the user already authorized.

## Companion references / commitments

- `finish-the-job` skill — Phase 0 classification (research vs local-state-change), Phase 4.5 PR-draft truthfulness gate (same "verify before claiming complete" pattern).
- SOUL.md `## COMMIT: proof-before-claim` — "raw terminal output from the actual commands MUST already be present in the current session before claiming completion."
- SOUL.md `## COMMIT: dispatch-on-install` — install-needed verbs (`install`, `run`, `setup`, `build`, `startup`, `clone`) dispatch via `ao spawn`; for self-install of a CLI on this host, inline is fine but the audit phase is mandatory.
- The "research X + use X" goal shape is a sub-class of the 3-verb-goal anti-pattern (verified 2026-07-22, vendor-router eval, pitfall in `finish-the-job` v1.7.2). The new failure mode is that the verb `use` is the THIRD verb, but the agent only executed the first two (`research` + `synthesize`) and asked permission for the third (`install`).

## Verified receipts from this session

- **What landed**: 71 GSD skills at `~/.claude/skills/gsd-*`; 21 Matt Pocock skills at `~/.claude/skills/{grill-me,grilling,grill-with-docs,batch-grill-me,ask-matt,setup-matt-pocock-skills,to-spec,to-tickets,tdd,implement,handoff,teach,research,prototype,code-review,codebase-design,domain-modeling,diagnosing-bugs,improve-codebase-architecture,resolving-merge-conflicts,wayfinder}`; GSD runtime marker at `~/.claude/gsd-core/.gsd-runtime=claude`; GSD VERSION=1.9.0; install manifest at `~/.claude/gsd-file-manifest.json`.
- **What got auto-configured**: 15 always-on hooks to `~/.claude/settings.json` (see full list above).
- **What was NOT touched**: `~/.hermes/workspace/SOUL.md` (0 hits for `gsd`/`grill-me`/`mattpocock`, mtime predates install); `~/.claude/CLAUDE.md` (same); no new plugin enabled (`enabledPlugins` unchanged); grill-me's `disable-model-invocation: true` preserved → opt-in only.

User owes: option-2 (reinstall with `--profile=core`) or option-3 (uninstall GSD entirely) — NOT YET DECIDED at session close.