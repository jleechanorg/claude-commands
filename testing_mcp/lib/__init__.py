"""Centralized test utilities for MCP testing.

This package provides reusable utilities for tests that create real campaigns
and perform real actions via the MCP server.
"""

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

__all__ = [
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
]
