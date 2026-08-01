# SOUL.md compression contract

**Trigger:** user requests a byte-count reduction of `~/.hermes/workspace/SOUL.md` (e.g. "compress the soul MD", "trim SOUL.md", "it's too long", "fit under X chars"). This is a RECURRING class — there is prior history:

- Commit `6e2470345c chore: trim SOUL.md to fit gateway 48,660-char limit (#706)` (jleechanorg/jleechanclaw).
- PR [#789](https://github.com/jleechanorg/jleechanclaw/pull/789) "compress SOUL.md ~30% (105KB → 73KB)" (2026-07-21, prior session).

The recurring nature is the signal: the file grows monotonically as new `## COMMIT:` blocks pile up, and the gateway loads it whole on session-init, so byte-bloat is paid by every future session. Skillify once so future compressions don't reinvent the invariants.

## The four invariants (NEVER violate)

After every compression, the following counts MUST be byte-equal pre/post:

```bash
grep -c '^## COMMIT:'  workspace/SOUL.md    # before: N, after: N
grep -c '^Trigger:'    workspace/SOUL.md    # before: N, after: N
grep -c '^Action:'     workspace/SOUL.md    # before: N, after: N
```

If any count DROPS, you deleted or merged a behavioral contract — that's a contract regression the gateway cannot recover from until the next session-init. STOP and reinstate.

If the count of `## COMMIT:` headers RISES, you accidentally added one — also a bug. The compression should be a strict byte reduction, not a re-authoring.

## The compression strategy that worked (verified 2026-07-21)

Whitespace tightening is a **0%** reduction (verified — the file is structurally tight). Real reduction comes from **prose rewriting** of the 10–15 longest `## COMMIT:` blocks:

1. **Rank blocks by length.** Use Python or `awk` to find blocks >2,500 bytes:
   ```python
   sections = re.split(r'(?=^## COMMIT: )', content, flags=re.MULTILINE)
   sized = sorted(((len(s), s.split('\n')[0], s) for s in sections[1:]), reverse=True)
   ```
2. **Rewrite each top block** by replacing verbose `Bug-ref / Why / multi-paragraph verification recipe / Test plan` prose with a compact `Trigger + Action + skill-pointer`. The pattern:
   - Drop `Why:` if it duplicates info already in the linked skill.
   - Drop `Test:` if a regression test already pins the contract.
   - Collapse `Bug-ref:` paragraphs to `<date>: <thread link>`.
   - Replace lists of `1. 2. 3. 4. verification steps` with `"Verify: <script-or-grep>"`.
3. **Add explicit skill-pointers** for any detail you cut (`Skill: ~/.hermes/skills/<name>/SKILL.md`). This is non-negotiable — the detail must live SOMEWHERE durable or it gets lost. SOUL.md's own self-directive:
   > *Keep SOUL.md high-level only; put detailed cadence/stop-state/anti-stall protocol in the skill file.*
4. **Verify invariants** with the four-count grep above before declaring done.

The 15 longest blocks (and their 2026-07-21 compression ratios):
- `novel-entry-proof-and-memory-ledger` — 6,147 → ~700 (-89%)
- `ms-on-new-task` — 5,258 → ~1,400 (-73%)
- `mcp-agent-mail-no-passive-slack-listening` — 5,189 → ~1,250 (-76%)
- `evidence-attach-presend-gate` — 4,998 → ~1,300 (-74%)
- `read-auth-gated-share-links-with-browserclaw` — 4,963 → ~1,400 (-72%)
- `explicit-af-task-lock` — 4,420 → ~300 (-93%)
- `prefer-builtin-slack-mcp` — 4,154 → ~1,000 (-76%)
- `hermes-tag-webhook-per-repo-routing` — 3,756 → ~1,600 (-57%)
- `dark-factory-canonical-locations` — 3,657 → ~1,400 (-62%)
- `meta-autonomy-violation-handler` — 3,364 → ~1,200 (-64%)
- `babysit-cron-self-cancel-discipline` — 3,166 → ~1,000 (-68%)
- `mcp-mail-ack` — 3,151 → ~500 (-84%)
- `deploy-failure-classify-by-symptom` — 3,068 → ~1,300 (-58%)
- `cloud-build-bastion-watchdog-always-on` — 2,581 → ~900 (-65%)
- `dropped-thread-watcher-of-watchers` — 2,581 → ~1,100 (-57%)

**Total: 105,042 → 73,314 (-30.2%)**

## The three-line contract test

Lock the invariants in `tests/test_soul_compression.py` in `jleechanclaw`. The test the operator should ship alongside any future compression PR:

```python
# tests/test_soul_compression.py
import re
from pathlib import Path

SOUL = Path("workspace/SOUL.md")

def test_soul_size_under_budget():
    """SOUL.md is loaded whole by the gateway on every session-init.
    Budget depends on runtime; current target is 75 KB."""
    assert SOUL.stat().st_size <= 75_000, f"SOUL.md is {SOUL.stat().st_size:,} bytes"

def test_commit_count_stable():
    """Each ## COMMIT: section is a behavioral contract the gateway reads."""
    count = len(re.findall(r"^## COMMIT: ", SOUL.read_text(), re.MULTILINE))
    # Adjust this constant as new contracts are intentionally added (PR review).
    assert count == 55, f"Expected 55 ## COMMIT blocks, got {count}"

def test_trigger_action_lines_unchanged():
    """Each ## COMMIT: block must keep its 'Trigger:' and 'Action:' lines."""
    text = SOUL.read_text()
    assert len(re.findall(r"^Trigger:", text, re.MULTILINE)) == 55
    assert len(re.findall(r"^Action:", text, re.MULTILINE)) == 55
```

Run before opening the PR. Run again after merge to `origin/main`. Same numbers = compression is safe.

## The deploy sequence (verified 2026-07-21)

Because the gateway loads from `~/.hermes_prod/SOUL.md` at session-init, the compression must be visible BEFORE the next session. The 3-place write:

1. **Edit staging worktree** — `cd $HOME/project_jleechanclaw/jleechanclaw` (or whichever clone is the source-of-truth for `workspace/SOUL.md`). Apply your compression here. This is what becomes the PR diff.
2. **Apply to live file** — `cp workspace/SOUL.md $HOME/.hermes/workspace/SOUL.md` (or whichever staging tree is the runtime-active symlink target — verify with `ls -la ~/.hermes/` first; on 2026-07-21 it is the `~/.hermes/` itself, no symlink). The running gateway has the live file open in memory; the next session-init re-reads it.
3. **Back up the pre-compress** — `cp ~/.hermes/workspace/SOUL.md ~/.hermes/workspace/SOUL.md.pre-compress.bak`. Always. The user is right to be skeptical of SOUL.md edits without a rollback.
4. **Stage + commit + push + PR** in the worktree. The push to `origin/main` triggers the next `deploy.sh` cycle if you let it run. Per the umbrella's "SOUL.md only" rule, the right flag combo is `--skip-pull --skip-restart` — let the user trigger the deploy on their own schedule.

## Pitfalls

### Don't merge two `## COMMIT:` blocks "to save space"

Two contracts sharing one section breaks the trigger-based-fire model (each section is independently scanned). The gateway cannot dispatch on the merged block. Keep them 1:1 — only compress internal prose.

### Don't drop the `Bug-ref:` line even when rewording

`Bug-ref:` is the audit trail that says WHY this rule exists. Future agents (and the user) need to be able to look up the originating incident. A 1-line `Bug-ref: 2026-07-02 Slack thread …` is enough; do not delete entirely.

### Watch out for the `workspace/` gitignore trap

`workspace/` is in `.gitignore` (with `!workspace/README.md` exception). When committing the compression from the source-of-truth clone:
```bash
git add -f workspace/SOUL.md      # force-add overrides gitignore for tracked files
```
Without `-f`, `git add` errors with `ignored by one of your .gitignore files` even though the file IS in `git ls-files`. Verified 2026-07-21.

### Verify the live file, not the worktree

The PR diff passes CI on the worktree. The runtime contract is the live file at `~/.hermes/workspace/SOUL.md`. After applying the change, run the three invariants on BOTH files:
```bash
diff <(grep -c '^## COMMIT:'  workspace/SOUL.md) \
     <(grep -c '^## COMMIT:'  $HOME/.hermes/workspace/SOUL.md)
# Both must be 55
```

### Don't push the compression onto a non-clean branch

If the staging worktree has uncommitted changes (other dirty files from prior sessions: `Cargo.lock`, `memory.db`, doctor.sh edits, etc.), `git worktree add -b chore/soul-md-compress <path> origin/main` will fail or create a polluted branch. Use `references/staging-dirty-quarantine-stash.md` to quarantine the unrelated dirty work first.

## Companion recipes

- `references/staging-dirty-quarantine-stash.md` — when the source-of-truth clone has unrelated dirty files, the right move is `git stash push -u -m "STASH pre-<purpose> — N files"` so the compression PR stays single-file clean.
- `references/jleechanclaw-slash-command-rollout.md` — the same file-tree routing rules apply for `workspace/SOUL.md` edits as they do for `.claude/commands/` rollouts: three wiring points (worktree PR + live staging + live prod) and the `git add -f` workaround.
