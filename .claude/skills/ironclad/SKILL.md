---
name: ironclad
description: Harden a stated goal into ironclad exit criteria (stronger than asked, binary, executable, externally anchored, anti-gaming, iterate-until), set them durably (bead/goal/STATE/memory), then execute toward them. Use when the user invokes /ironclad, asks for ironclad exit criteria, or sets a sparse goal that needs hardening before autonomous work.
---

# Ironclad exit criteria — harden, set, execute

**Provenance of the standard** (mined via /ms + /history, week of 2026-07-05..12):
- User, 2026-07-12 (session 40c1f666): *"whenever i do /goal i want the llm to brainstorm some ironclad exit criteria **better than what i asked for** and then run it"* → became the `~/.claude/hooks/goal-exit-criteria.sh` UserPromptSubmit hook (3–7 criteria, literal condition is the floor).
- User, 2026-07-10 (worldai-2d /goal): *"make ironclad exit criteria and **iterate until the game truly working**"* → ironclad implies an iterate-until-verified loop, not a one-shot checklist.
- Exit-criteria charter (dark-factory `cutover-exit-criteria.md`, R1–R6 + X1–X10; adopted by the spec-design-docs skill): binary, executable, externally anchored; implementer-authored artifacts are corroborating, never sufficient; the verifier **reproduces** rather than inspects; satisfied-via-mock/dry-run = FAIL; default verdict is FAIL.
- Live validation (DK2D mission, 2026-07-12): the iterate-until rule blocked a premature bead closure on a counting/provenance defect; the independent-verifier rule caught and retracted a stale-bundle sprite over-claim; the stronger-than-asked rule spawned an unrequested persona playthrough that found 3 real defects.

## What "ironclad" means (all six required per criterion)

1. **Stronger than asked** — the user's literal condition is the FLOOR. Each criterion must close a loophole the literal ask leaves open (ask "how could I technically satisfy the words while betraying the intent?" — then ban that).
2. **Binary** — pass/fail, no "mostly"/"improved"/"should".
3. **Executable** — a stated command or observable check anyone can run verbatim (quote it in the criterion).
4. **Externally anchored** — verified at the layer users experience (real system-of-record: merged PR state, live HTTP response, on-camera DOM, CI conclusion at head SHA) — never implementer logs/telemetry alone.
5. **Anti-gaming** — self-report insufficient; independent reproduction required (different agent/model than the author — adversarial verifier, cross-model review, or the human). Mock/dry-run/dev-mode satisfaction = FAIL. Serving-context matters (dev server ≠ vite preview ≠ backend-served SPA — the wc-1nli/wc-vs19 lesson: validate the SAME bundle/context the claim is about, and prove bundle identity by content hash).
6. **Iterate-until** — the goal stays open until ALL criteria hold simultaneously at the same HEAD/state; a criterion that regresses reopens the goal.

## Procedure

1. Restate the literal goal in one line.
2. Brainstorm 3–7 criteria per the six properties. State them as a numbered table: criterion | check command | external anchor | independent verifier.
3. **Set durably**: `br create "GOAL: <name>" --type task --priority 1` with the full criteria in the description (or `br update` the existing goal bead). Also set Claude Code's builtin `/goal` (Stop-hook enforcement + purple UI indicator); the bead carries the ironclad superset. **The model CAN set the builtin itself when running inside cmux** (proven 2026-07-12): `cmux identify` → caller.surface_ref, then `cmux send --surface <ref> '/goal <condition>'` + `cmux send-key --surface <ref> enter` — types into the session's own composer; the builtin processes it exactly as if the user typed it. Keep the condition short (the UI truncates); single-quote it for the shell. Write a repo-visible goal file (e.g. `roadmap/<mission>-goal-ironclad-<date>.md`) with a live status table when the user should be able to read progress.
4. Log to the mission STATE.md if a sidekick mission is active; add a memory pointer if the goal spans sessions.
5. Execute. Route work through the active orchestration model (/sidekick, /swarm lanes) — do not implement directly if the mission delegates.
6. On each claimed completion: run the check commands, cite outputs, get the independent verification, and only then mark the criterion. Default verdict is FAIL.

## Anti-patterns (ban list — each caught at least once in real missions)

- Criteria satisfied by artifact EXISTENCE ("video file present") instead of artifact CONTENT (all-frames read, >85% single-state = FAIL; region-aware clustering so side-panel text doesn't masquerade as game-world motion).
- "Tests pass" without naming which layer (unit-only proof is insufficient for production behavior).
- Tool-layer proof for end-state claims (`git push` ok ≠ PR mergeable; job "running" ≠ runner online; server "started" ≠ SPA served).
- Criteria the implementer can grade themselves with no reproduction path.
- Validating a DIFFERENT artifact than the claim covers (fresh build vs the stale bundle actually recorded; gate bundle ≠ served bundle).
- Vague quantifiers: "works well", "high quality", "properly handles".

ZFC note: the harness command is mechanical dispatch; the judgment (which loopholes exist, which criteria close them) is the model's, per the goal-exit-criteria.sh design.
