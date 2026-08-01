# Cmux iOS Pairing — Diagnostic Recipe

**Captured:** 2026-07-18 (Slack `C09GRLXF9GR/1784340748.608849`, "Try to get my cmux dev fork to use the pairing but do not restart it…")

## When to use this

User says any of:
- "pair my iOS app to cmux"
- "cmux mobile not connecting"
- "QR code isn't showing on the Mac"
- "iOS app can't see my workspaces"
- "I'm trying to use Cmux iOS" (verbatim trigger)

## The non-restart pairing contract

The user explicitly said **"do not restart it"** when asked to fix pairing on the dev fork. This is a hard preference — surface any restart-required path only as a last-resort option, and always check for an in-process fix first.

**In-process sign-in does NOT require a restart.** Auth state lives in the running app's actor; sign-in completes via a browser URL → URL-scheme callback into the same running process. `cmux reload-config` and `auth.begin_sign_in` preserve the host.

## Root-cause triage (run in this exact order)

### Step 1 — Confirm the dev fork is healthy

```bash
ls /Applications/ | grep -i cmux
# Identify which .app is running. Typical dev fork on this Mac:
#   cmux DEV dev-fork.app  (socket /private/tmp/cmux-debug-dev-fork.sock)
#   cmux.app               (stable; socket /tmp/cmux.sock or $CMUX_SOCKET_PATH)
#   cmux NIGHTLY.app       (nightly)

# Verify the app is alive and enumerate workspaces:
cmux --socket /private/tmp/cmux-debug-dev-fork.sock list-workspaces
# OR, if socket is the default stable one:
cmux list-workspaces
```

If `list-workspaces` works → the app is alive. Move on.

### Step 2 — Check pairing service state

```bash
cmux --socket /private/tmp/cmux-debug-dev-fork.sock rpc mobile.host.status '{}' | python3 -m json.tool
```

Look for:
- `host_service.is_running: true` → pairing is alive; the issue is somewhere else (QR display, iOS app side, network).
- `host_service.is_running: false` with `last_error: null` → not crashed, just not started. Go to Step 3.
- `host_service.is_running: false` with `last_error: "..."` → capture the error and search the source.

### Step 3 — Check auth state (THE most common blocker)

```bash
cmux --socket /private/tmp/cmux-debug-dev-fork.sock rpc auth.status '{}'
```

If `signed_in: false`:
```json
{
  "is_loading": false,
  "is_restoring_session": false,
  "signed_in": false,
  "timed_out": false
}
```

**This is almost always the root cause.** No account session → no Iroh endpoint → no QR. The iOS app would scan a QR and get nothing.

### Step 4 — Drive non-restart sign-in

```bash
cmux --socket /private/tmp/cmux-debug-dev-fork.sock rpc auth.begin_sign_in '{}'
```

Returns a URL like:
```
http://localhost:9290/handler/native-sign-in?after_auth_return_to=...
  &native_app_return_to=cmux-dev-dev-fork://auth-callback?cmux_auth_state%3D<UUID>
```

(The `native_app_return_to` scheme varies per build: `cmux://`, `cmux-dev://`, `cmux-dev-dev-fork://`. The host portion is what identifies the build variant.)

**Path A — drive the browser via Aside MCP (headless) or paste to user:**
Open the URL in the user's default browser. The user signs in. The callback lands in the running app via the URL scheme. `auth.status.signed_in` flips to `true`; `mobile.host.status.host_service.is_running` flips to `true`.

**Path B — sanity check the iOS app first:** if a previous pairing session is still cached on the iOS side, opening the iOS app may reconnect automatically even with the host service stopped. If a workspace shows up under "Available workspaces" without a fresh QR, the host service came up on its own. If no workspaces, Path A is required.

### Step 5 — Mint a fresh QR

Once `auth.status.signed_in: true` AND `mobile.host.status.is_running: true`:

```bash
cmux --socket /private/tmp/cmux-debug-dev-fork.sock rpc mobile.attach_ticket.create '{}'
```

Returns the QR payload (the `attach_ticket`). Display it in the cmux UI (or pipe to a QR generator if you need it programmatically — the iOS app expects the in-app QR panel normally).

User scans with iOS app → pairing completes.

## Capability reference (dev fork v0.64.16, as of 2026-07-18)

