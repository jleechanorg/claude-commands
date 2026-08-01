---
name: patch-review-taxonomy
description: Provenance + reusable taxonomy for `/advice` reviews of patches (trim, refactor, rename, "fix overclaim", content-edit) — distinct from the docs-accuracy template which targets static merged docs. Used by `advice` SKILL.md's "Patch review (trim / refactor / rename)" variant — re-derive the classification, do NOT trust this transcript as fresh evidence.
date: 2026-07-15
patch: sidekick-swarm-trim-20260715-143103.patch (Slack attachment F0BHMPC9TA6, 69KB)
verdict: docs MISLEADING — do NOT apply as-is
---

# Patch review taxonomy — 2026-07-15 worked example

This is the cached evidence supporting the `advice` skill's "Patch review (trim / refactor / rename)" template. **Do not cite it as fresh evidence** — re-derive the verdict from the live patch and source.

## When to use this template (not docs-accuracy)

Use the patch-review template when the artifact IS a patch / diff / content-edit, NOT a static merged doc:

- User uploaded a `.patch` / `.diff` and asked `/advice` on it
- User pasted a "fix typo / rename / trim / refactor" PR diff for review
- The artifact is a sequence of `--- a/path +++ b/path` hunks with `-`/`+` line pairs
- Reviewers must answer BOTH "is the new content accurate?" AND "did the diff remove anything load-bearing?"

The docs-accuracy template only covers the first question. Patch review needs both.

## The "what got removed" classification (Reviewer B's job)

Every `-` line in the patch must be classified into one of these five buckets. The classification drives the verdict:

| Bucket | Definition | Default action |
|---|---|---|
| **Flavor** | Timestamp, anecdote, agent count, marketing framing, incident description. Rule survives without it. | Safe to remove. |
| **Load-bearing example** | Specific PR number, specific bead ID, specific incident timestamp, specific commit SHA. Removing it weakens future re-discovery. | Restore, OR replace with a one-line pointer (e.g. "see PR #N for the original incident"). |
| **Safeguard / gotcha** | A warning, a counter-example, a "do not do X" rule. | Almost never safe to remove. If removed, the rule alone must still catch the failure mode. |
| **Cross-reference / pointer** | "See X for detail", "see Y section". If X is removed, the pointer becomes broken. | Check that the target survives; if not, fix the pointer. |
| **Snuck-in content** | NEW content in a "trim" or "typo fix" PR — anything that adds lines under cover of a removal PR. | Reject — opens to a separate PR with its own review. |

**Detection shortcut for "snuck-in":** sort the diff by `+` line count per file. If any file's `+` count exceeds its `-` count by more than 30% AND the PR title says "trim" / "cleanup" / "fix typo", suspect snuck-in content and inspect every `+` line.

## The "what was added" classification (Reviewer B + C joint)

Every `+` line must also be checked for:

1. **Factually accurate claims** (Reviewer A): does each new claim match the cited source? Not just "plausible" — actually traceable to file:line or live URL.
2. **Internal contradictions** (Reviewer C): does the new text reference something the removed text defined? Run `grep -n "<orphaned phrase>" <patch>` — any surviving text that references a removed concept is an orphan.
3. **Strawman / invented-feature disclaimers** (Reviewer A): hunks that say "NOT its <X> feature" must verify `<X>` is actually a feature of the cited source. The most common failure mode is naming a real feature just to disclaim it — see pitfall below.

## State-corruption pre-flight (NEW — Phase -0 for patch reviews)

**Before any reviewer runs**, verify the on-disk state matches the patch's expected source:

```bash
# For each file in the patch:
for f in $(grep -oE '^diff --git a/\S+' patch.diff | sed 's|^diff --git a/||'); do
  echo "=== $f ==="
  ls -la "$f"  # mtime + size
  md5 "$f"     # hash
  # Spot-check: does the file still have the load-bearing content the patch removes?
  # If the file has been REPLACED with unrelated content (e.g. sidekick/SKILL.md = swarm content),
  # git apply will produce .rej files or --reject conflict markers and the patch CAN'T apply.
done
```

If the on-disk state is corrupted:
1. Do NOT try to apply the patch — it won't work and you'll get `.rej` files that leave the workspace dirty.
2. Stop the review and report the corruption to the user.
3. Optionally restore from a known-good external copy (e.g. `projects_other/<repo>/<path>`).
4. Note the restoration in the synthesis output so the user knows state changed.

**Why this is a Phase -0 step:** patch reviews that assume on-disk state is correct will:
- Apply to corrupted files and silently ship bad content
- Produce `.rej` files that confuse downstream agents
- Wasted reviewer quota on a patch that physically can't apply

## Orphan-reference detection (Reviewer C's job)

After the patch is conceptually applied, grep the patched file (or the +/context lines of the patch) for phrases that reference removed content:

```bash
# Extract all + lines from the patch, grep for forward references
grep -E '^\+' patch.diff | grep -iE 'see .*section|see .*below|see .*\bskill\b|see .*\bdoc\b|forbid|mandatory|required|never'
# For each hit, verify the referenced section still exists in the new file.
```

**Real failure mode (this session):** new `sidekick/SKILL.md:107` and `commands/sidekick.md:441` both said "mid-task switching is forbidden below" — but the patch removed the section that originally forbade it. Doc promised a rule, didn't deliver.

