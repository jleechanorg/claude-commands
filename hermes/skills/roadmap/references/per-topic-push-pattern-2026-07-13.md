# Per-topic /roadmap push — AIEWF 2026 worked example (2026-07-13)

**Commit:** `44f73a2` on `jleechanorg/roadmap`
**Tree:** `reports/2026-07-13-aiewf-roadmap/` (12 files)
**Trigger:** Jeffrey asked in Slack `C09GRLXF9GR` thread `1783973641.450429`: *"Lets make an overall ~/roadmap doc for each topic and make an individual /roadmap md report and push all ~/roadmap changes to origin main and then link everything here by github.com url and report on background, context, what each person proposes, link to references, and how it can be better applied dto my setup"* — with OOB follow-up *"in the main report lets also look at teh sessions i attended and check them for learnings and all my granola and google docs notes and then pick top 3 learnings for me personally"*.

## What got produced

| File | Purpose |
|---|---|
| `01-overview-parent.md` | Frame: `Loops → Verification → Harness Engineering` dependency chain + sources index |
| `02-…11-<topic>.md` (×10) | One per AIEWF top-10: Verification Gap, Krieger frontier-far, Pocock skill checklist, Browne prompt debt, swyx Loopcraft, WorkOS software factory, AAuth vs auth.md, Tokenmaxxing → ROI, Autoresearch + Arena, Codex Micro |
| `99-personal-top-3-learnings.md` | Top 3 synthesized from sessions attended + Granola titles + workshop materials + pre-existing learnings log |

Every topic doc carries the five-section shape: Background · Context · What each person proposed · References (verified URLs) · **How it can be better applied to Jeffrey's setup** (with 1-week concrete deltas).

## Branch sequence that worked

```bash
cd ~/roadmap
git stash push -m "local-changes-pre-aiewf-2026-07-13" --include-untracked \
  -- learnings-2026-07.md 2026-07-12-mcp-mail-slackbot-investigation.md \
     hermes_mcp_slack_aside_memory_report_2026-07-13.md \
     mcp-mail-slack-recovery-report_2026-07-12.md \
     nextsteps-2026-07-12-directive-evidence-prs.md \
     nextsteps-2026-07-12-standard-ao-recoverable-backups.md
git checkout -B tmp/aiewf-roadmap origin/main
# ... write the 12 files ...
git add reports/2026-07-13-aiewf-roadmap/
git commit -m "roadmap: AIEWF 2026 top-10 per-topic + parent overview + personal top-3 ..."
git fetch origin
git rebase origin/main  # origin had +1 commit, clean replay
git push origin HEAD:main
git rev-parse origin/main HEAD  # both = 44f73a2be712b8a17c6ac9d4f1fb37dcfd0acbd9
```

## Granola synthesis — the gap

Granola MCP returned `401 Unauthorized` mid-session:

```
$ mcporter call granola search_granola_notes query="verification gap" limit=8
{ "error": "Granola API error: 401 Unauthorized" }
```

`granola meetings --range custom --start 2026-06-29 --end 2026-07-03` DID work and returned 8 meeting titles. So the personal synthesis in `99-` used **meeting titles as ground truth** for session mapping + cross-corroborated against Jeffrey's existing `learnings-2026-07.md` (14+ entries showing the verification / pruning / factory patterns) + the workshop materials Jeffrey shipped at AIEWF (`~/projects/workshop_worldfair/` for the Langfuse AI-engineering-loop workshop, `~/projects/aiewf-workshop-test-guide/` for the Arize AX Wonder Toys demo walkthrough).

The Slack reply flagged the gap explicitly + offered `granola auth` as the next-step fix.

## Slack reply shape (verified working)

Replied in-thread with: tree URL + commit SHA URL, one line per topic doc with full `https://github.com/jleechanorg/roadmap/blob/main/reports/.../0N-...md` URL, the personal-top-3 summary inline, gaps section, one short "what I can do next" list (granola auth / AO dispatch / LinkedIn draft).

The `🧠 Memories used:` citation block was included per SOUL.md `## COMMIT: ms-on-new-task` (multi-turn guard applies since this was a follow-up turn — cited from the parent turn's session_search).

## Reusable next time

- **Per-topic push pattern** is now codified in `roadmap/SKILL.md` § "Per-topic /roadmap push pattern (added 2026-07-13, verified)"
- **Granola MCP tool names** patch in `granola-cli/SKILL.md` so the next agent doesn't waste 4 turns discovering the same thing
- The 12-file AIEWF run is the canonical reference example for any future "top-N topics from <event> → /roadmap → push → GitHub URLs" task