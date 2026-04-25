---
name: nextsteps
description: Situational assessment, beads + roadmap sync after a work block; saves findings to roadmap, Claude auto-memory, mem0, and beads.
---

# /nextsteps — Situational Assessment & Roadmap Update

## When invoked

### Phase 1 — Gather context (parallel)
- `git log --oneline -10`
- `bd list --status open` (or `br list` if project uses br)
- `ls roadmap/`
- Use any user-provided line after `/nextsteps` as extra context.

### Phase 2 — Assess
- Match recent commits to open beads; close or update status.
- Note gaps → new beads.
- Update `roadmap/README.md` **Recent activity (rolling)** section with date + bullets (create section if absent).
- Identify learnings from the session worth persisting.

### Phase 3 — Execute (parallel where possible)
For each finding, run Phases 4–7 below.

### Phase 4 — Write to Claude auto-memory

For each learning/finding:

1. Determine type: `feedback` (rules, anti-patterns) | `project` (decisions, state) | `reference` (pointers)
2. Slug: lowercase, underscored, max 40 chars
3. Derive memory dir from git root and **ensure it exists**:
   ```bash
   git_root=$(git rev-parse --show-toplevel)
   project_key="${git_root//\//-}"
   memory_dir="$HOME/.claude/projects/${project_key}/memory"
   mkdir -p "$memory_dir"
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
5. Append pointer to `MEMORY.md`: `- [Title](filename) — one-liner`
6. Report: `✅ Claude auto-memory: {filename}`

### Phase 5 — Save to mem0

1. Check: skip if `~/.openclaw/.claude/hooks/mem0_save.py` absent or `GROQ_API_KEY` unset
2. Build text: `"{title}: {one_liner}. {body_1_sentence}"`
3. Run:
   ```bash
   echo '{"memory": "<text>", "user_id": "jleechan"}' \
     | python3 ~/.openclaw/.claude/hooks/mem0_save.py
   ```
4. Report: `✅ mem0 saved` or `⚠️ mem0 unavailable (skipped)`

### Phase 6 — Append to ~/roadmap learnings log

1. **Ensure the directory exists** (agents must not assume it is already there):
   ```bash
   mkdir -p "$HOME/roadmap"
   ```
2. File: `$HOME/roadmap/learnings-<YYYY-MM>.md` — create the file if absent, then append the entry.

Entry format:
```markdown
## <YYYY-MM-DD> — <title>
- **Type**: feedback|project|reference
- **Classification**: 🚨|⚠️|✅|❌
- **Summary**: <one-liner>
- **Bead**: <bd-id or none>
- **Files**: <paths changed if any>
```

Report: `✅ ~/roadmap/learnings-<YYYY-MM>.md updated`

### Phase 7 — Create or reference beads

For each gap/finding that warrants tracking:

1. Check if bead exists:
   ```bash
   python3 -c "
   import json
   beads = [json.loads(l) for l in open('.beads/issues.jsonl') if l.strip()]
   matches = [b for b in beads if '<keyword>' in b.get('title','').lower()]
   for m in matches[:3]: print(m['id'], m['title'])
   " 2>/dev/null
   ```
2. If no match, create:
   ```python
   import json, datetime, random, string
   bid = 'bd-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
   bead = {
     "id": bid, "title": "<title>", "status": "open",
     "description": "<one_liner>", "priority": 2,
     "issue_type": "task", "labels": ["evidence", "enforcement"],
     "created_at": datetime.datetime.utcnow().isoformat() + "Z",
     "updated_at": datetime.datetime.utcnow().isoformat() + "Z",
     "created_by": "jleechan", "source_repo": "."
   }
   with open('.beads/issues.jsonl', 'a') as f:
       f.write(json.dumps(bead) + '\n')
   print(bid)
   ```
3. Report: `✅ bead <bd-id> created/referenced`

### Phase 8 — Report

List all: beads updated/created, roadmap docs touched, memory files written, mem0 status, recommended next actions.