From `cmux capabilities`:

| RPC | Purpose |
|-----|---------|
| `mobile.host.status` | Host service state (is_running, port, routes, active_connection_count) |
| `mobile.attach_ticket.create` | Mint a fresh QR ticket (errors `unavailable: Mobile host routes are not available yet` if host not running) |
| `mobile.dev_stack_auth.configure` | Configure dev-stack auth token (`params.token` required) |
| `mobile.workspace.list` | List workspaces for the iOS app |
| `mobile.terminal.create / .input / .paste / .replay / .viewport` | Terminal control surface for the iOS app |
| `mobile.events.subscribe / .unsubscribe` | Subscribe to mobile-side events |
| `auth.status / .begin_sign_in / .login / .logout / .sign_in_url / .sign_out` | Account session lifecycle |
| `vm.attach_info` | VM/cloud attach info |

## "Latest stable" ambiguity (operator trap)

The user said "If it doesn't work download latest version of stable and test it." On this Mac as of 2026-07-18:
- `/Applications/cmux.app` (stable): **v0.64.16 (build 96)** — same as dev fork
- `/Applications/cmux DEV dev-fork.app`: v0.64.16 (build 96)
- Actual latest release: **v0.64.19** (2026-07-14, "Preserve Claude permission mode across session restore")

So "latest stable" really means **upgrading from 0.64.16 → 0.64.19**. Two ways:
- `brew upgrade --cask cmux`
- Download DMG from <https://github.com/manaflow-ai/cmux/releases/tag/v0.64.19>

**Don't assume the installed stable is actually the latest.** Always check:
```bash
defaults read /Applications/cmux.app/Contents/Info.plist CFBundleShortVersionString
gh api repos/manaflow-ai/cmux/releases/latest --jq '.tag_name'
```

## Where the source lives (verification trail)

- `Sources/Mobile/MobileHostIrohRuntime+Activation.swift` — the host service activation path (requires `accountID` from auth)
- `Packages/Shared/CMUXMobileCore/Sources/CMUXMobileCore/CmxPairingQRCode.swift` — QR payload construction
- `Packages/Shared/CMUXMobileCore/Sources/CMUXMobileCore/CmxManualPairingEntry.swift` — manual code entry fallback
- `Packages/Shared/CMUXMobileCore/Sources/CMUXMobileCore/CmxLegacyPrivateNetworkPairingCode.swift` — legacy LAN pairing
- `Packages/Shared/CMUXMobileCore/Sources/CMUXMobileCore/CmxIrohPathHint*.swift` — Iroh transport hints
- `Packages/Shared/CMUXMobileCore/Sources/CMUXMobileCore/CmxTailscalePeer*.swift` — Tailscale transport fallback
- `docs/iroh-offline-pairing-v1.md` — canonical offline-pairing spec (Ed25519 attestations, 24h lifetime, one-use consumption, 5-min local session)
- `docs/ios-release-notes.md` — iOS TestFlight "What to Test" pipeline

## Pitfalls

1. **"Pairing is broken" usually means auth.signed_in is false, not a network/code bug.** Verify before recommending code changes.
2. **`mobile.attach_ticket.create` erroring with `unavailable: Mobile host routes are not available yet` is the host-not-started symptom, NOT a ticket-format bug.** Fix the upstream cause (auth → host activation).
3. **The URL scheme in `native_app_return_to` identifies the build.** Don't strip it — `cmux://` (stable), `cmux-dev://` (regular dev), `cmux-dev-dev-fork://` (this dev fork). If you spawn the URL in a generic browser, the OS won't know which app to hand it back to.
4. **The 5-minute local pairing session is one-use.** If QR scan fails or the iOS app rejects it (wrong account, expired attestation), a new ticket is needed.
5. **`host_service.last_error: null` does not mean healthy.** It just means no exception was thrown; the service may simply be inactive.
6. **Don't conflate "stable" with "latest."** On this Mac, installed stable = dev fork version. Always verify against the GitHub release tag.
7. **The dev fork socket path is `/private/tmp/cmux-debug-dev-fork.sock` — not the default `/tmp/cmux.sock`.** Pass `--socket` explicitly. `CMUX_SOCKET_PATH` env var is NOT honored by the CLI in non-interactive shells.
