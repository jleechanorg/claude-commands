"""Centralized test utilities for MCP testing.

This package provides reusable utilities for tests that create real campaigns
and perform real actions via the MCP server.
"""

from .mcp_client import (
    MCPClient,
    MCPResponse,
)
from .model_utils import (
    DEFAULT_MODEL_MATRIX,
    settings_for_model,
    update_user_settings,
)
from .server_utils import (
    LocalServer,
    start_local_mcp_server,
    pick_free_port,
)
from .campaign_utils import (
    create_campaign,
    process_action,
    get_campaign_state,
    ensure_game_state_seed,
)
from .evidence_utils import (
    get_evidence_dir,
    capture_provenance,
    save_evidence,
    write_with_checksum,
    save_request_responses,
    create_evidence_bundle,
)
from .narrative_validation import (
    validate_narrative_compliance,
    validate_state_update_compliance,
    validate_directive_compliance,
)

__all__ = [
    # MCP client
    "MCPClient",
    "MCPResponse",
    # Model utilities
    "DEFAULT_MODEL_MATRIX",
    "settings_for_model",
    "update_user_settings",
    # Server utilities
    "LocalServer",
    "start_local_mcp_server",
    "pick_free_port",
    # Campaign utilities
    "create_campaign",
    "process_action",
    "get_campaign_state",
    "ensure_game_state_seed",
    # Evidence utilities
    "get_evidence_dir",
    "capture_provenance",
    "save_evidence",
    "write_with_checksum",
    "save_request_responses",
    "create_evidence_bundle",
    # Narrative validation utilities
    "validate_narrative_compliance",
    "validate_state_update_compliance",
    "validate_directive_compliance",
]
