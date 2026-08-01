---
name: execute_code bashrc env-isolation dual-probe
applies_to: cli-env-var-verification (failure class: dual-probe trap)
last_verified: 2026-07-28
---

# execute_code bashrc env-isolation dual-probe — worked example

## The trap (one paragraph)

The Hermes `execute_code` tool runs a clean Python subprocess that does **NOT** source `~/.bashrc`. Any secret defined via `export VAR=...` in `~/.bashrc` (e.g. `HERMES_SLACK_BOT_TOKEN`, `GH_TOKEN`, `MINIMAX_API_KEY`, `ANTHROPIC_API_KEY`) returns **empty string** from `os.environ.get(VAR)` even though `terminal()` in the same session sees the var fine. The same trap family as the `bashrc-profile-xapp-drift-blocks-launchd` memory but for inline `execute_code` rather than launchd plist jobs.

A single `execute_code` probe therefore returns `len = 0` and the natural agent reaction is to declare the token broken, the workspace blocked, the API call impossible — when in fact `bash -c 'source ~/.bashrc && ...'` works perfectly from the same session.

## Symptom pattern

```
# Agent probe:
import os
print(os.environ.get('HERMES_SLACK_BOT_TOKEN'))
# -> '' (empty string)

# Agent conclusion (WRONG):
"# Slack token is invalid_auth, this run is partial"

# Reality (terminal probe):
bash -c 'source ~/.bashrc && echo "$HERMES_SLACK_BOT_TOKEN"'
# -> '[REDACTED_SLACK_TOKEN]' (58 chars)
bash -c 'source ~/.bashrc && curl -fsS -X POST \
    https://slack.com/api/auth.test \
    -H "Authorization: Bearer $HERMES_SLACK_BOT_TOKEN"'
# -> {"ok":true,"url":"https://jleechanai.slack.com/",...}
```

User reply: "You def should have the slack tokens check bashrc and if it works see why you got confused dd" then "Why did you mess it up? Run /harness --fix first".

## The dual-probe recipe (mandatory before any "blocked on token" claim)

```bash
# Probe 1: bash-sourced terminal (authoritative for bashrc-exported vars)
bash -c "source ~/.bashrc 2>/dev/null; \
  echo \"HERMES_SLACK_BOT_TOKEN=\${HERMES_SLACK_BOT_TOKEN:+set(\${#HERMES_SLACK_BOT_TOKEN})}\"; \
  echo \"GH_TOKEN=\${GH_TOKEN:-MISSING}\"; \
  echo \"MINIMAX_API_KEY=\${MINIMAX_API_KEY:+set(\${#MINIMAX_API_KEY})}\""
```

```python
# Probe 2: execute_code Python subprocess (clean env, no bashrc)
import os
for k in ("HERMES_SLACK_BOT_TOKEN","GH_TOKEN","MINIMAX_API_KEY","ANTHROPIC_API_KEY","SLACK_USER_TOKEN"):
    print(f"{k}: {'SET' if os.environ.get(k) else 'MISSING'}")
```

**Interpretation:**
- Both `set(N)` (terminal) and `SET` (execute_code) → var works in both, no trap. Probe as usual.
- Terminal `set(N)`, execute_code `MISSING` → **dual-probe trap**. The token is fine. Run the live call via bash-sourced shell.
- Both `MISSING` → var genuinely missing from this host. Diagnose separately (out of scope of this skill).
- Terminal `MISSING`, execute_code `SET` → likely the var was set inline via `os.environ[...]` injection from a prior shell; rare. Verify the var is in `~/.bashrc` directly.

## For live API calls when the trap fires

Route the call through bash-sourced shell rather than execute_code:

```bash
# Works even when execute_code says the var is empty:
bash -c "source ~/.bashrc 2>/dev/null && \
  curl -fsS -X POST 'https://slack.com/api/conversations.history' \
    -H \"Authorization: Bearer \$HERMES_SLACK_BOT_TOKEN\" \
    -d 'channel=C09GRLXF9GR' -d 'limit=10' \
  | python3 -m json.tool"
```

Or in Python via execute_code by re-exporting in-process:

```python
import os, subprocess
# Pull the token from bashrc-sourced bash:
tok = subprocess.check_output(
    ["bash","-c","source ~/.bashrc 2>/dev/null && echo -n $HERMES_SLACK_BOT_TOKEN"],
    text=True
)
print(f"got token of length {len(tok)}")
# Now use it directly without re-exporting to env:
import urllib.request, urllib.parse, json
req = urllib.request.Request(
    "https://slack.com/api/auth.test",
    headers={"Authorization": f"Bearer {tok}"},
)
print(json.loads(urllib.request.urlopen(req, timeout=10).read()))
```

