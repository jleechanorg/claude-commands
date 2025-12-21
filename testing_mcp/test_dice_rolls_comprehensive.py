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
import re
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from pathlib import Path

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
        "allow_single_on_miss": True,
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

DEFAULT_DISTRIBUTION_ROLLS = 200
EDGE_CASES = [
    {"notation": "invalid", "expected_total": 0, "expected_rolls": 0},
    {"notation": "1d0+5", "expected_total": 5, "expected_rolls": 0},
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


def start_local_mcp_server(
    port: int,
    *,
    env_overrides: dict[str, str] | None = None,
    log_dir: Path | None = None,
) -> LocalServer:
    """Start an HTTP-only MCP server (env overrides control mock/production behavior)."""
    python_bin = PROJECT_ROOT / "venv" / "bin" / "python"
    if not python_bin.exists():
        python_bin = Path(sys.executable)

    env = dict(os.environ)
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    if env_overrides:
        env.update(env_overrides)

    # Some environments set WORLDAI_GOOGLE_APPLICATION_CREDENTIALS globally.
    # When present, the app requires an explicit dev-mode acknowledgement.
    if env.get("WORLDAI_GOOGLE_APPLICATION_CREDENTIALS") and not env.get("WORLDAI_DEV_MODE"):
        env["WORLDAI_DEV_MODE"] = "true"

    # Load provider keys from Secret Manager if possible.
    _load_secret(env, secret_name="gemini-api-key", env_var="GEMINI_API_KEY")
    _load_secret(env, secret_name="cerebras-api-key", env_var="CEREBRAS_API_KEY")
    _load_secret(env, secret_name="openrouter-api-key", env_var="OPENROUTER_API_KEY")

    log_root = log_dir or EVIDENCE_DIR
    log_root.mkdir(parents=True, exist_ok=True)
    log_path = log_root / f"local_mcp_{port}.log"
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


def get_campaign_state(client: MCPClient, *, user_id: str, campaign_id: str) -> dict[str, Any]:
    payload = client.tools_call(
        "get_campaign_state",
        {"user_id": user_id, "campaign_id": campaign_id},
    )
    if payload.get("error"):
        raise RuntimeError(f"get_campaign_state error: {payload['error']}")
    return payload


def update_campaign(client: MCPClient, *, user_id: str, campaign_id: str, updates: dict[str, Any]) -> None:
    payload = client.tools_call(
        "update_campaign",
        {"user_id": user_id, "campaign_id": campaign_id, "updates": updates},
    )
    if payload.get("error"):
        raise RuntimeError(f"update_campaign error: {payload['error']}")


def ensure_game_state_seed(
    client: MCPClient, *, user_id: str, campaign_id: str
) -> bool:
    state_payload = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    game_state = state_payload.get("game_state") or {}
    pc = game_state.get("player_character_data") or {}
    npc_data = game_state.get("npc_data") or {}

    missing_pc = not (pc.get("name") and pc.get("attributes"))
    missing_goblin = not any(
        isinstance(value, dict) and value.get("name", "").lower() == "goblin"
        for value in npc_data.values()
    )

    if not missing_pc and not missing_goblin:
        return False

    seeded_pc = {
        "string_id": "pc_aric_001",
        "name": "Aric",
        "level": 1,
        "class": "Fighter",
        "hp_current": 12,
        "hp_max": 12,
        "attributes": {
            "strength": 16,
            "dexterity": 12,
            "constitution": 14,
            "intelligence": 10,
            "wisdom": 10,
            "charisma": 12,
        },
        "proficiency_bonus": 2,
    }
    seeded_goblin = {
        "string_id": "npc_goblin_001",
        "name": "Goblin",
        "hp_current": 7,
        "hp_max": 7,
        "armor_class": 13,
        "status": "healthy",
        "present": True,
    }

    state_changes: dict[str, Any] = {}
    if missing_pc:
        state_changes["player_character_data"] = seeded_pc
    if missing_goblin:
        state_changes["npc_data"] = dict(npc_data)
        state_changes["npc_data"]["npc_goblin_001"] = seeded_goblin

    god_mode_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(state_changes)}"
    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=god_mode_payload,
    )
    if result.get("error"):
        raise RuntimeError(f"GOD_MODE_UPDATE_STATE failed: {result['error']}")
    return True


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
    if scenario.get("allow_single_on_miss") and len(dice_rolls) == 1:
        roll_text = " ".join(str(x) for x in dice_rolls)
        if "miss" in roll_text.lower():
            min_dice = 1
    if len(dice_rolls) < min_dice:
        errors.append(f"expected >= {min_dice} dice_rolls, got {len(dice_rolls)}")

    joined = "\n".join(str(x) for x in dice_rolls)
    for s in scenario.get("expect_substrings", []):
        if s not in joined:
            errors.append(f"expected dice_rolls to contain '{s}'")

    return errors


