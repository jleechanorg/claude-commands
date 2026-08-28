"""Fail-closed command line boundary for Beads redirect convergence.

The CLI is intentionally a thin adapter around the public engine functions.
It owns argument validation, captured artifact decoding, and machine-readable
receipts; it does not provide an approval bypass or a multi-repository write
operation.
"""

from __future__ import annotations

import argparse
import datetime as datetime_module
import hashlib
import json
import os
import pwd
import stat
import sys
from collections.abc import Sequence
from dataclasses import asdict, is_dataclass
from pathlib import Path

from .adapters import BrSqliteV1Adapter
from .approval import SignedApproval, SshApprovalVerifier
from .codec import canonical_json_bytes, decode_manifest, sha256_hex
from .inventory import build_manifest
from .models import ApprovalEnvelope, BinaryBinding, Manifest, Registry
from .planner import Plan, build_plan, plan_all
from .registry import ValidatedRepository, load_registry, validate_registry
from .transaction import (
    ApplyRequest,
    FileControlStore,
    RecoveryRequest,
    apply_plan,
    recover_run,
)

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2
TOOL_VERSION = "beads-convergence-cli-v1"
REGISTRY_SCHEMA = "beads.redirect-convergence.registry.v1"
MANIFEST_SCHEMA = "beads.redirect-convergence.manifest.v1"
PLAN_SCHEMA = "beads.redirect-convergence.plan.v1"


class CliUsageError(ValueError):
    """An argument was absent or not part of the public command contract."""


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliUsageError(message)


