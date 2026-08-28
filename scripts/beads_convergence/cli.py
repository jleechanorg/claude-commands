"""Fail-closed command line boundary for Beads redirect convergence.

The CLI owns argument validation, read-only registry/inventory/planning
dispatch, and machine-readable results. Production apply and recovery remain
unavailable before any registry, artifact, or control-state access.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from dataclasses import asdict, is_dataclass
from pathlib import Path

from .adapters import BrSqliteV1Adapter
from .codec import canonical_json_bytes, sha256_hex
from .inventory import build_manifest
from .models import Registry
from .planner import Plan, build_plan, plan_all
from .registry import ValidatedRepository, load_registry, validate_registry
from .transaction import TransactionError

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2
TOOL_VERSION = "beads-convergence-cli-v1"
REGISTRY_SCHEMA = "beads.redirect-convergence.registry.v1"


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


def _validated_repo(registry: Registry, repo_id: str) -> tuple[ValidatedRepository, tuple[ValidatedRepository, ...]]:
    repositories = validate_registry(registry)
    selected = [item for item in repositories if item.config.repo_id == repo_id]
    if len(selected) != 1:
        for item in repositories:
            item.close()
        raise ValueError(f"unknown repo ID: {repo_id}")
    return selected[0], repositories


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

    if args.command in ("apply", "recover"):
        raise TransactionError(
            "production writer lease is unavailable; "
            f"{args.command} is disabled before mutation"
        )

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
