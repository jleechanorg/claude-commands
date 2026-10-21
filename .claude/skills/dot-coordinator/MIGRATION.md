# CLI-neutral coordinator migration

Canonical package: dot-coordinator; wrapper: dot-coordinator-wrapper.sh. New
inactive labels: ai.dot-coordinator.00/.20/.40 on macOS and
ai.dot-coordinator-10/-30/-50 on Linux. New private configuration lives under
~/.config/dot-coordinator. CLI executable/argv remain configurable; preserve the
existing Pi/lunaroute choice and environment/credential helper.

## Shared compatibility anchors

Keep ~/.local/state/ai.gemini.agy-dot-coordinator and
/tmp/ai.gemini.agy-dot-coordinator.lock unchanged. Both new launcher and old
forwarders share them; Dot's STOP default stays there. Preserve every STOP,
pending ledger, retained attempt receipt, state.json and state_<account>.json
in place. Never initialize a second empty state domain. Explicit state/lock
and DOT_LOCK_BASE/TMPDIR overrides must agree across every caller. Do not alter
profile paths, SingletonLocks, credentials or account bindings.

The old package contains relative symlink aliases to the single canonical implementation, with no additional launcher logic or state. Installer manifests preserve these links. Existing schedule.json
adapter paths continue working with both packages installed. Install/review the
pair together; do not remove old paths or update only half the pair. Old full
installations stay valid until the activation owner performs a reviewed switch.

## Separately approved operator migration

1. Inventory and privately back up scripts, configs, registered service/timer
   labels and hashes; identify active hold owners.
2. Do not reuse deployment tooling that rejects source symlinks or packages only
   the legacy directory. Review a deployment that stages BOTH packages while
   preserving relative symlinks and validating their targets; back up the full
   old package first. Retain the compatibility state/lock paths, and render
   new definitions to a fresh private /tmp directory. Inspect accounts, identity
   bindings, unchanged minutes and CLI argv. Linux env files belong under
   ~/.config/dot-coordinator; Mac uses the existing private log directory.
3. Obtain separate activation approval. Unregister the old schedule set and
   verify no in-flight coordinator before registering the new set. Never load
   both label sets: shared flock prevents concurrency, not two sequential sends.
4. Preserve genuine STOP and uncertain delivery throughout. Verify exactly one
   registered schedule set, unchanged hold/ledger inodes/content, shared lock
   contention and profile/cadence. A held tick must remain held. No forced send.
5. Roll back by unloading the new set before restoring backed-up old labels.
   Retain state and forwarding entrypoints. Remove aliases only in a later
   reviewed change after every caller/runtime projection is migrated.

Source installers render inactive definitions only. This PR does not install,
start, stop, migrate, delete or enable services/state. Existing host schedules
remain unchanged. Unrelated AGY provider tooling is out of scope.
