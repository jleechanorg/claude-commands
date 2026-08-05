---
name: runtime-mirror-sync
description: Use when old instructions mention self-hosted-oss, install.sh runtime mirroring, or ~/.local/share/worldarchitect-runners.
type: reference
---

# Runtime Mirror Sync (Retired)

The `self-hosted-oss/install.sh` runtime-mirror workflow no longer exists. Do
not recreate it, edit `~/.local/share/worldarchitect-runners/`, or follow old
copy/install instructions.

Current ownership:

- Fleet health and in-repo support: use `runner-health`.
- Host daemon and deployment: use the user-scope `ezgha-watchdog` guidance and
  the external `ez-gh-actions` repository.
- In-repo runner support scripts: `self-hosted-colima/scripts/`.

If an active instruction still points to `self-hosted-oss/`, treat that as a
stale reference and update it to the current owner.
