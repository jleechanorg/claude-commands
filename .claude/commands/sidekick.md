# /sidekick — spawn or respawn the persistent orchestrator teammate

Load and follow the `sidekick` skill at `~/.claude/skills/sidekick/SKILL.md` (Skill tool: `sidekick`).

Usage: `/sidekick [model] [mission...]`

- `/sidekick` — respawn from the current branch's `/tmp/<repo>/sidekick/<branch_name>/STATE.md` (crash recovery; `/`→`-` in branch names), default model sonnet
- `/sidekick fable` — respawn on the Fable model (token-economy block included: sub-agents cost-routed to sonnet/haiku)
- `/sidekick fable fix CI, then drive PRs to green` — fresh mission: write initial STATE.md, create tasks, spawn

Behavior contract (details in the skill):
1. State file first — respawns never overwrite an existing STATE.md
2. One named background teammate via Agent tool; shared TaskList lanes
3. Commit-often discipline propagated verbatim to all sub-agents
4. Never merge / never force-push; milestone reports relayed to the user
