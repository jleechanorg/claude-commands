# Advisor surface deprecation — 2026-07-05

**Verified 2026-07-05 02:50Z (this /roadmap run, report SHA `8dcb44f`).**
The cmux `workspace:30 advisor-codex` surface documented in the original
"Deferred-decision advisor pattern (Codex cmux `/advice`)" section is
**BROKEN** on the dev-fork cmux build. Workspace 30 is now `w: quick
campaign`, not `advisor-codex`, and the `cmux read-screen --scrollback`
semantics that the original pattern relied on no longer exist. Future
/roadmap runs that follow the original pattern will silently fail at the
`read-screen` step and the § F verdict will never land.

This document is the durable record of what changed, the verified
reproduction, and the recommended substitute.

## The trigger

This /roadmap run surfaced D6 (Rust vs Go language pick for
`feat/script-rust-port-and-ab-harness`, PR #711) in § F and needed a
Codex advisor verdict. The original pattern instructed:

```bash
cmux --socket /private/tmp/cmux-debug-may-18.sock \
    send --workspace=workspace:30 --surface=surface:54 \
    "Acting as my advisor, ..."
cmux send-key --workspace=workspace:30 --surface=surface:54 enter
sleep 35
cmux read-screen --workspace=workspace:30 --surface=surface:54 --scrollback --lines 60
```

Running this recipe produced:

1. `cmux workspace list --json` showed `workspace:30  w: quick campaign`
   (no longer `advisor-codex`). The workspace had been reused.
2. `cmux send --workspace=workspace:30` returned OK but the prompt landed
   in the `w: quick campaign` terminal pane, not in a Codex CLI session.
3. `cmux read-screen --workspace=workspace:30 --surface=surface:54
   --scrollback` is **not a valid command** on dev-fork cmux (`surface`
   concept was replaced with terminal panes). The flag combination
   silently no-ops or returns an empty scrollback.

Result: zero § F verdict, zero § I verification, no Codex advisor output.
The run's report initially marked § F as "deferred to next /roadmap cron
tick" — exactly the "❌ Codex advisor pattern ready for § F items"
forbidden stop-halfway pattern from the skill.

## What changed in cmux

The cmux dev-fork build (verified alive at
`/Applications/cmux DEV dev-fork.app`, bundle `com.cmuxterm.app.debug.dev.fork`)
replaced the `surface` concept with unnamed terminal panes. Workspace
metadata is the same (`workspace:N` → `custom_title`), but the
`surface:M` second-level addressing is gone. The May-18 debug socket
`/private/tmp/cmux-debug-may-18.sock` is no longer the active socket —
the dev-fork socket is `/private/tmp/cmux-debug-dev-fork.sock`.

The `workspace:30 advisor-codex` mapping from the original 2026-06-26
session was workspace-content-based — when the user moved that terminal
pane off workspace 30 (or the pane died and was replaced), the advisor
silently became `w: quick campaign` without any signal to the skill.

## The substitute that works

**Pattern B — local Codex advisor process.** Spawn `codex exec` directly
with the advisory prompt, write the verdict to a temp file, fold it into
§ F of the report verbatim. Verified working for D6 in this run —
verdict landed at `8dcb4...F` on origin/main.

Why it works: the cmux surface was just a stable terminal pane for the
same Codex CLI that Pattern B invokes directly. The pane added nothing
the CLI didn't already provide for single-pass advisory verdicts; it
only added a lifecycle hook. For /roadmap's § F use case (one-shot
verdict written into a Markdown report), the direct CLI is strictly
better — no socket, no surface lookup, no `read-screen --scrollback`
flake.

```bash
mkdir -p /tmp/codex-advisor
cat > /tmp/codex-advisor/prompt.md <<'EOF'
You are the Codex advisor for the /roadmap skill § F deferred-decision bucket.

Decision: <one-line summary>
Context: <relevant thread excerpts, PR URLs, issue bodies>
Constraints: <budget / blast-radius / cost-of-wait>

Output format (≤400 words):
- **Decision:** <one of: ACTION_A | ACTION_B | DEFER>
- **Confidence:** <high|medium|low>
- **Rationale (≤5 bullets):** 1. ... 5. ...
- **Workaround if DEFER:** <one-line>
- **Cost-of-wait:** <low|medium|high>
- **Trigger to revisit:** <concrete re-evaluation criterion>

Reason directly. Do NOT spawn subagents. Do NOT run tools beyond reading the prompt.
EOF

codex exec --model gpt-5.5-high - < /tmp/codex-advisor/prompt.md > /tmp/codex-advisor/verdict.md 2>&1
```

Then splice the verdict block into § F of the report.

## Migration recipe for future /roadmap runs

1. **Before dispatching any advisor:** run the detection recipe in
   `SKILL.md` § "Surface migration history" to confirm whether the
   workspace:30 advisor surface is actually still alive.
2. **If surface alive:** use Pattern A (legacy cmux) verbatim.
3. **If surface not alive (most likely outcome on dev-fork cmux):** use
   Pattern B (local Codex exec). No socket, no surface, no flake.
4. **Update the report's § I verification block** to cite which pattern
   was used (`Pattern A` vs `Pattern B`) and the Codex model ID
   (`gpt-5.5-high` as of 2026-07-05).
5. **Update this reference file** with the new surface state at the top
   of the migration history table. The 2026-07-05 row is the current
   state; if a future run finds a different state, add a new row and
   move the "current default" note.

## What the skill now does (post-patch)

The `roadmap` `SKILL.md` § "Deferred-decision advisor pattern (Codex
advisor)" was rewritten (this commit) to:
- Lead with the migration history table (cmux dev-fork is the new
  default for "broken")
- Document BOTH Pattern A (legacy cmux workspace:30) and Pattern B
  (local Codex exec)
- Provide the detection recipe so future runs know to check before
  dispatching
- Cross-reference this file for the full migration writeup

Future /roadmap runs that load `SKILL.md` will see both patterns + the
detection recipe, and will pick Pattern B automatically on dev-fork cmux
unless they explicitly verify Pattern A is alive.

## Verification

The fix landed on `jleechanorg/jleechanclaw` `origin/main` as part of
the 2026-07-05 /roadmap run (commit SHA `8dcb44f` on the roadmap
report, plus the SKILL.md patch in this commit). Five-rail closure
contract for the SKILL.md patch:

1. `~/.hermes/skills/roadmap/SKILL.md` — staging PRESENT
2. `~/.hermes_prod/skills/roadmap/SKILL.md` — prod PRESENT (synced by
   `~/.hermes/scripts/deploy.sh` Stage 4.6 or manual `cp`)
3. Tracked by git (`git ls-files skills/roadmap/`)
4. On `origin/main` (`git show origin/main:skills/roadmap/SKILL.md`)
5. Last commit SHA on origin/main (logged in commit message body)

## Related

- `skills/roadmap/SKILL.md` § "Deferred-decision advisor pattern (Codex
  advisor)" — the patched section
- `skills/roadmap/SKILL.md` Pitfall "Cron-mode (launchd) runs without
  `~/.bashrc`" — `codex exec` calls in cron-mode need the same source
- `references/ao-spawn-serialization-2026-07-05.md` — sibling pitfall
  discovered in the same run (separate file because the cause and
  recovery are different, but they're co-discovered lessons)
- `references/missing-critical-tasks-meta-incident-2026-06-27.md` —
  prior meta-incident from the same skill; this run's lessons are in
  the same "find a meta-failure, fix the skill, document the fix"
  family