---
name: codex-exec-pitfalls
version: 1.0.0
description: |
  Pitfalls when using `codex exec` to drive a third-party CLI tool, skill, plugin, or workflow
  (NOT for using Codex as a coding agent — see the bundled `codex` skill for that).
  Class-level skill. Triggers when the task involves driving any external tool via `codex exec`,
  especially when: (a) the tool needs an env var to gate a network call or feature flag,
  (b) the tool needs stdin to receive a secret or code, (c) the agent must follow a multi-phase
  protocol (preflight → enroll → hand-off → poll), or (d) you want the agent to run scripts
  that you could just as easily run yourself.
  
  Anti-trigger: pure coding tasks ("add dark mode", "fix this bug") → use the bundled `codex` skill.
  Anti-trigger: one-shot shell commands you can run directly → skip `codex exec` entirely.

metadata:
  hermes:
    tags: [codex, codex-exec, pitfalls, env-scrub, login-shell, gate]
    verified: 2026-07-16 (Cloud Build plugin via codex exec — 3 runs, 2 gate fires, 1 successful end-to-end via direct-script path)
---

# Codex exec pitfalls

`codex exec` is a useful primitive for letting an LLM agent drive an external tool, but it has several gotchas that bite in non-obvious ways. This skill encodes the lessons from driving a third-party plugin (Cloud Build) via `codex exec`, plus the generalizable patterns.

## Pitfall 1 — `bash -lc` login-shell env scrub (THE big one)

**Symptom:** you set an env var in the outer process that launches `codex exec` (or via `-c env={...}` on the codex CLI), but the agent's bash subprocess cannot see it. The tool the agent runs reports "env var not set" or returns a gate failure.

**Cause:** `codex exec` runs every shell command as `bash -lc '<cmd>'` — a login shell that re-sources `~/.bash_profile`/`~/.profile`/`~/.bashrc`. Two specific paths that DO NOT propagate env vars to the agent's bash:

1. **Outer-process env vars:** Python `subprocess.run(["codex", "exec", ...], env={"FOO": "1"})` — the `env=...` dict is set on the codex subprocess but is NOT inherited by the agent's `bash -lc` shell. The login shell starts from a fresh env table, re-sources profile scripts, and only keeps vars those scripts export.
2. **`-c 'env={"FOO":"1"}'` config layer on the codex CLI:** this adds to codex's own config (model selection, sandbox settings) but does NOT add to the agent's bash env.

**Verified:** 2026-07-16, Cloud Build plugin. Setting `CLOUD_HERMETIC_CONFIRMED=1` via both methods above had no effect — the cloud-build skill's `preflight-local.sh` still reported `preflight FAIL: set CLOUD_HERMETIC_CONFIRMED=1`.

**Workarounds (in priority order):**

1. **Have the agent export the var in its own prompt.** Add to the prompt: "Env var `FOO=1` is required. Run `export FOO=1` before any other commands." The agent will run the export first; the var persists for the rest of the session because `bash -lc` evaluates each command in the same shell session.
2. **Drive the underlying tool directly from your gateway.** If the env var is gating a network call (SSH enrollment, API auth, etc.), the most reliable path is to invoke the underlying scripts yourself rather than asking the agent. Example: `bash scripts/preflight-local.sh <dir> <plan>` → `bash scripts/cb-client-setup.sh` (with code on stdin) → `bash scripts/lib-client.sh cloud_build_handoff ...`. This bypasses Codex's bash-scrub entirely.
3. **Add a `~/.bash_profile.d/` shim that re-exports your vars.** Heavy-handed; only do this for session-wide defaults.

**How to verify:** at the top of the agent's prompt, ask it to run `echo "FOO=$FOO"` and report the value. If it's empty, the env scrub is biting. Don't waste time debugging downstream tools before confirming the var is actually visible.

## Pitfall 2 — Code on stdin can be hard to inject

**Symptom:** the tool requires a secret/code on stdin (an enrollment code, an OAuth code, a one-time password), but `codex exec` doesn't expose a clean stdin injection point. Your first runs end with the agent saying "I tried to pipe the code in but couldn't" or the tool hanging on `read -r` because stdin is the terminal, not the pipe.

**Cause:** `codex exec` doesn't have a `--stdin <file>` flag. The agent either types the code into its prompt (then has to pipe it through `printf` etc.) or `bash -lc` consumes stdin in unexpected ways.

**Workarounds:**

1. **Append the code to the prompt as a `<stdin>` block.** Codex automatically reads stdin and appends it as a `<stdin>` block in the user message. The agent can then run `printf '%s\n' '<code>' | bash setup.sh`.
2. **Have the agent write the code to a temp file**, then `bash setup.sh < temp_file` — works but creates a small attack surface (code persists in `/tmp`).
3. **Drive the tool directly from your gateway** (recommended for sensitive one-time codes). Pass the code on your own subprocess stdin.

**Verified:** 2026-07-16, Cloud Build enrollment. Codex appended the code correctly and the agent successfully ran `printf '<code>' | bash scripts/cb-client-setup.sh`.

## Pitfall 3 — Multi-phase protocols need explicit phase boundaries in the prompt

**Symptom:** the tool has a multi-phase protocol (preflight → enroll → hand-off → poll → land) and the agent burns tokens re-reading the SKILL.md, gets confused about which phase it's in, or skips phases entirely.

**Cause:** the SKILL.md is usually verbose (8-15 KB). The agent reads it, summarizes it, then loses the exact phase ordering.

**Workarounds:**

