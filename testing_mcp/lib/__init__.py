"""Centralized test utilities for MCP testing.

This package provides reusable utilities for tests that create real campaigns
and perform real actions via the MCP server.
"""

from .arc_validation_utils import (
    detect_companions,
    extract_companion_arc_event,
    extract_companion_arcs,
    extract_narrative,
    extract_next_companion_arc_turn,
    filter_arc_states,
    find_arc_themes_in_narrative,
    find_companions_in_narrative,
    validate_arc_event_structure,
    validate_arc_structure,
    validate_companion_dialogue_in_narrative,
)
from .campaign_utils import (
    aggregate_validation_summary,
    create_campaign,
    ensure_game_state_seed,
    get_campaign_state,
    get_turn_count,
    process_action,
    reset_turn_tracking,
)
from .evidence_utils import (
    capture_provenance,
    create_evidence_bundle,
    get_evidence_dir,
    save_evidence,
    save_request_responses,
    write_with_checksum,
)
from .firestore_validation import (
    validate_action_resolution_in_firestore,
    validate_story_entry_fields,
)
from .game_constants import XP_GAIN_PATTERNS, XP_THRESHOLDS
from .mcp_client import (
    MCPClient,
    MCPResponse,
)
from .model_utils import (
    DEFAULT_MODEL_MATRIX,
    settings_for_model,
    update_user_settings,
)
from .narrative_validation import (
    validate_directive_compliance,
    validate_narrative_compliance,
    validate_state_update_compliance,
)
from .regression_oracle import (
    DifferenceClass,
    InvariantChecker,
    InvariantViolation,
    RegressionOracle,
    RegressionResult,
    load_regression_snapshot,
    save_regression_snapshot,
    validate_multi_turn_test,
)
from .server_utils import (
    LocalServer,
    pick_free_port,
    start_local_mcp_server,
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
    "reset_turn_tracking",
    "get_turn_count",
    "aggregate_validation_summary",
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
    # Regression oracle utilities
    "RegressionOracle",
    "InvariantChecker",
    "RegressionResult",
    "InvariantViolation",
    "DifferenceClass",
    "validate_multi_turn_test",
    "save_regression_snapshot",
    "load_regression_snapshot",
    # Game constants
    "XP_THRESHOLDS",
    "XP_GAIN_PATTERNS",
    # Firestore validation utilities
    "validate_action_resolution_in_firestore",
    "validate_story_entry_fields",
    # Arc validation utilities
    "extract_companion_arcs",
    "extract_companion_arc_event",
    "extract_next_companion_arc_turn",
    "extract_narrative",
    "validate_arc_structure",
    "validate_arc_event_structure",
    "detect_companions",
    "filter_arc_states",
    "find_companions_in_narrative",
    "find_arc_themes_in_narrative",
    "validate_companion_dialogue_in_narrative",
]
