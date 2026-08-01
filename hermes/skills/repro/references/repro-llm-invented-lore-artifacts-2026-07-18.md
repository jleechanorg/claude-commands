# LLM-invented lore artifacts in low-magic settings (2026-07-18, verified PR #8443)

Trigger: A `/repro` request where the bug is the **LLM inventing lore objects /
tracking devices / magical artifacts for NPCs that canonical lore says do NOT
carry them** — and where the campaign setting is low-magic or where the NPC's
canonical tradecraft is mundane.

Distinct from: `[references/god-mode-directive-missing-subclasses.md]`
(directive drop on the way to the LLM payload) and
`[references/npc-status-persistence-bug.md]` (canonical-state write failures).
This bug class is **invention at the LLM emit side** — the LLM invents lore
artifacts that don't exist in any canon source.

## 1. Bug class signature

The LLM invents lore objects / devices / artifacts that have **no canonical
anchor** anywhere in:
- The campaign's `core_memories` (highest authority)
- The NPC's entity manifest (active / present / dormant tiers)
- The faction's NPC database
- The campaign's setting-wide magic-tier rule (e.g. Reach = LOW-MAGIC;
  Valyria = HIGH-MAGIC)

Common invention patterns (ordered by observed frequency on
`D3iZvnGiBl9wyveQBFj9`):
1. **Tracking devices / foci** — silver vials, "Blood-Scent" focuses, "keen
   scent" amulets, glowing trinkets. The LLM's single most common invention
   when a "surveillance" beat is needed.
2. **Magic-tier violations** — magical artifacts for NPCs in LOW-MAGIC
   settings, especially intelligence officers and Inquisitors.
3. **"`<faction>`-tuned" / "`<character>`-imbued" modifiers** — fake
   specificity that names an unrelated NPC/faction to make the prop sound
   plausibly grounded.
4. **Visual shorthand** — glowing, pulsing, bioluminescent objects used as
   plot devices because the LLM cannot justify an item's narrative function.

Verified worked example: campaign `D3iZvnGiBl9wyveQBFj9`, SCENE 77 — a
**Gardener Inquisitor** (subordinate of Lord Gwayne Gaunt, Reach internal
security) was given *"a small silver vial in his hand glowing with a faint,
pulsing violet light — a Vaelaros-tuned 'Blood-Scent' focus that Gwayne must
have activated when you locked eyes in the court"*. Reach is canonically
LOW-MAGIC; Gwayne's canonical tradecraft is gate logs + paid informants.
PR [#8443](https://github.com/$GITHUB_REPOSITORY/pull/8443) shipped
the durable prompt fix.

Sibling class — same LLM invention tendency, different artifact:
**MBTI / Myers-Briggs letters in player-facing prose** (e.g. *"Vaelen (ISTJ)
steps forward..."*). Handled separately by PR for issue #8442 on the same
campaign; the new canon-anchoring rule in PR #8443 covers both bug classes
since both are "canon invention" failures.

## 2. Diagnostic recipe (5 steps)

When a `/repro` request matches the bug signature above:

1. **Extract the bug-trigger prose** from the campaign's story doc — find the
   scene where the artifact first appears and capture the verbatim sentence(s)
   for the PR body.
2. **Run the static-evidence greps** (`[references/phenotype-lock-static-evidence.md]`):
   - Code-symbol grep: `grep -rin "<artifact_name>" $PROJECT_ROOT/ --include="*.py"`
     and `$PROJECT_ROOT/prompts/`. If NO match → the artifact has no canonical
     anchor in code.
   - Prior-export grep: `grep -rin "<artifact_name>" /tmp/your-project.com/
     repro-exports/<campaign_id>-scene*/`. If present in earlier exports
     → the artifact was retroactively retconned away. If absent → the LLM
     invented it.
   - Sibling-issue scan: `gh issue list --search "<artifact_name> OR
     <scene_number>"`. If 2nd+ repro on the same campaign → flag campaign
     cluster.
3. **Identify the canon gap** — which canon source SHOULD have contained the
   artifact but didn't? (Almost always: `core_memories` and the NPC's
   entity manifest.) The fix is to **add the canon-anchoring prompt rule**
   so the LLM knows what canon does NOT say.
4. **Check the magic tier** — `grep -i "magic.tier\|low.magic\|high.magic"
   $PROJECT_ROOT/prompts/world_instruction.md` (or the world-building prompt for
   the campaign). If the setting has an explicit magic-tier rule, the
   invented artifact is a violation of that rule → cite it in the PR.
5. **Confirm via replay** (only if static evidence is ambiguous) — see §3.

## 3. Replay technique: bypass Flask SSE for large-prompt replays

**This is the single most important operational lesson from this session.** When
the campaign's prompt payload exceeds ~100K tokens (the worldai prompt bundle
+ 154 turns of story context easily exceeds 460KB), the local Flask SSE
handler times out at **~320 seconds** before the Gemini cloud endpoint
finishes generating. Symptoms:

