# GitHub Actions Runner Crontab Configuration

Example crontab for running GitHub Actions self-hosted runners with maximum reliability.

## Files

- `crontab-example.txt` - Sanitized production crontab (tokens redacted, includes organization-specific jobs)
- `monitor.sh` - Runner health check and auto-restart script (referenced by crontab)

## Runner Automation Jobs

### 1. Heartbeat Job (HOURLY)
```bash
0 * * * * pgrep -f "Runner.Listener.*$HOME/actions-runner" > /dev/null || \
  (cd ~/actions-runner && ./run.sh --once >> ~/actions-runner/heartbeat.log 2>&1)
```

**Purpose:** Prevents GitHub from auto-deleting inactive runner registrations

**How it works:**
- Runs every hour at :00
- Checks if runner already running (prevents conflicts)
- Executes one job cycle to ping GitHub if not running
- Keeps registration active (GitHub deletes after 30+ days inactivity)

### 2. Monitor Job (Every 15 Minutes)
```bash
*/15 * * * * ~/actions-runner/monitor.sh
```

**Purpose:** Auto-restart runner if it crashes

**How it works:**
- Runs every 15 minutes
- Checks if `Runner.Listener` process is running
- Attempts restart via `svc.sh start` or `run.sh` if down
- Logs to `~/actions-runner/monitor.log`

## Protection Layers

Three redundancy layers:

1. **LaunchAgent** (Primary) - Persistent macOS service
2. **Monitor Cron** (Every 15m) - Auto-restart if crashed
3. **Heartbeat Cron** (Hourly) - Keep-alive ping

## Installation

```bash
# 1. Copy monitor script to runner directory
cp self-hosted/scripts/monitor.sh ~/actions-runner/
chmod +x ~/actions-runner/monitor.sh

# 2. Setup runner with redundancy
./self-hosted/scripts/setup-github-runner-redundant.sh

# 3. Verify cron jobs
crontab -l | grep "GitHub Actions Runner"

# 4. Monitor logs
tail -f ~/actions-runner/monitor.log
tail -f ~/actions-runner/heartbeat.log
```

## Clock Drift Workflow

To run system clock ahead (e.g., +10 minutes):

```bash
# 1. Setup with synced clock
./self-hosted/scripts/setup-runner-with-drift.sh

# 2. Restore your drift
./self-hosted/scripts/restore-clock-drift.sh
```

Runner continues working with drift because registration uses correct timestamps and session tokens aren't affected by subsequent drift.

## Troubleshooting

**Runner offline:**
```bash
cd ~/actions-runner && ./svc.sh status
tail -30 ~/Library/Logs/actions.runner.*/stdout.log
./svc.sh stop && ./svc.sh start
```

**Cron not running:**
```bash
crontab -l
tail -f ~/actions-runner/monitor.log
```

## Security

- Never commit actual tokens (example file redacts all sensitive data)
- Use `gh auth login` for secure credential storage
- Cron inherits `gh` CLI authentication automatically

## References

- [GitHub Self-Hosted Runners](https://docs.github.com/en/actions/hosting-your-own-runners)
- [Setup Scripts](./setup-github-runner-redundant.sh)
- [Clock Drift Support](./setup-runner-with-drift.sh)
