#!/bin/bash
# Shared utility for setting up production environment for MCP server
# Used by both run_local_server.sh and start_mcp_production.sh

setup_mcp_production_env() {
    # Clear any testing/mock environment variables
    unset TESTING
    unset MOCK_SERVICES_MODE
    unset MOCK_MODE

    # Ensure production mode is explicit
    export PRODUCTION_MODE="true"

    echo "🔧 Production environment configured:" >&2
    echo "  TESTING=${TESTING:-unset}" >&2
    echo "  MOCK_SERVICES_MODE=${MOCK_SERVICES_MODE:-unset}" >&2
    echo "  PRODUCTION_MODE=${PRODUCTION_MODE}" >&2

    # Test Firebase environment detection (robust to invocation path)
    if command -v python3 &> /dev/null; then
        echo "🔧 Testing Firebase environment detection..." >&2
        local SCRIPT_DIR; SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
        local REPO_ROOT; REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." >/dev/null 2>&1 && pwd)"
        REPO_ROOT="${REPO_ROOT}" python3 - <<'PY' 2>&1 || echo "  Could not test Firebase detection" >&2
import os, sys
repo_root = os.environ.get("REPO_ROOT", ".")
mvp_site_path = os.path.join(repo_root, "mvp_site")
sys.path.insert(0, mvp_site_path)
# Firebase utils removed - testing mode eliminated
# Firebase is now always initialized in production
print("  Firebase: Always enabled (testing mode removed)")
PY
    fi
}

# If script is sourced, just define the function
# If script is executed directly, run the setup
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    setup_mcp_production_env
fi
