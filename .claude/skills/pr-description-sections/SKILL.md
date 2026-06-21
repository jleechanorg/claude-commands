---
name: pr-description-sections
description: "Use when writing PR descriptions. Enforces 6 sections in order: Background, Goals, Tenets, High-level description, Testing, Low-level details."
---

# PR description — required sections (canonical)


The PR description must use the following sections, in this order:

1. **Background** — context, problem, link to the driving issue/bead.
2. **Goals** — concrete outcomes this PR delivers (bullet list).
3. **Tenets** — the rules/principles/constraints this PR respects or introduces; flag any new tenets explicitly.
4. **High-level description of changes** — file/path-level summary grouped by area (backend, frontend, tests, docs).
5. **Testing** — what was tested, what was not tested, and the evidence path (commands, logs, screenshots, video).
6. **Low-level details** — non-obvious decisions, schema/prompt deltas, gotchas, follow-ups.

This is the source of truth for the `your-project.com` `.github/pull_request_template.md` and any new agent-led PR. The Skeptic Gate reads the PR description as the canonical review context; consistency with this section list is required.

**Design-doc gate (CI):** the `design-doc-gate.yml` Gate 0 regex accepts `## Design Decision`, `## Governing Design Doc & Tracking`, **or** `## Tenets` as the design-doc/artifact-link header. If you rename or restructure that header in the future, update the regex in the same PR — otherwise production PRs >50 lines will fail CI even when the design-doc and bead links are present under the new name.