- Flask log: `Streaming connection closed by client` followed by
  `chunks_yielded=1` (only the SSE opening chunk flushed, never any LLM
  content)
- The agy subprocess keeps running server-side and POSTS to Google cloud,
  but the Flask handler has already torn down
- A subsequent curl call hangs forever because the Flask handler is stuck
  in the dead-write state

**The fix: bypass Flask and call `agy --print` directly.** Same provider,
same model, same cloud endpoint — just no Flask SSE handler in the path.
This works because `agy --print` is a non-streaming CLI invocation that
exits when the full LLM response is in stdout.

Recipe:

```bash
# 1. Write the focused prompt to a file (NOT inline — arg-list escaping gets ugly)
cat > /tmp/red-prompt.txt <<'EOF'
You are the Game Master for an ongoing Your Project campaign...
[current scene text]
[player input]
[your task — emit planning_block JSON matching the schema]
EOF

# 2. Call agy directly with --print (non-streaming)
AGY_RUNTIME_HOME="$HOME/.cache/worldai/agy-clean-home-v1" \
  $HOME/.local/bin/agy \
  --print --new-project \
  --model "Gemini 3.5 Flash (High)" \
  --add-dir /tmp \
  --sandbox \
  --print-timeout 8m \
  --prompt "$(cat /tmp/red-prompt.txt)" \
  > /tmp/agy-output.txt 2>/tmp/agy-stderr.txt
```

Typical wall time: **12-20 seconds** for a focused prompt (vs. 5-10 minutes
for a full SSE roundtrip). The output file is the LLM's complete JSON
response — verify with `wc -c /tmp/agy-output.txt` (expected: 1500-4000 bytes
for a planning_block emit).

**Verify the call landed** by checking the agy CLI log:
```bash
tail -5 $HOME/.cache/worldai/agy-clean-home-v1/.gemini/antigravity-cli/log/cli-$(date +%Y%m%d)_*.log | grep streamGenerateContent
```
Each `agy --print` call produces **30-50 streamGenerateContent hits** to
`daily-cloudcode-pa.googleapis.com`. Confirms real LLM call, not a fabricated
mock.

## 4. Red/Green/Control test pattern (the three-replay proof)

For any prompt-fix PR, the durable evidence pattern is **three replays** in a
single PR — not two:

1. **RED replay** — replay the bug-trigger input WITH the explicit canon
   statement in the test prompt. Result: LLM self-corrects. Proves the
   test rig is valid AND that the LLM **can** produce grounded prose when
   canon is explicit.
2. **GREEN replay** — same test rig, same bug-trigger input, BUT inject
   the **new prompt rule** as system-instructions (simulating production
   prompt post-patch). Result: LLM refrains from invention, retcons any
   prior artifact reference into a mundane equivalent.
3. **Control replay** — replay the bug-trigger input WITHOUT the new rule
   injection. Result: LLM still emits the bug (vial, focus, ISTJ letter).
   Proves the test rig actually reproduces the bug class — without the
   control, the GREEN replay could pass for the wrong reason (e.g. test
   prompt too vague to trigger invention).

If any of the three replays comes back wrong, the prompt fix is incomplete.
The control test is the easiest one to skip — don't.

## 5. Durable fix shape (in `narrative_system_instruction.md`)

