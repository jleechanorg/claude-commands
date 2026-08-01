#!/usr/bin/env bash
# install_cmux_resume_watchdog.sh — install the bundled cmux-resume-watchdog
# as a launchd job on macOS. Run after copying the skill to its final location.
#
# Source of truth: $GITHUB_REPOSITORY PR #38 + $GITHUB_REPOSITORY
# `feat/cmux-resume-watchdog-export` (this skill). The skill bundles the
# watchdog Python script + run wrapper + launchd plist template + test suite.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
# LABEL is a stable namespace — NOT dependent on $USER, because launchd plists
# do not expand shell variables. The literal "localhost" matches the
# com.localhost.X convention common in vendored skills.
LABEL="com.localhost.cmux-resume-watchdog"
DEST="$HOME/.local/libexec/cmux-resume-watchdog"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

mkdir -p "$DEST"
cp "$SKILL_DIR/cmux_resume_watchdog.py" "$DEST/"

# Substitute placeholders: @HOME@ → $HOME, @LABEL@ → $LABEL, @DEST@ → $DEST
sed -e "s|@HOME@|$HOME|g" \
    -e "s|@LABEL@|$LABEL|g" \
    -e "s|@DEST@|$DEST|g" \
    "$SKILL_DIR/cmux-resume-watchdog.plist.template" \
    > "$PLIST"

# Note: the plist points at the run-cmux-resume-watchdog.sh wrapper that lives
# in the SKILL_DIR. If you move the skill, re-run this installer to update the
# path (or symlink the wrapper into ~/.local/bin).

# Retire any old watchdog that pointed at the user_scope checkout (or any other path).
if launchctl print "gui/$(id -u)/$LABEL" >/dev/null 2>&1; then
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
fi
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "installed $LABEL (source: $SKILL_DIR)"
echo "verify with: launchctl print gui/$(id -u)/$LABEL"
