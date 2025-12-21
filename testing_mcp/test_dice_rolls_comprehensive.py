#!/usr/bin/env python3
"""Comprehensive dice roll tests against an MCP server (local or preview).

These tests exercise the system THROUGH MCP (`/mcp`) and do not import provider
SDKs or call provider endpoints directly.

- No API keys are required in the *test runner*.
- The target server (preview or your local MCP server) must have its own provider
  API keys configured if it will perform real inferences.

Run (local MCP already running):
    cd testing_mcp
    python test_dice_rolls_comprehensive.py --server-url http://127.0.0.1:8001

Run (start local MCP automatically; requires `gcloud` access to Secret Manager):
    cd testing_mcp
    python test_dice_rolls_comprehensive.py --start-local
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from mcp_client import MCPClient

PROJECT_ROOT = Path(__file__).parent.parent
EVIDENCE_DIR = Path(__file__).parent / "evidence" / "mcp_dice_rolls"


TEST_SCENARIOS: list[dict[str, Any]] = [
    {
        "name": "Combat Attack Roll",
        "user_input": "I attack the goblin with my longsword. Resolve the attack and damage.",
        "expect_substrings": ["d20"],
        "min_dice_rolls": 2,
    },
    {
        "name": "Skill Check (Stealth)",
        "user_input": "I try to sneak past the guards. Make a Stealth check.",
        "expect_substrings": ["d20"],
        "min_dice_rolls": 1,
    },
    {
        "name": "Saving Throw (CON)",
        "user_input": "I brace myself against dragon fire. Make a Constitution saving throw.",
        "expect_substrings": ["d20"],
        "min_dice_rolls": 1,
    },
]

DEFAULT_MODEL_MATRIX = [
    "gemini-3-flash-preview",
    "qwen-3-235b-a22b-instruct-2507",
]


@dataclass
class LocalServer:
    proc: subprocess.Popen[bytes]
    base_url: str
    log_path: Path

    def stop(self) -> None:
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()


def _which(name: str) -> str | None:
    for d in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(d) / name
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _load_secret(env: dict[str, str], *, secret_name: str, env_var: str) -> None:
    if env.get(env_var):
        return
    if not _which("gcloud"):
        return

    project = env.get("GCP_PROJECT") or env.get("GOOGLE_CLOUD_PROJECT") or "worldarchitecture-ai"
    try:
        value = subprocess.check_output(
            [
                "gcloud",
                "secrets",
                "versions",
                "access",
                "latest",
                "--secret",
                secret_name,
                "--project",
                project,
            ],
            stderr=subprocess.DEVNULL,
        ).decode("utf-8").strip()
        if value:
            env[env_var] = value
    except Exception:
        return


def start_local_mcp_server(port: int) -> LocalServer:
    """Start an HTTP-only MCP server with mock Firestore (no Firebase creds)."""
    python_bin = PROJECT_ROOT / "venv" / "bin" / "python"
    if not python_bin.exists():
        python_bin = Path(sys.executable)

    env = dict(os.environ)
    env["PYTHONPATH"] = str(PROJECT_ROOT)

    # Use in-memory Firestore for local tests so we don't need Firebase creds.
    env["MOCK_SERVICES_MODE"] = "true"
    env["TESTING"] = "false"
    env.pop("PRODUCTION_MODE", None)

    # Some environments set WORLDAI_GOOGLE_APPLICATION_CREDENTIALS globally.
    # When present, the app requires an explicit dev-mode acknowledgement.
    if env.get("WORLDAI_GOOGLE_APPLICATION_CREDENTIALS") and not env.get("WORLDAI_DEV_MODE"):
        env["WORLDAI_DEV_MODE"] = "true"

    # Load provider keys from Secret Manager if possible.
    _load_secret(env, secret_name="gemini-api-key", env_var="GEMINI_API_KEY")
    _load_secret(env, secret_name="cerebras-api-key", env_var="CEREBRAS_API_KEY")
    _load_secret(env, secret_name="openrouter-api-key", env_var="OPENROUTER_API_KEY")

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    log_path = EVIDENCE_DIR / f"local_mcp_{port}.log"
    log_f = open(log_path, "wb")  # noqa: SIM115

    proc = subprocess.Popen(
        [
            str(python_bin),
            "-m",
            "mvp_site.mcp_api",
            "--http-only",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=log_f,
        stderr=subprocess.STDOUT,
    )

    return LocalServer(proc=proc, base_url=f"http://127.0.0.1:{port}", log_path=log_path)


def create_campaign(client: MCPClient, user_id: str) -> str:
    payload = client.tools_call(
        "create_campaign",
        {
            "user_id": user_id,
            "title": "MCP Dice Test Campaign",
            "character": "Aric the Fighter (STR 16)",
            "setting": "A roadside ambush outside Phandalin",
            "description": "Test campaign for dice roll validation",
        },
    )
    campaign_id = payload.get("campaign_id") or payload.get("campaignId")
    if not isinstance(campaign_id, str) or not campaign_id:
        raise RuntimeError(f"create_campaign returned unexpected payload: {payload}")
    return campaign_id


def update_user_settings(client: MCPClient, *, user_id: str, settings: dict[str, Any]) -> None:
    payload = client.tools_call(
        "update_user_settings",
        {"user_id": user_id, "settings": settings},
    )
    if payload.get("error"):
        raise RuntimeError(f"update_user_settings error: {payload['error']}")


def settings_for_model(model_id: str) -> dict[str, Any]:
    model = model_id.strip()
    model_lower = model.lower()
    if model_lower.startswith("gemini-"):
        return {"llm_provider": "gemini", "gemini_model": model}
    if model_lower.startswith("qwen-") or model_lower in {"zai-glm-4.6", "llama-3.3-70b", "gpt-oss-120b"}:
        return {"llm_provider": "cerebras", "cerebras_model": model}
    if "/" in model_lower:
        return {"llm_provider": "openrouter", "openrouter_model": model}
    raise ValueError(f"Unknown model/provider mapping for: {model}")


def process_action(client: MCPClient, *, user_id: str, campaign_id: str, user_input: str) -> dict[str, Any]:
    return client.tools_call(
        "process_action",
        {"user_id": user_id, "campaign_id": campaign_id, "user_input": user_input, "mode": "character"},
    )


def validate_result(result: dict[str, Any], scenario: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if result.get("error"):
        errors.append(f"server returned error: {result['error']}")
        return errors

    dice_rolls = result.get("dice_rolls") or []
    if not isinstance(dice_rolls, list):
        return [f"dice_rolls not a list: {type(dice_rolls)}"]

    min_dice = int(scenario.get("min_dice_rolls", 1))
    if len(dice_rolls) < min_dice:
        errors.append(f"expected >= {min_dice} dice_rolls, got {len(dice_rolls)}")

    joined = "\n".join(str(x) for x in dice_rolls)
    for s in scenario.get("expect_substrings", []):
        if s not in joined:
            errors.append(f"expected dice_rolls to contain '{s}'")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="MCP dice roll tests (no direct provider calls)")
    parser.add_argument(
        "--server-url",
        default=os.environ.get("MCP_SERVER_URL") or "http://127.0.0.1:8001",
        help="Base server URL (with or without /mcp)",
    )
    parser.add_argument("--start-local", action="store_true", help="Start local MCP server automatically")
    parser.add_argument("--port", type=int, default=0, help="Port for --start-local (0 = random free port)")
    parser.add_argument(
        "--models",
        default=os.environ.get("MCP_TEST_MODELS", ""),
        help=(
            "Comma-separated model IDs to test (e.g. "
            "gemini-3-flash-preview,qwen-3-235b-a22b-instruct-2507). "
            "Defaults to a Gemini+Qwen matrix."
        ),
    )
    args = parser.parse_args()

    local: LocalServer | None = None
    base_url = str(args.server_url)

    try:
        if args.start_local:
            port = int(args.port) if int(args.port) > 0 else _pick_free_port()
            local = start_local_mcp_server(port)
            base_url = local.base_url

        client = MCPClient(base_url, timeout_s=180.0)
        client.wait_healthy(timeout_s=45.0)

        tools = client.tools_list()
        tool_names = {t.get("name") for t in tools if isinstance(t, dict)}
        for required in ("create_campaign", "process_action"):
            if required not in tool_names:
                raise RuntimeError(f"tools/list missing required tool {required}: {sorted(tool_names)}")

        models = [m.strip() for m in (args.models or "").split(",") if m.strip()]
        if not models:
            models = list(DEFAULT_MODEL_MATRIX)

        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        session_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_file = EVIDENCE_DIR / f"run_{session_stamp}.json"

        run_summary: dict[str, Any] = {"server": base_url, "models": [], "scenarios": []}

        ok = True
        for model_id in models:
            model_settings = settings_for_model(model_id)
            user_id = f"mcp-dice-tests-{model_id.replace('/', '-')}-{int(time.time())}"
            update_user_settings(client, user_id=user_id, settings=model_settings)
            campaign_id = create_campaign(client, user_id)

            run_summary["models"].append(
                {"model": model_id, "settings": model_settings, "campaign_id": campaign_id}
            )

            for scenario in TEST_SCENARIOS:
                result = process_action(
                    client,
                    user_id=user_id,
                    campaign_id=campaign_id,
                    user_input=str(scenario["user_input"]),
                )
                errors = validate_result(result, scenario)
                run_summary["scenarios"].append(
                    {
                        "model": model_id,
                        "name": scenario["name"],
                        "user_input": scenario["user_input"],
                        "dice_rolls": result.get("dice_rolls"),
                        "errors": errors,
                    }
                )

                if errors:
                    ok = False
                    print(f"❌ {model_id} :: {scenario['name']}: {errors}")
                else:
                    dice_count = len(result.get("dice_rolls") or [])
                    print(f"✅ {model_id} :: {scenario['name']}: {dice_count} dice roll(s)")

        session_file.write_text(json.dumps(run_summary, indent=2))
        print(f"Evidence: {session_file}")

        if local is not None:
            print(f"Local MCP log: {local.log_path}")

        return 0 if ok else 2
    finally:
        if local is not None:
            local.stop()


if __name__ == "__main__":
    raise SystemExit(main())
