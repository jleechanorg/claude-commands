#!/usr/bin/env python3
"""Model-backed, provider-neutral cmux session resume watchdog."""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Callable, NamedTuple
from zoneinfo import ZoneInfo


HOME = Path(os.environ.get("HOME", str(Path.home())))
STATE_FILE = HOME / ".local/state/cmux-resume-watchdog/state.json"
SOCKET_GLOBS = (
    "/tmp/cmux*.sock",
    "/private/tmp/cmux*.sock",
    str(HOME / ".local/state/cmux/*.sock"),
    str(HOME / "Library/Application Support/cmux/*.sock"),
)
LOCAL_TZ = ZoneInfo("America/Los_Angeles")
WATCHDOG_MARKER = "[cmux-resume-watchdog]"
RESUME_PROMPT = (
    "Continue the in-flight work from where it stopped. Read any STATE.md or "
    f"checkpoint first. {WATCHDOG_MARKER}"
)
DEBOUNCE_SECONDS = 15 * 60
MAX_RESUME_BACKOFF_SECONDS = 60 * 60
# Per-surface attempt ceiling. After MAX_ATTEMPT_COUNT consecutive
# WOULD_RESUME attempts, the surface is parked for 24 hours even if the
# classifier still classifies it as quota/network. Prevents a mislabeled
# surface from spamming cmux send-input indefinitely (verified failure
# mode: state.json showed attempt_count=7 on one surface after PR #38
# merged, with 1h backoff floor = ~24 resumes/day forever).
MAX_ATTEMPT_COUNT = 24
# Process-wide daily resume cap. After DAILY_RESUME_CAP successful sends
# across all surfaces in a single UTC day, the watchdog refuses to send
# any more until midnight UTC. Prevents classifier-mislabel cascade from
# turning into dozens of stray cmux inputs per tick.
DAILY_RESUME_CAP = 50
FASTEMBED_ACTION_THRESHOLD = 0.68
FASTEMBED_CLEAR_THRESHOLD = 0.58
LLM_TIMEOUT_SECONDS = 12




# Mechanical UI/state evidence only. Semantic eligibility is model-owned.
BUSY_RE = re.compile(r"esc to interrupt|Working \(|[✢✻✽∗·✳]\s+\S+…\s+\(", re.I)
RETRY_RE = re.compile(r"\bRetrying in \d+\s*s\b|\battempt\s+\d+/\d+\b", re.I)
TITLE_BUSY_RE = re.compile(r"^[⠀-⣿✳✴]")
AGENT_CHROME_RE = re.compile(
    r"^\s*❯|OpenAI Codex|Use /skills to list available skills|ctx\s+[ー#-]+|bypass permissions",
    re.I | re.M,
)
STRUCTURAL_FAILURE_RE = re.compile(
    r"^\s*[⏺●⎿›»•·]\s|HTTP\s+\d{3}|\bcode\s+\d{3}\b|\"type\"\s*:\s*\"error\"|API Error:|Request rejected|overloaded|rate_limit|stalled mid-stream|idle timeout|fetch failed|connection failed|connection reset|RESOURCE_EXHAUSTED|Too many requests|hit your",
    re.I | re.M,
)
MENU_RE = re.compile(r"Stop and wait for limit to reset|Enter to confirm", re.I)
QUICK_QUOTA_HINT_RE = re.compile(
    r"(?im)(?:^[\s⏺●⎿▝▜█▙▟▛▜✦✧◆◇▶▷▸◀◁◂◃►▻›»•·❘❙❚▒▓░▢▣▤▥▦▧▨▩▪▫]*"
    r"(?:what do you want to do\?|"
    r"1\.\s*stop and wait for limit to reset|"
    r"you've hit your (?:weekly|session|usage|message) limit|"
    r"⚠?\s*individual quota reached"
    r"))",
)

RESET_CLOCK_RE = re.compile(r"\bresets?(?:\s+will)?(?:\s+at)?\s+(\d{1,2})(?::(\d{2}))?\s*([ap]m)\b", re.I)
RESET_ISO_RE = re.compile(r"\b(20\d\d-\d\d-\d\dT\d\d:\d\d(?::\d\d)?(?:Z|[+-]\d\d:\d\d)?)\b")
RESET_DATE_RE = re.compile(r"\bresets?\s+([A-Z][a-z]{2})\s+(\d{1,2}),\s+(20\d\d)\b")
RESET_RELATIVE_RE = re.compile(r"\bresets?\s+in\s+([^\n.]+)", re.I)

