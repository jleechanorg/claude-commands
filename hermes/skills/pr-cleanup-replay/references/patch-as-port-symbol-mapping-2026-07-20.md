# patch-as-port: external patch targets a different module split

**One-line:** A patch generated from a sibling repo (e.g. snap_factory) applied to an upstream fork (e.g. dark-factory) whose module split has been refactored. The `sed`-rename recipe in the upstream GUIDE only works when the module is renamed verbatim — not when the symbols have been split into multiple files.

## Verified incident — 2026-07-20, infra03q-inpipeline-receipt.patch

**Patch source:** `snap_factory` HEAD (internal Snap GHE mirror).
**Patch target (assumed by user):** `jleechanorg/dark-factory` (the public/personal fork referenced in the GUIDE).

**Upstream module split at the time of port:**

| snap_factory (patch source) | jleechanorg/dark-factory (port target) | Notes |
|---|---|---|
| `snap_factory/engine.py` 1932-line `AttractorEngine` class | `runner/engine.py` 96-line re-export shim + `runner/engine_*.py` modules + `runner/handler_*.py` modules | Refactored in PR #77 (file-ownership-map); `engine.py` is no longer the LLM dispatch |
| `snap_factory/engine.py::_run_llm` | `runner/handler_codergen.py::_codergen` | The LLM dispatch — same role, different name, different location |
| `snap_factory/engine.py::_finalize_review_status` | (no upstream equivalent) | Net-new — port to `runner/handler_verdict.py` |
| `snap_factory/engine.py::_reproduction_receipt_gaps` | (no upstream equivalent) | Net-new — port to `runner/handler_verdict.py` |
| `snap_factory/engine.py::_has_final_status_contract` | (no upstream equivalent) | Net-new — port to `runner/handler_verdict.py` |
| `tests/test_engine.py::TestLLMNodeDispatch` hunk 2738 | `tests/test_engine.py::TestLLMNodeDispatch` (different line number, more methods) | Inline add to existing class |
| `tests/test_review_reproduction_receipt.py` (net-new) | `tests/test_review_reproduction_receipt.py` (net-new) | Verbatim port |
| `docs/ungameable-cold-gate.md` (net-new) | `docs/ungameable-cold-gate.md` (net-new) | Verbatim port |

**GUIDE's recipe:** `sed -e 's|snap_factory/engine.py|dark_factory/engine.py|g'`. **Result if blindly applied:** patch still fails because `dark_factory/engine.py` doesn't exist in this checkout (it's `runner/engine.py` + `runner/handler_codergen.py`); the symbols would have to be **ported** to different modules, not just renamed.

## Detection recipe (before writing any code)

```bash
# 1. Confirm the patch actually applies to the target repo
cd <target-repo>
git apply --check /path/to/external.patch
# Expect errors like:
#   error: snap_factory/engine.py: No such file or directory
#   error: patch failed: tests/test_engine.py:2738

# 2. List every file the patch touches
grep -nE '^diff --git' /path/to/external.patch | head -30

# 3. For each path, ask: does it exist in the target repo? Where is the
#    corresponding symbol implemented?
for path in $(grep -oE '^diff --git a/([^ ]+) b/[^ ]+' /path/to/external.patch | sed 's|.*a/||'); do
  echo "=== $path ==="
  git -C <target-repo> cat-file -e "HEAD:$path" 2>/dev/null \
    && echo "EXISTS in target" \
    || echo "MISSING in target"
done

# 4. For each function/class insertion (look for `@@ -<line>,<count> +<line>,<count> @@`),
#    extract the function name and find the upstream equivalent:
grep -A2 '^@@ ' /path/to/external.patch | grep -E '^@@.*def |^@@.*class ' | head -20
```

## Operational rules

1. **Always `git apply --check` from inside the target repo**, not from `$HOME` or another parent directory. From a parent dir, missing-file errors are suppressed as warnings and `git apply --stat` returns 0 even when `git apply --check` would fail.

2. **Build the symbol-mapping table BEFORE writing any code.** Each `def <name>` line in the patch → row in the table with (a) target file:line, (b) what the new function does, (c) what existing upstream function it parallels (or "net-new — no upstream equivalent").

3. **Surface the symbol-mapping table to the user before opening the PR.** The user explicitly approved this kind of port with "if you understand the goals" — but they can't verify the port without seeing the table.

4. **When the patch has a `tests/test_*.py` hunk on an existing class** (e.g. `tests/test_engine.py::TestLLMNodeDispatch`), add new methods inline on the existing class — do NOT create a parallel test file just because the patch's hunk header suggests a new file.

5. **When the patch has a `docs/<name>.md` hunk on a file that doesn't exist yet**, port the doc verbatim — docs have no path-dependent content unless they cite module names.

## Worked example — 2026-07-20 infra03q port plan

8-stage execution plan produced from this discipline (committed in Slack thread `C09GRLXF9GR/p1784582518.247009`):

1. Fresh worktree from `origin/main` at `infra03q-inpipeline-receipt-upstream-port` (no dirty branch carry-over).
2. Write `runner/handler_verdict.py` additions (`_finalize_review_status`, `_reproduction_receipt_gaps`, `_has_final_status_contract`) + re-export from `runner/handlers.py`.
3. Wire the re-derivation into `runner/handler_codergen.py::_codergen::_finalize` for gating-review-shape nodes only.
4. Port `tests/test_review_reproduction_receipt.py` verbatim + extend `tests/test_engine.py::TestLLMNodeDispatch` with 3 new tests + 1 fixture fix.
5. Port `docs/ungameable-cold-gate.md` verbatim.
6. `/advice` Reviewer B + C fan-out (Reviewer A is rate-limited until 8pm PT).
7. `pytest tests/ -q` (full suite, expect green).
8. `git commit` + `git push -u origin HEAD:infra03q-inpipeline-receipt-upstream-port` + `gh pr create`.

Single tap from user: GO / SCOPE DOWN / SCOPE UP. Default GO + also file the watchdog bug as a separate bead.

## Cross-references

- `pr-cleanup-replay` SKILL.md Phase -2 — the umbrella this reference belongs to
- `references/git-secret-guard-blocks-main-derived-pushes-2026-07-17.md` (sibling) — covers a different "patch from elsewhere" failure mode (history-scanned secrets)
- `references/bastion-watchdog-handoff-user-mismatch-2026-07-20.md` (sibling under `superpowers-cloud-build`) — covers the broken `/super` dispatch path that this port had to route around

## Source provenance

Verified 2026-07-20 on Slack thread `C09GRLXF9GR/p1784582518.247009`. Operator said "lets just adapt it to this repo if you understand the goals." Pattern: external patch from `snap_factory` (1932-line AttractorEngine class) applied to `jleechanorg/dark-factory` (96-line re-export shim + handler split). The agent must NOT use `git apply --stat` from a parent dir as the go/no-go gate — always `git apply --check` from inside the target repo. The agent must NOT blindly sed the patch — build the symbol-mapping table first.