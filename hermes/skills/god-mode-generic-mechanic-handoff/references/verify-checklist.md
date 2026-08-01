# PR #8541 verify checklist (2026-07-23)

| Gate | Required evidence | Command |
|---|---|---|
| Branch clean replay | 4 intended files only, no drift | `git -C $WT diff --name-only origin/main..HEAD` |
| Local = remote HEAD | identical SHA | `git -C $WT rev-parse origin/$BR HEAD` |
| PR headRefOid == HEAD | `0b0bc4ac7...` matches | `gh pr view 8541 --json headRefOid` |
| /es real-server + real-LLM | gunicorn alive, LLM trace contains "Canonical Formula Registry" | `tail -1 evidence/*.jsonl` |
| No secrets in PR body / diff | `outbound_secret_gate.py check --file` | — |

## Drift caught and cleaned
PR HEAD originally was `0c5a2b6a64` which included:
- `$PROJECT_ROOT/bq_logging.py` (+21 lines)
- `$PROJECT_ROOT/world_logic.py` (+92 / -XX)
- `$PROJECT_ROOT/tests/test_godmode_directive_lifecycle_events.py` (332 lines deleted)
- `roadmap/README.md` (-1)
- `roadmap/activity/2026-07-23.md` (-33)

Recovery:
```
git checkout -B <branch> origin/main
git show 0c5a2b6a64 -- <four intended files> | git apply --include=<each>
git commit
git push --force-with-lease origin <branch>
```

Final clean HEAD: `0b0bc4ac73521c14b402d0c5dd1211730479a469` (4 files / +651 / -0).
