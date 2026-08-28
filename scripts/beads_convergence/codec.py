"""Strict JSON decoders and canonical serialization for convergence contracts."""

import hashlib
import json
import math
from dataclasses import fields, is_dataclass
from pathlib import Path

from .models import (
    BinaryBinding,
    HealthFingerprint,
    Manifest,
    Plan,
    RedirectState,
    Registry,
    RepositoryConfig,
    SourceFingerprint,
    WorktreeRecord,
)


class ContractError(ValueError):
    """Raised when a contract payload is malformed or violates its schema."""


_CLASSIFICATIONS = {
    "canonical",
    "redirected_canonical",
    "noncanonical",
    "unresolved_noncanonical",
    "missing",
    "unsupported",
}


def canonical_json_bytes(value: object) -> bytes:
    """Serialize JSON-compatible values with stable, compact UTF-8 encoding."""

    return json.dumps(
        _json_value(value),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def sha256_hex(payload: bytes) -> str:
    """Return the lowercase SHA-256 digest for *payload*."""

    if not isinstance(payload, bytes):
        raise TypeError("payload must be bytes")
    return hashlib.sha256(payload).hexdigest()


def decode_registry(value: object) -> Registry:
    payload = _object(value)
    _exact(payload, {"schema", "host_id", "repositories"}, "registry")
    _schema(payload["schema"], "beads.redirect-convergence.registry.v1")
    _string(payload["host_id"], "host_id", nonempty=True)
    repositories = payload["repositories"]
    _list(repositories, "repositories")
    decoded = tuple(_decode_repository(item) for item in repositories)
    ids = [item.repo_id for item in decoded]
    if len(set(ids)) != len(ids):
        raise ContractError("repositories contains duplicate repo_id")
    return Registry(payload["schema"], payload["host_id"], decoded)


def decode_manifest(value: object) -> Manifest:
    payload = _object(value)
    _exact(
        payload,
        {
            "schema",
            "registry_sha256",
            "repo_id",
            "adapter",
            "canonical_beads",
            "tracker_binary",
            "git_binary",
            "worktrees",
            "redirect_codec",
            "redirect_intended_bytes",
            "redirect_oracle_receipt_sha256",
        },
        "manifest",
    )
    _schema(payload["schema"], "beads.redirect-convergence.manifest.v1")
    registry_sha = _hash(payload["registry_sha256"], "registry_sha256")
    repo_id = _repo_id(payload["repo_id"])
    adapter = _adapter(payload["adapter"])
    canonical = _path(payload["canonical_beads"], "canonical_beads")
    tracker = _decode_binary(payload["tracker_binary"], "tracker_binary")
    git = _decode_binary(payload["git_binary"], "git_binary")
    worktrees = payload["worktrees"]
    _list(worktrees, "worktrees")
    records = tuple(_decode_worktree(item) for item in worktrees)
    return Manifest(
        payload["schema"],
        registry_sha,
        repo_id,
        adapter,
        canonical,
        tracker,
        git,
        records,
        _nullable_string(payload["redirect_codec"], "redirect_codec"),
        _nullable_string(
            payload["redirect_intended_bytes"], "redirect_intended_bytes"
        ),
        _nullable_hash(
            payload["redirect_oracle_receipt_sha256"],
            "redirect_oracle_receipt_sha256",
        ),
    )


def decode_plan(value: object) -> Plan:
    payload = _object(value)
    _exact(
        payload,
        {
            "schema",
            "manifest_sha256",
            "repo_id",
            "adapter",
            "canonical_beads",
            "actions",
        },
        "plan",
    )
    _schema(payload["schema"], "beads.redirect-convergence.plan.v1")
    manifest_sha = _hash(payload["manifest_sha256"], "manifest_sha256")
    repo_id = _repo_id(payload["repo_id"])
    adapter = _adapter(payload["adapter"])
    canonical = _path(payload["canonical_beads"], "canonical_beads")
    actions = payload["actions"]
    _list(actions, "actions")
    for index, action in enumerate(actions):
        _object(action, f"actions[{index}]")
    return Plan(
        payload["schema"], manifest_sha, repo_id, adapter, canonical, tuple(actions)
    )


def _decode_repository(value: object) -> RepositoryConfig:
    payload = _object(value, "repository")
    _exact(
        payload,
        {
            "repo_id",
            "adapter",
            "repository_seed",
            "canonical_beads",
            "allowed_worktree_roots",
            "additional_worktrees",
            "tracker_binary",
            "git_binary",
            "evidence_root",
        },
        "repository",
    )
    roots = payload["allowed_worktree_roots"]
    extras = payload["additional_worktrees"]
    _list(roots, "allowed_worktree_roots")
    _list(extras, "additional_worktrees")
    return RepositoryConfig(
        _repo_id(payload["repo_id"]),
        _adapter(payload["adapter"]),
        _path(payload["repository_seed"], "repository_seed"),
        _path(payload["canonical_beads"], "canonical_beads"),
        tuple(_path(item, "allowed_worktree_roots item") for item in roots),
        tuple(_path(item, "additional_worktrees item") for item in extras),
        _decode_binary(payload["tracker_binary"], "tracker_binary"),
        _decode_binary(payload["git_binary"], "git_binary"),
        _path(payload["evidence_root"], "evidence_root"),
    )


def _decode_binary(value: object, field: str) -> BinaryBinding:
    payload = _object(value, field)
    _exact(payload, {"path", "version", "sha256"}, field)
    return BinaryBinding(
        _path(payload["path"], f"{field}.path"),
        _string(payload["version"], f"{field}.version", nonempty=True),
        _hash(payload["sha256"], f"{field}.sha256"),
    )


def _decode_worktree(value: object) -> WorktreeRecord:
    payload = _object(value, "worktree")
    _exact(
        payload,
        {
            "path",
            "classification",
            "directory_device",
            "directory_inode",
            "sources",
            "redirect",
            "backend",
            "health",
        },
        "worktree",
    )
    classification = _string(payload["classification"], "classification", nonempty=True)
    if classification not in _CLASSIFICATIONS:
        raise ContractError("classification has unknown value")
    sources = payload["sources"]
    _list(sources, "sources")
    redirect = payload["redirect"]
    return WorktreeRecord(
        _path(payload["path"], "worktree.path"),
        classification,
        _nonnegative_int(payload["directory_device"], "directory_device"),
        _nonnegative_int(payload["directory_inode"], "directory_inode"),
        tuple(_decode_source(item) for item in sources),
        None if redirect is None else _decode_redirect(redirect),
        _string(payload["backend"], "worktree.backend")
        if payload["backend"] is not None
        else None,
        None if payload["health"] is None else _decode_health(payload["health"]),
    )


def _decode_source(value: object) -> SourceFingerprint:
    payload = _object(value, "source")
    _exact(payload, {"name", "device", "inode", "size", "sha256"}, "source")
    return SourceFingerprint(
        _string(payload["name"], "source.name", nonempty=True),
        _nonnegative_int(payload["device"], "source.device"),
        _nonnegative_int(payload["inode"], "source.inode"),
        _nonnegative_int(payload["size"], "source.size"),
        _hash(payload["sha256"], "source.sha256"),
    )


def _decode_redirect(value: object) -> RedirectState:
    payload = _object(value, "redirect")
    _exact(
        payload,
        {
            "present",
            "mode",
            "bytes",
            "parent_device",
            "parent_inode",
            "codec",
            "intended_bytes",
            "oracle_receipt_sha256",
        },
        "redirect",
    )
    if type(payload["present"]) is not bool:
        raise ContractError("redirect.present must be a boolean")
    mode = payload["mode"]
    if mode is not None:
        mode = _nonnegative_int(mode, "redirect.mode")
    for field in ("bytes", "codec", "intended_bytes"):
        item = payload[field]
        if item is not None:
            _string(item, f"redirect.{field}")
    return RedirectState(
        payload["present"],
        mode,
        payload["bytes"],
        _nonnegative_int(payload["parent_device"], "redirect.parent_device"),
        _nonnegative_int(payload["parent_inode"], "redirect.parent_inode"),
        payload["codec"],
        payload["intended_bytes"],
        None
        if payload["oracle_receipt_sha256"] is None
        else _hash(payload["oracle_receipt_sha256"], "redirect.oracle_receipt_sha256"),
    )


def _decode_health(value: object) -> HealthFingerprint:
    payload = _object(value, "health")
    _exact(
        payload,
        {
            "dirty_count",
            "db_newer",
            "jsonl_newer",
            "workspace_health",
            "receipt_sha256",
        },
        "health",
    )
    dirty = _nonnegative_int(payload["dirty_count"], "health.dirty_count")
    if type(payload["db_newer"]) is not bool:
        raise ContractError("health.db_newer must be a boolean")
    if type(payload["jsonl_newer"]) is not bool:
        raise ContractError("health.jsonl_newer must be a boolean")
    _string(payload["workspace_health"], "health.workspace_health", nonempty=True)
    return HealthFingerprint(
        dirty,
        payload["db_newer"],
        payload["jsonl_newer"],
        payload["workspace_health"],
        _hash(payload["receipt_sha256"], "health.receipt_sha256"),
    )
def _json_value(value: object) -> object:
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return {
            field.name: _json_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, dict):
        return {_json_value(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def _object(value: object, field: str = "payload") -> dict[str, object]:
    if isinstance(value, (bytes, bytearray, str)):
        try:
            value = json.loads(
                bytes(value) if not isinstance(value, str) else value,
                parse_constant=_reject_constant,
                object_pairs_hook=_pairs_without_duplicates,
            )
        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
            _DuplicateField,
            _NonStandardJson,
        ) as exc:
            if isinstance(exc, _DuplicateField):
                raise ContractError(f"{field} has duplicate field {exc}") from exc
            if isinstance(exc, _NonStandardJson):
                message = f"{field} contains non-standard JSON constant"
                raise ContractError(message) from exc
            raise ContractError(f"{field} is not valid JSON") from exc
    if type(value) is not dict:
        raise ContractError(f"{field} must be an object")
    _strict_json_members(value, field)
    return value


class _DuplicateField(ValueError):
    pass


class _NonStandardJson(ValueError):
    pass


def _reject_constant(value: str) -> None:
    raise _NonStandardJson(value)


def _strict_json_members(value: dict[str, object], field: str) -> None:
    for key, item in value.items():
        if type(key) is not str:
            raise ContractError(f"{field} must use string keys")
        _strict_json_value(item, field)


def _strict_json_value(value: object, field: str) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ContractError(f"{field} contains non-standard JSON number")
    if type(value) is dict:
        _strict_json_members(value, field)
    elif type(value) is list:
        for item in value:
            _strict_json_value(item, field)


def _pairs_without_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateField(key)
        result[key] = value
    return result


def _exact(payload: dict[str, object], expected: set[str], field: str) -> None:
    unknown = set(payload) - expected
    if unknown:
        raise ContractError(f"{field} has unknown field {min(unknown)!r}")
    missing = expected - set(payload)
    if missing:
        raise ContractError(f"{field} missing required field {min(missing)!r}")


def _schema(value: object, expected: str) -> None:
    if value != expected:
        raise ContractError(f"schema must be exactly {expected!r}")


def _adapter(value: object) -> str:
    value = _string(value, "adapter", nonempty=True)
    if value != "br-sqlite-v1":
        raise ContractError("adapter must be exactly 'br-sqlite-v1'")
    return value


def _string(value: object, field: str, *, nonempty: bool = False) -> str:
    if type(value) is not str or (nonempty and not value):
        raise ContractError(f"{field} must be a string")
    return value


def _nullable_string(value: object, field: str) -> str | None:
    return None if value is None else _string(value, field)


def _nullable_hash(value: object, field: str) -> str | None:
    return None if value is None else _hash(value, field)


def _repo_id(value: object) -> str:
    value = _string(value, "repo_id", nonempty=True)
    if (
        len(value) > 64
        or not ("a" <= value[0] <= "z" or "0" <= value[0] <= "9")
        or any(
            char not in "abcdefghijklmnopqrstuvwxyz0123456789._-"
            for char in value[1:]
        )
    ):
        raise ContractError("repo_id has invalid format")
    return value


def _path(value: object, field: str) -> Path:
    value = _string(value, field, nonempty=True)
    if (
        "\x00" in value
        or value.startswith(("~", "$", "`"))
        or not Path(value).is_absolute()
    ):
        raise ContractError(f"{field} must be an absolute path")
    return Path(value)


def _hash(value: object, field: str) -> str:
    value = _string(value, field, nonempty=True)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ContractError(f"{field} must be lowercase 64-hex characters")
    return value


def _list(value: object, field: str) -> list[object]:
    if type(value) is not list:
        raise ContractError(f"{field} must be an array")
    return value


def _nonnegative_int(value: object, field: str) -> int:
    if type(value) is int:
        result = value
    elif type(value) is float and math.isfinite(value) and value.is_integer():
        result = int(value)
    else:
        raise ContractError(f"{field} must be a non-negative integer")
    if result < 0:
        raise ContractError(f"{field} must be a non-negative integer")
    return result
