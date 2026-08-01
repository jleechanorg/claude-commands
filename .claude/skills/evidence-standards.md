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

**Real-LLM provider note:** The `agy` CLI (Google Antigravity) is the cost-saving
**default** real-LLM provider for local/test runs since PR #7971 (`008c55aaaa`), selected by
`is_agy_provider_mode()` in `$PROJECT_ROOT/llm_providers/provider_gateway.py`. For evidence that
proves LLM judgment, agy-by-default is valid — it is a real LLM, not a mock. Do **not**
treat an agy-backed judgment run as "mocked" or insufficient. This does **not** prove the
production Gemini-SDK streaming or native tool-call path: `agy_provider.py` has no true
streaming/native tool-call API, and `generate_content_stream` yields a single completed
response. If the claim depends on token-by-token SSE, Gemini SDK tool-call behavior, or
production streaming semantics, require an explicit Gemini SDK run with
`AGY_PROVIDER_ENABLED=false` and record that rationale in the evidence bundle.
Conversely, if a bundle sets `AGY_PROVIDER_ENABLED=false`, the evidence should state the
matching reason rather than opting out silently: if the claim is about streaming or
tool-calling behavior, reason (1) — validating the production streaming/tool-calling
path — applies. For a **non-streaming judgment claim**, only reason (2) applies — the
flow depends on strict JSON-mode output and hits agy's known JSON-reliability gap (agy
lists "JSON-only response grammar" as a non-goal); reason (1) does not justify opting out
of a claim that was never about streaming in the first place. Silent opt-out is a cost
regression, not an evidence defect, but reviewers should flag the missing or mismatched
rationale.

### BQ-Logged Real LLM Request/Response Requirement (Mandatory for LLM-communication changes)

Any PR that changes logic affecting **what is sent to or received from the LLM** —
prompt construction/assembly, request payload shaping, provider selection/dispatch
(`gemini_provider.py`, `agy_provider.py`, `provider_gateway.py`), response parsing
(`llm_parser.py`), or the god-mode/directive/state-update contract the model reads or
writes — must include real LLM request/response evidence sourced from **BigQuery**
(`worldarchitecture-ai.llm_forensics.llm_payloads` and/or `.log_events`), not only a
local `llm_request_responses.jsonl` capture.

**Why BQ, not just local capture:** local jsonl captures are written by the same process
under test and are trivially editable/fabricable (this repo caught fabricated local
evidence — byte-identical RED/GREEN pytest hashes — on PR #8132 during review, 2026-07-09).
BQ rows are written by the production `log_llm_payload()` path independent of the evidence
bundle, are timestamped server-side, and can be independently queried by a reviewer who
never touched the PR's branch — making them meaningfully harder to fabricate or
misrepresent than a file the author generated locally.

**Minimum BQ evidence for an LLM-communication-affecting PR:**
1. A `bq query` (or gist of one) against `llm_payloads`, filtered to the campaign/run used
   for the PR's evidence, showing at least one real row **within the evidence run's window — between test start
   and bundle creation. Do NOT require rows at-or-after the bundle timestamp:
   `metadata.timestamp`/`bundle_timestamp` is assigned when `create_evidence_bundle()` runs
   AFTER the scenario has already driven the LLM calls
   (`testing_mcp/lib/evidence_utils.py`), so matching rows logged earlier in the same run
   are valid** — with non-placeholder `request_json` / `response_text` content (i.e. not
   `is_test = true` synthetic fixtures unless the PR is explicitly testing-infrastructure-only).
2. The row's `model`, `campaign_id`, and `event_type` must match what the PR's evidence
   bundle claims was exercised — a BQ query that can't be tied to the specific claim (wrong
   campaign, wrong event type, wrong time window) does not satisfy this rule.
