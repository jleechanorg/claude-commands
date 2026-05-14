#!/bin/bash
# Reload a launchd plist safely — detects user agent vs system daemon and uses correct command.
# Usage: ao-launchd-reload.sh <path-to-plist>
set -euo pipefail

PLIST="$1"
if [[ ! -f "$PLIST" ]]; then
  echo "ERROR: plist not found: $PLIST" >&2
  exit 1
fi

LABEL=$(PlistBuddy -c "Print :Label" "$PLIST" 2>/dev/null || \
  sed -n 's/.*<key>Label<\/key>.*<string>\([^<]*\)<\/string>.*/\1/p' "$PLIST" | head -1)

if [[ -z "$LABEL" ]]; then
  echo "ERROR: could not read Label from $PLIST" >&2
  exit 1
fi

# Determine if user agent (~/Library/LaunchAgents) or system daemon
if [[ "$PLIST" == "$HOME/Library/LaunchAgents/"* ]]; then
  echo "[user agent] Using launchctl bootout gui/$(id -u)/$LABEL"
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
  launchctl load "$PLIST"
elif [[ "$PLIST" == "/Library/LaunchDaemons/"* ]]; then
  echo "[system daemon] Using sudo launchctl unload"
  sudo launchctl unload "$PLIST" 2>/dev/null || true
  sudo launchctl load "$PLIST"
else
  echo "ERROR: plist must be in ~/Library/LaunchAgents/ or /Library/LaunchDaemons/" >&2
  exit 1
fi

echo "OK: $LABEL reloaded"
