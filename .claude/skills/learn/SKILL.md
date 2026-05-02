---
name: learn
description: Capture durable learnings from failures, corrections, repeated mistakes, successful recovery patterns, or direct /learn requests. Use whenever the user invokes /learn, asks to save/remember/capture a lesson, or when a workflow failure should become reusable process knowledge. Always persist to Claude memory, optional mem0, ~/roadmap, beads, and wiki-ingest.
---

# Learn

Use this skill to turn a concrete lesson into durable, discoverable artifacts. Do
not stop at a chat summary. A complete learning capture writes the file-backed
records that future agents and reviewers will actually find.

## Required outputs

Every confirmed learning must produce or update all of these:

1. Claude auto-memory under `~/.claude/projects/<project-key>/memory/`.
2. Optional mem0 save when the configured helper and API key are available.
3. Monthly roadmap log at `~/roadmap/learnings-YYYY-MM.md`.
4. A closed or referenced bead in `.beads/issues.jsonl` when the current repo has beads.
5. LLM wiki ingest under `~/llm_wiki`: raw source copy, source page, index entry, log entry, and relevant concept/entity updates.

If a persistence target is unavailable, report the exact blocker and continue
with the remaining targets. Do not silently skip wiki ingest.

## Workflow

### 1. Extract the learning

- If the user supplied a lesson, use it as the source.
- If the user invoked `/learn` without specifics, inspect the recent
  conversation and extract the most actionable failure, correction, or pattern.
- Classify it as `Critical`, `Mandatory`, `Best Practice`, or `Anti-Pattern`.
- Prefer precise references: PR URLs, commit SHAs, file paths, commands, error
  strings, artifacts, and verification results.
- Search existing local records before writing:
  - `~/.claude/projects/**/memory`
  - `~/roadmap/learnings-*.md`
  - `.beads/issues.jsonl`
  - `~/llm_wiki/wiki/index.md` and relevant `concepts/` pages

### 2. Write Claude auto-memory

Use the current git root to derive the project memory path:

```text
project_key = git_root.replace("/", "-")
memory_dir = ~/.claude/projects/<project_key>/memory/
```

Create or update:

- `<type>_YYYY-MM-DD_<slug>.md`
- `MEMORY.md`

The memory file must include frontmatter:

```yaml
---
name: <learning title>
description: <one-line summary>
type: feedback|project|reference
bead: <bead id or none>
---
```

The body must include context, technical detail, solution or rule, verification,
references, and a reusable pattern.

### 3. Save to mem0 when available

Save a concise text record only when a configured helper and required API key are
available. Prefer the repo-local helper when present:

- `$(git rev-parse --show-toplevel)/.claude/hooks/mem0_save.py` with
  `OPENAI_API_KEY`
- otherwise any user-configured helper already documented in the active command
  or policy

If unavailable, report `mem0 unavailable` with the missing dependency. This is
non-blocking.

### 4. Append `~/roadmap` learning log

Append to `~/roadmap/learnings-YYYY-MM.md`:

```markdown
## YYYY-MM-DD - <learning title>

- **Type**: feedback|project|reference
- **Classification**: Critical|Mandatory|Best Practice|Anti-Pattern
- **Summary**: <one-line summary>
- **Bead**: <bead id or none>
- **Files**: <paths created or updated>
- **References**: <PRs, commits, artifact links, commands>
```

### 5. Create or reference a bead

If `.beads/issues.jsonl` exists:

- Reuse a matching learning bead when one already exists.
- Otherwise create a closed task bead with labels including `learning` and
  `documentation`.
- Use the repository's normal bead id prefix when possible. In worldarchitect.ai,
  prefer `br create ... --type task --priority 3` or the existing `rev-` prefix
  rather than inventing a `bd-` id.
- Record the bead id in the Claude memory frontmatter and roadmap entry.

If beads are unavailable, write `none` and report why.

### 6. Always wiki-ingest

Wiki ingest is mandatory for `/learn`.

Use the Claude memory file or roadmap entry as the source document. Follow the
`wiki-ingest` workflow:

1. Copy the source to `~/llm_wiki/raw/<basename>`.
2. Create `~/llm_wiki/wiki/sources/<slug>.md`.
3. Add the source to `~/llm_wiki/wiki/index.md` under `## Sources`.
4. Append `~/llm_wiki/wiki/log.md` with `## [YYYY-MM-DD] ingest | <title>`.
5. Update existing concept/entity pages when a relevant page already exists.
   Create a new concept/entity page only when the learning introduces a reusable
   concept that is not already represented.
6. State whether the learning affects `[[jeffrey-oracle]]`; most technical
   workflow learnings do not.

Do not skip wiki ingest because the learning seems "not wiki-bearing"; the
learning itself is the source.

### 7. Validate and report

Before reporting complete:

- Verify files exist for each persistence target that was available.
- Validate `.beads/issues.jsonl` parses when modified.
- Check duplicate bead ids when a bead was created manually.
- Run a whitespace check for repo changes when applicable.

Final report must name the created/updated paths and any skipped persistence
target with its reason.