3. If the claim is about a SPECIFIC content property (e.g. "the model no longer echoes a
   stale fact," "the directive is now honored," "the field carries `_updated_at`"), quote the
   actual `request_json`/`response_text` substring from the BQ row demonstrating it — a row
   existing is not sufficient; its content must support the claim.
4. Cross-reference: the metadata/SHA tying the evidence to PR HEAD (per "What Real Server +
   Real LLM Means" above) still applies — a BQ row proves the LLM call was real, not which
   code version produced it. Both are required together.

This requirement is **in addition to**, not a replacement for, the local
`llm_request_responses.jsonl` capture already required under "What Real Server + Real LLM
Means" — the two corroborate each other (local capture proves the harness ran against a
specific code checkout; BQ proves the call actually reached the LLM and wasn't just
written by the harness itself).

**Does not apply** to: prompt-adjacent PRs that don't change LLM-communication *logic*
(e.g. a pure prose/wording tweak to an instruction file, where the Prompt File Rule's
local-capture requirement is sufficient on its own — unless the wording change itself is
the claim under test), or to changes entirely outside the LLM request/response path
(UI-only, CSS, non-LLM backend routes).

### AGY Local Evidence Guardrail

For local AGY evidence, configuration alone is insufficient. The bundle must contain
`provider_http_request_responses.jsonl` (or an equivalent raw provider capture) with a
successful `agy_request` and matching `agy_response`. Local launchers must fail closed
when the sanitized AGY runtime is missing; run `$PROJECT_ROOT/install.sh` rather than silently
falling back to the Gemini SDK.

### Decision Rule for Reviewers

1. **Did any prompt files change?** (`$PROJECT_ROOT/prompts/**`) → require Server + LLM evidence with real LLM output. Never N/A.
2. **Does the change affect LLM-communication logic** (prompt construction, provider dispatch, request/response parsing, or the directive/state-update contract)? → require the BQ-Logged Real LLM Request/Response Requirement above, in addition to local capture. Never satisfied by a local-only jsonl file or a unit test alone.
3. **Does the change touch LLM-interacting code?** → require Server + LLM evidence.
4. **Is there a running server?** Check `provenance.server.pid`. If empty/null and the tier requires a server → FAIL.
5. **Are there real LLM calls?** Check for `llm_request_responses.jsonl`. If absent and tier requires LLM → FAIL.
6. **Does the change affect what a user sees?** → check for video evidence. If absent → FAIL.
7. **Does the git SHA match the PR HEAD?** If not → apply Evidence Staleness Tolerance.

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

### Visual evidence → gist (MANDATORY for PNGs / GIFs / MP4s / MP3s / .cast)

Visual evidence binaries (screenshots, gameplay captures, before/after images, video, audio) MUST live in a public GitHub gist, NOT committed to the PR branch. Committing binaries bloats the PR diff and makes it unreviewable. Procedure:

1. Create a public gist for the bundle: `gh api /gists` with `{public: true, description, files: {README.md: {content: "..."}}}`.
2. Clone the gist locally: `git clone https://<token>@gist.github.com/<id>.git /tmp/gist-<id>`.
3. Copy the real binary bytes in (do NOT use `gh gist create --public` with base64 — it stores the bytes as utf-8 text and serves `text/plain`, which prevents rendering).
4. Commit + push: `git add . && git commit -m "..." && git push origin HEAD`.
5. Reference each binary in the PR body via the **raw URL** with the commit SHA: `https://gist.githubusercontent.com/<user>/<id>/raw/<sha>/<filename>`. The `/raw/HEAD/` form returns 404 — always use a real commit SHA.
6. Verify the raw URL serves the right `content-type`: `curl -sSI <url>` must show `content-type: image/png` (or `image/gif`, `video/mp4`, etc.) — not `text/plain`.

For Slack threads (where the same binary is also surfaced to the user as a downloadable attachment), use the 3-stage Slack `files.completeUploadExternal` API: stage 1 `files.getUploadURLExternal`, stage 2 `POST <upload_url>` with the file body, stage 3 `files.completeUploadExternal` with `files=[{id, title}]`. The bare `MEDIA:/absolute/path` text convention does NOT work through `mcp__slack__conversations_add_message`; Slack renders the literal text without creating an attachment.

Anti-pattern: passing `MEDIA:/path/to/file.png` inline as message text — Slack shows the path string, no attachment is created, and the user sees nothing.

### Repo gates that override gist-first

Some repo gates may require in-tree evidence paths (e.g., a deployment script that downloads artifacts from `docs/evidence/`). When a gate explicitly requires in-tree paths, follow the gate; otherwise default to gist-first.


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

## RED PROOF — A past bug report is NOT red proof (HARD GATE)

A red proof (i.e. the "this bug reproduces" step of `/redgreen` Phase 1) MUST be a fresh,
real failing test that runs locally against the codebase and FAILS before the fix is applied.
This is a non-negotiable hard gate. The following do NOT constitute red proof, no matter
how complete they look:

| Source | Counts as red proof? | Why |
|--------|----------------------|-----|
| A past bug report (Slack thread, GitHub issue, user transcript) | **NO** | Narrative only — was never a test run. |
| BigQuery / Firestore / GCP logs showing the bug in prod | **NO** on its own | Observational, not a reproducible test. May be used as inspiration for the test, but the test itself must run. |
| A copy-campaign script that replays inputs through an offline or wrapper LLM | **NO** | The replay is a script, not a test that asserts the failure. |
| A modified prompt + LLM output that "looks broken" to a human | **NO** | Subjective. The test must mechanically assert the missing behavior. |
| A unit test that asserts a prompt contains the fix strings | **CONDITIONAL YES** — deterministic contract red proof, but **only sufficient as a stand-alone red proof when ALL THREE hold**: (i) the asserted string is the documented load-bearing rule the model is told (not a side-effect description); (ii) there is no plausible non-contract path for the bug to recur (e.g. no sibling rule the model could contradict the new rule against); AND (iii) the PR also ships **either** a VCR regression fixture (a recorded raw LLM request/response capturing the buggy output) **or** a paired LLM-output assertion in `testing_mcp/test_*.py` that runs against the real local server + real LLM and FAILS pre-fix for the same reason as prod. If any of (i)/(ii)/(iii) fails, the contract test alone is **INSUFFICIENT** and the PR must ship a real-LLM red proof. | Prompt-string contract tests are necessary but not sufficient on their own — they reproduce the *contract gap*, but a behavior-level reproduction is required to prove the fix actually changes model output. |
| A `testing_mcp/test_*.py` test that runs against a real local server + real LLM and FAILS pre-fix for the same reason as prod | **YES** (full Layer 2 red proof) | This is the gold standard and is sufficient on its own. Set `AGY_PROVIDER_ENABLED=false` to bypass wrapper tooling and use the real Gemini API directly. |
| A unit test that mocks the model and asserts the parser handles bad output | **YES** for parser regressions only — NOT acceptable as red proof for LLM-behavior bugs | Mocking the model hides the very behavior being tested. |

**Conditional-yes examples that have passed review:** a contract test for a brand-new ESSENTIALS clause that has no sibling contradiction candidate AND is paired with a VCR fixture or `testing_mcp` real-LLM assertion of the model-output change.

**Conditional-yes examples that have FAILED review:** a contract test alone for a rule that the model has historically contradicted with a sibling clause (e.g. a new "MUST propagate NPC capture status" rule added while a sibling rule says "MUST keep narrative concise"). The contract was added, the model still chose the contradicting sibling, and the contract test alone never caught it. Such fixes require a real-LLM red proof.

**If you cannot produce a red proof, STOP.** Do not write the fix. Do not proceed to GREEN.
Ship a bead (`br create ...`) documenting the missing red proof as the blocker.

**Where to put red proof in a PR description:** link the failing-test invocation output
(red run) and the passing-test invocation output (green run) in the `## Unit Test Evidence`
section (for the contract test) or `## Non-Unit Test Evidence` section (for the real-LLM
test run via `testing_mcp/`). Cite exact commit SHAs for both runs.

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

### Example 4 — Changing what `custom_campaign_state.character_identity` sends to the LLM (PROD_BEHAVIOR_CHANGE + BQ requirement)

A PR changes the canonicalization path in `$PROJECT_ROOT/game_state.py`
(`validate_and_correct_state` → the `character_identity` normalize block) so
`character_identity` is retained and stamped with `_updated_at`, and stops
`_strip_llm_redundancies()` in `$PROJECT_ROOT/llm_service.py` from popping it — so the field is
now sent to the model instead of being stripped. This is a direct change to
LLM-communication logic (what the prompt contains). Evidence required:

- Local `llm_request_responses.jsonl` capture showing the field present with a stamp (per
  "What Real Server + Real LLM Means").
- A `bq query` against `llm_forensics.llm_payloads` for the campaign used in the repro
  (e.g. `WHERE campaign_id = "xK3fp5XrV24oarIINTF7" AND event_type = "gameplay_streaming"
  ORDER BY ingested_at DESC LIMIT 1`), with the row's `request_json` quoted showing
  `character_identity` present with the expected `_updated_at` value, and `response_text`
  quoted showing the model's narrative is now consistent with the authoritative field
  (not just that a timestamp exists — a stamped-but-still-wrong value does not satisfy this
  claim).
- If the PR's claim is "this stops a specific hallucination" (e.g. a false parentage
  relationship), the BQ row's `response_text` must be checked for absence of the specific
  stale claim, not merely presence of the corrected field in the request.

