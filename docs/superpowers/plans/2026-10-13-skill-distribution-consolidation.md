# Plan: Consolidate skill-distribution mechanisms (staged deletion milestone)

Spec: `docs/superpowers/specs/2026-10-13-skill-distribution-consolidation-design.md`

Each stage is independently testable and reversible. Run `python3 -m unittest discover -s tests -p "test_*.py"` after every stage.

## Stage A — one marketplace manifest + decision record
1. RED: add `tests/test_single_marketplace_manifest.py` asserting:
   - `.agents/plugins/marketplace.json` is a symlink resolving to `.claude-plugin/marketplace.json`
   - both paths parse to identical JSON
   Run it: expect FAIL (`Not a symlink`).
2. Implement: `git rm .agents/plugins/marketplace.json && ln -s ../../.claude-plugin/marketplace.json .agents/plugins/marketplace.json`
3. GREEN: rerun the new test → PASS.
4. Docs: in `SHARED-SKILLS.md`, add a "One bundle, one verifier, one installer" section naming `shared-skills.json` as the only bundle, `portable/` as deprecated, and the single live canonical tree.
5. Verify: full suite green apart from the known macOS-only `test_tdd_skill_integration` path failure.

## Stage B — one verifier over the single manifest
1. RED: add `tests/test_shared_manifest_verifier.py` asserting `scripts/verify_shared_skills.py`:
   - refuses when a listed skill is missing or a digest mismatches
   - passes on the committed manifest
   Run it: expect FAIL (script absent).
2. Implement `scripts/verify_shared_skills.py`: read `shared-skills.json`, assert `skills` == the selected directories under `.claude/skills/` that the manifest ships, assert every `files` entry matches the bytes, refuse symlinked skill roots.
3. GREEN: rerun; then run it against the repo root → exit 0.
4. Keep `scripts/verify_portable_skills.py` until Stage C completes (its format is still referenced by tests).

## Stage C — delete the duplicate portable bundle
1. RED: rewrite `tests/test_portable_install.py` to assert against `shared-skills.json` + `scripts/verify_shared_skills.py` (no `portable/` path), and update `tests/test_cross_host_catalog.py` fixtures that create `portable/skills` to use `.claude/skills` instead. Run both: expect FAIL against the current tree only where they still reference `portable/`.
2. Implement: `git rm -r portable/` (34 files, 180K) and delete `scripts/verify_portable_skills.py`.
3. GREEN: full suite passes (minus the known macOS path failure); `grep -rn "portable/" --include=*.py --include=*.md .` returns no live references outside history/archive.
4. Commit as a deletion milestone; report net LOC.

## Stage D — retire the dead installer (conditional)
1. Precondition: `grep -rn "install-claude-commands.sh" ~/Library/LaunchAgents launchd crontab -l 2>/dev/null` shows no live invocation. If any exists, STOP and reduce the script to a wrapper that execs the catalog installer instead of deleting it.
2. If clear: `git rm install-claude-commands.sh`; update README/INSTALL.md references to point at `scripts/install_shared_catalog.py`.
3. Verify: full suite + a dry-run of the catalog installer.

## TDD Plan Check
| Task | Sequence checked | Notes |
|---|---|---|
| A | RED test → symlink impl → GREEN | behavior change (path identity) pinned by a new test |
| B | RED test → verifier impl → GREEN | behavior change (verification gate) pinned |
| C | Tests migrated first → deletion → GREEN | deletion milestone; tests are the guard |
| D | Precondition grep → (wrapper or delete) → GREEN | conditional; guard is the precondition check, `TDD: N/A` for pure file removal with a documented precondition |
