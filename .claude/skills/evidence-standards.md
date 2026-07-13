---
name: evidence-standards-worldai
description: Worldarchitect.ai-specific evidence requirements. Extends the global /es skill with worldai-only rules (LLM API calls, streaming SSE, prompt-library, dice/faction roll traces, PR-class gating). Use when reviewing or producing evidence for any PR touching $PROJECT_ROOT/**, world_logic.py, rewards_engine.py, prompt_library.py, or any LLM/streaming path. For general evidence policy see ~/.claude/skills/evidence-standards/SKILL.md.
scope: your-project.com only — for general evidence policy see ~/.claude/skills/evidence-standards/SKILL.md
---

# Evidence Standards — Worldarchitect.ai

## What worldai needs beyond the global /es

The global `/es` skill at `~/.claude/skills/evidence-standards/SKILL.md` defines the cross-project evidence policy (bundle shape, checksums, three-evidence rule, mock-mode prohibition, video evidence). This file does **not** duplicate that. It only adds the worldai-specific rules that come from the fact that worldai is a 14-agent D&D TTRPG engine whose production paths call real LLM APIs (OpenAI, Anthropic, Gemini) and stream SSE responses to a browser, with a heavy prompt-library + level-up + rewards_engine pipeline plus a dice integrity layer.

Read the global `/es` first, then this file. Read `~/.claude/CLAUDE.md` for master policy (the disallow-unit-tests rule lives there).

## Worldai-specific evidence modes

A claim touching any of the following code paths requires the matching evidence mode. If the global /es rules apply but no worldai mode applies, follow the global rules alone.

| Mode | Code path it covers | Required evidence |
|------|---------------------|-------------------|
| **LLM API call** | `$PROJECT_ROOT/world_logic.py`, `$PROJECT_ROOT/rewards_engine.py`, `$PROJECT_ROOT/agents.py` — any call into OpenAI / Anthropic / Gemini | Raw provider transcript in **`llm_request_responses.jsonl`** (the raw LLM request/response — NOT `request_responses.jsonl`, which per `docs/evidence-standards/bundle-anatomy.md` is local MCP/tool traffic and does not prove a real provider call). `system_instruction_files` captured at runtime. If `CAPTURE_RAW_LLM=true`, also `raw_request_payload` + `raw_response_text`. Tie to the same `request_id` as the `streaming_execution_trace`. |
| **Streaming SSE** | Flask/MCP routes that emit `text/event-stream` chunks (the response that the browser renders token-by-token) | Raw chunk bytes (UTF-8 hexdump of at least 2 chunks + the `data: [DONE]` frame). The `streaming_response_signature` (SHA-256 over canonical JSON of `request_id` + `response_text` + `execution_trace`). `provider` / `mock_callable` recorded per phase; `mock_local_fallback` MUST be absent in real mode. |
| **Prompt library** | `$PROJECT_ROOT/prompt_library.py`, `prompts/*.md` — which prompt files were loaded and their combined char count | `debug_info.system_instruction_files` list, `system_instruction_char_count`, and `system_instruction_text` only when `CAPTURE_SYSTEM_INSTRUCTION_MAX_CHARS > 0`. Static code references alone are insufficient — runtime capture is required. |
| **Dice / faction roll trace** | `$PROJECT_ROOT/dice.py`, `$PROJECT_ROOT/dice_integrity.py`, `$PROJECT_ROOT/dice_provably_fair.py`, `$PROJECT_ROOT/dice_strategy.py` | `dice_audit_events[*].dc_reasoning` showing the DC was set BEFORE `random.randint()`, the actual `roll` integer, and `tool_results[].args.dc_reasoning` for the LLM tool-call path. Two-phase strategy: capture `args` (request) and `result` (response) with `campaign_id` for cross-log lookup. |
| **Rewards / level-up pipeline** | `$PROJECT_ROOT/rewards_engine.py`, `$PROJECT_ROOT/game_state.py` (XP math) | Before/after `game_state_snapshot.json` showing the flag transitions (e.g. `level_up_available: false → true`), plus the prompt that triggered the decision and the normalized output. |

## mvp_site Evidence Policy (Mandatory)

### Fail-Closed Trigger

Any non-test change under `$PROJECT_ROOT/**` requires `/es` evidence.

For this rule, "non-test" means any changed file under `$PROJECT_ROOT/` except files
under `$PROJECT_ROOT/tests/**` or `$PROJECT_ROOT/test_integration/**`. Treat ambiguous
paths as production/runtime until proven otherwise. Do not downgrade this to
"targeted tests only" because the user did not explicitly type `/es`; the path
trigger is enough.

Minimum evidence tier:
- Runtime/server-only files that cannot touch LLM behavior: real local server
  request/response proof and server provenance.
- LLM-interacting files (routes, agents, world logic, rewards, game state,
  providers, prompt paths): real local server + real LLM capture + real
  Firebase/state evidence.
- User-visible behavior: the applicable tier above plus captioned browser/video
  evidence showing the behavior.

Unit tests, CI status, screenshots, PR prose, and agent summaries are never a
replacement for this `/es` evidence on non-test `$PROJECT_ROOT/**` diffs.

**Unit tests are NEVER valid `/es` evidence for changes under `$PROJECT_ROOT/`.**

### Fail-Closed Scope Rule

`Non-test change` means any `$PROJECT_ROOT/**` change except `$PROJECT_ROOT/tests/**`,
`$PROJECT_ROOT/test_integration/**`, and files whose sole purpose is test fixtures
or test harness support. When in doubt, treat as production-impacting.

### Prompt File Rule (Mandatory)

Any change to files under `$PROJECT_ROOT/prompts/**` (or any file referenced by `prompt_tool_contracts.json`) **always requires Server + LLM evidence** — never N/A and never server-only.

**Minimum evidence for prompt changes:**
1. Real local server running with the updated prompt
2. Real LLM API call(s) captured in `llm_request_responses.jsonl`
3. The LLM response must demonstrate the changed instruction is followed
4. Contract version/hash bump in `prompt_tool_contracts.json` (if applicable)

**Unit tests and E2E tests with fake/synthetic LLM responses do NOT satisfy this rule.**

### Two-Tier Evidence Requirement

| Tier | When Required | What It Proves |
|------|---------------|----------------|
| **Server + LLM** (mandatory baseline) | Changes touching LLM-interacting code (routes, prompt templates, agent logic, rewards, game state, providers) — **includes ALL prompt file changes** | Real local server running, real LLM API calls, real Firebase, real responses |
| **Server + LLM + UI/Browser video** | When the change affects anything a user would see or experience differently | Above + captioned video (GIF/MP4/cast) showing before/action/after |
| **Server only** (no LLM required) | Changes to static assets, CSS, client-side JS, HTML templates, or config that never touches LLM paths | Real server running + HTTP request evidence |
| **N/A — documented justification** | Pure comments, docstrings, type hints, or import reordering with no behavioral change | Explicit `N/A` note with one-line justification |

**Prompt file changes can NEVER claim N/A.**

### What "Real Server + Real LLM" Means

Evidence must show ALL of these:
- `provenance.server.pid` — a real server process was running
- `provenance.server.process_cmdline` — the actual server command
- `request_responses.jsonl` or equivalent — real HTTP requests to the local server
- `llm_request_responses.jsonl` or equivalent — real LLM API calls with real responses (not mocked)
- `metadata.json` with git SHA (matching PR HEAD preferred; if SHA differs, apply Evidence Staleness Tolerance)

### Decision Rule for Reviewers

1. **Did any prompt files change?** (`$PROJECT_ROOT/prompts/**`) → require Server + LLM evidence with real LLM output. Never N/A.
2. **Does the change touch LLM-interacting code?** → require Server + LLM evidence.
3. **Is there a running server?** Check `provenance.server.pid`. If empty/null and the tier requires a server → FAIL.
4. **Are there real LLM calls?** Check for `llm_request_responses.jsonl`. If absent and tier requires LLM → FAIL.
5. **Does the change affect what a user sees?** → check for video evidence. If absent → FAIL.
6. **Does the git SHA match the PR HEAD?** If not → apply Evidence Staleness Tolerance.

### Evidence Staleness Tolerance for Test/Docs-Only Changes

Evidence captured at a prior SHA remains valid at HEAD when only non-behavioral changes occurred between the evidence SHA and HEAD:

| Category | Examples | Why no rerun needed |
|----------|----------|---------------------|
| **Test-only** | `*_test.py`, `tests/`, `$PROJECT_ROOT/tests/` | Tests exercise existing behavior; they don't change it |
| **Docs-only** | `*.md`, `docs/`, `README`, `CLAUDE.md` | Documentation describes behavior; it doesn't alter it |
| **CI/workflow** | `.github/workflows/*test*.yml`, lint configs — **excluding** `deploy*.yml`, `*preview*.yml` | Deployment workflows always require fresh evidence |
| **Type hints/comments** | `*.pyi`, type annotations, docstrings, comments | No runtime effect |



## Publication (gist-first)

When evidence is ready for a PR:

1. **Publish to a secret/unlisted gist** with sanitized artifacts (README, metadata, pytest output, checksums).
2. Put **only the gist URL** in the PR `## Evidence` section (and linked sections as required by the description gate).
3. **Do not commit** evidence bundles under `docs/evidence/` on the PR branch unless a repo gate explicitly requires in-tree paths — local `/tmp/<repo>/<branch>/` is the working bundle; gist is the published copy.
4. Gate-6 accepts `gist.github.com/` URLs; prefer that over `docs/evidence/` tree links in the PR body.


## Minimum Viable Evidence Checklist

**Every test MUST capture these at minimum:**

```python
def capture_provenance():
    provenance = {}
    provenance["git_head"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True).strip()
    provenance["git_branch"] = subprocess.check_output(
        ["git", "branch", "--show-current"], text=True).strip()
    provenance["merge_base"] = subprocess.check_output(
        ["git", "merge-base", "HEAD", "origin/main"], text=True).strip()
    provenance["commits_ahead_of_main"] = int(subprocess.check_output(
        ["git", "rev-list", "--count", "origin/main..HEAD"], text=True).strip())
    provenance["diff_stat_vs_main"] = subprocess.check_output(
        ["git", "diff", "--stat", "origin/main...HEAD"], text=True).strip()
    port = BASE_URL.split(":")[-1].rstrip("/")
    pids = subprocess.check_output(["lsof", "-i", f":{port}", "-t"], text=True).strip().split("\n")
    pids = [pid for pid in pids if pid]
    provenance["server"] = {
        "pid": pids[0] if pids else None,
        "port": port,
        "process_cmdline": subprocess.check_output(
            ["ps", "-p", pids[0], "-o", "command="], text=True).strip() if pids else None,
    }
    return provenance
```


## Mock Mode Prohibition

**MOCK MODE = INVALID EVIDENCE** for: production server validation, API integration claims,
data integrity verification (dice rolls, state changes), bug fix confirmation, performance
claims, and security validation.

**Mock mode tests ONLY prove:** code syntax is correct, function signatures work, basic logic
flow in isolation.

For any `$PROJECT_ROOT/**` non-test change, there is no acceptable substitute for real-server
+ real-LLM evidence.

## Disallow-unit-tests rule (mirrors `~/.claude/CLAUDE.md`)

**Unit-only proof is NOT sufficient** for any `PROD_BEHAVIOR_CHANGE` or `LOGGING_INFRASTRUCTURE` PR. A behavior verified only by unit tests (Layer 1, mocked/isolated) is not proven. `/es` and `/er` must treat unit-only evidence as **INSUFFICIENT** — require at least Layer 2 end-to-end integration proof (real callstack, mock only at external API boundaries), or real-service evidence where the production path uses an LLM or external service.

**Three exceptions** (unit-only IS acceptable):

1. Non-production changes (docs, tests, tooling, scripts).
2. Production changes under 100 delta lines of non-test code — provided the PR class is NOT `PROD_BEHAVIOR_CHANGE` (e.g. refactoring, performance improvements without behavioral impact, or internal restructuring). `PROD_BEHAVIOR_CHANGE` always requires at least Layer 2 evidence regardless of size.
3. Classes classified `LOGGING_ONLY` **outside `$PROJECT_ROOT/**`** or `TEST_ONLY` per the table below. A `LOGGING_ONLY` change under `$PROJECT_ROOT/**` still requires the minimal real-server run from the table (unit-only is NOT sufficient there).

**Always warn the user explicitly** when a claim is unit-only — the burden of disclosure is on the agent, not the reviewer.

## PR-class classification → required evidence

Before collecting evidence, classify the PR. The class decides what evidence is required at all.

| PR class | Definition | Evidence required |
|----------|------------|-------------------|
| `LOGGING_ONLY` | Adds `logger.info` / structured-log calls; no behavior change; no production code path difference | **Outside `$PROJECT_ROOT/**`** (scripts, orchestration, tooling): none beyond the diff itself — verify the log line exists and existing tests pass. **Under `$PROJECT_ROOT/**`** the fail-closed trigger still applies even for logging-only: provide one real local-server run with server provenance showing the new log line actually fires in captured server output. No LLM assertion, video, or full bundle needed — but unit tests alone are NOT sufficient for `$PROJECT_ROOT/**`. |
| `LOGGING_INFRASTRUCTURE` | Adds a new log handler, a log-routing script, a structured-logging field, a launchd log-rotation job | A captured sample of the new log output (one real run), the config file or plist diff, and `launchd print` / `systemctl status` showing the new job is loaded. Unit tests alone are insufficient — show the handler actually fires. |
| `TEST_ONLY` | Adds or modifies tests only; no production code change | The new/modified test run output and a `git diff --stat origin/main...HEAD` confirming no production file is touched. |
| `PROD_BEHAVIOR_CHANGE` | Any change to a production code path that runs in real mode (LLM call, dice roll, streaming, prompt load, level-up decision, faction state) | Full evidence: real-mode run with the worldai-specific evidence mode(s) from the table above, plus git provenance, plus a UI/tmux video if the change touches rendered output. Unit tests are NEVER sufficient. |
| `NEEDS_HUMAN` | Cannot be classified from the diff alone (e.g. ambiguous refactor, security-sensitive change, prompt rewrite that needs gameplay review) | STOP. Post a comment asking the human to classify before evidence collection starts. Do not start the evidence run. |

A single PR can carry multiple classes — split evidence by file. `$PROJECT_ROOT/logger.py` edits are `LOGGING_INFRASTRUCTURE`; `$PROJECT_ROOT/world_logic.py` edits in the same PR are `PROD_BEHAVIOR_CHANGE`.

## Worldai examples (concrete)

### Example 1 — Real dice roll via OpenAI tool-call (PROD_BEHAVIOR_CHANGE)

A PR adds a new `dc_reasoning` field to the LLM's tool-call args. Evidence required:

- One real `request_responses.jsonl` line showing the full MCP request to `/mcp` and the LLM response.
- `debug_info.system_instruction_files` = `["prompts/master_directive.md", "prompts/dice_tool_directive.md", ...]`.
- `dice_audit_events` in `run.json` showing `dc_reasoning: "target is a CR 2 ogre guard, DC 13 Wisdom save per 5e"` BEFORE the `roll: 17` integer.
- `tool_results[].args.dc_reasoning` matching the audit event (proves LLM tool-call payload carried the field).
- A `run.json` or command transcript with `"sha": "<git-rev-parse-HEAD-output>"` embedded at capture time — tying the artifact to the PR commit. A separate `git rev-parse HEAD` call alone proves only checkout state, not that evidence was actually captured at that SHA.

### Example 2 — Streaming SSE bytes (PROD_BEHAVIOR_CHANGE)

A PR changes SSE chunking behavior. Evidence required:

- `curl -N http://localhost:8005/mcp/stream -d '...'` saved to `artifacts/sse_raw.bin`.
- Hexdump of the first 2 chunks (≥ 16 bytes each) and the terminal `data: [DONE]\n\n` frame — confirms UTF-8 framing and that chunks are JSON-encoded `data:` events, not raw tokens leaking.
- `streaming_response_signature.digest` = SHA-256 of canonical JSON over `(request_id, response_text, execution_trace)`.
- `streaming_execution_trace` records `provider: "openai"`, `mock_callable: null` for every phase — `mock_local_fallback` MUST be absent.
- A 10-second tmux recording showing the curl command + the bytes on stdout.

### Example 3 — LOGGING_ONLY PR under `$PROJECT_ROOT/` (minimal real-run proof)

A PR adds a single `logger.info("rewards_decision", extra={...})` call in `$PROJECT_ROOT/rewards_engine.py`. Classify as `LOGGING_ONLY`, but because the file is under `$PROJECT_ROOT/**` the fail-closed trigger still applies. Evidence required:

- The `git diff` line for the new log call.
- One real local-server run with `provenance.server.pid` / `process_cmdline` showing the new log line in captured server output.

Do NOT require an LLM assertion, video, or full streaming bundle — but unit tests alone are NOT sufficient under `$PROJECT_ROOT/`. (A truly evidence-free logging change must live outside `$PROJECT_ROOT/**` — e.g. `scripts/` or `orchestration/`.)

## Cross-references

- **Global /es skill** (general evidence policy, bundle shape, checksums, three-evidence rule, mock-mode prohibition, video evidence): `~/.claude/skills/evidence-standards/SKILL.md` — always read first.
- **Master policy** (the disallow-unit-tests rule and the master evidence policy statement): `~/.claude/CLAUDE.md` — line ~284 has the unit-only-insufficient rule and its three exceptions.
- **Worldai docs dir** (deep-dive evidence subtopics — streaming evidence, bundle anatomy, three-evidence rule in full, tmux/UI video templates, checksum modes): `your-project.com/docs/evidence-standards/` — point to the specific sub-doc, do not re-derive the rules here.
- **Writing worldai evidence tests** (real-mode test-authoring craft — LLM scenario forcing for multi-round paths, partial-state-update assertion handling, model-settings pinning): `your-project.com/docs/evidence-standards/writing-worldai-evidence-tests.md` — read when authoring a `testing_mcp`/`testing_ui` real-mode test, not when reviewing a bundle.
- **Sister skills**: `your-project.com/.claude/skills/dice-authenticity-standards.md`, `dice-roll-audit.md`, `streaming-evidence-standards.md`, `dice-real-mode-tests.md`, `tmux-video-evidence.md`, `ui-video-evidence.md`, `browser-testing-ocr-validation.md` — load alongside this file when the claim touches dice, streaming, video, OCR, or browser.
