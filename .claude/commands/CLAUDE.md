---
description: Command export maintenance policy and metadata contract
type: documentation
execution_mode: none
---

# Command Export Policy

This file scopes maintenance under `.claude/commands/`. It is documentation,
not an executable `/claude` command.

Every executable command starts with:

```yaml
---
description: <short trigger or outcome>
type: <execution|planning|testing|git|orchestration|quality|ai|research|review>
execution_mode: <immediate|deferred|manual>
---
```

Keep command wrappers thin:

- point to an existing canonical `.claude/skills/<name>/SKILL.md`;
- do not duplicate a skill's workflow or GitHub API recipes;
- preserve aliases only when a real consumer uses them;
- use portable placeholders instead of application-specific paths;
- verify every named command or skill target exists.

For PR readiness, delegate to `green.md` and the canonical
`pr-green-definition/SKILL.md`. `/green` has exactly two current-head gates:
required CI success and mergeable/no conflicts. Advisory review and draft
quality steps must not be restated as merge-readiness gates.

Run command metadata, link/reference, and relevant repository tests after
changes.
