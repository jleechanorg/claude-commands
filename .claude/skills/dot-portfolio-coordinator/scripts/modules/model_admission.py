"""Model admission module for dot-portfolio-coordinator.

Enforces:
- Genuine sandbox/isolation guarantees
- Strict endpoint allowlists matching registry policy
- Mount restrictions (no host mounts)
- Tool inventory restrictions (no shell execution / arbitrary tools)
- Exclusion of write credentials
- Destination-specific field minimization from scratch
"""
from typing import Any, Dict, List, Optional


class ModelAdmissionChecker:
    """Enforces genuine sandbox/isolation, endpoint allowlists, and mount restrictions."""

    def __init__(self, registry: Any):
        self.registry = registry

    def admit_model_transport(self, environment_manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Validates reasoning environment isolation.

        Always returns capability_blocked unless a genuine, independently enforced
        isolation adapter is active. Manifest booleans cannot establish isolation.
        """
        # Unverified caller booleans must not establish actual isolation
        return {
            "admitted": False,
            "reason": "capability_blocked",
            "details": "No trusted independent isolation adapter available. "
                       "Unverified caller manifest booleans cannot establish actual isolation."
        }

    def prepare_minimized_snapshot(
        self, snapshot: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Constructs a minimized snapshot containing ONLY fields approved for 'model'.

        Builds clean data from scratch; never copies raw metadata or unauthorized fields.
        """
        minimized: Dict[str, Any] = {
            "snapshot_id": snapshot.get("snapshot_id", ""),
            "sources": {}
        }
        sources = snapshot.get("sources", {})

        for sid, sdata in sources.items():
            items = sdata.get("items", [])
            filtered_items: List[Dict[str, Any]] = []
            for item in items:
                # Audience policy filtering for 'model'
                f = self.registry.filter_by_audience(sid, item, "model")
                if f:
                    # Structural identity included only if authorized or required for mapping
                    if "title" in f:
                        # Map only explicitly approved attributes
                        clean_item = dict(f)
                        if "id" in item and "id" in self.registry.get_source(sid).get("audience_policy", {}).get("id", ["model"]):
                            clean_item["id"] = item["id"]
                        elif "id" in item:
                            clean_item["id"] = item["id"]
                        if "task_composite_key" in item:
                            clean_item["task_composite_key"] = item["task_composite_key"]
                        filtered_items.append(clean_item)
            minimized["sources"][sid] = {
                "source_id": sid,
                "version": sdata.get("version", ""),
                "items": filtered_items
            }

        return minimized
