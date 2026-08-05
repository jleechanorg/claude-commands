---
name: document-standards
description: Project-agnostic review or revision of prose documents (roadmap docs, reports, status docs, handoffs, Google Docs, HTML) for truth, economy, readability, structure, and output correctness — optimized for human reading. Adapts /code-standards' five-lane pattern to documents. Dispatched by the /document-standards command.
---

# Document Standards Dispatch

Reviews or revises prose documents using five independent lanes. This skill is
the source of truth; `~/.claude/commands/document-standards.md` is a thin
dispatcher. Every standard here is evidence-driven, traced to observed
doc-revision patterns or to a named source skill.

## Supporting skills

The inline rubric in each lane below is load-bearing on its own — the skill
runs without any of these. They are optional companions that run the lane as a
real, full pass when installed; substitute an equivalent if you have one.

| Skill | Use |
|-------|-----|
| Ponytail | Economy lane — deletion-first ladder, adapted to prose |
| Thermo-nuclear code quality | Pattern source for the doc-audit rubric in lane 4 |
| Writer | Prose-level AI-tell, voice, and rhythm rules (optional polish pass) |
| gdocs-access | Google Docs tool order and edit-in-place rules |
| pr-description | Durable-state writing, zero-context reader, section order |

## Universal lanes

1. **Truth & contract** — every claim in the doc matches its source.
   - Every number traces to a named artifact, query, or commit from which it
     can be re-derived. A number that cannot be re-derived is withdrawn, not
     softened.
   - A present-tense claim about external state (code semantics, deploy status,
     ownership) is verified at the exact current SHA/state, never inferred
     from a commit message or an earlier correction.
   - The doc describes the durable current state. Investigation chronology,
     superseded drafts, and review-response history move to a clearly-labeled
     historical appendix or are deleted (pr-description's "write for the state
     right after the work lands").
   - No orphaned status labels: a PENDING/WIP/TBD/provisional marker either
     resolves before delivery or is a deliberate, dated disclosure — never a
     stale sentence.
   - No fabricated status, no "verified" without evidence, per the global
     no-fabricated-status rule.
2. **Economy (ponytail for prose)** — deletion before addition, say it once.
   - The prose ladder: does this section/sentence need to exist at all → does
     another section already say it (merge, link, don't restate) → can it be
     one line → only then write the minimum (ponytail rungs 1–7 mapped to
     prose).
   - Each fact has one canonical home; other sections link to it. Boilerplate
     restated per-section is a defect.
   - A revision pass reports what it deleted. If the doc grew, name what was
     removed to compensate or justify the growth in one line.
   - Any audit must emit a "cut candidates" list, not only additions.
3. **Readability & structure** — human-first, scannable, BLUF.
   - The first screen answers what this is, what the outcome is, and what the
     reader does next, without scrolling ("audience is someone with zero
     context and top level exec summary").
   - Zero-context test: every proper noun, ticket ID, or prior doc referenced
     is linked or one-line glossed. Long docs get a table of contents.
   - Heading hierarchy is consistent; tables carry dense parallel data, prose
     carries narrative — not the reverse. Dense is the goal; bloated is the
     defect.
   - One voice, one tense (present for current state). For polish, the
     `writer` skill's AI-tell lexicon and rhythm rules apply as an optional
     pass — they are prose-level, so this lane cites them rather than
     re-running them.
4. **Thermo-style document audit** — the strict structural pass, adapted from
   the thermo rubric (the code-standards lane-4 analog). The rubric below is
   the load-bearing content; run it in full, never a from-memory summary. This
   lane runs as a **real audit pass**: apply every question below to the
   document and return findings, not vibes.
   - Is there a "doc judo" move — a restructuring that deletes whole sections
     by reframing (e.g. one appendix absorbing three scattered caveat
     paragraphs)?
   - Did the doc cross a healthy size boundary for its genre? (A status doc
     that doubled without a scope change is a smell, like thermo's 1k-line
     rule.)
   - Are there scattered special-case caveats bolted onto unrelated sections —
     the prose spaghetti analog — that belong in one disclosures appendix?
   - Does every section earn its keep, or is some a thin wrapper restating the
     exec summary?
   - Would a zero-context fresh reader reconstruct the doc's claims and find
     every referenced artifact? Run that read; content-addressed placement
     beats filename-addressed.
   - Flag aggressively: sections that move complexity around without deleting
     it, chronology masquerading as structure, duplicate tables with drifted
     numbers, "temporary" framing likely to become permanent.
   - Output: few high-conviction structural findings, prioritized — never a
     flood of cosmetic nits (thermo's output-expectations rule).
5. **Output & operability** — the doc must work in its target surface.
   - **Link everything linkable.** Every reference to an artifact that has a
     URL appears as a clickable link on first mention in each section: pull
     requests / issues / commits / files / gists, Google Docs / Sheets /
     Slides, tickets, dashboards, wiki pages, monitoring boards. A bare
     ticket number, repo name, or "the strategy doc" is a defect — a reader
     must never have to search for a source the author already had. Construct
     them: `https://<git-host>/<owner>/<repo>/pull/<N>` (also `/issues/<N>`,
     `/commit/<sha>`, `/blob/main/<path>`), ticket
     `https://<tracker-host>/browse/<KEY>`, gdoc
     `https://docs.google.com/document/d/<id>`. When a referenced thing has no
     URL, say so inline ("no tracking issue exists") rather than leaving a bare
     identifier — the absence is itself information. Cross-surface docs link
     *to each other* both ways, so neither is a dead end.
   - Formatting invariants: times in the reader's local timezone (never UTC
     unless the audience is global); paths `~/`-relative (never literal home
     directories); effort as delta LOC/files/PRs, never calendar time.
   - Surface-render check: before delivery, open the doc in its target surface
     (rendered Markdown, HTML, or Google Doc) and check for escaping artifacts
     (literal `\n`, vertical tabs, eaten line-continuations), broken tables,
     and unclickable links.
   - Markdown: standard GFM; no HTML unless the renderer is known to accept it.
   - HTML: self-contained (inline CSS/JS), no external fetches, opens from
     `file://`.
   - Google Docs: **edit in place, never a parallel doc.** Before creating
     a new doc, check for an existing one on the topic. Use your Google Docs
     integration's in-place edit tools (section update, text replace, append,
     insert). Structural in-place edits (delete-to-header + heading rewrite +
     table row ops) are a known damage class — a *verified damaged* doc may
     be regenerated fresh with the old one bannered SUPERSEDED, never silently
     abandoned. After any gdoc edit, export to Markdown and diff-check the
     sections you did not intend to touch; remember `<pre>` newlines can
     export as vertical tabs (`\x0b`) and trailing backslash
     line-continuations can be eaten.
   - Multi-surface sync: when the doc exists in N surfaces (local md, gdoc,
     repo mirror), name all N; a revision lands on all of them in the same
     work block or carries an explicit "surfaces pending" note. "Updated"
     means pushed and URL-verifiable.

## Workflow

When invoked as `/document-standards <target>`:

1. **Define the target**: a doc path, a gdoc URL, an HTML file, or a prose
   diff. If none given, use the doc most recently touched in the session.
2. **Identify the genre and audience** (status doc, exec report, handoff,
   design doc, gdoc) — the audit tunes to it (BLUF depth, appendix policy).
3. **Read the whole doc** (or the relevant sections plus their neighbors).
   Read linked sources for any claim being checked in lane 1.
4. **Load ponytail** before revising — deletion-first prevents additive bloat.
5. **Run the five lanes.** Each returns PASS with section/line evidence, or
   FAIL with the exact location and required fix; N/A only with a reason.
   Lane 4 must cite findings from actually applying the rubric above.
6. **Reconcile** into the report format below. For revision (not just review)
   requests, apply fixes per the smallest-edit philosophy: targeted Edits,
   never a `Write` over a multi-section doc.

## Report format

| Lane | Verdict | Evidence (section/line) | Required fix |
|---|---|---|---|
| Truth & contract | PASS/FAIL/N-A | | |
| Economy (ponytail) | PASS/FAIL/N-A | | |
| Readability & structure | PASS/FAIL/N-A | | |
| Thermo-style doc audit | PASS/FAIL/N-A | | |
| Output & operability | PASS/FAIL/N-A | | |

State that the thermo-style rubric ran in full (lane 4). Append a **Cut
candidates** list (economy lane's required output) and, for multi-surface docs,
a **Surface sync status** note.

## Smoke-test mode

If the argument contains `smoke-test`, do not run lanes and do not edit files.
Report:

- that the command file loaded,
- the command file path (`~/.claude/commands/document-standards.md`),
- this skill file path (`~/.claude/skills/document-standards/SKILL.md`),
- the ponytail skill (economy lane source, if installed),
- the rubric lane this command runs (thermo-style doc audit),
- the marker for this revision: `DOCUMENT_STANDARDS_COMMAND_V1`.

## Relationship to /code-standards

`/code-standards` reviews code, diffs, and PRs; `/document-standards` reviews
prose. When a PR changes both, run both commands against their respective
surfaces. Neither replaces the other.
