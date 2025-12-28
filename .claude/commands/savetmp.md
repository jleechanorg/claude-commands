---
description: Save evidence to /tmp structure
type: llm-orchestration
execution_mode: immediate
---
## EXECUTION INSTRUCTIONS

Execute `.claude/commands/savetmp.py` to archive evidence following `.claude/skills/evidence-standards.md`.

**Features:**
- SHA256 checksums for all evidence files (evidence integrity)
- Git provenance capture (HEAD commit, origin/main, changed files)
- Parallel git command execution for speed
- Structured `/tmp/<repo>/<branch>/<work>/<timestamp>/` layout

## Quick Usage

```bash
python .claude/commands/savetmp.py "<work_name>" \
  --methodology "<testing approach>" \
  --evidence "<results summary>" \
  --notes "<follow-up notes>" \
  --artifact <path/to/file-or-directory>
```

## Flags

| Flag | Purpose |
| ---- | ------- |
| `--methodology` / `--methodology-file` | Testing methodology |
| `--evidence` / `--evidence-file` | Evidence summary |
| `--notes` / `--notes-file` | Additional notes |
| `--artifact` | Copy file/dir to artifacts/ (repeatable) |
| `--skip-git` | Skip git commands for faster execution |

## Output Structure

```
/tmp/<repo>/<branch>/<work>/<timestamp>/
├── methodology.md + .sha256
├── evidence.md + .sha256
├── notes.md + .sha256
├── metadata.json + .sha256   # Includes git_provenance
├── README.md + .sha256
└── artifacts/
```

## Evidence Standards Reference

See `.claude/skills/evidence-standards.md` for:
- Three Evidence Rule (Configuration, Trigger, Log)
- Mock vs Real mode decision tree
- Git provenance requirements
- Checksum verification
