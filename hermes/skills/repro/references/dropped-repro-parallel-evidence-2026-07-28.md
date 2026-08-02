# Dropped-Thread /repro Recovery — Parallel Static-Evidence Recipe (2026-07-28)

## The class

A user posts a `/repro <campaign_url>` invocation into a Slack channel
before any agent session ends. The dropped-thread cron only nudges when a
bot has *already* replied in the thread; pure operator posts with no bot
reply in the lookback window don't get automated recovery. The next
session opens with the user's pushback: *"why did you miss this?"*

The skill trap: open with apology + 6 turns of self-narration. The user
already knows the message was missed (he wrote *"why did you miss"*).
What he wants is the parallel evidence that pins down whether the
reported bug is real — fast.

## Verified worked example: campaign `FsiyESY987DF2lfgolCI`, `#worldai-bugs` `C0BDEAJH8PK/1785197466.704939`

- User post: **2026-07-28T00:11:06Z** (no session picked it up until now).
- Pushback: *"why did you miss this?"* (same thread, ~6 hours later).
- Live URL: <https://mvp-site-app-dev-i6xf2p72ka-uc.a.run.app/game/FsiyESY987DF2lfgolCI>

## The recipe (run in parallel, single reply turn)

In the SAME first reply, do ALL of these in parallel via
`execute_code` / `terminal` / MCP tool calls:

1. **State candidly** that the message was missed (don't narrate
   uncertainty about what happened — the user already knows). One
   sentence about the failure mode (dropped thread, dropped cron, or
   closed session).
2. **Pull the most recent campaign export** at
   `/tmp/your-project.com/repro-exports/<campaign_id>/`. These exports
   capture `game_state.json` + `story.txt` on demand via
   `mcp__worldai__admin_download_campaign` (or `download_campaign.py`).
   The export is dated by file mtime, not by in-game clock — check
   mtime vs the user's "latest scenes" complaint.
3. **Grep the user's verbatim quote** in `story.txt`. The user's typed
   input appears in `story.txt` lines surrounded by scene markers like
   `SCENE 222`. The export is plain prose; one grep gives the scene
   number and the LLM's response scene(s).
4. **Read the LLM's response scene(s)** to capture the LLM's own
   acknowledgment + the structured `combat_state.in_combat` /
   `encounter_state` / state-values it manipulates. This is the
   "second witness" — if the LLM itself produced the bug-acknowledgment
   in narrative, the bug class is captured in the export verbatim.
5. **Cross-reference prior-merged PRs on the same campaign**: `git
   log --oneline --grep "<campaign_id>" -10 origin/main` AND
   `gh issue list --repo $GITHUB_REPOSITORY --state all
   --search "<campaign_id> OR <bug_token>" --json number,title,state
   --limit 30`. Look specifically for `fix/<issue>-combat-...`,
   `fix/<issue>-intent-classifier-...` branches merged into
   `origin/main`. If the same bug class has a merged PR, the verdict is
   "already fixed at the canonical layer; rerun the live URL against
   main to confirm."
6. **Read current state of the routing layer**: `grep -n
   "CombatAgent\|matches_game_state\|in_combat" $PROJECT_ROOT/agents.py` +
   `grep -n "MODE_COMBAT\|intent_classifier" $PROJECT_ROOT/intent_classifier.py`.
   This gives the line numbers to cite in the verdict.

Total work: ~6 tool calls in a single parallel batch. Total elapsed
time: under 30 seconds. Replies with verdict in the same turn.

## Anti-pattern: blocking menu before static evidence

After the parallel evidence, IF the verdict is still genuinely ambiguous
(e.g. needs the real-world timestamp of a live turn to disambiguate
"live combat" from "post-combat god-mode"), post ONE clarifying question
with two specific data points the user can confirm:

> *"The scene where you saw combat-mode-agent *not* being selected —
> was it during live combat (you typed an attack, expected dice rolls,
> got god-mode prose instead), or during a post-combat god-mode
> correction turn? If live combat, give me the timestamp from the URL
> header bar (`14:09`, `22:30`, etc.) and I run the BQ
> `llm_payloads` diagnostic against that turn. If post-combat correction,
> that's expected routing and I'll close it as not-planned."*

DO NOT post A/B/C/D options. DO NOT post a 3-way fork. One question,
two specific data points, the user picks or skips.

## Verified verdict on the 2026-07-28 case