def _absolute(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or any(part in (".", "..") for part in path.parts):
        raise argparse.ArgumentTypeError("path must be absolute and traversal-free")
    return path


def _hash(value: str) -> str:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise argparse.ArgumentTypeError("hash must be lowercase 64-hex characters")
    return value


def _add_registry_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--registry", required=True, type=_absolute)
    parser.add_argument("--expected-registry-sha256", required=True, type=_hash)


def _add_repo_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo", required=True)
    _add_registry_args(parser)


def _add_binary_binding_args(parser: argparse.ArgumentParser, prefix: str) -> None:
    label = prefix.replace("_", "-")
    parser.add_argument(f"--expected-{label}-path", required=True, type=_absolute)
    parser.add_argument(f"--expected-{label}-version", required=True)
    parser.add_argument(f"--expected-{label}-sha256", required=True, type=_hash)


def _add_transaction_args(parser: argparse.ArgumentParser, *, recover: bool) -> None:
    _add_repo_args(parser)
    parser.add_argument(
        "--manifest",
        required=True,
        type=_absolute,
    )
    parser.add_argument(
        "--expected-manifest-sha256",
        required=True,
        type=_hash,
    )
    parser.add_argument("--expected-plan-sha256", required=True, type=_hash)
    parser.add_argument("--expected-canonical", required=True, type=_absolute)
    parser.add_argument("--expected-adapter", required=True)
    _add_binary_binding_args(parser, "tracker")
    _add_binary_binding_args(parser, "git")
    parser.add_argument("--approval", required=True, type=_absolute)
    parser.add_argument("--approval-signature", required=True, type=_absolute)
    if recover:
        parser.add_argument("--run-id", required=True)
        parser.add_argument("--expected-journal-sha256", required=True, type=_hash)
        parser.add_argument("--recover", action="store_true", required=True)
    else:
        parser.add_argument("--apply", action="store_true", required=True)


def build_parser() -> argparse.ArgumentParser:
    """Build the public parser; mutation flags exist on one-repo commands only."""

    parser = _ArgumentParser(prog="beads-converge")
    subcommands = parser.add_subparsers(
        dest="command", required=True, parser_class=_ArgumentParser
    )

    registry = subcommands.add_parser("registry")
    registry_commands = registry.add_subparsers(
        dest="registry_command", required=True, parser_class=_ArgumentParser
    )
    validate = registry_commands.add_parser("validate")
    _add_registry_args(validate)

    inventory = subcommands.add_parser("inventory")
    _add_repo_args(inventory)

    plan = subcommands.add_parser("plan")
    _add_repo_args(plan)

    aggregate = subcommands.add_parser("plan-all")
    _add_registry_args(aggregate)

    apply = subcommands.add_parser("apply")
    _add_transaction_args(apply, recover=False)

    recover = subcommands.add_parser("recover")
    _add_transaction_args(recover, recover=True)
    return parser


def _capture(path: Path) -> bytes:
    """Read one regular artifact through a no-follow descriptor."""

    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(os.fspath(path), flags)
    except OSError as exc:
        raise ValueError(f"cannot open artifact: {path}") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError(f"artifact is not a regular file: {path}")
        chunks: list[bytes] = []
        while chunk := os.read(fd, 1024 * 1024):
            chunks.append(chunk)
        after = os.fstat(fd)
        if (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise ValueError(f"artifact changed while being read: {path}")
        return b"".join(chunks)
    finally:
        os.close(fd)


def _load_manifest(path: Path, expected_sha256: str) -> Manifest:
    raw = _capture(path)
    measured = hashlib.sha256(raw).hexdigest()
    if measured != expected_sha256:
        raise ValueError("manifest SHA-256 does not match expected digest")
    try:
        return decode_manifest(raw)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc


def _load_json(path: Path) -> object:
    try:
        return json.loads(
            _capture(path),
            object_pairs_hook=_unique_pairs,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        raise ValueError(f"malformed JSON artifact: {path}") from exc


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def _approval(path: Path, signature_path: Path) -> SignedApproval:
    value = _load_json(path)
    if type(value) is not dict:
        raise ValueError("approval must be a JSON object")
    fields = {
        "schema",
        "operation",
        "repo_id",
        "nonce",
        "issued_at",
        "expires_at",
        "registry_sha256",
        "manifest_sha256",
        "plan_sha256",
        "canonical_beads",
        "adapter",
        "tracker_binary",
        "git_binary",
        "canonical_device",
        "canonical_inode",
        "tool_tree_sha256",
        "run_id",
        "journal_sha256",
        "signer_principal",
        "signer_fingerprint",
    }
    if set(value) != fields:
        raise ValueError("approval has missing or unknown fields")
    tracker = _approval_binary(value["tracker_binary"], "tracker_binary")
    git = _approval_binary(value["git_binary"], "git_binary")
    envelope = ApprovalEnvelope(
        value["schema"],
        value["operation"],
        value["repo_id"],
        value["nonce"],
        value["issued_at"],
        value["expires_at"],
        value["registry_sha256"],
        value["manifest_sha256"],
        value["plan_sha256"],
        Path(value["canonical_beads"]),
        value["adapter"],
        tracker,
        git,
        value["canonical_device"],
        value["canonical_inode"],
        value["tool_tree_sha256"],
        value["run_id"],
        value["journal_sha256"],
        value["signer_principal"],
        value["signer_fingerprint"],
    )
    signature = _capture(signature_path)
    if not signature:
        raise ValueError("approval signature is empty")
    return SignedApproval(envelope, signature)


def _approval_binary(value: object, field: str) -> BinaryBinding:
    if type(value) is not dict or set(value) != {"path", "version", "sha256"}:
        raise ValueError(f"approval {field} is malformed")
    if (
        not isinstance(value["path"], str)
        or not Path(value["path"]).is_absolute()
        or any(part in (".", "..") for part in Path(value["path"]).parts)
    ):
        raise ValueError(f"approval {field}.path must be absolute")
    if not isinstance(value["version"], str) or not value["version"]:
        raise ValueError(f"approval {field}.version must be a nonempty string")
    if (
        not isinstance(value["sha256"], str)
        or len(value["sha256"]) != 64
        or any(char not in "0123456789abcdef" for char in value["sha256"])
    ):
        raise ValueError(f"approval {field}.sha256 must be lowercase 64-hex")
    return BinaryBinding(Path(value["path"]), value["version"], value["sha256"])


def _repo(registry: Registry, repo_id: str) -> object:
    matches = [item for item in registry.repositories if item.repo_id == repo_id]
    if len(matches) != 1:
        raise ValueError(f"unknown repo ID: {repo_id}")
    return matches[0]


def _validated_repo(registry: Registry, repo_id: str) -> tuple[ValidatedRepository, tuple[ValidatedRepository, ...]]:
    repositories = validate_registry(registry)
    selected = [item for item in repositories if item.config.repo_id == repo_id]
    if len(selected) != 1:
        for item in repositories:
            item.close()
        raise ValueError(f"unknown repo ID: {repo_id}")
    return selected[0], repositories


def _binding_args_match(args: argparse.Namespace, config: object, manifest: Manifest) -> None:
    expected_tracker = BinaryBinding(
        args.expected_tracker_path,
        args.expected_tracker_version,
        args.expected_tracker_sha256,
    )
    expected_git = BinaryBinding(
        args.expected_git_path,
        args.expected_git_version,
        args.expected_git_sha256,
    )
    if args.expected_adapter != manifest.adapter:
        raise ValueError("expected adapter binding does not match manifest")
    if args.expected_canonical != manifest.canonical_beads:
        raise ValueError("expected canonical binding does not match manifest")
    if expected_tracker != manifest.tracker_binary or expected_git != manifest.git_binary:
        raise ValueError("expected executable binding does not match manifest")
    _config_binding_args_match(args, config, expected_tracker, expected_git)


def _config_binding_args_match(
    args: argparse.Namespace,
    config: object,
    expected_tracker: BinaryBinding | None = None,
    expected_git: BinaryBinding | None = None,
) -> None:
    if expected_tracker is None:
        expected_tracker = BinaryBinding(
            args.expected_tracker_path,
            args.expected_tracker_version,
            args.expected_tracker_sha256,
        )
    if expected_git is None:
        expected_git = BinaryBinding(
            args.expected_git_path,
            args.expected_git_version,
            args.expected_git_sha256,
        )
    if (
        config.adapter != args.expected_adapter
        or config.canonical_beads != args.expected_canonical
        or config.tracker_binary != expected_tracker
        or config.git_binary != expected_git
    ):
        raise ValueError("expected binding does not match registry")


def _control_root() -> Path:
    """Derive the non-overridable control namespace from the effective user."""

    home = Path(pwd.getpwuid(os.geteuid()).pw_dir)
    return home / ".local" / "state" / "beads-convergence" / "control"


def _pinned_verifier() -> SshApprovalVerifier:
    """Construct the verifier from the fixed host executable, never approval data."""

    path = Path("/usr/bin/ssh-keygen")
    digest = sha256_hex(_capture(path))
    return SshApprovalVerifier(BinaryBinding(path, "system", digest))


def _transaction_context(args: argparse.Namespace) -> dict[str, object]:
    """Return non-secret operator bindings for success and failure receipts."""

    context: dict[str, object] = {
        "repo_id": getattr(args, "repo", None),
        "adapter": getattr(args, "expected_adapter", None),
        "registry_sha256": getattr(args, "expected_registry_sha256", None),
        "manifest_sha256": getattr(args, "expected_manifest_sha256", None),
        "plan_sha256": getattr(args, "expected_plan_sha256", None),
        "canonical_beads": str(getattr(args, "expected_canonical", "")),
        "tracker_path": str(getattr(args, "expected_tracker_path", "")),
        "tracker_version": getattr(args, "expected_tracker_version", None),
        "tracker_sha256": getattr(args, "expected_tracker_sha256", None),
        "git_path": str(getattr(args, "expected_git_path", "")),
        "git_version": getattr(args, "expected_git_version", None),
        "git_sha256": getattr(args, "expected_git_sha256", None),
    }
    journal_sha = getattr(args, "expected_journal_sha256", None)
    if journal_sha is not None:
        context["journal_sha256"] = journal_sha
    return {key: value for key, value in context.items() if value not in (None, "")}


def _transaction_failure(args: argparse.Namespace, error: str) -> dict[str, object]:
    fields = _transaction_context(args)
    fields.update(
        {
            "schema": "beads.redirect-convergence.cli.v1",
            "tool_version": TOOL_VERSION,
            "operation": args.command,
            "ok": False,
            "error": error,
        }
    )
    if args.command == "apply":
        fields["applied"] = False
    if args.command == "recover":
        fields["recovered"] = False
    return fields


def _transaction_success(
    args: argparse.Namespace,
    receipt: object,
    *,
    status: str,
) -> int:
    fields = _transaction_context(args)
    fields.update(
        {
            "schema": "beads.redirect-convergence.cli.v1",
            "tool_version": TOOL_VERSION,
            "operation": args.command,
            "ok": status in ("COMMITTED", "ROLLED_BACK"),
            "status": status,
            "run_id": receipt.run_id,
            "journal_sha256": receipt.journal_sha256,
        }
    )
    if args.command == "apply":
        fields.update(
            {
                "canonical_key": receipt.canonical_key,
                "signer_principal": receipt.signer_principal,
                "signer_fingerprint": receipt.signer_fingerprint,
            }
        )
        fields["applied"] = status == "COMMITTED"
    if args.command == "recover":
        # Recovery is successful both when it restores pre-state (ROLLED_BACK)
        # and when it regenerates a receipt for a previously committed run.
        fields["recovered"] = status in ("COMMITTED", "ROLLED_BACK")
    _emit(fields)
    return EXIT_OK if fields["ok"] else EXIT_FAILURE


def _plan_payload(plan: Plan) -> dict[str, object]:
    payload = asdict(plan)
    payload["sha256"] = plan.sha256
    return payload


def _emit(payload: object) -> None:
    if is_dataclass(payload):
        payload = asdict(payload)
    sys.stdout.buffer.write(canonical_json_bytes(payload) + b"\n")


def _success(operation: str, **fields: object) -> int:
    _emit({"schema": "beads.redirect-convergence.cli.v1", "tool_version": TOOL_VERSION, "operation": operation, "ok": True, **fields})
    return EXIT_OK


def _run(args: argparse.Namespace) -> int:
    if args.command == "registry":
        registry = load_registry(args.registry, args.expected_registry_sha256)
        if args.registry_command != "validate" or registry.schema != REGISTRY_SCHEMA:
            raise ValueError("unsupported registry command or schema")
        repositories = validate_registry(registry)
        try:
            return _success(
                "registry.validate",
                registry_sha256=sha256_hex(canonical_json_bytes(registry)),
                host_id=registry.host_id,
                repositories=[item.config.repo_id for item in repositories],
            )
        finally:
            for item in repositories:
                item.close()

    registry = load_registry(args.registry, args.expected_registry_sha256)
    registry_sha256 = sha256_hex(canonical_json_bytes(registry))

    if args.command == "plan-all":
        receipt = plan_all(registry)
        results = []
        for result in receipt.results:
            item: dict[str, object] = {"repo_id": result.repo_id, "ok": result.ok}
            if result.plan is not None:
                item["plan"] = _plan_payload(result.plan)
            if result.error is not None:
                item["error"] = result.error
            results.append(item)
        _emit({
            "schema": "beads.redirect-convergence.cli.v1",
            "tool_version": TOOL_VERSION,
            "operation": "plan-all",
            "ok": receipt.exit_code == 0,
            "registry_sha256": registry_sha256,
            "results": results,
        })
        return receipt.exit_code

    config = _repo(registry, args.repo)
    if args.command in ("inventory", "plan"):
        selected, repositories = _validated_repo(registry, args.repo)
        try:
            adapter = BrSqliteV1Adapter()
            manifest = build_manifest(selected, adapter)
            if args.command == "inventory":
                return _success(
                    "inventory",
                    repo_id=args.repo,
                    registry_sha256=registry_sha256,
                    manifest=asdict(manifest),
                    manifest_sha256=sha256_hex(canonical_json_bytes(manifest)),
                )
            plan_value = build_plan(manifest)
            return _success(
                "plan",
                repo_id=args.repo,
                registry_sha256=registry_sha256,
                manifest_sha256=sha256_hex(canonical_json_bytes(manifest)),
                plan=_plan_payload(plan_value),
            )
        finally:
            for item in repositories:
                item.close()

    if args.command == "apply":
        # Apply must attest the complete registry before it consumes any
        # operator-supplied artifact.  The transaction layer repeats its own
        # checks and still rejects the production adapter/control boundary.
        _, repositories = _validated_repo(registry, args.repo)
        for item in repositories:
            item.close()
        manifest = _load_manifest(args.manifest, args.expected_manifest_sha256)
        if manifest.repo_id != args.repo or manifest.registry_sha256 != registry_sha256:
            raise ValueError("manifest repository or registry binding does not match")
        _binding_args_match(args, config, manifest)
        plan_value = build_plan(manifest)
        if plan_value.sha256 != args.expected_plan_sha256:
            raise ValueError("recomputed plan SHA-256 does not match expected digest")
        signed = _approval(args.approval, args.approval_signature)
        request = ApplyRequest(
            True,
            registry,
            manifest,
            plan_value,
            BrSqliteV1Adapter(),
            signed,
            _pinned_verifier(),
            FileControlStore(_control_root()),
            datetime_module.datetime.now(datetime_module.timezone.utc).isoformat().replace("+00:00", "Z"),
        )
        receipt = apply_plan(request)
        return _transaction_success(args, receipt, status=receipt.status)

    if args.command == "recover":
        if args.repo != config.repo_id:
            raise ValueError("recovery repository binding does not match")
        _, repositories = _validated_repo(registry, args.repo)
        for item in repositories:
            item.close()
        _config_binding_args_match(args, config)
        # Rebuild the manifest from retained validation authority.  The supplied
        # artifact remains an independent operator binding, not a mutable plan
        # input or an authorization source.
        supplied_manifest = _load_manifest(args.manifest, args.expected_manifest_sha256)
        if supplied_manifest.repo_id != args.repo or supplied_manifest.registry_sha256 != registry_sha256:
            raise ValueError("manifest repository or registry binding does not match")
        _binding_args_match(args, config, supplied_manifest)
        selected, repositories = _validated_repo(registry, args.repo)
        try:
            adapter = BrSqliteV1Adapter()
            manifest = build_manifest(selected, adapter)
        finally:
            for item in repositories:
                item.close()
        if sha256_hex(canonical_json_bytes(manifest)) != sha256_hex(canonical_json_bytes(supplied_manifest)):
            raise ValueError("fresh recovery manifest does not match expected manifest")
        plan_value = build_plan(manifest)
        if plan_value.sha256 != args.expected_plan_sha256:
            raise ValueError("recomputed plan SHA-256 does not match expected digest")

        # Recovery is deliberately still delegated to the transaction boundary;
        # the production implementation rejects non-fixture control stores.
        signed = _approval(args.approval, args.approval_signature)
        if (
            signed.envelope.operation != "recover"
            or signed.envelope.repo_id != args.repo
            or signed.envelope.registry_sha256 != registry_sha256
            or signed.envelope.canonical_beads != args.expected_canonical
            or signed.envelope.adapter != args.expected_adapter
            or signed.envelope.tracker_binary != config.tracker_binary
            or signed.envelope.git_binary != config.git_binary
            or signed.envelope.run_id != args.run_id
            or signed.envelope.journal_sha256 != args.expected_journal_sha256
        ):
            raise ValueError("recovery approval binding does not match")
        control = FileControlStore(_control_root())
        journal = control.load_journal(args.run_id)
        if sha256_hex(canonical_json_bytes(journal)) != args.expected_journal_sha256:
            raise ValueError("journal SHA-256 does not match expected digest")
        if journal.get("repo_id") != args.repo or journal.get("canonical_beads") != str(args.expected_canonical):
            raise ValueError("journal binding does not match operator bindings")
        request = RecoveryRequest(
            control,
            adapter,
            args.run_id,
            True,
            registry,
            manifest,
            plan_value,
            signed,
            _pinned_verifier(),
            datetime_module.datetime.now(datetime_module.timezone.utc).isoformat().replace("+00:00", "Z"),
            args.expected_journal_sha256,
        )
        receipt = recover_run(request)
        return _transaction_success(args, receipt, status=receipt.status)

    raise ValueError("unknown command")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a stable process exit code."""

    parser = build_parser()
    args: argparse.Namespace | None = None
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
        return _run(args)
    except CliUsageError as exc:
        _emit({"schema": "beads.redirect-convergence.cli.v1", "tool_version": TOOL_VERSION, "ok": False, "error": str(exc)})
        print(f"beads-converge: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except Exception as exc:  # noqa: BLE001 - CLI must fail closed without a traceback
        if args is not None and args.command in ("apply", "recover"):
            _emit(_transaction_failure(args, str(exc)))
        else:
            _emit({"schema": "beads.redirect-convergence.cli.v1", "tool_version": TOOL_VERSION, "ok": False, "error": str(exc)})
        print(f"beads-converge: {exc}", file=sys.stderr)
        return EXIT_FAILURE


if __name__ == "__main__":
    raise SystemExit(main())
