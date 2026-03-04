# Ralph Agents Notes

Code changes in `ralph/` are repository-specific implementation details for this repo.
They are intentionally decoupled from the conceptual upstream implementation:

- Snark Ralph upstream reference: https://github.com/snarktank/ralph
- Keep local adaptations isolated to `ralph/` patterns and workflow in this repository.
- Do not promote experimental local orchestration changes back into
  `snarktank/ralph` without explicit review and a dedicated upstream PR.
- Preserve upstream compatibility: updates here are for repo-specific operations only and should not
  be treated as authoritative changes to the conceptual upstream without explicit sync.
