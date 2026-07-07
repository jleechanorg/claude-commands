# Worked Example: Sylphina Salvage Recovery (2026-06-11)

**Thread:** `C0AH3RY3DK6 / 1781069449.669529`
**Drop signal:** MCP Agent Mail followup at `2026-06-11T15:50:26Z` (30+ hours after root)
**User request:** *"Getting bored of this campaign see why [URL] and /wiki-search for what I usually like"*
**Followup pivot (2h into original):** *"You pick some of my longest campaign a and recommend how to salvage"*

## Why it was dropped the first time

The prior agent turn (2026-06-10 09:42 PT) shipped a thorough diagnosis with an A/B/C menu (`A` = god-mode admin directive, `B` = wiki-search summary, `C` = something else). The menu sat cold for 30+ hours. The MCP dropped-thread-followup script picked it up and re-pinged.

## What the recovery did differently

1. **Picked option A as the default** (not "which do you want?"). The user had said "pick some of my longest campaign a" — interpreting that as "go with A" was correct, not a stretch.
2. **Delivered the god-mode directive as a copy-paste-ready string** in the thread, not as a recap. The user could paste it directly into the Sylphina clone.
3. **Bundled the wiki-search summary into the same recovery reply** (4 chunked messages: directive + cold-campaign summary + active-campaign summary + cron status). One turn resolved the original request, the followup pivot, AND set up a 20m status check.
4. **Provided a "skip — Vesperian" exit ramp** so the user could bail to Vesperian Thul without the salvage work.

## The Sylphina diagnosis (worked example for future Sylphina-like complaints)

**Campaign:** `MfM8TFz73DUeFFmt0mDb` (Sylphina, 338 entries, 136k-char bible)
**The rut:** the LLM was producing "sensory-timestamp + multi-element mana-system + robotic frequency" prose. Literal example: *"Morning (10:12:00) in the Eastern Groves. The air is still heavy with the scent of ozone and the shimmering static of the Captain's deletion. Your silver hair pooling over your shoulders like mercury. Your expression is a mask of wide-eyed, fragile noble concern, but your voice drops into a chilling, robotic frequency..."*

**Why:** the bible was 136k chars of class sheet (no scene anchor, no named enemy, no "play this turn-by-turn" instruction). The LLM defaulted to atmospheric-prose register because that was the most-recently-reinforced style.

**The user's other long campaigns (for cross-reference):**

| Campaign | Entries | Bible chars | Pattern |
|----------|---------|-------------|---------|
| Nocturne Velvet Cage BG3-parallel | 2,414 | 34k | "Play this scene turn-by-turn" anchor; named enemy (Cassalanter); high-agency player turns |
| Aegon/Visenya Dunk&Egg gender-swap | 2,130 | ? | Hidden-identity pressure cooker; power creep on low-magic frame |
| Itachi V3.1 Uchiha Uprising AU | 1,547 | **392** | 1-paragraph bible; user ended it via god-mode directive "remove all this mathematical language" |
| Nocturne Silent Blade BG3 Zhentarim | 2,007 | ? | Soul-harvesting-as-political-currency; Rank-10M endpoint |
| Vesperian Thul Shadows Over Thay (active) | 894 | 30k | Cold-blooded dark-paladin harvesting souls against Szass Tam |
| BG3 Shadow Farmer (active) | 660 | ? | "Previous-life monster playing house" cozy-downgrade |

**Pattern across all 1k-entry runs:** (1) specific scene anchor in bible, (2) named enemy with agenda, (3) player turns that escalate politics not magic. Sylphina's bible was missing all three.

