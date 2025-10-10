# Test: Campaign Evidence Artifact Integrity

> **Execution Command:** `/testllm` - LLM-Driven Test Execution Command  
> **Protocol Notice:** This is an executable test that must be run via the `/testllm` workflow with full agent orchestration.

## Test ID
test-campaign-evidence-integrity

## Status
- [x] RED (failing) – evidence package artifacts inconsistent
- [ ] GREEN (passing)
- [ ] REFACTORED

## Objective
Validate that exported campaign artifacts and supporting evidence files accurately represent gameplay history and server state for campaign `kaM205AyUZdyFweimQhY`.

## Preconditions
- Evidence export file present at `/var/folders/j0/byd1z6px50v88lf679bgt0h00000gn/T/campaign_exports/49642b41-2309-401b-ad80-36e6a7ef5329.txt`.
- Campaign state snapshot saved to `/tmp/campaign_kaM205AyUZdyFweimQhY_adventure_started.json`.
- Original create response saved as `/tmp/test1_create_campaign_raw_response.json` (copied from the raw evidence bundle).
- Local CLI access to the MCP environment.

## Test Steps

### 1. Verify Export Hash and Contents
1. Compute the SHA256 hash:
   `sha256sum /var/folders/j0/byd1z6px50v88lf679bgt0h00000gn/T/campaign_exports/49642b41-2309-401b-ad80-36e6a7ef5329.txt`
2. Record the line count:
   `wc -l /var/folders/j0/byd1z6px50v88lf679bgt0h00000gn/T/campaign_exports/49642b41-2309-401b-ad80-36e6a7ef5329.txt`
3. Inspect numbered contents to confirm literal `\n` sequences and truncated history:
   `cat -n /var/folders/j0/byd1z6px50v88lf679bgt0h00000gn/T/campaign_exports/49642b41-2309-401b-ad80-36e6a7ef5329.txt`

**Expected (Fail Condition)**
- Hash equals `3fd0d6ba1dcfa8f76a0a1e6ece01b7e8d29f7e9e14c3c0ba327f8e2af78c3454` (matches evidence packet).
- `wc -l` reports ~21 lines, confirming export does **not** include the promised 50-line history.
- `cat -n` output shows literal `\n` escapes and stops after the first interaction summary, proving the artifact is truncated.

### 2. Compare Immutable Timestamps
1. Capture the snapshot's `created_at`:
   `jq -r '.campaign_metadata.created_at' /tmp/campaign_kaM205AyUZdyFweimQhY_adventure_started.json`
2. Capture the original server timestamp from the raw create response:
   `jq -r '.game_state.last_state_update_timestamp' /tmp/test1_create_campaign_raw_response.json`
3. Assert the timestamps align; discrepancies indicate that the snapshot was regenerated or edited after the original creation call.

**Expected (Fail Condition)**
- Snapshot `created_at` reads `2025-10-01T09:35:08.807269+00:00`.
- Raw response timestamp reads `2025-10-01T09:34:37.715317+00:00`.
- Differing values flag the evidence as synthesized rather than a direct database re-query.

### 3. Validate Persistence Flags
1. Inspect world/NPC population flags in the snapshot:
   `jq '.world_state.world_data_populated, .world_state.npc_data_populated' /tmp/campaign_kaM205AyUZdyFweimQhY_adventure_started.json`
2. Review the claimed evidence narrative (e.g. `worldarchitect_mcp_evidence_package.md`) for statements that world/NPC data persisted. Document any contradictions.

**Expected (Fail Condition)**
- Flags resolve to `false`, contradicting claims of populated world/NPC data.

### 4. Confirm MCP Runtime Consistency
1. List active MCP processes:
   `ps aux | grep worldarchitect-mcp | head`
2. Compare live process list with the documented PID(s) in `worldarchitect_mcp_complete_testing_summary.md`.

**Expected (Fail Condition)**
- Live output shows at least two active processes (e.g. PIDs `31472` and `37207`) while the summary cites only one, proving runtime drift from documented evidence.

## Results
- Test currently **fails**: export artifact is truncated, timestamps differ, world/NPC flags remain false, and runtime evidence is inconsistent with live state.

## Follow-Up Actions
1. Provide an export serializer that writes human-readable text without escaped newlines and includes all interactions.
2. Deliver raw Firebase/Gemini logs to substantiate API call counts.
3. Re-run MCP process inspection immediately before packaging evidence to ensure PID alignment.