def _get_debug_info(result: dict[str, Any]) -> dict[str, Any]:
    debug_info = result.get("debug_info") or {}
    return debug_info if isinstance(debug_info, dict) else {}


def _extract_actual_provider_model(result: dict[str, Any]) -> tuple[str | None, str | None]:
    debug_info = _get_debug_info(result)
    provider = result.get("llm_provider") or debug_info.get("llm_provider")
    model = result.get("llm_model") or debug_info.get("llm_model")
    return (str(provider) if provider else None, str(model) if model else None)


def _write_raw_response(
    evidence_dir: Path, *, model_id: str, scenario_name: str, raw_text: str
) -> str:
    safe_model = model_id.replace("/", "-")
    safe_name = scenario_name.lower().replace(" ", "_").replace("/", "-")
    filename = f"raw_{safe_model}_{safe_name}.txt"
    path = evidence_dir / filename
    path.write_text(raw_text)
    return str(path)


def _roll_dice_tool(client: MCPClient, notation: str, purpose: str) -> dict[str, Any]:
    payload = client.tools_call("roll_dice", {"notation": notation, "purpose": purpose})
    if payload.get("error"):
        raise RuntimeError(f"roll_dice error: {payload['error']}")
    if payload.get("result"):
        return payload["result"]
    return payload


def _distribution_stats(rolls: list[int]) -> dict[str, Any]:
    if not rolls:
        return {"count": 0}
    mean = sum(rolls) / len(rolls)
    return {
        "count": len(rolls),
        "min": min(rolls),
        "max": max(rolls),
        "mean": mean,
    }


