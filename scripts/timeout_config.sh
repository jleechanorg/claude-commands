#!/bin/bash
# Centralized timeout definitions for WorldArchitect.AI
#
# All layers (Cloud Run services + load balancer, Gunicorn, MCP client, and both
# frontends) must stay aligned on the same ceiling to avoid premature timeouts
# during long-running Gemini/API calls. Adjust the value here and propagate via
# exported environment variables rather than hard-coding elsewhere.

# Base timeout in seconds (10 minutes default)
export WORLDARCH_TIMEOUT_SECONDS="${WORLDARCH_TIMEOUT_SECONDS:-600}"

# Derived values for consumers that require milliseconds or minutes
export WORLDARCH_TIMEOUT_MILLISECONDS="${WORLDARCH_TIMEOUT_MILLISECONDS:-$((WORLDARCH_TIMEOUT_SECONDS * 1000))}"
export WORLDARCH_TIMEOUT_MINUTES="${WORLDARCH_TIMEOUT_MINUTES:-$((WORLDARCH_TIMEOUT_SECONDS / 60))}"

# Frontend build-time env vars (Vite/CRA) derived from the same source so bundles
# share the server ceiling.
export VITE_REQUEST_TIMEOUT_MS="${VITE_REQUEST_TIMEOUT_MS:-$WORLDARCH_TIMEOUT_MILLISECONDS}"
export REACT_APP_REQUEST_TIMEOUT_MS="${REACT_APP_REQUEST_TIMEOUT_MS:-$WORLDARCH_TIMEOUT_MILLISECONDS}"
