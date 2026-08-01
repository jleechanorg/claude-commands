# 4-PART master-doc stitch template

Copy-paste-ready template for the header + TOC + provenance footer. The middle is filled by the source file contents (with their leading `# Title` lines replaced by `# PART N — <Subtitle>`).

## Header (paste at top)

```markdown
# <Campaign Name> — <One-Line Pitch> (<Subtitle>)

*Last updated: <YYYY-MM-DD>. Compiled from `<worktree-path>`.*

**Purpose:** This is the canonical, single-source-of-truth for the <Campaign Name> campaign and its underlying <mechanic framework>. It contains the campaign bible, the V1 general <mechanic> spec, the V2 general spec, and the <setting>-specific specialization — stitched together in reading order so you can review, share, and play without flipping between files.

**Source conversation:** <Gemini/Claude/other share link> (<N> design iterations culminating in the <X>-word self-contained "<Final Design Name>" campaign).

**GitHub PR (live):** <https://github.com/$GITHUB_REPOSITORY/pull/N> — `<title>` (<N> commits, <M> files, +<A>/-<B>, state=<OPEN|MERGED>, head `<branch>`).

**Setting:** <Setting>. <The original V1 is setting-specific; V2 added YYYY-MM-DD is explicitly setting-agnostic.>

---

# TABLE OF CONTENTS

1. **The Campaign Bible** — `` (<setting> specific, narrative + mechanics)
2. **<Mechanic> — General (V1)** — `` (system-agnostic baseline, <key features>)
3. **<Mechanic> — V2 General Spec** — `` (extending V1: <key features>)
4. **<Setting> V2 — <System> Specialization** — `` (<key features>)

---

```

## Part header transformation

For each source file, the leading `# Title` line gets replaced by:

```markdown
# PART N — <Subtitle>

*<One-line description of which part this is.>*
```

Then append the file body (skipping the leading `# Original Title` line).

## Section separator (between parts)

```markdown

---

```

## Footer (paste at bottom)

```markdown
---

# PROVENANCE & NEXT STEPS

- **Campaign module SHA:** `<relative/path>` @ HEAD `<40-char SHA>` ([PR #N](<url>))
- **V1 spec SHA:** `<relative/path>` @ HEAD `<40-char SHA>` ([PR #N](<url>))
- **V2 spec SHA:** `<relative/path>` @ HEAD `<40-char SHA>` ([PR #N](<url>))
- **<Setting> spec SHA:** `<relative/path>` @ HEAD `<40-char SHA>` ([PR #N](<url>))
- **<Source> source:** `<URL>` (full archive at `<local-path>`, <size>)
- **Companion PRs on world_reference:**
  - [PR #N1](<url>) (<state>): `<title>` — <one-line description>
  - [PR #N2](<url>) (<state>): `<title>` — <one-line description>
- **Companion code:** `<relative/path>`, `<relative/path>`, `<relative/path>` — <status>
- **Wiki source (sister module):** `<relative/path>` — <one-line description>

## What this Doc enables

- **Reading the whole story + mechanic without leaving the browser** — share with collaborators
- **Cross-reference anchor** for the world_reference/ markdown files in [PR #N](<url>)
- **Provenance artifact** for the iterative design that started with <source1> → merged <source2> → V2 overlay
- **Future iteration input** — when you say "iterate on <campaign>," this Doc is the canonical state anchor

## Recommended next iterations (after [PR #N](<url>) merges)

1. **Update <source> V<n+1> continuation** — ask <source> to read this Doc and design V<n+1>
2. **Add a wiki source page** at `<wiki-source-path>` (Karpathy frontmatter, audit-checked)
3. **Run `wa-campaign-content-analysis`** to score this Doc against the campaign-template benchmark
4. **`/superlight` pass** to rewrite the Doc with the user's standing character-personality template formatting
5. **Ingest into Firestore** — extract `<canonical_description.txt>` for `create_campaign_unified` after constants wiring

---

*This Doc is the canonical state anchor for the <Campaign Name> campaign as of <YYYY-MM-DD>. All <N> source files are live on <branch> or [PR #N](<url>).*
```

## Stitch algorithm (Python pseudocode)

```python
import os

files = {
    'campaign': '/path/to/worktree/world_reference/campaign_module_X.md',
    'general_v1': '/path/to/worktree/world_reference/X_general.md',
    'general_v2': '/path/to/worktree/world_reference/X-v2-general.md',
    'specialization': '/path/to/worktree/world_reference/X-v2-Y.md',
}
contents = {k: open(v).read() for k, v in files.items()}

# Replace leading # Title with # PART N — <Subtitle>
contents['campaign'] = contents['campaign'].replace(
    '# Original Title',
    '# PART 1 — The Campaign Bible (<setting> specific)\n\n*<description>. Part 1 of 4.*',
    1
)
# ... repeat for each file

combined = (
    header +
    contents['campaign'] +
    '\n\n---\n\n# ' + contents['general_v1'].lstrip('#').strip().lstrip() +
    '\n\n---\n\n# ' + contents['general_v2'].lstrip('#').strip().lstrip() +
    '\n\n---\n\n# ' + contents['specialization'].lstrip('#').strip().lstrip() +
    footer
)

with open('/tmp/X_master_doc.md', 'w') as f:
    f.write(combined)
```

Verified pattern from 2026-07-21 God of Murder run: produces ~104 KB / 1,479 lines / ~16K words doc that uploads cleanly in one `gog docs write` call.

## Worked example (God of Murder, 2026-07-21)

| Part | File | Subtitle | Lines | Words |
|------|------|----------|-------|-------|
| 1 | `campaign_module_god_of_murder.md` | The Campaign Bible (BG3 / Faerûn Specific) | 674 | ~9,300 |
| 2 | `god_mechanics_general.md` | God Mechanics — General Spec (V1, System-Agnostic) | 357 | ~3,400 |
| 3 | `god-mechanics-v2-general.md` | God Mechanics — V2 General Spec (System-Agnostic, V2 Overlay) | 182 | ~1,200 |
| 4 | `nocturne-v2-god-mechanics-design.md` | Nocturne V2 — D&D 5e Faerûn Specialization | 232 | ~1,600 |
| **Total** | | | **1,479** | **~16,000** |

Doc ID produced: `1QzhBAzV19S-pptssylgUpbrl7_DK0mAf2LzZHVnsK2U`
PR linked: [#8488](https://github.com/$GITHUB_REPOSITORY/pull/8488)
