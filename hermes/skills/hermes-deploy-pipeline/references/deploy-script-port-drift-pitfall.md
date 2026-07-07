# Deploy Script Port-Drift Pitfall (2026-06-12)

**Symptom:** `~/.hermes/scripts/deploy.sh` exits with "Gateway did not come
up on port N within Ns" — but the gateway IS up and healthy, just on a
different port than the script polls.

**Root cause:** the deploy script hard-codes `PROD_PORT` (e.g. `8643`)
but `~/.hermes_prod/config.yaml` actually says `port: 8642` (or whatever
the staging-vs-prod drift settled on). When the staging config changed
and the prod config was not synced, the two trees drifted on the port
field, and the script polls the wrong port.

**How to diagnose (3-step "is the gateway actually up?" recipe):**

```bash
# 1. What port is the prod config requesting?
grep -A1 "^port:" ~/.hermes_prod/config.yaml | head -3

# 2. What port is something actually bound to?
lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null | grep -E "hermes|python|node" | head -5
# Or more targeted:
lsof -nP -p "$(pgrep -f 'run_agent.py' | head -1)" 2>/dev/null | grep -E "TCP|IPv" | head -10

# 3. Curl the actual port the config says
curl -sf --max-time 3 http://127.0.0.1:$(grep -E "^port:" ~/.hermes_prod/config.yaml | awk '{print $2}')/health
# Expect: {"status":"ok","platform":"hermes-agent"}
```

**If the gateway is healthy on a different port than the deploy script
expects:**

- The deploy IS functionally complete — script's port check is a false
  negative.
- To make the script correct, read `PROD_PORT` from
  `~/.hermes_prod/config.yaml` instead of hard-coding it. The
  authoritative source is the config file the gateway itself reads.
- Until the script is patched, treat any "Gateway did not come up on
  port 8643" message as **"check 8642 next, then grep config.yaml"**
  rather than "deploy failed."

**Why the false negative is dangerous:**

The deploy script's failure message is alarming ("did not come up
within 30s"). A future operator might roll back, restart in a loop, or
diff staging vs prod unnecessarily — all wasted work. The gateway is
fine. The script is wrong.

**Related: `launchctl print` pid extraction pitfall**

The deploy script's pid-extraction step is:
```bash
PID="$(launchctl print "${DOMAIN}/${LABEL}" 2>/dev/null | grep '^ *pid' | awk '{print $3}' || true)"
```
This requires `^ *pid` — a line starting with whitespace then `pid`.
On some `launchctl print` output formats the line is `pid = 25373`
(with spaces around the `=`), which DOES match `^ *pid`. But on
others it's `state = running` with no pid line at all (when the job
is loaded but not running), and the script proceeds to "wait for
8643" with no kill. That's the case in the 2026-06-12 incident:
the script said "No running pid found" (correct), then the old
gateway was NEVER killed, so the new gateway attempt couldn't bind.
The fix: after extracting an empty PID, restrict termination to the launchd-managed gateway PID or add a command-line check (e.g., verify that the process command line actually contains 'hermes-agent') before killing, ensuring that only the Hermes-owned process is stopped and preventing arbitrary listener termination.

**Provenance / worked example:** 2026-06-12, deploy of SOUL.md
COMMIT `slack-channel-agentf-maps-to-local-agentf`. Script reported
failure at Stage 4 ("port 8643 within 30s"). Actual state: prod
gateway on `127.0.0.1:8642` returning
`{"status":"ok","platform":"hermes-agent"}`, SOUL.md change
`111c5ae0db` in `~/.hermes_prod/SOUL.md`, gateway processing
messages. Deploy was functionally complete; the script's port check
was the bug.