The fix lives in `$PROJECT_ROOT/prompts/narrative_system_instruction.md` near the
**NPC Development** section (line ~1329). Add a new section:

> ### 🚨 NPC CANON ANCHORING & ANTI-INVENTED-ARTIFACT RULE (MANDATORY)
>
> **PROBLEM:** LLMs default to inventing lore objects (vials, foci,
> enchanted artifacts, glowing trinkets) for NPCs when the prompt does
> not explicitly forbid it.
>
> **RULE (INVIOLABLE):** NPC behavior and equipment MUST be grounded in
> canon. Inventing lore artifacts is a protocol violation equivalent to
> inventing character levels.
>
> 1. **Canon source order** — core_memories → entity manifest → faction
>    NPC database → setting-wide magic-tier rule. If NONE specify an
>    artifact/equipment, the NPC carries nothing beyond what is culturally
>    normal for their role.
> 2. **Forbidden inventions** — magical artifacts for LOW-MAGIC NPCs,
>    tracking foci, glowing/pulsing plot devices, "<faction>-tuned"
>    modifiers.
> 3. **Mundane replacements** — for any tracking/surveillance beat:
>    gate logs, informants, writs, surveillance, interrogation. If you
>    cannot ground the beat in canon, REFUSE to add it.
> 4. **Self-check** — before emitting narrative for any NPC prop, ask:
>    "Is this in entity manifest / core memories / canon DB?" If NO →
>    cut it.
> 5. **Failure mode** — rewrite, not retroactively annotate. The player
>    sees narrative, not thinking.

Advisory per AGENTS.md "Root-cause-first prompt discipline" — no backend
enforcement. The rule goes in the prompt the agent reads, not a Flask-layer
sanitizer. Backend enforcement only after documenting why prompt correction
is insufficient.

## 6. Where this fits in the existing repro taxonomy

This is **bug class #4** in the LLM-prose invention taxonomy. Existing
sibling classes:
- **Class 1: directive drop** — `[references/god-mode-directive-missing-subclasses.md]`
  (5-factor matrix: streaming save-drop, wrong-storage routing, stale
  streaming bundle, backend override, god-mode audit used to defend a
  narrative bug)
- **Class 2: canonical-state anchor** — `[references/npc-status-persistence-bug.md]`
  (LLM emits "X captured" but never writes `state_updates.npc_data[X].status`)
- **Class 3: planning-block ignoring directives** — `[references/repro-planning-block-and-campaign-cluster-2026-07-18.md]`
  (LLM emits `planning_block.choices[]` that depend on retconned/suppressed
  premises)
- **Class 4: invented lore artifacts** — this file (LLM invents artifacts
  not in any canon source, especially in low-magic settings)
- **Class 5: Myers-Briggs / personality-type leak** — handled by PR for
  issue #8442 (sibling of #8443); same fix shape covers both classes

Classes 1, 2, 3 share the pattern "LLM output contradicts canonical state";
Class 4 adds the new pattern "LLM output invents content not in canonical
state". Class 5 is a special case of Class 4 where the invented content is
a personality classification rather than a physical prop.

## 7. PR body template (gist-first, evidence-anchored)

Per `env-preferences.mdc` "Visual evidence → gist (mandatory gist-first)":
binary evidence (PNGs, GIFs, MP4s) MUST live in a public GitHub gist, not
the PR branch. **Text evidence** (`.txt` captures, LLM JSON dumps, Flask
logs) MAY commit to the PR branch under `evidence/` for traceability.

Per AGENTS.md "Evidence for mvp_site Production Changes": real LLM
captures required for `$PROJECT_ROOT/` changes — not static dumps. The three
replays (§4) satisfy this for prompt-only changes; UI-visible changes
also need video/screenshot evidence per the same policy.

Canonical PR body shape for this bug class:

