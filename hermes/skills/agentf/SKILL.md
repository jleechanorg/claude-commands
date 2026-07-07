---
name: agentf
description: Private-org (Agnt-F) dispatch plumbing for Agent-Orchestrator. Load this companion to the `agento` skill when dispatching AO work against repos under the user's private `$USER-af` GitHub account / Agnt-F org, which the default AO bot token cannot see. Documents the token-override spawn pattern, project base stub, and self-push/gist authoring under the private account. This skill is machine-local and intentionally NOT tracked in jleechanorg/$ORG (the block-agentf-push hook keeps private-org names out of the public org).
---

# agentf — private-org dispatch plumbing

Companion to the `agento` skill. Load this whenever an AO dispatch targets a repo
under the user's **private GitHub account** (`$USER-af`) / **Agnt-F org** —
those repos are invisible to AO's default `AO_BOT_GH_TOKEN` (the jleechanao bot),
so `--claim-pr` returns 404 unless you override the token.

> **Why this lives outside the repo:** the `block-agentf-push-to-jleechanorg.sh`
> PreToolUse hook refuses any push to `jleechanorg/*` whose diff contains
> `agnt-f` / `agent-f` / `agf-` / `$USER-af`. That keeps private-org project
> names and account handles out of the public org. This file is therefore kept
> machine-local (gitignored) and is loaded by agents at runtime like any other
> skill.

## Config: the project base stub

`ao` resolves its config via a walk-up overlay (see the `agento` skill for the
general mechanism). The stub at `~/.openclaw/agent-orchestrator.yaml` is a
3-project base (`onboarding-test`, `agf-api`, `agf-lambda`) that gets **overlaid**
by the canonical config at `~/.hermes_prod/agent-orchestrator.yaml`.

When `ao` cannot auto-resolve a project (cwd outside any project dir), it prints
the full enumerated list, which includes the private-org keys:

```
Multiple projects configured. Specify one: agent-orchestrator, agf-api, agf-lambda, claude-commands, ai-universe-lite, cmux, dark-factory, heretic-lab, $ORG, mcp-mail, mctrl-test, merge_train, openclaw-sso, ralph, smartclaw, worldai-claw, worldarchitect
```

Pass `-p <short-project-key>` explicitly (e.g. `-p agf-api`) — don't rely on cwd
auto-detection when in a worktree.

## Account + token plumbing

Agnt-F repos are private under the user's `$USER-af` GitHub account. AO's
default `AO_BOT_GH_TOKEN` (jleechanao bot) cannot see them, so `--claim-pr`
returns 404. To dispatch Agnt-F work:

1. Confirm `GH_TOKEN_AGENTF` exists in `~/.bashrc` (it does as of 2026-06-04).
   This is a `gh_pat_*` personal access token scoped to the Agnt-F org + the
   `$USER-af` account.
2. Spawn with all three token env vars overridden so the AO subprocess and its
   `gh` CLI use the right account:
   ```bash
   env GITHUB_TOKEN="$GH_TOKEN_AGENTF" \
       AO_BOT_GH_TOKEN="$GH_TOKEN_AGENTF" \
       GH_TOKEN="$GH_TOKEN_AGENTF" \
     ao spawn -p <project> --agent claude-code --claim-pr <N> "<task text>"
   ```
   (On macOS, still wrap this in the `env -i` ARG_MAX wrapper documented in the
   `agento` / `dispatch-task` skills — pre-resolve the tokens in the outer shell
   first, since `env -i` strips PATH.)
3. Author gists / comments under the `$USER-af` account by exporting
   `GH_TOKEN="$GH_TOKEN_AGENTF"` first (the private-gist skill documents this).

If `ao start` hangs when registering the project, the repo is likely already
cloneable manually — clone to `~/.worktrees/<project>-main` directly, add a
project entry to `agent-orchestrator.yaml`, and the lifecycle worker is usually
already running (verify with `pgrep -fl lifecycle-worker`). If `ao spawn` still
complains "lifecycle polling is inactive", write `~/.agent-orchestrator/running.json`
by hand — see the `running.json` bootstrap section in the `agento` skill for the
JSON template.

## See also

- `agento` skill — the general AO dispatch skill (project resolution, spawn
  pitfalls, ARG_MAX `env -i` wrapper, post-spawn wire-up).
- `dispatch-task` skill — bead-ID format, `env -i` spawn wrapper, `ao send`
  long-body caveat.
- The private-gist skill — authoring gists under the `$USER-af` account.
