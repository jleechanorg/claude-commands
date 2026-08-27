"""Contract tests for the convergence engine's portable JSON boundary."""

import dataclasses
import json
import unittest
from pathlib import Path

from scripts.beads_convergence.codec import (
    ContractError,
    canonical_json_bytes,
    decode_manifest,
    decode_plan,
    decode_registry,
    sha256_hex,
)
from scripts.beads_convergence.models import (
    ApprovalEnvelope,
    BinaryBinding,
    Manifest,
    Plan,
    Registry,
    RepositoryConfig,
)


def valid_binary(path: str = "/absolute/bin/br") -> dict[str, str]:
    return {"path": path, "version": "0.4.0", "sha256": "a" * 64}


def valid_repository() -> dict[str, object]:
    return {
        "repo_id": "worldarchitect.ai",
        "adapter": "br-sqlite-v1",
        "repository_seed": "/absolute/projects/worldarchitect.ai",
        "canonical_beads": "/absolute/projects/worldarchitect.ai/.beads",
        "allowed_worktree_roots": ["/absolute/projects"],
        "additional_worktrees": [],
        "tracker_binary": valid_binary(),
        "git_binary": valid_binary("/absolute/bin/git"),
        "evidence_root": "/absolute/evidence/worldarchitect.ai",
    }


def valid_registry_dict() -> dict[str, object]:
    return {
        "schema": "beads.redirect-convergence.registry.v1",
        "host_id": "test-host",
        "repositories": [valid_repository()],
    }


def valid_manifest_dict() -> dict[str, object]:
    return {
        "schema": "beads.redirect-convergence.manifest.v1",
        "registry_sha256": "b" * 64,
        "repo_id": "worldarchitect.ai",
        "adapter": "br-sqlite-v1",
        "canonical_beads": "/absolute/projects/worldarchitect.ai/.beads",
        "tracker_binary": valid_binary(),
        "git_binary": valid_binary("/absolute/bin/git"),
        "worktrees": [
            {
                "path": "/absolute/projects/worldarchitect.ai",
                "classification": "canonical",
                "directory_device": 1,
                "directory_inode": 2,
                "sources": [],
                "redirect": None,
            }
        ],
    }


def valid_plan_dict() -> dict[str, object]:
    return {
        "schema": "beads.redirect-convergence.plan.v1",
        "manifest_sha256": "c" * 64,
        "repo_id": "worldarchitect.ai",
        "adapter": "br-sqlite-v1",
        "canonical_beads": "/absolute/projects/worldarchitect.ai/.beads",
        "actions": [],
    }


