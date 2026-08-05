#!/usr/bin/env bash
# install_cmux_resume_watchdog.sh
# Install / reinstall the cmux-resume-watchdog daemon on this machine.
# Re-run after editing the Python script.

set -euo pipefail

SKILL_DIR="${SKILL_DIR:-$(cd "$(dirname "$0")" && pwd)}"
LIBEXEC_DIR="${HOME}/.local/libexec/cmux-resume-watchdog"
PLIST_LABEL="com.$USER.cmux-resume-watchdog"
PLIST_SRC="${SKILL_DIR}/com.$USER.cmux-resume-watchdog.plist"   # @HOME@-templated
PLIST_RENDERED="${SKILL_DIR}/com.$USER.cmux-resume-watchdog.plist.rendered"
PLIST_DST="${HOME}/Library/LaunchAgents/${PLIST_LABEL}.plist"

# 1. Mirror the script into libexec (canonical install location)
mkdir -p "$LIBEXEC_DIR"
cp "$SKILL_DIR/scripts/cmux_resume_watchdog.py" "$LIBEXEC_DIR/cmux_resume_watchdog.py"
cp "$SKILL_DIR/scripts/semantic_classifier.py" "$LIBEXEC_DIR/semantic_classifier.py"
cp "$SKILL_DIR/scripts/cmux_surface_utils.py" "$LIBEXEC_DIR/cmux_surface_utils.py"
cp "$SKILL_DIR/scripts/run-cmux-resume-watchdog.sh" "$LIBEXEC_DIR/run-cmux-resume-watchdog.sh"
chmod +x "$LIBEXEC_DIR/run-cmux-resume-watchdog.sh"

# 2. Render the @HOME@ template if needed
if [[ ! -f "$PLIST_RENDERED" ]]; then
    sed "s|@HOME@|$HOME|g" "$PLIST_SRC" > "$PLIST_RENDERED"
fi

# 3. Install the rendered plist (so ~/Library/LaunchAgents/ has the runtime copy)
cp "$PLIST_RENDERED" "$PLIST_DST"

# 4. (Re)load via launchd. launchd's bootout→bootstrap pair can transiently
# return "Input/output error" if the prior service is still tearing down.
# Tolerate that and retry once with kickstart -k.
UID_NUM=$(id -u)
launchctl bootout "gui/${UID_NUM}/${PLIST_LABEL}" 2>/dev/null || true
if ! launchctl bootstrap "gui/${UID_NUM}" "$PLIST_DST" 2>/dev/null; then
    echo "  (transient bootstrap error — kicking the service)"
    launchctl kickstart -k "gui/${UID_NUM}/${PLIST_LABEL}" 2>/dev/null || true
fi

# 5. Verify
echo ""
echo "=== install summary ==="
echo "libexec:    $LIBEXEC_DIR (mirrored from skill)"
echo "plist:      $PLIST_DST (rendered)"
echo ""
echo "=== launchd state ==="
launchctl print "gui/${UID_NUM}/${PLIST_LABEL}" 2>&1 | grep -E 'state|runs|run interval|last exit code' | head -5