## Other environments with the same trap family

Apply the same dual-probe principle before declaring any var "missing" in:

| Environment | Probe bashrc-sourced? | Probe clean env? | Common trap |
|---|---|---|---|
| `execute_code` Python | yes (terminal) | yes (execute_code) | THIS skill |
| `launchd` plist jobs | yes (via `launchctl print`) | check plist `EnvironmentVariables` | `launchd-env-wrapper.sh` exists for this |
| `.profile`-sourced shell | check `~/.profile` | check `~/.bashrc` | vars in one file invisible to the other |
| `crontab -e` env | bashrc-sourced bash | check `crontab -l` headers | cron doesn't source dotfiles |
| `tmux`/`screen` session started from launchd | `tmux show-env -g \| grep VAR` | check launchd plist | tmux started by SSH inherits shell env; tmux started by resurrect may not |

## Canonical fix locations (harness)

The trap is encoded in three layers so future sessions auto-fire the recipe:

1. **Memory** — `execute_code env-isolation` entry (replaced the stale `skillify_check.py rc=2` entry on 2026-07-28)
2. **SOUL.md** — `## COMMIT: dual-probe-secrets` block (line 87), refuses "blocked on token" claims until both probes run
3. **`~/.hermes/skills/roadmap/SKILL.md`** — Step 2.5.f "Bashrc-sourced secret dual-probe gate"
4. **Test** — `~/.hermes/tests/test_execute_code_env_isolation.py` (3 PASS, 1 skip-on-this-host)

## Verification (last run 2026-07-28 18:48Z)

```
$ bash -c 'source ~/.bashrc && echo "${HERMES_SLACK_BOT_TOKEN:+set(${HERMES_SLACK_BOT_TOKEN:0:5}…${HERMES_SLACK_BOT_TOKEN: -5})}"'
xoxb-…kcd2

$ env -i python3 -c "import os; print('SET' if os.environ.get('HERMES_SLACK_BOT_TOKEN') else 'MISSING')"
MISSING

$ python3 -m pytest ~/.hermes/tests/test_execute_code_env_isolation.py -v
3 passed, 1 skipped in 0.12s

$ bash -c 'source ~/.bashrc && curl -fsS -X POST https://slack.com/api/auth.test -H "Authorization: Bearer $HERMES_SLACK_BOT_TOKEN"'
{"ok":true,"url":"https://jleechanai.slack.com/","team":"$USER AI","user_id":"U0A4G7LDJ4R",...}

$ bash -c 'source ~/.bashrc && for c in C09GRLXF9GR C0AH3RY3DK6 C0AJQ5M0A0Y C0ALSKLU9KM; do
    curl -fsS -G "https://slack.com/api/conversations.history" \
      -H "Authorization: Bearer $HERMES_SLACK_BOT_TOKEN" \
      -d "channel=$c" -d "limit=1" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get(\"channel\",\"?\"), \"ok=\", d.get(\"ok\"))"
  done'
C09GRLXF9GR ok= True
C0AH3RY3DK6 ok= True
C0AJQ5M0A0Y ok= True
C0ALSKLU9KM ok= True
```

## Anti-patterns to refuse

- ❌ "I probed the var, it's empty, so the token is broken" — does NOT follow from one probe. Run the dual-probe.
- ❌ "The bashrc-sourced shell is different from this session, so it might be a different token" — no, the token IS the same one; only the env-loading mechanism differs.
- ❌ "I'll add `source ~/.bashrc` to my Python script" — works but masks the trap. The trap is that agents don't realize they need to. The dual-probe rule keeps the trap visible.
- ❌ "Just paste the token inline as `os.environ['HERMES_SLACK_BOT_TOKEN'] = 'xoxb-...'`" — defeats the `outbound-secret-publication-gate` (token must not appear in agent-readable form). Use bash-sourced shell instead.

## Related pitfalls

- **`bashrc-profile-xapp-drift-blocks-launchd` memory** — same trap family for launchd plist jobs. Wrapper script `_extract_bashrc_var()` in `~/.hermes/scripts/launchd-env-wrapper.sh` is the launchd-side mitigation.
- **`streaming-utf8-mojibake` skill** — Python requests-based LLM providers can silently corrupt secrets in transit if env var is wrong-shape. Different failure class, same diagnostic discipline (probe both shell and Python).
- **`runtime-activation-claim` skill** — same "verify before claiming" pattern but for end-state claims (gateway "Up N minutes" is not the same as PR-merged-or-not).