def _extract_totals_from_dice_rolls(dice_rolls: list[str]) -> list[int]:
    totals: list[int] = []
    for roll in dice_rolls:
        if not isinstance(roll, str):
            continue
        match = re.findall(r"=\s*(-?\d+)\s*(?:vs|\(|$)", roll)
        if match:
            totals.append(int(match[-1]))
    return totals


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
        "--real-services",
        action="store_true",
        help="Disable mock services and forced test model selection for local server.",
    )
    parser.add_argument(
        "--production-mode",
        action="store_true",
        help="Set PRODUCTION_MODE=true for local server (requires real credentials).",
    )
    parser.add_argument(
        "--evidence",
        action="store_true",
        help="Enable evidence capture (raw LLM, tool results, provider/model metadata).",
    )
    parser.add_argument(
        "--raw-max-chars",
        type=int,
        default=20000,
        help="Max chars of raw LLM output to capture when --evidence is enabled.",
    )
    parser.add_argument(
        "--dice-seed",
        default=os.environ.get("DICE_SEED", ""),
        help="Optional deterministic dice seed for server-side rolls.",
    )
    parser.add_argument(
        "--enable-dice-tool",
        action="store_true",
        help="Expose test-only roll_dice MCP tool (requires server restart).",
    )
    parser.add_argument(
        "--distribution-rolls",
        type=int,
        default=0,
        help="Run server-side dice distribution tests with this many rolls.",
    )
    parser.add_argument(
        "--evidence-dir",
        default=str(EVIDENCE_DIR),
        help="Directory to store evidence artifacts.",
    )
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
    evidence_dir = Path(args.evidence_dir)

    if args.evidence and args.distribution_rolls == 0:
        args.distribution_rolls = DEFAULT_DISTRIBUTION_ROLLS

    try:
        if args.start_local:
            port = int(args.port) if int(args.port) > 0 else _pick_free_port()
            env_overrides: dict[str, str] = {}
            if args.real_services or args.evidence:
                env_overrides["MOCK_SERVICES_MODE"] = "false"
            else:
                env_overrides["MOCK_SERVICES_MODE"] = "true"
            env_overrides["TESTING"] = "false"
            env_overrides["FORCE_TEST_MODEL"] = "false"
            env_overrides["FAST_TESTS"] = "false"
            if args.production_mode:
                env_overrides["PRODUCTION_MODE"] = "true"
            if args.evidence:
                env_overrides["CAPTURE_EVIDENCE"] = "true"
                env_overrides["CAPTURE_RAW_LLM"] = "true"
                env_overrides["CAPTURE_TOOL_RESULTS"] = "true"
                env_overrides["CAPTURE_RAW_LLM_MAX_CHARS"] = str(args.raw_max_chars)
            if args.enable_dice_tool or args.distribution_rolls > 0 or args.evidence:
                env_overrides["ENABLE_DICE_TEST_TOOL"] = "true"
            if args.dice_seed:
                env_overrides["DICE_SEED"] = str(args.dice_seed)
            local = start_local_mcp_server(port, env_overrides=env_overrides, log_dir=evidence_dir)
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

        evidence_dir.mkdir(parents=True, exist_ok=True)
        session_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = evidence_dir / session_stamp
        session_dir.mkdir(parents=True, exist_ok=True)
        session_file = session_dir / "run.json"

        run_summary: dict[str, Any] = {
            "server": base_url,
            "models": [],
            "scenarios": [],
            "env": {
                "evidence": args.evidence,
                "real_services": args.real_services,
                "production_mode": args.production_mode,
                "dice_seed": args.dice_seed or None,
                "distribution_rolls": args.distribution_rolls,
            },
            "distribution_tests": [],
            "edge_case_tests": [],
        }

        ok = True
        for model_id in models:
            model_settings = settings_for_model(model_id)
            if args.evidence:
                model_settings["debug_mode"] = True
            user_id = f"mcp-dice-tests-{model_id.replace('/', '-')}-{int(time.time())}"
            update_user_settings(client, user_id=user_id, settings=model_settings)
            campaign_id = create_campaign(client, user_id)
            seeded_character = ensure_game_state_seed(
                client, user_id=user_id, campaign_id=campaign_id
            )

            run_summary["models"].append(
                {
                    "model": model_id,
                    "settings": model_settings,
                    "campaign_id": campaign_id,
                    "seeded_character": seeded_character,
                }
            )

            for scenario in TEST_SCENARIOS:
                result = process_action(
                    client,
                    user_id=user_id,
                    campaign_id=campaign_id,
                    user_input=str(scenario["user_input"]),
                )
                errors = validate_result(result, scenario)
                debug_info = _get_debug_info(result)
                actual_provider, actual_model = _extract_actual_provider_model(result)
                dice_strategy = result.get("dice_strategy") or debug_info.get("dice_strategy")
                tool_results = result.get("tool_results") or debug_info.get("tool_results")
                raw_response = result.get("raw_llm_response") or debug_info.get("raw_response_text")
                raw_response_path = None
                if isinstance(raw_response, str) and raw_response:
                    raw_response_path = _write_raw_response(
                        session_dir,
                        model_id=model_id,
                        scenario_name=scenario["name"],
                        raw_text=raw_response,
                    )

                if actual_model and actual_model != model_id:
                    errors.append(
                        f"actual model mismatch: expected {model_id}, got {actual_model}"
                    )
                if dice_strategy == "native_two_phase" and (
                    scenario.get("min_dice_rolls", 0) > 0
                ):
                    if not tool_results:
                        errors.append("expected server tool_results for native_two_phase dice")
                if dice_strategy == "code_execution" and (
                    scenario.get("min_dice_rolls", 0) > 0
                ):
                    if not (debug_info.get("code_execution_used") or debug_info.get("stdout")):
                        errors.append("missing code_execution evidence for dice roll")
                if tool_results:
                    expected_totals: list[int] = []
                    for tool_result in tool_results:
                        result_payload = (
                            tool_result.get("result")
                            if isinstance(tool_result, dict)
                            else None
                        )
                        if not isinstance(result_payload, dict):
                            continue

                        def _coerce_total(value: Any) -> int | None:
                            try:
                                return int(value)
                            except (TypeError, ValueError):
                                return None

                        attack_roll = result_payload.get("attack_roll")
                        if isinstance(attack_roll, dict):
                            total = _coerce_total(attack_roll.get("total"))
                            if total is not None:
                                expected_totals.append(total)

                        damage = result_payload.get("damage")
                        if isinstance(damage, dict):
                            total = _coerce_total(damage.get("total"))
                            if total is not None:
                                expected_totals.append(total)

                        total = _coerce_total(result_payload.get("total"))
                        if total is not None:
                            expected_totals.append(total)

                    parsed_totals = _extract_totals_from_dice_rolls(
                        [str(x) for x in (result.get("dice_rolls") or [])]
                    )
                    if expected_totals:
                        if not parsed_totals:
                            errors.append(
                                f"dice_rolls missing totals for tool_results: expected {expected_totals}"
                            )
                        else:
                            missing = [
                                total for total in expected_totals if total not in parsed_totals
                            ]
                            if missing:
                                errors.append(
                                    f"dice_rolls/tool_results mismatch: missing totals {missing}, parsed {parsed_totals}"
                                )

                run_summary["scenarios"].append(
                    {
                        "model": model_id,
                        "name": scenario["name"],
                        "user_input": scenario["user_input"],
                        "dice_rolls": result.get("dice_rolls"),
                        "dice_audit_events": result.get("dice_audit_events"),
                        "actual_provider": actual_provider,
                        "actual_model": actual_model,
                        "dice_strategy": dice_strategy,
                        "tool_results": tool_results,
                        "raw_response_path": raw_response_path,
                        "errors": errors,
                    }
                )

                if errors:
                    ok = False
                    print(f"❌ {model_id} :: {scenario['name']}: {errors}")
                else:
                    dice_count = len(result.get("dice_rolls") or [])
                    print(f"✅ {model_id} :: {scenario['name']}: {dice_count} dice roll(s)")

        roll_dice_available = "roll_dice" in tool_names
        if args.distribution_rolls > 0:
            if not roll_dice_available:
                run_summary["distribution_tests"].append(
                    {"skipped": True, "reason": "roll_dice tool not available"}
                )
                print("⚠️ distribution tests skipped (roll_dice tool unavailable)")
            else:
                for notation, expected_mean, tolerance in (
                    ("1d6", 3.5, 0.7),
                    ("1d20", 10.5, 2.5),
                ):
                    rolls: list[int] = []
                    errors: list[str] = []
                    for _ in range(args.distribution_rolls):
                        result = _roll_dice_tool(client, notation, "distribution_test")
                        roll_values = result.get("rolls") if isinstance(result, dict) else None
                        if isinstance(roll_values, list) and roll_values:
                            rolls.append(int(roll_values[0]))
                        elif isinstance(result, dict) and result.get("total") is not None:
                            rolls.append(int(result["total"]))

                    stats = _distribution_stats(rolls)
                    if stats.get("count", 0) == 0:
                        errors.append("no rolls collected")
                    else:
                        mean = stats.get("mean")
                        if mean is not None and not (expected_mean - tolerance <= mean <= expected_mean + tolerance):
                            errors.append(
                                f"mean out of bounds: {mean:.2f} not in [{expected_mean - tolerance:.2f}, {expected_mean + tolerance:.2f}]"
                            )
                        if stats["count"] >= 20:
                            faces = {}
                            for value in rolls:
                                faces[value] = faces.get(value, 0) + 1
                            die_size = int(notation.split("d")[1])
                            if len(faces) < min(stats["count"], die_size):
                                errors.append("not all faces appeared in sample")

                    run_summary["distribution_tests"].append(
                        {
                            "notation": notation,
                            "rolls": stats.get("count", 0),
                            "stats": stats,
                            "errors": errors,
                        }
                    )
                    if errors:
                        ok = False
                        print(f"❌ distribution {notation}: {errors}")
                    else:
                        print(f"✅ distribution {notation}: mean={stats.get('mean'):.2f}")

        if roll_dice_available:
            for case in EDGE_CASES:
                errors: list[str] = []
                result = _roll_dice_tool(client, case["notation"], "edge_case_test")
                rolls = result.get("rolls") if isinstance(result, dict) else []
                total = result.get("total") if isinstance(result, dict) else None
                if len(rolls or []) != case["expected_rolls"]:
                    errors.append(
                        f"expected {case['expected_rolls']} rolls, got {len(rolls or [])}"
                    )
                if total != case["expected_total"]:
                    errors.append(
                        f"expected total {case['expected_total']}, got {total}"
                    )
                run_summary["edge_case_tests"].append(
                    {
                        "notation": case["notation"],
                        "result": result,
                        "errors": errors,
                    }
                )
                if errors:
                    ok = False
                    print(f"❌ edge case {case['notation']}: {errors}")
                else:
                    print(f"✅ edge case {case['notation']}")
        else:
            run_summary["edge_case_tests"].append(
                {"skipped": True, "reason": "roll_dice tool not available"}
            )

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
