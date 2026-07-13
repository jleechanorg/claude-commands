---
name: nextsteps
description: Situational assessment, beads + roadmap sync after a work block; writes a self-contained nextsteps markdown doc (TOC, executive summary, full detail, bead links), updates learnings + README, Claude auto-memory, mem0, and beads. Prefers editing existing roadmap docs over creating new files.
---

# /nextsteps — Situational Assessment & Roadmap Update

Situational assessment and roadmap sync after a work block.

## Fail-closed rule

A `/nextsteps` run is **incomplete** unless it leaves **all** of these artifacts:

1. **Independent summary markdown doc** (see [Nextsteps document](#nextsteps-document-mandatory)) — TOC, executive summary, then full self-contained detail; bead links throughout  
2. Beads updated/created via `br`  
3. Claude memory files written with `MEMORY.md` pointers  
4. `~/roadmap/learnings-YYYY-MM.md` appended  
5. **`roadmap/activity/YYYY-MM-DD.md`** appended with session bullet (repo git root — create file if absent). If that date is brand-new, prepend one date link to `roadmap/README.md`'s `## Recent activity (by day)` section.

If the session has no repo checkout, skip item 5 only and note that in the Phase 8 report.

### Continuous completion contract

A normal `/nextsteps` invocation authorizes **both stages** below. Complete Stage 1 and Stage 2 in the same run before yielding a final response.

- Do not pause for approval, ask whether to proceed, or stop at the stage boundary.
- Parallelize independent work when slots are available. If parallel capacity is unavailable, continue locally or sequentially; lack of a subagent slot is never a reason to stop.
- Interim user updates are non-blocking status messages, not approval checkpoints.
- If mem0, GitHub Issues, or another optional sink is unavailable, record the exact attempted result, complete every other artifact, and report the unavailable sink in the final checklist.
- Stop only for a genuine blocker that requires new authority or information and cannot be safely worked around. Routine external failures, disabled integrations, or partial tool availability are not stopping conditions.

## Doc discovery — prefer update over create

Before writing the independent summary or touching roadmap files:

1. **Search for existing nextsteps / session / sync docs** (in order):
   - Repo: `roadmap/nextsteps*.md`, `roadmap/NEXT-STEPS.md`, `roadmap/session-*.md`, `docs/nextsteps*.md` (if present)
   - Home: `~/roadmap/nextsteps-latest.md`, `~/roadmap/nextsteps-*.md`
2. **Prefer:** append a new **dated section** to an existing rolling file (e.g. `nextsteps-latest.md` or the newest `nextsteps-YYYY-MM-DD.md` in the same month), or add a subsection under an existing “Work queue” / “Next steps” heading.
3. **Create new file only when** no suitable file exists. Default **new** path: `~/roadmap/nextsteps-<YYYY-MM-DD>.md` (or `roadmap/nextsteps-<YYYY-MM-DD>.md` if the repo standard is to keep session docs in-repo — match sibling files if any).
4. **Activity log:** append the session bullet to **`roadmap/activity/YYYY-MM-DD.md`** (create file with `# Activity — YYYY-MM-DD` header if absent). If this is the first entry for that date, prepend a `- [YYYY-MM-DD](activity/YYYY-MM-DD.md)` line to the `## Recent activity (by day)` list in `roadmap/README.md`. Do not prepend to README for subsequent entries on the same date — only the per-day file changes. This keeps README conflict-free across concurrent PRs.

## Nextsteps document (mandatory)

The independent `.md` file is the **handoff artifact**: a reader must be able to execute the queue without opening beads or chat.

**Document order (fixed):**

1. **Title line** — e.g. `# Nextsteps — <topic or repo> — <YYYY-MM-DD>`
2. **Table of contents** — Markdown list linking to **every** following `##` section (Executive summary through Roadmap pointer). Use GitHub-style anchors (lowercase, hyphenated, dedupe if titles repeat). Update whenever headings change.
3. **Executive summary** — Short, skimmable block (bullets OK): what this block accomplished, what is blocked or at risk, top priorities / sequencing, beads and PRs that matter (**ids with links**). No deep procedural detail — that lives in the sections below.
4. **Full detail (all following `##` sections)** — Each section is **self-contained** (definitions, file paths, acceptance criteria, dependencies). Do not rely on “see chat” or unstated context. Order: Context → Bead index → Work queue → PR / merge state → Learnings pointer → Roadmap pointer.

**Required `##` sections after Executive summary (skip only if genuinely N/A — one line stating why):**

| Section | Content |
|--------|---------|
| **Context** | 2–6 sentences: what block just ended, repo(s), branch/PR if relevant, scope boundaries |
| **Bead index** | Table: `bd-…` id, title, priority/status if known, **link** — every open bead touched or created this run. Prefer `https://github.com/<owner>/<repo>/issues/<n>` when the bead syncs to GitHub Issues; else `br show <id>` as fallback. Link the id in every row. |
| **Work queue** | Numbered tasks; each task **self-contained**: goal, acceptance criteria, files/areas, dependencies/blockers, suggested order; **reference beads** inline as linked `[bd-xxx](url)` where applicable |
| **PR / merge state** | Same session truth as Phase 1b (`PR #n: OPEN \| MERGED \| CLOSED`) for any PR referenced; full PR URLs |
| **Learnings pointer** | Path/link to the new `~/roadmap/learnings-YYYY-MM.md` entry for this date; one-line summary of what was logged |
| **Roadmap pointer** | Confirm `roadmap/activity/YYYY-MM-DD.md` appended (and README date link added if new date) |

**Link rules**

- **Beads:** linked in **Bead index**, and again **inline** in Work queue items where a task maps to a bead.
- **PRs/issues:** full `https://github.com/owner/repo/pull/n` (or `/issues/n`) when known.
- **Internal:** link from TOC entries to each `##` section anchor.

**Example skeleton**

```markdown
# Nextsteps — <repo> — 2026-04-19

## Table of contents

- [Executive summary](#executive-summary)
- [Context](#context)
- [Bead index](#bead-index)
- [Work queue](#work-queue)
- [PR / merge state](#pr--merge-state)
- [Learnings pointer](#learnings-pointer)
- [Roadmap pointer](#roadmap-pointer)

## Executive summary

- Outcomes: …
- Risks / blockers: …
- Next: …
- Beads: [bd-abc123](https://github.com/org/repo/issues/NN) (short label)

## Context

…

## Bead index

| Bead | Title | Link |
|------|-------|------|
| bd-… | … | [bd-…](https://github.com/org/repo/issues/NN) |

## Work queue

1. … — tracks [bd-…](https://github.com/org/repo/issues/NN)

## PR / merge state

- https://github.com/org/repo/pull/123 — OPEN

## Learnings pointer

- `~/roadmap/learnings-2026-04.md` — section `2026-04-19 — …`

## Roadmap pointer

- Appended `roadmap/activity/YYYY-MM-DD.md` — Recent activity (per-day file)
```

## When invoked — Two-Stage Continuous Execution

### Stage 1: Local Updates

#### Phase 1a — Memory Search Context (parallel subagent)
**Run as a parallel subagent** (Agent tool, subagent_type=Explore) so Phase 1b can start simultaneously:
1. Search memory files for key terms from the user-provided context after `/nextsteps`
2. Check `~/roadmap/nextsteps-*.md` for most recent session doc (target for append vs new file)
3. Check `~/roadmap/learnings-YYYY-MM.md` tail for existing entries
4. Report: existing bead IDs, open items from prior sessions, path of most recent nextsteps doc

#### Phase 1b — Gather context (parallel subagent)
**Run as a parallel subagent** (Agent tool, subagent_type=Explore) concurrently with Phase 1a:
- `git log --oneline -10`
- `br list --status open --limit 0`
- `ls roadmap/` (and `ls ~/roadmap/` for home docs)
- Run [Doc discovery](#doc-discovery--prefer-update-over-create) — note target file for the summary doc (existing vs new path)
- Use any user-provided line after `/nextsteps` as extra context.
- **PR truth (same session):** From open beads, roadmap merge stacks, and user notes, collect every distinct GitHub PR number you will reference. For each `n`, resolve the repo (default: `gh repo view --json nameWithOwner -q .nameWithOwner` from the git root; if the work spans another repo, pass that owner/name explicitly) and run:
  ```bash
  gh pr view <n> --repo <owner/repo> --json state,mergedAt,closedAt,headRefName
  ```
  Map JSON to a human line for the report and the **Nextsteps document**: **`PR #n: OPEN`** if `state` is `OPEN`; **`PR #n: MERGED`** if `mergedAt` is non-null; else **`PR #n: CLOSED`** (closed without merge). Do not recommend “land PR *n*” without this check in the **same** `/nextsteps` run.

#### Phase 2 — Assess & Update Local Assets
- Match recent commits to open beads; close or update status.
- Note gaps → determine new beads to create.
- Create or update beads using `br`:
  ```bash
  br create "<title>" --type task --priority 2
  ```
- Append session bullet to **`roadmap/activity/YYYY-MM-DD.md`** (create with header if new date). Only touch `roadmap/README.md` when the date file is brand-new (prepend one date link to `## Recent activity (by day)`).
- Identify learnings from the session worth persisting, and append them to `~/roadmap/learnings-<YYYY-MM>.md` (create if absent) using this format:
  ```markdown
  ## <YYYY-MM-DD> — <title>
  - **Type**: feedback|project|reference
  - **Classification**: 🚨|⚠️|✅|❌
  - **Summary**: <one-liner>
  - **Bead**: <bd-id or none>
  - **Files**: <paths changed if any>
  - **Nextsteps doc**: <path to independent summary md>
  ```

#### Phase 3 — Write/Update Nextsteps Document & Show to User
- Apply [Doc discovery](#doc-discovery--prefer-update-over-create).
- Write or append to the Nextsteps document: **table of contents**, **executive summary**, then **full detail** sections per [Nextsteps document (mandatory)](#nextsteps-document-mandatory).
- Record the clean table of created/updated beads, learnings, roadmap activity changes, and the Nextsteps document path for the final report.
- Continue directly to Stage 2. Do not yield a final response or request confirmation here.

---

### Stage 2: Memory & Tool Sync (Parallel When Available)

Run the remaining tasks immediately in the same invocation. Use parallel subagents when available; otherwise perform the tasks locally or sequentially and finish the stage.

#### Subagent A: Claude Auto-Memory Sync
Create a subagent (`TypeName=self` or a custom subagent) to execute the memory write for each learning/finding:
1. Determine type: `feedback` (rules, anti-patterns) | `project` (decisions, state) | `reference` (pointers)
2. Slug: lowercase, underscored, max 40 chars
3. Derive memory dir from git root:
   ```bash
   git_root=$(git rev-parse --show-toplevel)
   project_key="${git_root//\//-}"
   memory_dir="$HOME/.claude/projects/${project_key}/memory"
   ```
4. Write file `${memory_type}_${date}_${slug}.md` with frontmatter:
   ```markdown
   ---
   name: <title>
   description: <one-liner>
   type: feedback|project|reference
   bead: <bd-id or none>
   ---

   <body>

   **Why:** <reason>

   **How to apply:** <when/where this kicks in>
   ```
5. Append pointer to `MEMORY.md` (create file if missing): `- [Title](filename) — one-liner`
6. Report back: `✅ Claude auto-memory: {filename}`

#### Subagent B: mem0 Sync
Create a subagent (or run concurrently) to save to mem0:
1. Check: skip if `~/.hermes/scripts/mem0_shared_client.py` is absent.
2. Build text: `"{title}: {one_liner}. {body_1_sentence}"`
3. Run:
   ```bash
   python3 ~/.hermes/scripts/mem0_shared_client.py add "<text>" \
     --user-id $USER \
     --no-infer
   ```
4. Report back: `✅ mem0 saved` or `⚠️ mem0 unavailable (skipped)`

#### Subagent C: GitHub Issues Creation
For each bead created in Stage 1, attempt to create a linked GitHub Issue. Run all issue creates in parallel:
```bash
# Resolve repo from git remote (default jleechanorg/agent-orchestrator-ts)
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "jleechanorg/agent-orchestrator-ts")

gh issue create --repo "$REPO" \
  --title "[resilience] <bead title>" \
  --body "## Summary
<one-paragraph description>

## Acceptance criteria
- [ ] <criterion 1>
- [ ] <criterion 2>

**Bead:** <bd-id>" \
  --label "task" 2>&1
```
- If `gh issue create` returns "repository has disabled issues", log `⚠️ GH Issues disabled on <repo> — bead only` and continue.
- If it succeeds, capture the issue URL and add it to the bead index in the Nextsteps document.
- Report back: `✅ GH Issue #N created` or `⚠️ GH Issues disabled`

#### Phase 8 — Report completion
Once the subagents complete, summarize the results and print the final artifact checklist:
- `[x]` **Nextsteps independent `.md`**
- `[x]` Beads (`br`) written
- `[x]` Claude memory + `MEMORY.md` pointers written
- `[x]` mem0 sync succeeded or exact unavailable result recorded
- `[x]` GitHub Issue sync succeeded, was already linked, or exact disabled/unavailable result recorded
- `[x]` `~/roadmap/learnings-YYYY-MM.md` updated
- `[x]` `roadmap/activity/YYYY-MM-DD.md` (or `roadmap/README.md`) updated

**Merge-order sanity:** If any recommended action was “merge **A** before **B**” (or “land A then rebase B”), re-assert **A** using the Phase 1 `gh pr view` results from **this** run. If **A** is **MERGED**, do **not** tell the reader to land A; say instead to **rebase B on `main`** (or the appropriate default branch). If **A** is still **OPEN**, keep the ordering advice. If **A** is **CLOSED** without merge, drop merge-order advice and flag that the stack needs re-triage.