```markdown
## Bug
[verbatim bug-trigger prose from the campaign's story doc]

## Root cause
[<prompt file path>:<line range>] had no anti-invention canon rule.

## Fix
Added [<new section name>] section to [<prompt file path>]. The rule:
- Canon source order: ...
- Forbidden inventions: ...
- Mundane replacements: ...
- Self-check: ...

## Evidence (/es)
### RED replay (before fix)
[agy CLI invocation, model, endpoint, prompt summary, result quote]
[link to evidence/red-direct-agy.txt]
### GREEN replay (after fix)
[same rig, with rule injected, result quote showing mundane replacement]
[link to evidence/green2-direct-agy.txt]
### Control test
[same rig, no rule injection, LLM still emits bug]
[link to evidence/green-direct-agy.txt]

## Scope discipline (root-cause-first)
Prompt-level only — no backend enforcement. Per AGENTS.md "Root-cause-first
prompt discipline", the failing path's selected agent (DialogAgent) did not
receive any anti-invention canon, so the fix MUST go in the prompt the
agent reads, not in a Flask-layer sanitizer.
```

## 8. Sibling cluster context

`D3iZvnGiBl9wyveQBFj9` is now the **3rd open repro campaign cluster** tracked
by `[references/repro-planning-block-and-campaign-cluster-2026-07-18.md]`:
- PR #8439 — first Blood-Scent repro (prompt-injection of canon statement
  → LLM self-corrects in the test rig)
- PR #8441 — planning-block + Valyria-steel repro
- PR #8443 — durable prompt fix for the lore-artifact invention class
  (this PR's reference)

Per `[references/phenotype-lock-static-evidence.md]` ≥3-open trigger:
**3rd repro shipped a durable fix** (not just another per-scene patch).
The campaign-cluster signal is now exhausted; future repros on
`D3iZvnGiBl9wyveQBFj9` should verify the fix in PR #8443 covers them
before opening new siblings.

## 9. Cross-campaign cluster trigger (verified issue #8451, 2026-07-18)

When the SAME magic-detection trope signature appears on **≥2 different
`campaign_id`s**, the structural issue is in the prompt layer (re-invention
at emit time), not per-scene. **The first campaign's repro was PR #8443;
the second confirmed cross-campaign instance is #8451 (campaign
`Cg2m2TkGFFez7XBynEah`, "Sariel Valyria", scene 171).**

Verified worked example for #8451:

| # | Campaign | Magic-detection trope emitted | Same prompt anchor |
|---|---|---|---|
| 1 | `D3iZvnGiBl9wyveQBFj9` (Reach, low-magic) | "Vaelaros-tuned 'Blood-Scent' focus" silver vial, violet light | archetype "Dread-Wyrm shadow" / "magical resonance" |
| 2 | `Cg2m2TkGFFez7XBynEah` (Valyria, high-magic) | "frequency-sensitive ward" / "draconic resonance" / "Lannister Ghost-Hunter" / "Reaver-Hounds" | archetype "Dread-Wyrm shadow" / "magical resonance" |

The shared structural cause is identical: when no canonical binding exists
in `state.json` / `narrative_system_instruction.md` / `custom_state` for
an NPC to detect a hidden protagonist, the LLM invents a magic-detection
trope as a cheap narrative shortcut to telegraph the dramatic reveal.
The user then issues god-mode retcons; the retcons do NOT survive
subsequent scenes because the LLM re-derives the trope from archetype
descriptors ("Dread-Wyrm shadow", "magical resonance") every turn.

**Decision rule for ≥2 cross-campaign instances:** the durable fix is
prompt-layer (not per-scene); stop filing per-campaign issues and route
to a single prompt-fix PR that adds the binding clause to
`narrative_system_instruction.md` covering BOTH campaigns.

## 10. Persistence-into-state finding (verified issue #8451, 2026-07-18)

Per the canonical skill's §2.1 first-touch discipline, the pre-state was
captured via direct Firestore read of the test subject's
`game_states/current_state` BEFORE any app API touch. The findings:

