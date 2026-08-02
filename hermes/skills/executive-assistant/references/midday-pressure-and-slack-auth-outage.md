# Midday EA Sweep: Critical Machine Pressure and Slack Credential Outage

## Reusable lessons

### Treat load, disk, and swap as one pressure signal
A load-average spike is much more actionable when paired with storage and swap evidence. Run and report all three together:

```bash
uptime
df -h /System/Volumes/Data
sysctl vm.swapusage
```

Escalate prominently when several dimensions are red at once, such as very high load, Data volume at or above 95%, and swap nearly exhausted. Do not bury this under routine system status.

### Aggregate processes by command family
A top-CPU snapshot can miss the real cause when dozens of individually modest workers are duplicated. Add a family-count probe:

```bash
ps -Ao command | sort | uniq -c | sort -nr | head -20
```

Use this to identify restart storms and duplicated MCP/agent families. Report counts and command families; do not kill or modify them during an EA sweep unless a separate remediation workflow authorizes it.

### Validate every Slack credential path before declaring coverage
When Slack reads fail, probe each configured identity independently and retry each authentication check twice:

- `HERMES_SLACK_BOT_TOKEN`
- `SLACK_MCP_XOXB_TOKEN`
- `SLACK_USER_TOKEN`
- `SLACK_MCP_XOXP_TOKEN`

For every token, run `auth.test` twice and a cheap `conversations.list?limit=1` cross-check. If every path remains `invalid_auth`, label the Slack section **coverage blocked**. Do not claim there are no action items, and do not carry an older Slack queue forward as current fact unless live history can revalidate it.

### Distinguish cron execution health from delivery and source coverage
A cron row showing `Last run: ... ok` proves only that the sweep process exited successfully. It does not prove:

- Slack source channels were readable,
- DM dedup was performed,
- the final message was delivered.

State these gates separately. The scheduler-delivered final response can remain the fallback artifact while Slack is unavailable.

### Calendar CLI compatibility probe
If the documented calendar invocation returns a 404 or flag mismatch, inspect `gog calendar events --help` and use the currently supported all-calendar form. In the observed CLI this was:

```bash
gog calendar events -a $USER@gmail.com --all \
  --from 'YYYY-MM-DDT00:00:00-07:00' \
  --to 'YYYY-MM-DDT00:00:00-07:00' \
  --max 100 --json --results-only
```

After retrieval, filter events by local start date. Multi-week events may legitimately overlap the window, while unrelated rows outside the local-date range should not enter the brief.

## Output discipline

When Slack coverage is blocked but other sources contain material changes:

1. Publish the partial brief through the cron response rather than returning `[SILENT]`.
2. Put newly discovered human deadlines first.
3. Put simultaneous load/disk/swap pressure next.
4. Explicitly label Slack action-item coverage as unverified.
5. Archive the exact brief locally with command-level proof.