- `combat_state.in_combat=false`, `combat_phase="ended"` in the export —
  EXPECTED state because combat has ended. Routing through
  GodModeAgent / StoryModeAgent for god-mode corrections is INTENDED
  per the dispatch table at `$PROJECT_ROOT/agents.py:26` ("5c. CombatAgent:
  Active combat forces CombatAgent - STATE-BASED").
- PR [#8022](https://github.com/$GITHUB_REPOSITORY/pull/8022)
  merged `96133fc31cc` (2026-07-10) — added 17 MODE_COMBAT mid-battle
  turn-handoff anchors. PR [#8490](https://github.com/$GITHUB_REPOSITORY/pull/8490)
  merged `e54dbd97676` (2026-07-21) — Combat Scope Classifier + God-Mode
  Worked Example. Both on `origin/main`. The bug class the user
  reported was the prior instance; it shipped.
- Scene 222 contains the user's verbatim quote: *"also i should have
  extra attack and a hasted extra attack did you forget htose? also why
  isnt combat mode agent being used?"*
- Scene 223 LLM response: *"The previous turns were not utilizing the
  specialized Combat Agent because the `combat_state.in_combat` flag
  was incorrectly set to `false`. I have manually toggled this to
  `true`..."* (LLM itself acknowledges + fixes in-narrative).
- Scene 224: three attack rolls (`Attack 1 / Damage 1 / Attack 2 /
  Damage 2 / Haste Attack`) rendered in proper CombatAgent format with
  ROUND 3 / initiative order / HP display. Routing fix took.

**Verdict: "not a reproducible bug at the canonical layer; LLM-internal
fix landed at scene 224; PR #8022 + #8490 cover the underlying class."**

Posted one clarifying question (live-combat vs post-combat) and waited.

## Parallel-evidence recipes by skill domain

| Domain | Fastest static path | Reference |
|---|---|---|
| Worldarchitect agent routing | export `story.txt` + `game_state.json` + grep agent class | (this file) |
| Directive-loss | BQ `gemini_provider.stream` + `request_json` `offset%` check | `references/bq-llm-payload-truncation-pitfall.md` |
| Latency | cross-campaign `cache_hit_pct` BQ aggregation | Step 0.76 in repro/SKILL.md |
| Auth-gate fallback | Cloud Logging `client_diag` tracebacks | `references/auth-gate-fallback-repro.md` |
| GitHub rate-limit | `gh api rate_limit` + REST fallback | `references/gh-rate-limit-rest-fallback.md` |

## One-time follow-up cron (mandatory after this recipe)

In the SAME reply, arm a one-shot 20-min cron:

```
cronjob action=create schedule="20m" deliver="slack:<chan>:<thread_ts>"
  repeat=1 name="<topic> /repro followup"
  prompt="Read the Slack thread at channel=<chan> thread_ts=<thread_ts>.
  [route verdict-branch logic]. Self-cancel on PR MERGED or 24h idle."
```

Without this, a second drop on the same thread repeats the failure.
Verified cron-job pattern in SOUL.md `## COMMIT: one-time-status-cron-after-every-task`.

## Pitfalls

1. **Export mtime vs in-game clock.** The export is named by campaign
   title + ID, but the timestamps in `story.txt` are in-game clock
   ("ATC 25 14:09:00"), NOT real-world. Cross-reference the file
   mtime to figure out when the export was actually captured
   (`ls -la /tmp/your-project.com/repro-exports/<cid>/`).
2. **`contents: 0` in `game_state.json` ≠ empty campaign.** The
   `contents` field is the conversation doc index; empty contents is
   normal for a campaign where conversation history is in
   `story.txt` / Firestore conversation docs only. Read `combat_state`,
   `encounter_state`, and `custom_campaign_state` for the real game
   state.
3. **`_agent_selection_tracker` is null.** Recent export may show
   `custom_campaign_state._agent_selection_tracker = null` even though
   `llm_service.py:535` writes a value on every agent selection. The
   value is in the live Firestore doc, not necessarily in the export;
   don't conclude the field is broken from the export alone.
4. **Don't conflate god-mode turns with combat turns.** A god-mode
   correction turn by definition routes through GodModeAgent, never
   CombatAgent, even if combat is active. The user's complaint
   "combat mode agent isn't being selected" is a misclassification
   symptom when the turn is god-mode.
