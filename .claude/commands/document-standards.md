---
description: "Review or revise prose documents (roadmap docs, reports, status docs, handoffs, Google Docs, HTML) for truth, economy, readability, structure, and output correctness, optimized for human reading. Adapts /code-standards' five-lane pattern to documents; runs ponytail economy and a thermo-style document audit as real lanes."
type: quality
execution_mode: immediate
---

# /document-standards [target]

> `/document-standards` is **authoritative for the five universal document
> lanes**. A repo-local addendum may add lanes and product rules; it cannot
> subtract.

Read `~/.claude/skills/document-standards/SKILL.md` and execute the full
five-lane workflow against `<target>` — a doc path, Google Doc URL, HTML file,
or prose diff — or the doc most recently touched in this session if no target
is given.

The economy and audit lanes are **real lanes**: economy runs the
deletion-first, say-it-once ponytail ladder, and the audit lane applies the
thermo-style document rubric in the SKILL.md — adapted from the thermo-nuclear
code-quality review the same way `/code-standards` invokes `thermo` — in full,
never a from-memory paraphrase.

## Quick reference

| Lane | Source | How it runs |
|---|---|---|
| Truth & contract | Claims verified against sources; durable-state writing; no orphaned status labels | inline |
| Economy (ponytail) | Ponytail — deletion-first, say it once | inline |
| Readability & structure | BLUF, zero-context reader, heading/table discipline | inline |
| Thermo-style doc audit | rubric in SKILL.md, adapted from thermo-nuclear code-quality review | real audit pass |
| Output & operability | Markdown/HTML/gdoc surface rules; edit-in-place; formatting invariants (clickable URLs, ~/ paths) | inline |

## Flags

- `smoke-test` — load-only check; reports command/skill paths, the rubric
  lane, and the revision marker without running lanes or editing files.

## Examples

```
/document-standards
/document-standards ./docs/status-report.md
/document-standards https://docs.google.com/document/d/<id>/edit
/document-standards smoke-test
```

Revision marker: `DOCUMENT_STANDARDS_COMMAND_V1`
