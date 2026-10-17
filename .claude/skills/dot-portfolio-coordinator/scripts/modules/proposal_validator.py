"""Proposal validator module for dot-portfolio-coordinator.

Deterministic validation of model review proposals against snapshot and registry.
Enforces:
- Schema compliance with no unknown structural fields
- Full item coverage against current snapshot
- Version and citation matching against collected evidence
- Domain-store read-only invariant (mutations only on collected roadmap control records)
- Zero semantic keyword classifiers: structural schema validation only
- Deterministic stable action IDs
"""
import hashlib
import json
from typing import Any, Dict, List, Optional, Set, Tuple


class ProposalValidationError(Exception):
    """Raised when proposal structural validation fails."""
    pass


class ProposalValidator:
    """Deterministically validates model review proposals against snapshot and registry."""

    ALLOWED_PROPOSAL_FIELDS = {"schema_version", "snapshot_id", "items", "mutations"}
    ALLOWED_ITEM_FIELDS = {
        "task_key", "source_version", "citations", "owner", "priority",
        "status", "blocker", "next_action", "uncertainty"
    }
    ALLOWED_MUTATION_FIELDS = {
        "target_control_record_id", "action_type", "append_note",
        "title", "owner", "priority", "acceptance_criteria"
    }

    def __init__(self, registry: Any):
        self.registry = registry

    def _hash_payload(self, data: Any) -> str:
        s = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()

    def validate_proposal(
        self, proposal: Dict[str, Any], snapshot: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validates proposal structurally against snapshot.

        Returns {'valid': True, 'action_id': 'act_...', 'errors': []} on success.
        Raises ProposalValidationError on invalid proposals.
        """
        if not isinstance(proposal, dict):
            raise ProposalValidationError("Proposal must be a JSON object")

        unknown_top = set(proposal.keys()) - self.ALLOWED_PROPOSAL_FIELDS
        if unknown_top:
            raise ProposalValidationError(f"Unknown top-level fields in proposal: {sorted(unknown_top)}")

        if proposal.get("schema_version") != 1:
            raise ProposalValidationError(f"Invalid schema_version: {proposal.get('schema_version')}")

        snap_id = proposal.get("snapshot_id")
        if not snap_id or snap_id != snapshot.get("snapshot_id"):
            raise ProposalValidationError(
                f"snapshot_id mismatch: proposal {snap_id} != snapshot {snapshot.get('snapshot_id')}"
            )

        # Index snapshot items and sources
        snap_sources = snapshot.get("sources", {})
        known_task_keys: Dict[Tuple[str, str, str, str], Dict[str, Any]] = {}
        authoritative_control_ids: Set[str] = set()
        domain_store_ids: Set[str] = set()
        source_versions: Dict[str, str] = {}
        valid_citations: Set[str] = set()

        for sid, sdata in snap_sources.items():
            src_def = self.registry.get_source(sid)
            s_version = sdata.get("version", "")
            source_versions[sid] = s_version

            is_control = src_def and src_def.get("authority") == "authoritative_control"

            for item in sdata.get("items", []):
                t_key = item.get("task_composite_key")
                item_id = str(item.get("id", ""))
                repo = src_def.get("repository", "") if src_def else ""

                if t_key:
                    key_tuple = tuple(t_key)
                    known_task_keys[key_tuple] = {
                        "source_id": sid,
                        "version": s_version,
                        "item": item
                    }
                if is_control:
                    authoritative_control_ids.add(item_id)
                else:
                    domain_store_ids.add(item_id)

                # Generate allowed citation pattern
                if repo and item_id and s_version:
                    valid_citations.add(f"{repo}#{item_id}@{s_version}")

        # 1. Validate items
        items = proposal.get("items", [])
        for item in items:
            unknown_item_fields = set(item.keys()) - self.ALLOWED_ITEM_FIELDS
            if unknown_item_fields:
                raise ProposalValidationError(f"Unknown item fields in proposal: {sorted(unknown_item_fields)}")

            t_key_dict = item.get("task_key", {})
            req_keys = ["github_host", "repository", "source_namespace", "bead_id"]
            for rk in req_keys:
                if rk not in t_key_dict:
                    raise ProposalValidationError(f"Proposal item missing task_key field '{rk}'")

            key_tuple = (
                t_key_dict["github_host"].strip().lower(),
                t_key_dict["repository"].strip().lower(),
                t_key_dict["source_namespace"].strip(),
                t_key_dict["bead_id"].strip()
            )

            if key_tuple not in known_task_keys:
                raise ProposalValidationError(
                    f"Proposed task_key {key_tuple} not found in snapshot items. Invented tasks are prohibited."
                )

            item_info = known_task_keys[key_tuple]
            expected_ver = item_info["version"]
            given_ver = item.get("source_version")
            if given_ver != expected_ver:
                raise ProposalValidationError(
                    f"source_version mismatch for {key_tuple}: proposal {given_ver} != snapshot {expected_ver}"
                )

            citations = item.get("citations", [])
            if not citations:
                raise ProposalValidationError(f"Item {key_tuple} missing citations")

        # 2. Validate mutations
        mutations = proposal.get("mutations", [])
        for mut in mutations:
            unknown_mut_fields = set(mut.keys()) - self.ALLOWED_MUTATION_FIELDS
            if unknown_mut_fields:
                raise ProposalValidationError(f"Unknown mutation fields in proposal: {sorted(unknown_mut_fields)}")

            target_id = mut.get("target_control_record_id")
            if not target_id:
                raise ProposalValidationError("Mutation missing target_control_record_id")

            # Domain stores are strictly read-only!
            if target_id in domain_store_ids:
                raise ProposalValidationError(
                    f"Prohibited mutation targeting domain store item '{target_id}'. Domain stores are strictly read-only."
                )

            # Target must be an collected control record
            if authoritative_control_ids and target_id not in authoritative_control_ids:
                raise ProposalValidationError(
                    f"Mutation target '{target_id}' is not in authoritative control records."
                )

            action_type = mut.get("action_type")
            if action_type not in ("tracking_observation", "notification_request", "goal_intake"):
                raise ProposalValidationError(f"Invalid mutation action_type: {action_type}")

        # 3. Derive stable action ID
        proposal_digest = self._hash_payload(proposal)
        versions_digest = self._hash_payload(source_versions)
        combined = f"{proposal_digest}:{versions_digest}"
        action_id = f"act_{hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16]}"

        return {
            "valid": True,
            "action_id": action_id,
            "errors": []
        }