ANCHORS = {
    "quota": [
        "account usage allocation is exhausted and work cannot continue until quota resets",
        "token plan usage limit reached upgrade the plan or purchase credits",
        "weekly usage limit reached and resets later",
        "session usage limit reached and resets later",
        "message limit reached and limits will reset",
        "usage limit reached purchase credits or try again later",
        "resource exhausted individual quota reached",
        "too many requests because the API account quota is exhausted",
        "monthly usage limit reached and resets in several days",
        "rate limit error caused by account quota exhaustion",
        "five hour usage limit reached and work is blocked until reset",
        "bugbot usage limit reached for this user or team",
        "overloaded error the service is temporarily overwhelmed by requests",
        "response exceeded the output token maximum limit",
    ],
    "network": [
        "the API connection was lost and the agent stopped waiting for input",
        "network connection failed with ENOTFOUND",
        "request failed because the service is unreachable",
        "connection reset or timed out and the agent could not continue",
        "service unavailable and the last turn failed",
        "API returned an empty or malformed response check for a proxy or gateway intercepting the request",
        "socket hang up or connection refused by the remote host",
        "502 bad gateway or 503 service unavailable response from proxy",
        "response stalled mid-stream or stream idle timeout no chunks received",
    ],
    "clear": [
        "the coding agent is idle and ready for a new user request",
        "the task completed successfully and no API failure is active",
        "source code or documentation discusses rate limits as an example",
        "a bot report mentions another user's usage limit",
        "a shell command prints or searches historical error text",
        "the agent is actively working or retrying a request",
        "github API quota documentation is being discussed",
    ],
}


LLM_PROMPT = """Classify this live terminal tail for an automatic resume watchdog.
Return exactly one token: QUOTA, NETWORK, or CLEAR.

QUOTA means the idle coding agent's last turn is blocked by an account, token,
message, session, weekly, monthly, credit, or subscription usage ceiling.
NETWORK means the idle coding agent's last turn died from connectivity or API
availability. CLEAR means active work, retrying work, a successful/idle shell,
quoted source/docs/history, bot commentary, or uncertainty. Do not explain.

Terminal tail:
{screen}
"""


class Surface(NamedTuple):
    socket: str
    workspace: str
    surface: str
    title: str


class Decision(NamedTuple):
    kind: str | None
    score: float
    path: str
    eligible: bool
    action: str


def resume_backoff_seconds(attempt: int) -> float:
    attempt = max(1, attempt)
    return float(min(DEBOUNCE_SECONDS * (2 ** (attempt - 1)), MAX_RESUME_BACKOFF_SECONDS))


def log(message: str) -> None:
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}", flush=True)


def classification_text(screen: str) -> str:
    marker = screen.rfind(WATCHDOG_MARKER)
    tail = screen[marker + len(WATCHDOG_MARKER) :] if marker >= 0 else screen
    lines = [line.strip() for line in tail.splitlines() if line.strip()]
    return "\n".join(lines[-18:])[-2400:]


def title_is_busy(title: str) -> bool:
    return bool(title) and TITLE_BUSY_RE.match(title.strip()) is not None


def classify_screen(
    screen: str,
    semantic_predict: Callable[[str], tuple[str, float]],
    llm_predict: Callable[[str], str | None] | None = None,
) -> Decision:
    text = classification_text(screen)

    if RETRY_RE.search(text) or BUSY_RE.search(text):
        return Decision(None, 0.0, "fastembed", False, "WAIT_RETRY")

    if QUICK_QUOTA_HINT_RE.search(screen):
        return Decision("quota", FASTEMBED_ACTION_THRESHOLD, "chrome", True, "WOULD_RESUME")

    label, score = semantic_predict(text)
    path = "fastembed"
    label = label.lower()
    structural_evidence = STRUCTURAL_FAILURE_RE.search(text) is not None
    confident_clear = label == "clear" and score >= FASTEMBED_CLEAR_THRESHOLD and not structural_evidence
    has_timeout_signal = structural_evidence or _reset_hint_text(text) is not None
    confident_stall = (
        label in {"quota", "network"}
        and score >= FASTEMBED_ACTION_THRESHOLD
        and has_timeout_signal
    )
    if not confident_clear and not confident_stall:
        if llm_predict is not None and (structural_evidence or score >= 0.45):
            label = (llm_predict(text) or "clear").lower()
            path = "llm-fallback"
        elif structural_evidence and re.search(r"Token Plan|usage limit|429|quota|rate limit|resource.*exhausted|exceeded.*limit|account.*exhausted|overloaded|output token maximum|too many requests|hit your|402|insufficient credits", text, re.I):
            label = "quota"
        elif structural_evidence and re.search(r"empty or malformed|proxy or gateway|connection|connect|network|socket|econnreset|enotfound|etimedout|econnrefused|502|503|504|server error|fetch failed|api error|stalled mid-stream|idle timeout|529|connection closed|2064", text, re.I):
            label = "network"
        else:
            label = "clear"

    action = "WOULD_RESUME" if label in {"quota", "network"} else "NOT_ELIGIBLE"
    kind = label if label in {"quota", "network"} else None
    return Decision(kind, score, path, kind is not None, action)


