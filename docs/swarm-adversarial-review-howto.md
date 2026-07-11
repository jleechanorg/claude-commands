# How to run a /swarm adversarial review (reproduction guide)

Distilled from the 2026-07-10 reviews that hardened the sidekick/swarm skills
(PRs #322 merged, #323). Two variants were run; both are reproducible from this
doc alone. Evidence bundle with full transcripts: jleechanorg/jleechanclaw
PR #757, `docs/swarm-adversarial-review-2026-07-10/`.

## The shape (both variants)

```
main session (orchestrator — writes mission, spawns, supervises, folds findings)
  └─ sidekick: ONE claude process in a real tmux session (owns the review)
       ├─ lens 1: accuracy/evidence   — refute claims against primary sources
       ├─ lens 2: consistency         — find contradictions across the doc set
       └─ lens 3: operability         — role-play a cold reader; every guess is a finding
```

Invariants that make it adversarial rather than confirmatory:
1. **Refute-by-default prompts.** Each lens is told to REFUTE, not review.
   Findings survive only with a quoted line from the artifact.
2. **Record non-findings.** Each lens lists what it tried to refute and could
   not — coverage is explicit, so later passes don't re-litigate.
3. **Independent lenses.** Lenses don't see each other's output; the sidekick
   synthesizes and ranks by blast radius afterward.
4. **Findings flow back before shipping.** Every surviving finding is either
   applied to the artifact or logged as an accepted exception — never silently
   dropped.

## Step-by-step

### 1. Write the mission STATE.md (main session, ~1 min)

Path: `/tmp/<project-slug>/sidekick/<mission-slug>/STATE.md`. Sections:
Mission (the lens definitions + deliverable path), Ground truth (engine,
scope), Standing rules (READ-ONLY on the artifacts under review; findings doc
only; deliverables in a `docs/` subdir — root-file-pollution guards block
writes next to STATE.md), Progress Log, Next Actions. Full worked examples:
evidence bundle files `02-` and `11-`.

### 2. Spawn the sidekick (instant start — first tool call)

Interactive TUI (recommended — lenses run as a REAL Claude team):

```bash
STATE_DIR=/tmp/<project>/sidekick/<mission>
tmux new-session -d -s "sidekick-<mission>" -x 220 -y 50 \
  "cd '$STATE_DIR' && CLAUDE_CONFIG_DIR=\"${CLAUDE_CONFIG_DIR:-$HOME/.claude}\" CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude --model sonnet --teammate-mode tmux --dangerously-skip-permissions; exec bash"
# trust dialog: sleep ~10, then  tmux send-keys -t sidekick-<mission> Enter
# mission (text and Enter SEPARATELY — bundled Enter is swallowed):
tmux send-keys -t sidekick-<mission> "Read STATE.md in this directory and execute its Next Actions exactly."
sleep 2 && tmux send-keys -t sidekick-<mission> Enter
```

Headless variant (`-p` + prompt file): simpler completion marker but the lenses
fall back to Agent-tool subagents — NO team primitives exist in print mode.
Both launch commands and all gotchas (auth-env propagation, macOS session-slug
trap, `grep -qx` completion gate) are in `.claude/skills/sidekick/SKILL.md`.

### 3. Supervise (main session)

- Spawn a named supervision teammate (`sidekick-supervisor-<mission>`), told to
  poll via ONE background `until`-loop (foreground sleep chains get blocked)
  gating on `grep -qx "(mission complete)" STATE.md` **full-line match** — a
  substring grep false-positives on the mission description text — plus
  deliverable-file existence.
- The sidekick is NOT SendMessage-addressable (separate session). Steer via
  STATE.md edits and `tmux send-keys`; read via `tmux capture-pane`
  (`tmux -L default ...` if the supervisor lives inside another tmux server).

### 4. Collect and fold

- Lenses report to the sidekick; in team mode they go idle WITHOUT delivering —
  the sidekick must SendMessage-nudge each one for its report.
- The sidekick writes `docs/findings.md`: one section per lens, verified
  non-issues, then a ranked synthesis.
- Main session applies findings (or logs exceptions), commits, and pushes.

### 5. Evidence (per /es)

Record the run with asciinema (`--cols/--rows` matching the tmux size,
`--idle-time-limit 4`), `agg` → gif, `ffmpeg` → mp4; screenshots = ffmpeg frame
extraction from the mp4; captions = in-terminal `=== CAPTION: ... ===` banners
plus an `.srt` generated from the cast's banner timestamps. Show git
provenance in-video (HEAD SHA before and after). Publish: release upload +
`checksums.sha256` + a raw verification transcript + links in the PR body's
`## Evidence` section. If any asset must stay private (e.g. TUI banners expose
account identity), log it as an accepted PARTIAL exception — never report it
as "published."

## Models used in the reference runs

| Role | Model |
|------|-------|
| Orchestrator | Claude Fable 5 |
| Sidekick + lenses + personas + supervisors | Claude Sonnet |
| /advice reviewers | Opus + Fable 5 (research) + cursor-agent (cross-model) |
| Codex engine under test | codex-cli 0.144.1, `gpt-5.6-sol` (high) |

## Known gaps

See `swarm-review-gaps-root-cause.md` (same directory) — including why a fresh
Fable /er reviewer caught packaging/verifiability defects that this entire
multi-swarm pipeline missed.