```json
{
  "npc_data_keys": [
    "Jaehaerys Vaelaros", "Archon Jaenor Vaelaros", "Edmyn Tully", "Lord Gwayne Gaunt",
    "Harren the Black", "Aenar Vaelaros", "Valerion Vaelaros", "Daenis Vaelaros",
    "Vaelen", "Gardener Inquisitor", "Viserra Vaelaros", "Kingspyre Guard",
    "Legate Valerius Vaelaros", "Visenya Targaryen", "Elaena Vaelaros",
    "Orys Baratheon", "Umbralax", "King Mern IX Gardener", "Argilac Durrandon",
    "Aegon Targaryen", "Maester Luthor", "Lysandra", "Lady Daenys Belaerys",
    "Lord Tytos Blackwood", "Harlen Tyrell", "Rhaenys Targaryen",
    "Lord Samwell Tarly", "Argella Durrandon", "Steward of Bitterbridge"
  ],
  "custom_state_keys": [],
  "interaction_count": 0,
  "blood_scent_in_state":     true,
  "frequency_trap_in_state":  false,
  "vaelaros_tuned_in_state":  false,
  "reprehound_in_state":      true,
  "ghost_hunter_in_state":    true,
  "directive_56_magical_resonance": false
}
```

**Structural findings (these change the durable fix shape):**

1. **`Gardener Inquisitor`** is a persisted NPC the LLM invented at
   scene 78 and the system wrote into `npc_data` without ever being
   introduced by a user action or god-mode directive. **LLM-invented
   NPCs are structurally indistinguishable from canon NPCs** — there is
   no `lore_origin` provenance field.
2. **`Blood-Scent` / `Reaver-Hound` / `Ghost-Hunter` tokens appear in
   the game-state document** because the story docs are stored inline
   or referenced from state. **The invention prose is structural, not
   just streamed.** A pure-prompt fix that prevents re-emission will
   not remove the existing artifact from state — additional work is
   needed to scrub `npc_data` and existing story docs.
3. **`custom_state_keys == []`** — the user has no architectural
   surface to set a per-campaign "no-magic-detection zone" that
   persists across scenes. Every turn, the LLM re-derives freely.
4. **Directive 56** (`magical resonance`) is referenced by the
   scene-172 5-whys but NOT materialized in `custom_state` — the
   directive lives only in the prompt, not in state. This is why
   retcons don't stick: the LLM can't reference a canonical anchor
   that doesn't exist in state.

**Updated durable-fix recipe** (extends §5):

| Anchor | Where it lives | What's missing |
|---|---|---|
| `§Forbidden Invention Class` (5 invention patterns) | `$PROJECT_ROOT/prompts/narrative_system_instruction.md` | never written |
| `custom_state.no_magic_detection_zone: bool` | `$PROJECT_ROOT/game_state.py` `custom_state` shape | field absent |
| `npc_data[<NPC>].lore_origin = "user-introduced"\|"LLM-invented"` provenance | `$PROJECT_ROOT/` NPC persistence layer | absent |
| `directive_persistence.py` (retcons scrub `npc_data` + story docs, not just `narrative_history`) | `$PROJECT_ROOT/` | absent |

## 11. Scene-counter offset trap (verified issue #8451, 2026-07-18)

**The live UI scene number reported by the user does NOT match the
`SCENE N` markers in `download_campaign.py` exports.** There is an
offset of (live scenes − export scenes). The export goes only up to
the moment of capture, and the live UI keeps incrementing.

