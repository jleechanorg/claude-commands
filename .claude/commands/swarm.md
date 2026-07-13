---
description: /swarm — orchestrate multi-agent swarms (ultracode workflows + agent-team lanes) with adversarial verification
type: llm-orchestration
execution_mode: immediate
---

# /swarm <goal> [--engine workflow|team] [--shape retro|review|solutions|innov|triage] [--sidekick [model]]

Run the goal as a multi-agent swarm with adversarial verification, cost-routed subagents, and artifacts committed to a PR. The sidekick wrap is mandatory regardless of `--engine`.

Read `~/.claude/skills/swarm/SKILL.md` and execute the full playbook with the provided goal — including the instant-start sequence (STATE.md, in-session Agent Teams lanes, tmux sidekick), engine selection, canonical phase shapes, hard rules, and execution recipe.

## Input

$ARGUMENTS
