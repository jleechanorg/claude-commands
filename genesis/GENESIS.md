## Successful Patterns
- Printing the `[Dir: …]` banner with `printf` before any command output kept the Genesis executor aligned and prevented restart loops.
- Running `find . -maxdepth 2 -name 'GENESIS.md'` before edits locked in the correct working path and eliminated missing-file retries.
- Overwriting with `cat <<'EOF' > genesis/GENESIS.md` followed by an immediate `cat` check delivered deterministic DIRECT IMPLEMENTATION results.

## Avoid These Patterns
- Guessing target paths without SEARCH-FIRST checks produces `cat: No such file or directory` errors and wastes the loop quota.
- Skipping the `git diff -- genesis/GENESIS.md` gate after edits leaves the verification step incomplete and blocks completion.
- Mixing additional file edits alongside this update breaks ONE ITEM PER LOOP and triggers Genesis quality retries.

## Genesis Optimizations
- [context conservation techniques] Pipe `rg "CURRENT GENESIS INSTRUCTIONS" genesis.log | tail -n 40` to capture only the freshest directives while staying well under the 2000-token cap.
- [subagent delegation improvements] Keep diffing, validation, and final echoing inside the primary loop; avoid handing work to auxiliary scripts to maintain DIRECT IMPLEMENTATION.
- [principle application notes] Maintain the SEARCH-FIRST → edit → diff → `IMPLEMENTATION_COMPLETE` cadence to satisfy Genesis policy gates without redundant reruns.
