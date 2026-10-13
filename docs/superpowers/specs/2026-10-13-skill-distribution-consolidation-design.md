# Design: Consolidate skill-distribution mechanisms to one bundle + one verifier

Date: 2026-10-13 · Repo: jleechanorg/jleechan-skills

## Context (evidence, verified 2026-10-13)
| Mechanism | Payload | Evidence |
|---|---|---|
| `.claude/skills/` | 239 skills | README: "source of truth" |
| `shared-skills.json` (`jleechan-shared-skills-v1`) | 4 reconciled skills, sha256-pinned | `install_shared_skills.py`, `tests/test_shared_skills.py`, `SHARED-SKILLS.md` |
| `portable/manifest.json` (`jleechan-portable-skills-v1`) | 29 skills / 32 files **+ a duplicate `portable/skills/**` tree (34 files, 180K)** | `scripts/verify_portable_skills.py`, `tests/test_portable_install.py`, `tests/test_cross_host_catalog.py` fixtures |
| `.claude-plugin/marketplace.json` + `.agents/plugins/marketplace.json` | same 1 plugin, two manifest copies | both files present |
| `install-claude-commands.sh` | whole-home installer | SHARED-SKILLS.md: "Do not use the older portable installer or the whole-home Claude installer" |
| `scripts/sync_live_config.py` | repo<->live freshness machine | sync-live-config skill |
| live trees | `~/.claude/skills` 643, `~/.agents/skills` 645, `~/.codex/skills` 469 | host inventory |

## Problem
Five distribution channels (two bundle formats, two verifiers, three installers, two marketplaces,
three live discovery trees, four sync/verify checkers) make authoritative state ambiguous and
create guaranteed drift: the same 29 skills exist twice in-repo (`portable/skills/**` duplicates
`.claude/skills/**`), and "what is installed" has three different answers.

## Assumptions and Recommended Defaults (auto-picked; /sq invocation authorizes these)
| Question | Auto-picked answer | Rationale |
|---|---|---|
| Which manifest is authoritative? | `shared-skills.json` | SHARED-SKILLS.md names it the current flow; README names `.claude/skills/` the source for *content* |
| Delete `portable/` or regenerate it? | Delete the duplicate `portable/skills/**` tree; keep a dated deprecation stub manifest OR remove the dir entirely after migrating its two tests | Removing duplicate bytes is the actual win; a projection that is not regenerated is drift waiting to happen |
| Keep `verify_portable_skills.py`? | Fold its SHA256 verification into one verifier over the single manifest; retire the portable-format branch once no manifest uses it | One verifier per manifest format is defensible; two formats is not |
| Marketplace duplication | Make `.agents/plugins/marketplace.json` a symlink to `.claude-plugin/marketplace.json` | One canonical plugin manifest |
| Live discovery trees | `~/.claude/skills` canonical; treat `.agents/skills` + `~/.codex/skills` as generated links (or drop the `.codex` projection) | `/up` skill already says "Do not add .codex user projections" |
| Dead installer | Retire `install-claude-commands.sh` (or reduce to a wrapper that calls the catalog installer) | Docs already tell users not to use it |
| Sequencing | Stage as deletion milestone: (A) single marketplace manifest + decision record; (B) retrain verifier on one manifest; (C) delete `portable/` + migrate tests; (D) retire the dead installer | Each stage independently testable, reversible |

## Alternatives considered
1. **Keep both bundles, document precedence only.** Rejected: leaves duplicated bytes; documentation does not prevent drift.
2. **Make `portable/` the single bundle, retire `shared-skills.json`.** Rejected: `shared-skills.json` is the flow the repo's own docs and installer designate as current, and its 4 reconciled entries are the ones with semantic sign-off.
3. **Single manifest (`shared-skills.json`) as the only bundle; delete the duplicate portable tree; one verifier; one marketplace manifest; one live canonical tree.** Chosen.

## Design
- **One manifest**: `shared-skills.json` is the only bundle definition. The `skills` list is the selected set; `files` carries sha256 for every shipped byte.
- **One verifier**: a single script verifies the selected manifest against `.claude/skills/**` (inventory + digest), replacing format-specific verification.
- **One installer**: `install_shared_catalog.py` (reversible consumer links) is the only install/activate path.
- **One marketplace manifest**: `.claude-plugin/marketplace.json`; `.agents/plugins/marketplace.json` becomes a symlink.
- **One live canonical tree**: `~/.claude/skills`; other runtimes get discovery links generated from it.
- **One sync authority**: `sync_live_config.py` for freshness; no per-format checkers.
- **Duplication removed**: `portable/skills/**` deleted; the two tests that reference it migrated to assert against the chosen manifest instead.

## Implementation Preconditions
- None blocking for stages A-C. Stage D (installer retirement) requires confirming no launchd/cron job invokes `install-claude-commands.sh` on any host; verify before removal, else reduce to a wrapper.

## Out of scope
- Semantic reconciliation of the remaining `.claude/skills/**` entries into the shared bundle (separate reviewed work).
- Changing which skills exist.