def _reset_hint_text(screen: str) -> str | None:
    if match := RESET_ISO_RE.search(screen):
        return f"iso:{match.group(1)}"
    if match := RESET_DATE_RE.search(screen):
        return f"date:{match.group(1)} {match.group(2)} {match.group(3)}"
    if match := RESET_RELATIVE_RE.search(screen):
        return f"relative:{match.group(1).lower().strip()}"
    if match := RESET_CLOCK_RE.search(screen):
        return f"clock:{match.group(1)}:{match.group(2)} {match.group(3).lower()}"
    return None


def _cmux_env(socket_path: str) -> dict[str, str]:
    env = os.environ.copy()
    env["CMUX_SOCKET_PATH"] = socket_path
    env["CMUX_SOCKET"] = socket_path
    return env


def _run_cmux(socket_path: str, args: list[str], timeout: int = 12) -> subprocess.CompletedProcess[str]:
    cmux = shutil.which("cmux")
    if not cmux:
        raise RuntimeError("cmux CLI not found")
    return subprocess.run(
        [cmux, *args],
        text=True,
        capture_output=True,
        timeout=timeout,
        env=_cmux_env(socket_path),
        check=False,
    )


def socket_responds(socket_path: str) -> bool:
    try:
        proc = _run_cmux(socket_path, ["ping"], timeout=3)
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0 and "PONG" in proc.stdout


def discover_cmux_sockets() -> list[str]:
    candidates = set()
    for name in ("CMUX_SOCKET_PATH", "CMUX_SOCKET"):
        if os.environ.get(name):
            candidates.add(os.environ[name])
    for pattern in SOCKET_GLOBS:
        candidates.update(glob.glob(pattern))
    canonical = {os.path.realpath(path) for path in candidates}
    return sorted(path for path in canonical if socket_responds(path))


def list_terminal_surfaces(socket_path: str) -> list[Surface]:
    """Enumerate every terminal surface in every pane of every workspace on the
    socket via `cmux tree --all --json`.

    Both `cmux --json tree --all` and `cmux tree --all --json` are accepted by
    cmux 0.64.x — we try both orderings so the watchdog survives a future CLI
    flag-position change. cmux's `tree --all --json` enumerates the *selected*
    AND non-selected terminal surfaces per pane (verified 2026-08-01 against
    cmux 0.64.16: a 41-workspace install reports 54 terminal surfaces, of which
    5 are `selected: false`); no per-workspace fallback enumerator is needed.

    Earlier revisions of this function called a non-existent `cmux list_surfaces
    <UUID>` to fill in inactive tabs — that subcommand was never part of cmux
    and the call returned silently-empty results. Verified via `cmux list_surfaces
    --help` ("Unknown command") + `cmux --help` (no such verb in 0.64.16). The
    per-workspace fallback was removed; the tree output already covers it.
    """
    attempts = (["--json", "tree", "--all"], ["tree", "--all", "--json"])
    proc = None
    for args in attempts:
        try:
            candidate = _run_cmux(socket_path, list(args))
        except subprocess.TimeoutExpired:
            continue
        if candidate.returncode == 0:
            proc = candidate
            break
    if proc is None:
        raise RuntimeError(f"cmux tree failed for {socket_path}")
    data = json.loads(proc.stdout)
    seen: set[tuple[str, str]] = set()
    rows: list[Surface] = []
    for window in data.get("windows", []):
        for workspace in window.get("workspaces", []):
            workspace_ref = workspace.get("ref", "")
            for pane in workspace.get("panes", []):
                for surface in pane.get("surfaces", []):
                    if surface.get("type", surface.get("surface_type")) != "terminal":
                        continue
                    surface_ref = surface.get("ref", "")
                    surface_title = surface.get("title") or workspace.get("title", "")
                    if (workspace_ref, surface_ref) in seen:
                        continue
                    seen.add((workspace_ref, surface_ref))
                    rows.append(
                        Surface(
                            socket_path,
                            workspace_ref,
                            surface_ref,
                            surface_title,
                        )
                    )
    return rows


