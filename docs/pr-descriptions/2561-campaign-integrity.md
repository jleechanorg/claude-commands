## Summary

Implements LLM-driven Campaign Integrity Guidelines to address four structural flaws observed in long-running campaigns (based on Alexiel campaign analysis). These are **flexible guidelines** that adapt to campaign style (standard, epic, or power fantasy).

### Problem Statement (from docs/debugging/Alexiel assiah.txt analysis)

| Flaw | Symptom | Solution |
|------|---------|----------|
| "Speedrun" Progression | Level 1 → Level 50+ in single session | Milestone Leveling Protocol |
| "Yes-Man" NPCs | Kings fold to single Persuasion roll | Social HP System |
| "Infinite Ammo" | No resource tracking, unlimited spells | Resource Attrition Protocol |
| "Christmas Tree" | Unlimited magic item attunement | Configurable Attunement Economy |

## Changes vs origin/main

### Files Modified

| File | Lines | Description |
|------|-------|-------------|
| `mvp_site/prompts/mechanics_system_instruction.md` | +310 | Milestone Leveling, Attunement Economy, High-Magic Balance, Resource Attrition |
| `mvp_site/prompts/narrative_system_instruction.md` | +132 | Social HP System, NPC Hard Limits, Skill Challenge Protocol |
| `mvp_site/prompts/master_directive.md` | +19 | Version 1.6→1.9, Campaign Integrity Guidelines + merge with Data Query Protocol |
| `testing_mcp/test_campaign_integrity_real_api.py` | +438 | 7 test scenarios validating LLM adherence |
| `docs/merge-decisions/2025-12-27-campaign-integrity-merge.md` | +79 | Merge conflict resolution documentation |

### New Features

#### 1. Milestone Leveling Protocol (mechanics_system_instruction.md:102-178)
- **Recommendation:** +1-3 levels per major story arc
- **Campaign Styles:** Standard (cap L20), Epic (exceeds L20), Power Fantasy (rapid progression)
- **Pacing Warnings:** Flags when tiers are skipped without meaningful play
- **Flexibility:** DM discretion takes precedence

#### 2. Social HP System (narrative_system_instruction.md:55-136)
- **NPC Resistance Tiers:** Commoner (1-2), Noble (3-5), King (8-12), God (15+)
- **Skill Challenge Protocol:** Complex persuasion requires multiple successes
- **DC Guidance:** Momentum bonus (-2 per success), near-breakpoint bonus
- **Hard Limits:** NPCs have inviolable beliefs that cannot be overridden

#### 3. Resource Attrition Protocol (mechanics_system_instruction.md:475-577)
- **Spell Slot Tracking:** MANDATORY display after each cast
- **Exhaustion Rules:** Forced march penalties per D&D 5e
- **Resource State JSON:** Structured tracking in state_updates
- **Wait Command:** Autonomous resource management with pause for major decisions

#### 4. Attunement Economy (mechanics_system_instruction.md:330-474)
- **Configurable Modes:** Standard (3), Loose (5-6), None (unlimited)
- **High-Magic Balance:** Tier-based encounter design instead of item limits
- **Enemy Parity:** If players have magic items, enemies get equivalents
- **Stacking Rules:** Same-named bonuses don't stack

### ESSENTIALS Section (Token-Optimized Summary)

```markdown
- NON-COMBAT KILLS: Executions, ambushes, trap kills MUST award XP + loot
- NARRATIVE EVENTS: Quests, milestones, social victories MUST display XP
- MILESTONE LEVELING: Recommend +1-3 levels per arc. Epic campaigns may exceed L20.
- ATTUNEMENT: Configurable (Standard=3, Loose=5-6, None=unlimited)
- HIGH-MAGIC BALANCE: T1=5-7 encounters/day, T2=elite groups, T3=set-pieces
- RESOURCES: Track spell slots per cast. Forced march = exhaustion.
```

### Test Coverage

New test file `testing_mcp/test_campaign_integrity_real_api.py` with 7 scenarios:

| Category | Test | Validates |
|----------|------|-----------|
| milestone_leveling | Single Arc Level Up | Reasonable level progression |
| milestone_leveling | Epic Campaign High Level | Level 20+ with epic boons |
| social_hp | King Persuasion Resistance | High-authority NPC resistance |
| social_hp | Commoner Quick Persuasion | Low-authority NPC flexibility |
| npc_hard_limits | Paladin Oath | Inviolable beliefs respected |
| resource_attrition | Spell Slot Tracking | Resource mentions in narrative |
| attunement_economy | Standard Limit | Attunement limit awareness |

### Additional Test Coverage (Campaign Balance)

New test file `testing_mcp/test_campaign_balance_real_api.py` expands coverage beyond integrity-only checks:

| Category | Focus | Validates |
|----------|-------|-----------|
| spell_slots | Single cast decrement | Game state spell slots decrement after a 3rd‑level cast |
| attunement | Over‑cap item | Attunement limit enforced in narrative |
| level_cap | Standard D&D cap | Level does not exceed 20 |
| xp_sanity | CR‑appropriate award | XP gain is within a reasonable range |
| social_hp_multi | Multi‑turn persuasion | Gradual progress, no single‑roll domination |
| hard_limits_multi | NPC oath | Hard limits cannot be overridden |
| adversarial | Prompt abuse | Rejects infinite resources / forced outcomes |
| consistency | Repeated scenario | Enforcement rate across multiple runs |

### Evidence Bundle Expectations (Real Mode)

These tests are LLM‑behavior claims. Evidence bundles **must** include:
- `balance_test_results.json` + `.sha256`
- `request_responses.jsonl` + `.sha256` (raw request/response capture)
- `local_mcp_*.log` + `.sha256`
- `metadata.json` + `.sha256` (git + server provenance)

Verification checklist:
```bash
sha256sum -c balance_test_results.json.sha256
sha256sum -c request_responses.jsonl.sha256
sha256sum -c local_mcp_*.log.sha256
sha256sum -c metadata.json.sha256
```

### Scope & Limitations

- Evidence is **local‑real** (127.0.0.1), not production/preview.
- Test scenarios are representative but **not exhaustive**; they validate guideline adherence in specific cases.
- Consistency tests provide a small statistical sample, not full distribution guarantees.

### Merge Conflict Resolution

#### Merge #1: 2025-12-27 (Non-Combat XP)
Merged cleanly with main's Non-Combat XP rules (PR #2553). Both rule sets kept:
- **Main's rules:** XP transparency (display rewards visibly)
- **Our rules:** Campaign pacing/balance (prevent power creep)

See `docs/merge-decisions/2025-12-27-campaign-integrity-merge.md` for full rationale.

#### Merge #2: 2025-12-30 (Data Query Response Protocol)

**Conflict Location:** `mvp_site/prompts/master_directive.md`

**Conflict Details:**
| Region | HEAD (our branch) | main |
|--------|-------------------|------|
| Version header | v1.7, 2025-12-22 | v1.8, 2025-12-30 |
| Version history | v1.7 = Campaign Integrity | v1.7 = Data Query Protocol, v1.8 = Strengthened Query Protocol |

**Resolution Strategy:**
Both branches introduced independent, valuable features that need preservation:
- **main's contribution:** Data Query Response Protocol - ensures numeric questions get numeric answers first (v1.7→1.8)
- **Our contribution:** Campaign Integrity Guidelines - prevents power creep, yes-man NPCs, etc.

**Resolution Applied:**
1. **Version:** Advanced to **v1.9** (combining both contributions)
2. **Date:** Used main's date (2025-12-30) as most recent
3. **Version history:** Preserved main's v1.7 and v1.8 chronologically, added our Campaign Integrity as v1.9

**Rationale:**
- Both features are orthogonal (query formatting vs. game balance) - no semantic conflict
- Main's versions are chronologically earlier - should come first
- Our feature becomes v1.9 as the newest addition
- All feature content from both branches is preserved in the final file

## Token Impact

~5,000 additional tokens per request (~22% increase) in full mode. ESSENTIALS mode adds ~60 tokens.

## Test Plan

- [ ] Run `testing_mcp/test_campaign_integrity_real_api.py --start-local` 
- [ ] Verify milestone leveling doesn't produce Level 50+ jumps
- [ ] Verify kings don't fold to single Persuasion rolls
- [ ] Verify spell slot mentions appear after casting
- [ ] Verify attunement limits are mentioned when exceeded