class CodecTest(unittest.TestCase):
    def test_registry_decodes_to_frozen_path_bound_models(self) -> None:
        registry = decode_registry(valid_registry_dict())
        self.assertIsInstance(registry, Registry)
        self.assertIsInstance(registry.repositories[0], RepositoryConfig)
        self.assertIsInstance(registry.repositories[0].repository_seed, Path)
        self.assertIsInstance(registry.repositories[0].tracker_binary, BinaryBinding)
        self.assertTrue(dataclasses.is_dataclass(registry))
        self.assertTrue(dataclasses.fields(registry)[0])
        with self.assertRaises(dataclasses.FrozenInstanceError):
            registry.host_id = "changed"  # type: ignore[misc]

    def test_registry_rejects_unknown_field(self) -> None:
        payload = valid_registry_dict()
        payload["repositories"][0]["surprise"] = True  # type: ignore[index]
        with self.assertRaisesRegex(ContractError, "unknown field"):
            decode_registry(payload)

    def test_rejects_bad_schema_path_and_digest(self) -> None:
        payload = valid_registry_dict()
        payload["schema"] = "beads.redirect-convergence.registry.v2"
        with self.assertRaisesRegex(ContractError, "schema"):
            decode_registry(payload)

        payload = valid_registry_dict()
        repository = payload["repositories"][0]  # type: ignore[index]
        repository["repository_seed"] = "relative"  # type: ignore[index]
        with self.assertRaisesRegex(ContractError, "absolute path"):
            decode_registry(payload)

        payload = valid_registry_dict()
        repository = payload["repositories"][0]  # type: ignore[index]
        binary = repository["tracker_binary"]  # type: ignore[index]
        binary["sha256"] = "A" * 64  # type: ignore[index]
        with self.assertRaisesRegex(ContractError, "lowercase"):
            decode_registry(payload)

    def test_rejects_duplicate_json_fields(self) -> None:
        raw = json.dumps(valid_registry_dict(), separators=(",", ":"))
        raw = raw.replace('"host_id":"test-host"', '"host_id":"one","host_id":"two"')
        with self.assertRaisesRegex(ContractError, "duplicate field"):
            decode_registry(raw)

    def test_manifest_and_plan_decode_with_strict_nested_records(self) -> None:
        manifest = decode_manifest(valid_manifest_dict())
        plan = decode_plan(valid_plan_dict())
        self.assertIsInstance(manifest, Manifest)
        self.assertIsInstance(plan, Plan)
        self.assertEqual(manifest.worktrees[0].classification, "canonical")
        self.assertEqual(manifest.worktrees[0].directory_inode, 2)
        self.assertEqual(plan.actions, ())

        bad = valid_manifest_dict()
        bad["worktrees"][0]["unknown"] = 1  # type: ignore[index]
        with self.assertRaisesRegex(ContractError, "unknown field"):
            decode_manifest(bad)

    def test_only_sqlite_v1_adapter_is_accepted(self) -> None:
        for payload, decoder in (
            (valid_registry_dict(), decode_registry),
            (valid_manifest_dict(), decode_manifest),
            (valid_plan_dict(), decode_plan),
        ):
            payload["adapter"] = "unknown-adapter"
            with self.assertRaisesRegex(ContractError, "adapter"):
                decoder(payload)

    def test_plan_rejects_nonstandard_nan_in_raw_json(self) -> None:
        payload = valid_plan_dict()
        payload["actions"] = [{"cost": "NaN"}]
        raw = json.dumps(payload).replace('"NaN"', "NaN")
        with self.assertRaisesRegex(ContractError, "non-standard"):
            decode_plan(raw)

    def test_plan_rejects_non_string_action_keys_from_mapping(self) -> None:
        payload = valid_plan_dict()
        payload["actions"] = [{1: "invalid key"}]
        with self.assertRaisesRegex(ContractError, "string keys"):
            decode_plan(payload)

    def test_schema_integer_fields_are_nonnegative_integers(self) -> None:
        schema_path = (
            Path(__file__).parents[1]
            / ".claude/skills/beads-redirect-convergence/references"
            / "manifest-v1.schema.json"
        )
        manifest_schema = json.loads(
            schema_path.read_text()
        )
        for definition in ("source", "redirect", "worktree"):
            properties = manifest_schema["$defs"][definition]["properties"]
            for name, property_schema in properties.items():
                if name in {"device", "inode", "size", "mode", "parent_device",
                            "parent_inode", "directory_device", "directory_inode"}:
                    if isinstance(property_schema["type"], list):
                        self.assertIn("integer", property_schema["type"])
                    else:
                        self.assertEqual(property_schema["type"], "integer")
                    self.assertGreaterEqual(property_schema["minimum"], 0)
                    self.assertIn("x-python-exact-type", property_schema)

    def test_canonical_json_is_sorted_compact_utf8_and_hashable(self) -> None:
        self.assertEqual(canonical_json_bytes({"b": 2, "a": 1}), b'{"a":1,"b":2}')
        self.assertEqual(
            canonical_json_bytes({"message": "café"}), '{"message":"café"}'.encode()
        )
        self.assertEqual(
            sha256_hex(b"abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        )
        with self.assertRaises(ValueError):
            canonical_json_bytes({"not-json": float("nan")})

    def test_models_are_frozen(self) -> None:
        for model in (
            BinaryBinding,
            RepositoryConfig,
            ApprovalEnvelope,
            Manifest,
            Plan,
        ):
            self.assertTrue(dataclasses.is_dataclass(model))
            self.assertTrue(model.__dataclass_params__.frozen)


if __name__ == "__main__":
    unittest.main()