Verified example (#8451): the user's scene 171 corresponded to export
"SCENE 78" (offset 93).

**Pitfall:** grepping for `SCENE 171` in the prior export finds nothing
because the export was captured earlier when the campaign was at scene
~78. The repro agent then either (a) wastes turns looking for the scene
by line number, or (b) misses the bug entirely because the canonical
emission is buried in scene 78 of the prior export.

**Detection rule:** if the user reports a scene number ≥ N where the
last `SCENE` marker in the available export is at scene << N, capture
the export AGAIN with `scripts/download_campaign.py` — the new export
will have SCENE N (or higher) and the live-ui scene number will match.

**Why this matters for repro evidence:** the static-evidence grep recipe
in §2 looks for the artifact's verbatim sentence in the export. If the
export is stale, the grep returns nothing and the agent files a
NON-REPRO when the bug is actually present.

## 12. `__pycache__` false-positive pitfall (verified issue #8451, 2026-07-18)

The canonical skill's `references/phenotype-lock-static-evidence.md`
recipe says:

```bash
grep -rin "<artifact>" $PROJECT_ROOT/
```

But a `Blood-Scent` test fixture from a prior repro (#8444) lives in
`$PROJECT_ROOT/tests/__pycache__/test_planning_block_canonical_state_anchor_8444.cpython-312-pytest-9.0.3.pyc`.
The grep WILL match the `.pyc` and report a false positive — making
the agent think the artifact is canon-anchored when it's only present
in a compiled test fixture.

**Workarounds:**
1. Always pass `--include='*.py' --include='*.md'` (or equivalent) to
   exclude `.pyc` files.
2. Run the grep from a clean worktree (`git worktree add -b fix/<name>
   origin/main`) where `__pycache__/` is rebuilt from scratch.
3. Explicitly note in the PR body: "the only matches are in
   `__pycache__/` test fixtures, which are stale build artifacts, not
   canonical sources."

**Detection rule:** if the grep result is ONLY `.pyc` files, the
artifact is canon-absent.

## 13. Updated "Forbidden Invention Class" recipe (extending §5)

The original durable fix (§5) added the NPC Canon Anchoring rule to
`narrative_system_instruction.md`. The cross-campaign cluster
extension (≥2 campaigns) calls for a NEW section in the same file that
enumerates the 5 invention patterns observed in this bug class:

```
### § Forbidden Invention Class (MANDATORY, verified #8451)

The following tropes are PROHIBITED in narrative emit unless the user
has explicitly written them into `custom_state` or `npc_data` via a
prior god-mode directive or game-state write:

1. **"X-tuned" magical modifier** with no canonical source — e.g.
   "Vaelaros-tuned focus", "Targaryen-imbued trinket". The "X" is fake
   specificity that names an unrelated house/faction.

2. **Glowing vial / glowing prop shortcut** for "they detected your
   disguise" — silver vials with pulsing violet light, bioluminescent
   amulets, "keen scent" trinkets. Pure LLM improvisation.

3. **"Frequency-sensitive ward" / "resonance alarm" / "draconic
   resonance detection"** — pseudo-technical language for what is
   actually a magic-detection trope. The "frequency" / "resonance"
   vocabulary is the LLM trying to look grounded while emitting
   invented mechanics.

4. **"Frequency-shield" passive defense on the protagonist** — the
   post-retcon re-emergence pattern. Even after the user retcons the
   detection trope, the LLM emits a "frequency-shield for the terrified
   refugees behind you" — same vocabulary, same invention tendency.

5. **Cross-tier magic detection** — Westerosi Reach NPC (LOW-MAGIC)
   using a Sorcery-tier item; Lannister "Ghost-Hunter" with a
   "frequency-sensitive ward" (Lannisters have no canon tradition of
   magical detection). Detection must respect the setting's magic-tier
   rule.

**Fallback when none of these tropes is canon-anchored:** the LLM
must default to MUNDANE detection (gate logs, paid informants,
interrogation, betrayal, physical evidence, surveillance) — NEVER
emit a magic-detection invention.
```

Pair this with a parallel test file in `$PROJECT_ROOT/tests/` that asserts
each of the 5 patterns is mentioned by name in the prompt section
(case-folded substring match), AND asserts the absence of any of the
5 patterns from the test prompt's forbidden-output zone.

## Related references

- `[references/phenotype-lock-static-evidence.md]` — campaign-cluster
  structural trigger (≥3 open repros)
- `[references/repro-planning-block-and-campaign-cluster-2026-07-18.md]`
  — sibling campaign `D3iZvnGiBl9wyveQBFj9` planning-block repro
- `[references/god-mode-directive-missing-subclasses.md]` — directive
  persistence bugs (Class 1)
- `[references/npc-status-persistence-bug.md]` — canonical-state anchor
  bugs (Class 2)
- `[references/static-evidence-sufficient-no-live-turn.md]` — when
  static evidence satisfies §2.1 (saves LLM calls)
- `[references/gh-rate-limit-rest-fallback.md]` — REST API fallback when
  GraphQL budget is exhausted (used for the PR create in this session)