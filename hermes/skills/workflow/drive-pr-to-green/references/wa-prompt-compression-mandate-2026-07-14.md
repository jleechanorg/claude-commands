# WA prompt compression mandate (AGENTS.md § Prompt Duplication & Compression)

**Repo:** `$GITHUB_REPOSITORY`
**File:** `AGENTS.md` (workspace root)
**Section:** "Prompt Duplication & Compression" (or equivalent — read AGENTS.md in the target repo before compacting; the section name can drift)

**Rule:**
Files under `$PROJECT_ROOT/prompts/` MUST be compacted whenever they grow above a critical-token threshold. Compaction goals, in priority order:
1. **Maximize Gemini implicit cache hits** — shorter, denser prompts reuse cached tokens across turns.
2. **Reduce per-turn token overhead** — prompt bloat burns input tokens on every LLM call.
3. **Consolidate overlapping concepts to a single authoritative file** — when two prompt files describe the same rule, fold them into one and remove the duplicate. The canonical file is usually `narrative_system_instruction.md` (it owns the broadest cross-cutting rules); `living_world_instruction.md`, `dialog_system_instruction.md`, and `narrative_lite_system_instruction.md` should defer to it.

**Compact-form pattern (verified 2026-07-14, PR #8389 compaction round 2):**

| Original | Compact | Lines saved |
|----------|---------|-------------|
| `### 🌊 VICTORY RIPPLE PROTOCOL` — 18 lines + 3-row table + 3 narrative rules | `### 🌊 VICTORY RIPPLE` — 1 dense paragraph with 3 inline consequence shapes `(a)/(b)/(c)` | −16 |
| `### Momentum Counterpressure` — 18 lines + 4-bullet counter-response shapes + ratchet-prevention + DM-judgment-gate | `### Momentum Counterpressure (anti-ratchet)` — trigger line + shapes line + ratchet-lock line + fallback line | −10 |

**What to keep when compacting:**
- **Binding triggers** (the "when X happens, do Y" clause). Strip modifiers.
- **Three (or fewer) consequence shapes** — enumerate inline as `(a)/(b)/(c)`, not as a table.
- **Calibration / scaling rules** — fold into the same paragraph as the trigger, NOT a separate section.
- **Distribution rule / ratchet-lock / no-opposition fallback** — single line each, no preamble.

**What to drop:**
- Redundant `**Trigger:**`, `**Obligation:**`, `**Calibration:**`, `**Distribution rule:**`, `**Player agency:**` preamble headers — the LLM doesn't need each rule labeled.
- Per-shape examples ("The Reach's Tarly faction refuses...") — one example per category is enough; put it in a single inline phrase, not a 3-row table.
- Cross-references to other prompt sections that say "see Unforeseen Complication System" — keep the local rule self-contained.

**Workflow when compacting for /green PRs:**

1. Run `cat AGENTS.md | head -100` in the target repo to confirm the compression mandate section still applies (it can drift).
2. Read the prompt files on the PR's branch: `git show origin/<branch>:$PROJECT_ROOT/prompts/<file>.md`.
3. Compute the diff: original line count → compact line count. Aim for −40% to −60% line reduction on prose rules (table-to-inline conversions are the biggest wins).
4. Verify no rule is LOST in the compaction by re-reading both versions side-by-side and grep-checking that all named concepts (e.g., "surrendered", "SURRENDERED", "social HP = 0", "splinter", "power vacuum", "concrete cost") appear in the compact version.
5. Update the PR body with "Round N compaction" mention, link to AGENTS.md compression mandate, and cite the line-count delta.
6. Re-trigger CI on the compacted branch.

**Pair with:**
- `commit-same-test-name-rule` — pre-existing CI failures don't block the compaction commit.
- `commit-pr-clean-branch-from-main-no-history-bloat` — start compaction from `origin/main` clean.
- `pr-cleanup-replay` — if you accidentally inherited another PR's history, replay clean.

**Bead / provenance:**
- Session 2026-07-14 22:00 PT, dispatch-task → drive PR #8389 to green
- Branch: `fix/visenya-v8-difficulty-regression`
- Round 1 PR author: AO `[agento]` worker (commit `72c664886e`, +161 lines)
- Round 2 compaction author: this session (commit `0f95a61242`, +135 lines, −26 net)
- Lesson: the AO worker did NOT apply the compression mandate; it produced a working but verbose change. A Round-2 pass is sometimes needed.