## The "overclaim fix" pitfall (Reviewer A's most common find)

Patch descriptions like:
- "fix overclaim about <feature>"
- "remove inaccurate claim that <X> does <Y>"
- "correct attribution to <source>"

…require EXTRA scrutiny, not less. The author has already convinced themselves the claim is wrong, so they're working backwards to justify the rewrite.

**Verification recipe:**

```bash
# 1. Fetch the cited source (the thing the patch is correcting attribution TO)
curl -fsS "<source URL>" -o /tmp/source.html
# 2. Search for the exact phrases the patch is denying
python3 -c "
src = open('/tmp/source.html').read()
phrases = [
    'dynamic mid-session routing',  # the phrase the patch claims DOESN'T exist
    'cross-model cache',             # the phrase the patch claims DOESN'T exist
    # ... every feature the patch is disclaiming
]
for p in phrases:
    i = src.find(p)
    print(f'{p!r}:', 'HIT @', i if i>=0 else 'MISS')
"
```

**Common failure:** patch removes an accurate paraphrase and replaces it with an inaccurate strawman that denies real source features. The OLD text was right; the NEW text is wrong.

## Worked-example classification (this session)

The `sidekick-swarm-trim-20260715-143103.patch` removed -321/+198 = ~123 net lines across 3 files. Reviewer B's classification:

| Removed item | Bucket | Action |
|---|---|---|
| `PR #8292` retro cite + 23:42Z/23:56Z timestamps | Flavor (with load-bearing-lite subcase) | Safe to remove. Rule survives. The PR# is useful for re-discovery but not source-of-truth. |
| `rev-ewnuu` bead example in swarm/SKILL.md | Flavor (with load-bearing-lite subcase) | Safe to remove. Pattern survives in the bullet. `br show <mission>` reproduces the lookup. |
| Phase-shape agent counts ("42 agents, 7/10 confirmed") | Flavor | Safe to remove. Phase names + shape description are what agents pattern-match on; counts are vanity metrics. |
| Hard-rule 1 incident anecdote ("428 MiniMax-M3 / 367 claude-fable-5") | Flavor | Safe to remove. The rule + the "grep -n agent(" verification recipe survive. |
| Hard-rule 12 5-item defect checklist (data corruption / guard / timestamps / causation / test contract) | **Load-bearing example** | **Should restore** — the rule rhetorically survives but loses its "what to hunt for" actionability. |
| YAML frontmatter description in swarm ("2026-07 fable swarms") | Flavor | Safe to remove. |
| 5-minute checkpoint cadence + commit-safety rules | Safeguard (kept verbatim, merged into shorter paragraph) | Safe. The rule + the escape hatch (isolated `.tmp/<mission>-state-repo/`, WIP-branch `-- <state paths>`, `-f` for gitignored) all survive. |
| `Migration (either direction), single-writer` NEW bullet | **Snuck-in content** | **Reject — separate PR.** Originally in old commands/sidekick.md bullets 237–241, so it's a tightening not a true invention, but lifting it into a "trim" PR is questionable scope discipline. |

| Added item | Bucket | Action |
|---|---|---|
| "Pattern origin: Devin Fusion ... NOT its dynamic model routing / cross-model cache preservation" | **Strawman / invented-feature disclaimer** | **Reject.** Fusion's two headline techniques ARE dynamic mid-session routing + cache-preserving model switches. The OLD framing was the accurate paraphrase. |
| "mid-task switching is forbidden below" in sidekick/SKILL.md:107 + commands/sidekick.md:441 | **Orphan reference** | **Reject.** No surviving section actually forbids it. |
| Merged DEFAULT MODE + Team visibility sections | Flavor + redundancy | Defensible — the same point was made twice. |

## Aggregation: synthesis output

For a patch review, the synthesis MUST answer all four questions:

1. **Should this patch apply?** (yes / no / only with corrections)
2. **What state change does it make?** (file list + line delta + on-disk restoration if needed)
3. **What is correct?** (the safe parts — renames, length cuts, redundancy merges)
4. **What is wrong?** (the unsafe parts — overclaims, orphan refs, snuck-in content)

If the verdict is "no", say what evidence would change it (e.g. "user provides a known-good sidekick file" or "patch is regenerated against the post-Jul 11 directive version").

## Reproducibility checklist (for future patch reviews)

1. Download patch from source (Slack attachment, GH PR, paste). If MCP is down, use Path B curl with xoxp user token per `slack-cross-workspace-fallback-xoxp`.
2. Build the patch-review artifact (DECISION + ARTIFACT ≤150 lines + the 5-bucket classification table for the patch's `-` lines).
3. Phase -0: state-corruption pre-flight (md5/size/mtime of every file in the patch).
4. Fan out 3 reviewers (A: source-accuracy + the overclaim pitfall; B: 5-bucket classification; C: orphan refs + adversarial).
5. Synthesize with the 4-question shape above.
6. If verdict is "no": do NOT apply. Surface the path-choice question to the user.

## Cross-reference

- `advice` SKILL.md → "Patch review (trim / refactor / rename)" template variant (the entry point)
- `slack-cross-workspace-fallback-xoxp` SOUL.md COMMIT (Path B pattern when MCP-Slack is down)
- `research-integrity.mdc` (.cursor/rules/) — "proving presence needs only one hit, proving absence requires exhausting sources" (applies to the overclaim-pitfall verification)
