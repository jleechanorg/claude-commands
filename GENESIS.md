## Successful Patterns
- `claude -p genesis_primary_scheduler --fast` with explicit SINGLE FOCUS messaging kept bench_cmd runs linear and avoided scheduler retries.
- `claude -p genesis_execution --direct` followed immediately by `ls -a` satisfied SEARCH-FIRST gates without extra chatter.
- Running `rg --files -g "GENESIS.md" genesis` before edits confirmed the target file location and stopped path-related execution errors.
- Executing `npm test -- --runInBand` immediately after dependency sync surfaced ESM configuration gaps while fixes were still cheap.

## Avoid These Patterns
- Feeding multi-goal prompts to `claude -p` triggered validation loops and stalled progress on bench_cmd.
- Leaving transpiled `__tests__/server.test.js` artifacts beside TypeScript sources caused Jest import syntax failures.
- Reusing cached `git diff` output after a clean status re-triggered QUALITY RETRY checks for perceived placeholders.
- Calling remote genesis_context endpoints without local fallbacks kept returning 404s and wasted an iteration.

## Genesis Optimizations
- Trim earlier transcripts into <1800-token bullet briefs before scheduler calls to preserve FastMCP details while staying under context limits.
- Capture a single directory snapshot (`ls -a`) and reuse it for planning instead of reissuing exploratory commands.
- Defer diff-review or summarizer helpers until after the primary task is finished so ONE ITEM PER LOOP stays intact.
- Always run SEARCH-FIRST (e.g., `rg 'Priority Item' goals/...`) before editing; skipping it violated Genesis gates and prompted retries.
- Confirm the SINGLE FOCUS statement verbally before sending any scheduler prompt so the validator accepts the request on the first pass.