1. **Restate the phases explicitly in the prompt** as a numbered list. Example: "Follow these phases in order: Phase 1: preflight. Phase 2: enroll. Phase 3: hand-off. Phase 4: poll. Phase 5: stop after first poll." The agent treats the prompt as authoritative.
2. **Set a clear stop condition** — e.g. "After the first successful poll, print the full status JSON and stop. Do not poll again." Without this, the agent will loop indefinitely to "be thorough."
3. **Reference the SKILL.md by section, not whole document** — "Follow section 3 of `skills/cloud-build/SKILL.md` for the handoff, then section 4 for the follow loop. Skip section 5 (abort) and section 6 (land) — I'll do those."

## Pitfall 4 — Long sessions burn budget on redundant work

**Symptom:** `codex exec` runs for 30+ tool calls but the actual progress is 2-3 substantive operations. The token usage report shows 28k+ tokens for what should have been a 5-step flow.

**Cause:** the agent reads the SKILL.md multiple times (once per phase), re-lists the project files each time, and re-explains what it's about to do before each command.

**Workarounds:**

1. **Use `--ephemeral`** to skip session file writes — won't help with token burn but reduces disk noise.
2. **Drive the underlying tool yourself.** If your gateway can run the same scripts the agent would (and you can verify the output), skip `codex exec` entirely. The session in question drove the cloud-build library directly for the final run, after 3 codex-exec attempts burned 28k+ tokens each.
3. **Tell the agent explicitly "Do not re-read SKILL.md after Phase 1"** — sometimes works, often doesn't.

## Pitfall 5 — Codex without `--dangerously-bypass-approvals-and-sandbox` will refuse most tool calls

**Symptom:** `codex exec "do X"` returns immediately with "approval required for: <command>" without running anything. The agent loop never gets past the first action.

**Cause:** Codex defaults to a sandbox that requires approval for each shell command. Non-interactive runs have no human to approve.

**Workarounds:**

1. **Use `--dangerously-bypass-approvals-and-sandbox` and `-s danger-full-access`** for fully-automated workflows. The `-s` flag sets the sandbox mode; `--dangerously-bypass-approvals-and-sandbox` skips the per-command approval prompt. Both are required for headless automation.
2. **Read the run in your terminal instead** with `codex` (interactive TUI) — for debugging only, not for automation.

**Verified:** 2026-07-16 — without these flags, every codex exec call returned immediately with approval errors.

## Pitfall 6 — ChatGPT account model restriction

**Symptom:** `codex exec -m gpt-5 ...` returns `ERROR: The 'gpt-5' model is not supported when using Codex with a ChatGPT account.`

**Cause:** Codex authenticated via ChatGPT (not OpenAI API key) has a restricted model set. `gpt-5` may be API-only.

**Workarounds:**

1. **Drop the `-m` flag** — let Codex pick the default. The default usually works for ChatGPT accounts.
2. **Use `-m gpt-4o` or `-m o3`** for ChatGPT-authenticated runs.
3. **Re-authenticate Codex with an OpenAI API key** (`codex auth login`) for full model access.

## Pitfall 7 — Codex on a non-git directory refuses to start

**Symptom:** `codex exec ...` fails with "Not inside a trusted directory" or "directory is not a git repo."

**Cause:** Codex's sandbox requires the workdir to be a git repo. Bare `/tmp/foo` won't work.

**Workarounds:**

1. **`cd $(mktemp -d) && git init -q && codex exec ...`** — create a throwaway git repo for scratch work.
2. **`--skip-git-repo-check`** — bypasses the check but the agent may still complain about file operations.

## When to skip `codex exec` and drive the tool yourself

`codex exec` adds value when:
- The tool's protocol is poorly documented and the agent can read the source to figure it out
- The user wants the agent to make judgment calls (which test to run, which file to inspect)
- You want the agent to handle errors gracefully and decide whether to retry or fail

Skip `codex exec` when:
- The protocol is documented and deterministic (the cloud-build library is a good example — all scripts have well-defined inputs/outputs)
- The user wants proof the tool works, not proof the agent can figure it out
- Token cost matters (driving scripts directly uses 0 tokens)
- You need to inject secrets via stdin or env vars and Pitfalls 1+2 would both bite

**Rule of thumb:** if you can describe the entire flow as a 10-line bash one-liner, run it yourself. Use `codex exec` when the flow needs LLM judgment between steps.

## Reference: full env-scrub diagnostic

If you suspect the env-scrub is biting:

```bash
# Ask the agent to verify env vars
prompt = """At the START of the session, before doing anything else, run:
   echo "FOO=${FOO:-UNSET}"
   echo "BAR=${BAR:-UNSET}"
Report the exact output. If either is UNSET, the env scrub is biting — do NOT proceed."""

# Or drive the tool yourself from your gateway
import os, subprocess
env = os.environ.copy()
env["FOO"] = "1"
env["BAR"] = "bar_value"
r = subprocess.run(["bash", "-lc", f"cd {tool_dir} && bash {script} '{arg}'"],
                   env=env, capture_output=True, text=True, timeout=120)
print(r.stdout)
```

If the bash -lc path works from your gateway but doesn't work via the agent, you've confirmed the env-scrub is biting. Switch to direct-script driving.

## Pairing with other skills

- **`evidence-attach-to-slack`** — when the run produced a binary artifact (MP4, screenshot, log) that needs to land in the user's Slack thread.
- **`autonomous-ai-agents/codex`** — bundled coding-agent Codex skill (different scope; this skill covers Codex-as-driver, not Codex-as-coder).
- **`dispatch-task`** — for AO-based dispatch instead of `codex exec` (when you need a full git worktree + branch + PR lifecycle).