## Cross-references

- **Global /es skill** (general evidence policy, bundle shape, checksums, three-evidence rule, mock-mode prohibition, video evidence): `~/.claude/skills/evidence-standards/SKILL.md` — always read first.
- **Master policy** (the disallow-unit-tests rule and the master evidence policy statement): `~/.claude/CLAUDE.md` — line ~284 has the unit-only-insufficient rule and its three exceptions.
- **Worldai docs dir** (deep-dive evidence subtopics — streaming evidence, bundle anatomy, three-evidence rule in full, tmux/UI video templates, checksum modes): `your-project.com/docs/evidence-standards/` — point to the specific sub-doc, do not re-derive the rules here.
- **Writing worldai evidence tests** (real-mode test-authoring craft — LLM scenario forcing for multi-round paths, partial-state-update assertion handling, model-settings pinning): `your-project.com/docs/evidence-standards/writing-worldai-evidence-tests.md` — read when authoring a `testing_mcp`/`testing_ui` real-mode test, not when reviewing a bundle.
- **Sister skills**: `your-project.com/.claude/skills/dice-authenticity-standards.md`, `dice-roll-audit.md`, `streaming-evidence-standards.md`, `dice-real-mode-tests.md`, `tmux-video-evidence.md`, `ui-video-evidence.md`, `browser-testing-ocr-validation.md` — load alongside this file when the claim touches dice, streaming, video, OCR, or browser.
