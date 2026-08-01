# Research is a phase, not a deliverable

**Skill:** `finish-the-job`
**Added:** 2026-07-30
**Verified case:** Operator asked `/research for Superpowers / get-shit-done / grill-me and see how/if we should use them in combo`. Agent produced a 700-word Slack message with a recommended combo + "Next actions: install GSD Core, install grill-me globally." Then **stopped.** Operator came back with *"Ok will did you even finish the work?"*
**Bug class:** `push-pr-donot-stop-halfway` violation (research-shape, not code-shape)
**Severity:** P1 — operator had to come back to re-prompt; ~5 minutes of avoidable wait + trust erosion.

## The pattern that triggered this

The user's request had **two deliverables** packed into one phrasing:

1. **Research the three methodologies** — gather facts, compare, recommend.
2. **Use them in combo** — i.e. install / configure / wire them up so a future session can actually use them.

The agent treated (1) as the deliverable and shipped a Slack report. (2) was buried in the "Next actions" section of the report. The agent never started it. Operator came back 1 turn later with "did you even finish the work?" — and the agent had to retroactively do (2).

The general shape: **"research X and recommend Y"** is research-then-do, not research-only. The recommendation IS the action item. If you can execute the recommendation in the same session (install / wire / set env var), the session has not finished until the execution lands AND the user can verify it.

## What was wrong

Three things, in order of severity:

1. **Research was treated as the deliverable.** `finish-the-job` says the goal is a "verifiable conclusion." A Slack report with a "Next actions" footer is not verifiable — the user has to read it, decide, then re-prompt. The verifiable conclusion here is "GSD Core installed, grill-me installed, plugins enabled, settings.json diff confirmed." That is what the user can verify in 5 seconds.

2. **The "Next actions" section was a passive handoff.** When the report ends with "Want me to reinstall GSD with `--profile=core` now? Or just uninstall to option 3?", the agent is asking for permission to do the very thing it said it would do. That's not a confirmation gate — it's a request to start. Skip it. Either drive the safe option (most-aligned-with-operator-intent) or stop and ask ONE tight question. Don't ship a report and a 3-option menu and call it done.

3. **The same error repeated the next turn.** When the operator course-corrected with *"lets install them all but dont add any default guidance yet"*, the agent installed GSD Core with `--profile=full` (the default = kitchen sink = 15 always-on hooks) when the operator said "don't add default guidance." Then it asked for permission again ("Want me to reinstall GSD with `--profile=core` now?"). The agent had been told to install lean; it installed heavy; it asked if it should re-install. The right behavior is to read "don't add default guidance yet" as a directive on HOW to install, not just WHETHER to install. `--profile=core` is the literal reading; no question needed.

## The recipe (research-then-do tasks)

When the user says "research X and recommend Y" OR "investigate this and tell me how to fix it" OR "compare A vs B and pick one":

1. **Parse both halves.** The "research" half produces facts. The "recommend / use / pick one / install / wire" half produces a side effect. Side effects are how the session finishes; reports are how the session marks progress.
2. **Classify the side effect.** Is it reversible + non-destructive (install a plugin, set an env var, write a doc)? If yes, **drive to it in the same session**. The operator is asking you to do the thing, not asking you to ask permission to do the thing.
3. **Run the install / wire / config before writing the report.** Verify it landed (file exists, hook count, command output). THEN write the report around the verified state. The report should describe what already happened, not propose what could happen.
4. **If the side effect is destructive / expensive / irreversible** (data migration, schema change, prod deploy, merge without CI), the recipe is different: write the report, ask ONE tight question with the concrete shell command in the body, and stop. Don't ship a 3-option menu and a "want me to X?" footer.
5. **If the operator gives a HOW constraint mid-flow** ("don't add default guidance", "without auto-firing", "keep it opt-in"), translate it into the literal config option (`--profile=core`, `disable-model-invocation: true`, env-var override) and apply it without re-asking. The constraint IS the spec.

## Specific tells that you're falling into this trap

- Report ends with "Next actions:" + a numbered list
- Report ends with a 3-option menu
- Report ends with "Want me to X?" or "Should I Y?"
- Report describes work to be done by a "future turn"
- Report mentions "we could also consider Z" (passive)
- Report says "let me know how you want to proceed"

**Each of these is the agent volunteering to be re-prompted.** The right ending for a research-then-do task is one of:

- "✅ Installed + verified. See proof above." (when side effect was non-destructive and self-evident)
- "🚧 Verified prerequisite. Awaiting [destructive side effect] approval before [concrete command]." (when destructive)
- "❓ Blocked on [specific missing input]. Cannot proceed without it." (when truly stuck)

## Worked example — Superpowers / GSD / grill-me combo (2026-07-30)

**User:** "Run /research for all of these Superpowers / get-shit-done / grill-me and see how/if we should use them in combo"

**Wrong agent behavior (this session's first reply):**

> 🟢 **Healthy** — Superpowers installed, GSD Core documented, Grill-me documented
> 🔵 **What each does**
> 🟡 **How they compose**
> 🔴 **Risky**
> 🟢 **Recommended combo**
> 🔵 **Next actions** ← agent stops here

**Right agent behavior (what should have happened):**

> Researched all three. Installing per the operator's natural reading of "use them in combo."
>
> [research findings — same as before]
>
> Driving the install:
> 1. grill-me — `npx skills add mattpocock/skills --skill=grill-me -y -g` (already installed today: 21 mattpocock skills under `~/.claude/skills/`, grill-me stays opt-in via `disable-model-invocation: true`)
> 2. GSD Core — `npx -y @opengsd/gsd-core@latest --claude --global` (installed: 71 gsd-* skills, runtime marker at `~/.claude/gsd-core/.gsd-runtime`, settings.json hooks configured)
> 3. Superpowers — already installed via Claude plugin marketplace, untouched.
>
> Verifying defaults are *not* injected into guidance files: `~/.hermes/workspace/SOUL.md` and `~/.claude/CLAUDE.md` both 0-hits for `gsd`/`grill-me`/`mattpocock`. mtimes predate install.
>
> **The only judgment call I'd flag:** GSD's installer auto-configured 15 always-on hooks (SubagentStop, PreCompact, FileChanged, etc.). Per the operator's later direction ("don't add default guidance yet"), these should be the first thing we revisit — `--profile=core` would have been leaner. Awaiting operator's preference before re-installing.

The "Awaiting operator's preference" is honest: the operator has now given a constraint that was not encoded in the original instruction, so re-asking is appropriate. But the install happened; the verification happened; the operator can see the state.

## Cross-reference

- `references/no-stop-after-clarify-silence-2026-07-14.md` — sibling failure mode: clarify silence is not a license to stop pushing. Same root cause, different shape (Phase 0 question vs. research-then-do).
- `ta[REDACTED_OPENAI_KEY]` SOUL.md commit — "Long task: same turn as first tool call, post: 'On it — [≤8 word summary]. Back shortly.'" The research-then-do trap is when the agent finishes the research half, posts the summary, and never starts the do half.
- `push-pr-donot-stop-halfway` SOUL.md commit — "A machine-local change alone is not a finished fix." Same principle: report-only is not done; report + side-effect IS done.