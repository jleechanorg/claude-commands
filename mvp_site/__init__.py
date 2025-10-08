"""Package initialization for ``mvp_site``."""

from __future__ import annotations

import importlib
import sys
from typing import Dict

# Preserve legacy import paths that referenced modules from the repository root
# (e.g., ``import structured_fields_utils``). The canonical implementations now
# live under the ``mvp_site`` package, so we eagerly import them here and expose
# them via ``sys.modules`` for backward compatibility without maintaining shim
# files at the project root.
_ALIAS_MODULES = {
    name: importlib.import_module(f"mvp_site.{name}")
    for name in [
        "structured_fields_utils",
        "firestore_service",
        "logging_util",
        "entity_preloader",
        "entity_validator",
        "gemini_service",
        "memory_mcp_real",
        "robust_json_parser",
        "world_loader",
    ]
}  # type: Dict[str, object]

for alias, module in _ALIAS_MODULES.items():
    sys.modules.setdefault(alias, module)

# Re-export commonly used aliases for convenience
structured_fields_utils = _ALIAS_MODULES["structured_fields_utils"]

__all__ = list(_ALIAS_MODULES.keys())