def read_screen(surface: Surface) -> str:
    proc = _run_cmux(
        surface.socket,
        [
            "read-screen",
            "--workspace",
            surface.workspace,
            "--surface",
            surface.surface,
            "--lines",
            "45",
        ],
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip())
    return proc.stdout


def _llm_command_decision(command: list[str], prompt: str) -> str | None:
    try:
        proc = subprocess.run(
            command,
            input=prompt,
            text=True,
            capture_output=True,
            timeout=LLM_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    matches = re.findall(r"\b(QUOTA|NETWORK|CLEAR)\b", proc.stdout.upper())
    return matches[-1].lower() if matches else None


def classify_with_llm(screen: str) -> str | None:
    prompt = LLM_PROMPT.format(screen=screen[-2400:])
    codex = shutil.which("codex")
    if codex:
        model = os.environ.get("CMUX_RESUME_LLM_MODEL", "gpt-5.3-codex-spark")
        result = _llm_command_decision(
            [
                codex,
                "exec",
                "--skip-git-repo-check",
                "--ephemeral",
                "-s",
                "read-only",
                "--color",
                "never",
                "-m",
                model,
                "-",
            ],
            prompt,
        )
        if result:
            return result
    claude = shutil.which("claude")
    if claude:
        return _llm_command_decision(
            [
                claude,
                "--disable-slash-commands",
                "-p",
                "--output-format",
                "text",
                "--permission-mode",
                "dontAsk",
                "--tools",
                "",
            ],
            prompt,
        )
    return None


def build_semantic_predictor() -> Callable[[str], tuple[str, float]]:
    scripts_dir = str(Path(__file__).resolve().parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    try:
        from semantic_classifier import SemanticClassifier

        classifier = SemanticClassifier(
            anchor_phrases=ANCHORS,
            default_label="ambiguous",
            similarity_threshold=0.0,
        )
        if not classifier.initialize(timeout_seconds=60):
            log("fastembed unavailable after warmup; ambiguous screens will use LLM")
            return lambda _: ("ambiguous", 0.0)
        log("fastembed ready")
        return classifier.predict
    except Exception as exc:
        log(f"fastembed unavailable: {exc}")
        return lambda _: ("ambiguous", 0.0)


def parse_reset_epoch(screen: str, now: dt.datetime | None = None) -> float | None:
    now = now or dt.datetime.now(LOCAL_TZ)
    iso = RESET_ISO_RE.search(screen)
    if iso:
        value = iso.group(1).replace("Z", "+00:00")
        return dt.datetime.fromisoformat(value).timestamp() + 60
    date_match = RESET_DATE_RE.search(screen)
    if date_match:
        value = dt.datetime.strptime(" ".join(date_match.groups()), "%b %d %Y").replace(tzinfo=LOCAL_TZ)
        return value.timestamp() + 60
    relative = RESET_RELATIVE_RE.search(screen)
    if relative:
        segment = relative.group(1).lower()
        total_seconds = 0
        found = False
        for match in re.finditer(
            r"(\d+)\s*(d|day|days|h|hour|hours|m|min|mins|minute|minutes|s|sec|secs|second|seconds)",
            segment,
            re.I,
        ):
            amount, unit = match.groups()
            found = True
            value = int(amount)
            unit_l = unit.lower()
            if unit_l.startswith("d"):
                total_seconds += value * 86400
            elif unit_l.startswith("h"):
                total_seconds += value * 3600
            elif unit_l.startswith("m"):
                total_seconds += value * 60
            else:
                total_seconds += value
        if found:
            return now.timestamp() + max(total_seconds, 60) + 60
    clock = RESET_CLOCK_RE.search(screen)
    if clock:
        hour = int(clock.group(1)) % 12 + (12 if clock.group(3).lower() == "pm" else 0)
        value = now.replace(hour=hour, minute=int(clock.group(2) or 0), second=0, microsecond=0)
        if value < now - dt.timedelta(hours=12):
            value += dt.timedelta(days=1)
        return value.timestamp() + 60
    return None


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp = STATE_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
    temp.replace(STATE_FILE)


def send_resume(surface: Surface, menu_open: bool) -> None:
    if menu_open:
        _run_cmux(
            surface.socket,
            ["send-key", "--workspace", surface.workspace, "--surface", surface.surface, "esc"],
        )
        time.sleep(0.5)
    sent = _run_cmux(
        surface.socket,
        ["send", "--workspace", surface.workspace, "--surface", surface.surface, RESUME_PROMPT],
    )
    if sent.returncode != 0:
        raise RuntimeError(sent.stderr.strip())
    # Let the typed text commit into the input buffer before pressing Enter;
    # without this settle the Enter lands against an empty buffer on fast
    # surfaces and Claude Code replies "did not submit input" instead of
    # actually running the resume prompt.
    time.sleep(0.3)
    entered = _run_cmux(
        surface.socket,
        ["send-key", "--workspace", surface.workspace, "--surface", surface.surface, "enter"],
    )
    if entered.returncode != 0:
        raise RuntimeError(entered.stderr.strip())


def provider_display(title: str, screen: str) -> str:
    text = f"{title}\n{screen}".lower()
    if "codex" in text or "openai" in text:
        return "codex"
    if "claude" in text or "bypass permissions" in text:
        return "claude"
    return "unknown"


def run_tick(args: argparse.Namespace, semantic_predict: Callable[[str], tuple[str, float]]) -> int:
    dry_run = args.dry_run or args.scan_only
    llm_predict = None if dry_run else classify_with_llm
    state = {} if dry_run else load_state()
    now = time.time()
    scanned = eligible = resumed = 0
    sockets = discover_cmux_sockets()
    if not sockets:
        log("tick done sockets=0 surfaces=0 eligible=0 resumed=0")
        return 1

    for socket_path in sockets:
        try:
            surfaces = list_terminal_surfaces(socket_path)
        except (RuntimeError, json.JSONDecodeError) as exc:
            log(f"socket={socket_path} error={exc}")
            continue
        for surface in surfaces:
            if args.surface and surface.surface != args.surface:
                continue
            if args.workspace and surface.workspace != args.workspace:
                continue
            try:
                screen = read_screen(surface)
            except RuntimeError as exc:
                log(f"socket={surface.socket} workspace={surface.workspace} surface={surface.surface} read_error={exc}")
                continue
            if not (AGENT_CHROME_RE.search(screen) or STRUCTURAL_FAILURE_RE.search(screen) or QUICK_QUOTA_HINT_RE.search(screen)):
                continue
            scanned += 1
            decision = classify_screen(screen, semantic_predict, llm_predict)
            action = decision.action
            if decision.eligible and title_is_busy(surface.title) and not dry_run:
                action = "WAIT_RETRY"
            reset_hint = _reset_hint_text(screen)
            reset_epoch = parse_reset_epoch(screen, dt.datetime.fromtimestamp(now, LOCAL_TZ))
            reset_text = "none"
            retry_after = "none"
            key = f"{surface.socket}|{surface.workspace}|{surface.surface}"
            if decision.eligible:
                eligible += 1
                surface_state = dict(state.get(key, {}))
                if reset_epoch:
                    if reset_hint and reset_hint.startswith("relative:"):
                        cached_hint = str(surface_state.get("reset_hint", ""))
                        cached_epoch = surface_state.get("reset_epoch")
                        if cached_hint == reset_hint and cached_epoch:
                            cached = float(cached_epoch)
                            if cached > now:
                                reset_epoch = cached
                            else:
                                reset_epoch = None
                        else:
                            surface_state["reset_hint"] = reset_hint
                    elif reset_hint:
                        surface_state["reset_hint"] = reset_hint
                else:
                    surface_state.pop("reset_hint", None)

                if reset_epoch is None:
                    surface_state.pop("reset_epoch", None)
                elif reset_epoch > now:
                    surface_state["reset_epoch"] = reset_epoch
                else:
                    surface_state.pop("reset_epoch", None)
                if reset_epoch and reset_epoch > now:
                    # Future reset time — keep tracking it in state.json so the
                    # operator can see when the wait ends, but do NOT block the
                    # resume. The agent's input buffer stays primed for when the
                    # limit lifts, and the exponential backoff (separate gate)
                    # continues to throttle the resume cadence.
                    reset_text = dt.datetime.fromtimestamp(reset_epoch, LOCAL_TZ).isoformat()
                last_resume = float(surface_state.get("last_resume", 0))
                attempt_count = int(surface_state.get("attempt_count", 0))
                if not args.no_debounce:
                    next_backoff_seconds = resume_backoff_seconds(attempt_count + 1)
                    if now - last_resume < next_backoff_seconds:
                        action = "WAIT_DEBOUNCE"
                        retry_after = dt.datetime.fromtimestamp(
                            now + (next_backoff_seconds - (now - last_resume)),
                            LOCAL_TZ,
                        ).isoformat()
                    elif attempt_count >= MAX_ATTEMPT_COUNT:
                        # Per-surface ceiling: park this surface for 24h so a
                        # mislabeled one cannot spam cmux send-input. Operator
                        # sees PAUSE_24H + reset_epoch in the log line; the
                        # state.json attempt_count stays clamped until the
                        # surface is re-classified as clear (line 585).
                        action = "PAUSE_24H"
                        retry_after = dt.datetime.fromtimestamp(
                            now + 24 * 60 * 60, LOCAL_TZ,
                        ).isoformat()
                state[key] = surface_state

            if not decision.eligible and not dry_run:
                state.setdefault(key, {}).pop("attempt_count", None)

            log(
                f"socket={surface.socket} workspace={surface.workspace} surface={surface.surface} "
                f"title={surface.title!r} provider={provider_display(surface.title, screen)} "
                f"kind={decision.kind or 'clear'} action={action} path={decision.path} "
                f"score={decision.score:.3f} reset={reset_text} retry_after={retry_after}"
            )

            if action != "WOULD_RESUME" or dry_run:
                continue
            # Process-wide daily resume cap. Reads/writes the cumulative
            # counter at state["_meta"]["daily_resume_count"]; resets to 0
            # when the UTC day rolls over. Operator can override per-tick
            # with --no-debounce; we leave the cap in place even then since
            # it's a process-wide throttle, not a per-surface debounce.
            meta = state.setdefault("_meta", {})
            today_key = dt.datetime.fromtimestamp(now, LOCAL_TZ).strftime("%Y-%m-%d")
            if meta.get("daily_resume_date") != today_key:
                meta["daily_resume_date"] = today_key
                meta["daily_resume_count"] = 0
            if int(meta.get("daily_resume_count", 0)) >= DAILY_RESUME_CAP:
                log(
                    f"DAILY_CAP_HIT socket={surface.socket} workspace={surface.workspace} "
                    f"surface={surface.surface} cap={DAILY_RESUME_CAP} action=SKIP"
                )
                continue
            try:
                send_resume(surface, MENU_RE.search(screen) is not None)
                meta["daily_resume_count"] = int(meta["daily_resume_count"]) + 1
                key = f"{surface.socket}|{surface.workspace}|{surface.surface}"
                surface_state = dict(state.get(key, {}))
                surface_state["last_resume"] = now
                surface_state["kind"] = decision.kind
                surface_state["attempt_count"] = int(surface_state.get("attempt_count", 0)) + 1
                state[key] = surface_state
                save_state(state)
                resumed += 1
                log(
                    f"RESUMED socket={surface.socket} workspace={surface.workspace} "
                    f"surface={surface.surface} kind={decision.kind}"
                )
            except RuntimeError as exc:
                log(f"resume_error socket={surface.socket} workspace={surface.workspace} surface={surface.surface} error={exc}")

    if not dry_run:
        save_state(state)
    log(
        f"tick done sockets={len(sockets)} surfaces={scanned} eligible={eligible} "
        f"resumed={resumed} dry={str(dry_run).lower()}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--scan-only", action="store_true")
    parser.add_argument("--no-debounce", action="store_true")
    parser.add_argument("--daemon", action="store_true")
    parser.add_argument("--interval", type=float, default=120)
    parser.add_argument("--surface")
    parser.add_argument("--workspace")
    args = parser.parse_args(argv)

    semantic_predict = build_semantic_predictor()
    while True:
        status = run_tick(args, semantic_predict)
        if not args.daemon:
            return status
        time.sleep(max(5, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
