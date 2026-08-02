# CLI flag verification before shipping launchd-driven scripts

**Verify that every CLI flag a `~/.hermes/scripts/*.sh` relies on actually
exists in the installed CLI version — BEFORE the script is added to a
launchd plist and started firing unattended.**

The fix shipped 2026-07-21 in `cron-backup-sync.sh` (PRs [693f0f1876](https://github.com/jleechanorg/jleechanclaw/commit/693f0f1876)
+ [996be8cf81](https://github.com/jleechanorg/jleechanclaw/commit/996be8cf81))
is the canonical case study.

---

## The failure pattern (do NOT reproduce this)

1. A `~/.hermes/scripts/<name>.sh` calls `hermes cron list --json`
2. The author assumed `--json` exists because "every modern CLI
   supports `--json`".
3. It doesn't. argparse rejects the flag, prints
   `unrecognized arguments: --json`, exits 2.
4. The script's `CRON_JSON=$(hermes cron list --json 2>/dev/null) || true`
   swallows the failure silently — `CRON_JSON` is empty string.
5. Downstream `python3 -c "import json, sys; json.loads(...)"` fails on
   empty input. The script's `|| CRON_JOBS="$CRON_JSON"` falls back to
   the empty JSON.
6. `TOTAL=$(...python...) || echo "?"` and `ENABLED=$(...python...) || echo "?"`
   compute `?` placeholders.
7. The Slack message template `"Cron Backup: no changes. Total: $TOTAL jobs ($ENABLED enabled)."`
   renders as `Cron Backup: no changes. Total: ? jobs (? enabled).`
8. **For 6 days (2026-07-15 → 2026-07-21)** every Mon-Fri 08:25 PT
   `ai.hermes.schedule.cron-backup-sync.plist` posted that exact broken
   message to `#ai-general`.

User-visible signal: the launchd job appeared healthy (`exit 0`, log
file generated, Slack message delivered), so nobody noticed for 6
days. The user only spotted it because they were reading the chat
scrolling back through their own messages.

---

## The durable fix — 4 pre-deploy checks

Run these BEFORE adding a `scripts/<name>.sh` to a `launchd/<name>.plist.template`,
or BEFORE deploying an updated script via `scripts/deploy.sh`. If any
check fails, fix the script (or pin the CLI version) — do not deploy
the broken script.

### Check 1: confirm every flag the script uses is in the installed CLI's `--help`

```bash
# Replace <subcommand> and --<flag> with whatever the script invokes.
# Example for cron-backup-sync.sh's bug:
hermes cron list --help   # → confirms `--all` exists, `--json` does NOT

# Repeat for every distinct (subcommand, flag) pair in the script.
grep -nE '^\s*[A-Z_]+=\$\(hermes ' scripts/<name>.sh | \
    sed -E 's/.*hermes ([a-z]+) ([a-z]+) (--[a-z-]+).*/hermes \1 \2 \3/'
```

If a flag is missing, do not deploy. The script must either:

- Drop the flag (use the default output)
- Parse the table output instead (see Check 2)
- Pin the CLI version that had the flag (heavier; usually wrong trade-off)

### Check 2: if the script parses CLI output via `python3 -c`, dry-run it

```bash
# Reproduce what the script does, manually:
hermes cron list --all > /tmp/list.out
python3 -c '<parser script>' < /tmp/list.out | python3 -m json.tool
# Expect a valid pretty-printed JSON. Empty output / json.JSONDecodeError
# = script silently fails at runtime.
```

### Check 3: assert the script's computed variables are real numbers

Any shell variable that gets interpolated into a Slack / email / log
message MUST be a number or string, never `?` / `0` / `""` as a
default sentinel. If the parse fails, the script MUST exit with a
non-zero status, not gracefully degrade to a placeholder.

```bash
# Anti-pattern (the bug):
TOTAL=$(...python... || echo "?")

# Right pattern: fail loud OR emit a concrete empty value
TOTAL=$(...python... 2>/dev/null) || { log "ERROR: failed to compute TOTAL"; exit 1; }
TOTAL=${TOTAL:-0}  # empty -> 0, with the error already logged
```

### Check 4: end-to-end smoke run before adding the script to a plist

```bash
# Run the script the way launchd would (stripped PATH, no .bashrc sourced):
env -i HOME="$HOME" PATH=/usr/bin:/bin /usr/bin/bash "$HOME/.hermes/scripts/<name>.sh"
# Watch the script's log file (the plist's StandardOutPath) for the
# expected output. Verify the Slack message via the chat history.

# If the script writes a JSON file, check it's valid JSON and
# contains the expected rows:
python3 -m json.tool $HOME/.hermes/docs/context/<output>.json | head -20
```

---

## Companion: write a regression test alongside the script

For any launchd-driven script that has a non-trivial parser, ship a
test in `tests/test_<script_name>.py` that:

1. **Asserts the CLI flags the script depends on still exist.** Catches
   hermes upgrades that drop a flag without warning. Example from
   `tests/test_cron_backup_sync.py`:

   ```python
   def test_json_flag_is_rejected(self):
       out = subprocess.run(["hermes", "cron", "list", "--json"], capture_output=True, text=True)
       self.assertNotEqual(out.returncode, 0)
       self.assertIn("unrecognized", (out.stderr + out.stdout).lower())
   ```

2. **Asserts the parser's row count matches the upstream CLI's
   authoritative count** (e.g. `hermes cron status` "12 active job(s)").
   Catches schema drift in the CLI's table layout.

3. **Asserts the script's output template NEVER contains literal `?`
   placeholders.** This is the user-visible regression check — if the
   placeholder `?` sneaks back into the source, the test fails loudly.

The test file shell (`tests/test_cron_backup_sync.py`,
[996be8cf81](https://github.com/jleechanorg/jleechanclaw/commit/996be8cf81))
is the reference template. Pattern:

```python
"""Regression tests for ~/.hermes/scripts/<script>.sh.

Background (<date>): one-line root cause + symptom that motivates
these tests. Lock the contract here so the next script refresh cannot
silently regress.
"""

from __future__ import annotations
import json
import re
import subprocess
import unittest
from pathlib import Path

SCRIPT = Path.home() / ".hermes" / "scripts" / "<script>.sh"


class TestCLIFlagContract(unittest.TestCase):
    """Pins the CLI flags the script depends on."""

    def test_required_flag_exists(self):
        out = subprocess.run([...CLI...], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0)  # flag accepted
        self.assertNotIn("unrecognized", ...)


class TestParserContract(unittest.TestCase):
    """Mirrors the inline python in the script — keep regex in sync."""

    @staticmethod
    def _parse(raw: str) -> dict: ...

    def test_parser_matches_upstream_count(self):
        raw = subprocess.run([...CLI...], capture_output=True, text=True).stdout
        result = self._parse(raw)
        # e.g. active count must match `hermes cron status` "12 active job(s)"
        ...


class TestOutputContract(unittest.TestCase):
    """User-facing output never contains sentinel placeholders."""

    def test_template_has_no_question_marks(self):
        src = SCRIPT.read_text()
        self.assertNotIn("Total: ?", src)  # regression guard
        ...
```

---

## When to apply these checks

| Script type | Check 1 + 2 | Check 3 + 4 | Regression test |
|---|---|---|---|
| Backup / sync (writes JSON to git) | yes | yes | yes |
| Notification (posts to Slack / email) | yes | yes | optional |
| Read-only audit (logs result, no posting) | yes | yes | optional |
| One-shot CLI wrapper (no launchd) | yes | no | no |

Launchd-driven scripts get the full battery because they run
unattended and a silent bug can persist for weeks. One-shot scripts
get Check 1 + 2 only — a missed flag fails loud immediately.

---

## Cross-references

- `references/staging-dirty-surgical-sync.md` — different failure mode
  (fix is on `origin/main` but deployed file is stale). Does NOT apply
  here; the script-as-written was always broken.
- `references/launchd-env-injection-and-wrapper.md` — other launchd
  failure mode (PATH stripping, env vars not injected). Composable
  with this reference.
- `software-development/cli-env-var-verification` — sibling skill for
  env-var verification; the same "verify before assuming" failure
  pattern applies to flags too.
- `cli-env-var-verification` → "Adjacent patterns" — reuses the
  4-signal protocol for non-flag CLI behavior.