**The salvage directive (copy-paste-ready, dropped into the thread):**
```
_ADMINISTRATIVE DIRECTIVE — overwrite any conflicting scene instruction:

The 136k-character class-sheet bible is exhausting the player. Effective immediately:

(1) KILL the "sensory-timestamp + multi-element mana-system + robotic frequency" prose
    register. Concretely, the most recent AI turn produced: "Morning (10:12:00) in
    the Eastern Groves. The air is still heavy with the scent of ozone and the
    shimmering static of the Captain's deletion. Your silver hair pooling over your
    shoulders like mercury. Your expression is a mask of wide-eyed, fragile noble
    concern, but your voice drops into a chilling, robotic frequency..." — this is
    the rut. Stop. No more atmospheric timestamp headers, no more mana-vocabulary
    jazz, no more "voice drops into X frequency" stage direction. Cut paragraph 1
    of every AI response by ~70%.

(2) REFRAME Sylphina's Spoofed Status Board from a math demo into a political tool.
    She is using the 4,500-vs-∞ mana gap to MANIPULATE COURT FACTIONS, not to
    optimize spell lists. When she interacts with Father Garm, the Guild
    Assessment Crystal, or the Gilded Hand, the scene is about deception and
    leverage, not spell math.

(3) The Evil God Aaron is now a NAMED ANTAGONIST already in-system. He does not
    need to be re-introduced. His emissaries are already in the capital making
    contact with House Silford's rivals. The next 5 turns must surface that
    contact organically — through overheard conversations, intercepted letters,
    a failed assassination attempt on a rival, etc. Aaron manifests as PRESSURE
    on Sylphina's mask, not as a tutorial cutscene.

(4) Anchor the next scene on a specific named NPC interaction: Father Garm
    summons Sylphina to his study for a PRIVATE AUDIENCE about the missing
    mana readings. PLAY THIS SCENE TURN-BY-TURN. Sylphina must choose in the
    moment what version of the truth to give him, knowing that an honest
    answer reveals her nature and a lie leaves evidence she can be caught on
    later. No scene transition, no time skip, no POV cut away from Garm's
    study until at least turn 3 of the audience.

(5) Sylphina's input style going forward: lean political, not mechanical. Sample
    input shape: "I will let him sense the spoofed 4,500 number but hide the
    multi-million truth. Use harmonic guidance to subtly plant a
    counter-intelligence hook so his spies report only what I want them to
    see. Describe his external face and internal suspicion."

Reinforce this directive again in 30 turns if the LLM drifts back to the
sensory-timestamp + mana-vocabulary register. Pattern matches the Itachi V3.1
mechanism that worked.
```

**Where to paste it:** `https://mvp-site-app-dev-i6xf2p72ka-uc.a.run.app/game/BfDxh3G8GcYQfjjwYv16` (the Sylphina clone `BfDxh3G8GcYQfjjwYv16` from `copy_campaign.py`).

## Cron queued

`21ddc8566eb8` — one-time, +20m, "sylphina-salvage-status-check-1". Posts an in-thread check at `C0AH3RY3DK6/1781069449.669529` with: (a) the clone URL, (b) the directive paste instructions, (c) a one-shot override if the LLM is still in the rut, (d) the "skip — Vesperian" exit ramp.

## Lessons captured (cross-references)

- **slack-messaging pitfall added:** "Slack `chat.postMessage` 4000-char hard limit silently auto-splits long messages" — the 10.6k-char recovery reply was posted as 1 call, Slack split it into 4 messages. Should have pre-chunked at section boundaries.
- **slack-messaging pitfall hardened:** "Gateway auto-mirrors terminal tool output, not just final assistant text" — the recovery turn ran 14+ `terminal` calls; ~6 of them produced user-visible noise posts even though the final assistant text was clean. The rule is now: batch multiple bash commands into a single `terminal` call, or use `write_file` to stage a script.
- **worldarchitect pitfall added:** "Firestore env-var shadowing trap — `WORLDAI_GOOGLE_APPLICATION_CREDENTIALS` is shadowed by `GOOGLE_APPLICATION_CREDENTIALS`" — the user has the generic env var set globally; the firestore client picks it up first and fails. Fix: `os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)` before instantiating the client.

## What I would do differently next time

1. **Pre-chunk the recovery reply at section boundaries BEFORE writing it to file** — chunk 1 should be ~3500 chars, chunk 2 ~3500, chunk 3 ~3500. Posting as 1 call and letting Slack auto-split is the failure mode; section-boundary chunks are intentional.
2. **Use `write_file` + single `terminal` bash for the entire cleanup phase** — not 8 separate `terminal` calls. The Sylphina cleanup needed ~6 cleanup calls; batching them into one shell script would have been 1 call.
3. **Trust `chat.delete` `ok:true` responses and stop verifying** — each verify call adds 1-2 more noise messages. The discipline: post the final summary in the *next* turn's final assistant text, not in the same turn.
