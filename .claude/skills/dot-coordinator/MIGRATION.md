# CLI-neutral coordinator migration

Canonical package: dot-coordinator; wrapper: dot-coordinator-wrapper.sh. New
inactive labels: ai.dot-coordinator.00/.20/.40 on macOS and
ai.dot-coordinator-10/-30/-50 on Linux. New private configuration lives under
~/.config/dot-coordinator. CLI executable/argv remain configurable; preserve the
existing Pi/lunaroute choice and environment/credential helper.

## Minimal owner contract and compatibility transition

Each Dot owns its tasks. The scheduler only requests the fixed reminder. The
owned-browser transport retains ONE existing per-profile kernel flock plus its
system Chrome, keychain, SingletonLock and cleanup protections. There is no
coordinator global lock, review exclusion, task-progress ledger or new retained
attempt receipt. The old review helper fails closed without executing commands.

Only unresolved-submit information genuinely needs transport persistence: the
existing per-account pending marker binds payload/account/target/identity so an
unknown result is read back before retry. It is removed only after evidence
settles delivery or absence. This cooperative guard is not destination idempotency;
one schedule set is still required to prevent sequential duplicate reminders.

For compatibility, pending/legacy unknown-delivery data remains under
~/.local/state/ai.gemini.agy-dot-coordinator. Existing STOP is a READ-ONLY migration
guard, not a new review lifecycle: do not create, clear or reinterpret it. Old
state/attempt files and /tmp/ai.gemini.agy-dot-coordinator.lock remain untouched
on live hosts. The new launcher does not acquire that coordinator global lock.
Before activation, owners must explicitly reconcile these legacy holds; a held
source candidate remains held. No migration bypass flag or fresh state domain.
DOT_LOCK_BASE/TMPDIR and exact lexical profile paths must agree across transports.

Old executable paths are regular forwarding files to one canonical implementation, not
another scheduler. Install both packages together; do not update only half the
pair. Old full installations remain live until separately reviewed migration.

## Separately approved operator migration

1. Inventory and privately back up scripts, configs, registered service/timer
   labels and hashes; identify active hold owners.
2. Do not reuse deployment tooling that packages only the legacy directory.
   Source forwarding aliases are regular files, preserving strict catalog
   refusal of source symlinks. Stage BOTH packages and validate forwarding
   targets; back up the full old package first. Retain the compatibility state/lock paths, and render
   new definitions to a fresh private /tmp directory. Inspect accounts, identity
   bindings, unchanged minutes and CLI argv. Linux env files belong under
   ~/.config/dot-coordinator; Mac uses the existing private log directory.
3. Obtain separate activation approval. Unregister the old schedule set and
   verify no in-flight coordinator before registering the new set. Never load
   both label sets: shared flock prevents concurrency, not two sequential sends.
4. Preserve genuine STOP and uncertain delivery throughout. Verify exactly one
   registered schedule set, unchanged hold/ledger inodes/content, profile lock
   contention and profile/cadence. A held tick must remain held. No forced send.
5. Roll back by unloading the new set before restoring backed-up old labels.
   Retain state and forwarding entrypoints. Remove aliases only in a later
   reviewed change after every caller/runtime projection is migrated.

Source installers render inactive definitions only. This PR does not install,
start, stop, migrate, delete or enable services/state. Existing host schedules
remain unchanged. Unrelated AGY provider tooling is out of scope.
