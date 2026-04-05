#!/opt/homebrew/bin/python3
"""cmux-codex auto-approver — model-first, no regex intent detection.

Architecture:
  1. Read each cmux surface screen.
  2. Strip ANSI codes; skip if last non-empty line is an idle shell prompt.
  3. Everything else → classify_tail() (model API call) → ENTER/1/y/SKIP/DENY.

Regex is used only for:
  - ANSI escape code stripping (syntax, not semantics)
  - Idle shell prompt detection (deterministic syntax check, not judgment)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

HOME = Path(os.environ.get("HOME", "$HOME"))
CLI_PATH = os.pathsep.join(
    [
        str(HOME / ".local" / "bin"),
        "/opt/homebrew/bin",
        "/usr/local/bin",
        "/usr/bin",
        "/bin",
        "/usr/sbin",
        "/sbin",
    ]
)
LOG_FILE = Path(os.environ.get("LOG_FILE", "/tmp/cmux-codex-autoapprove.log"))
STATE_FILE = Path(os.environ.get("STATE_FILE", HOME / ".claude/supervisor/cmux-codex-launchd-state.json"))
LINES = int(os.environ.get("LINES", "80"))
TAIL_LINES = int(os.environ.get("TAIL_LINES", "30"))
CLASSIFY_TIMEOUT = int(os.environ.get("CLASSIFY_TIMEOUT", "30"))
ESCALATION_TIMEOUT = int(os.environ.get("ESCALATION_TIMEOUT", "30"))
CODEX_MODEL = os.environ.get("CODEX_MODEL", "")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "")
WORKSPACE_FILTER = os.environ.get("WORKSPACE_FILTER", "")
SURFACE_FILTER = os.environ.get("SURFACE_FILTER", "")
SURFACE_TITLE_FILTER = os.environ.get("SURFACE_TITLE_FILTER", "")
WORKER_POOL_SIZE = max(1, int(os.environ.get("WORKER_POOL_SIZE", "5")))
POST_APPROVE_WATCH_SECONDS = float(os.environ.get("POST_APPROVE_WATCH_SECONDS", "6"))
POST_APPROVE_POLL_SECONDS = float(os.environ.get("POST_APPROVE_POLL_SECONDS", "0.75"))
STUCK_COOLDOWN_SECONDS = float(os.environ.get("STUCK_COOLDOWN_SECONDS", "45"))

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
SHELL_PROMPT_RE = re.compile(r"[$%#>]\s*$")


def is_idle_prompt(line: str) -> bool:
    """True if line is a bare shell prompt with no pending input."""
    stripped = line.strip()
    if not stripped:
        return False
    if stripped in {"❯", ">", ">>"}:
        return True
    return bool(SHELL_PROMPT_RE.search(stripped))


def extract_screen_tail(screen: str) -> str:
    """Strip ANSI, return last TAIL_LINES of screen. Empty string if idle."""
    clean = ANSI_RE.sub("", screen)
    lines = [line.rstrip() for line in clean.splitlines()]
    non_empty = [line for line in lines if line.strip()]
    if not non_empty or is_idle_prompt(non_empty[-1]):
        return ""
    return "\n".join(lines[-TAIL_LINES:])


def log(message: str) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(f"[{timestamp}] {message}\n")


def load_state() -> dict[str, dict[str, float | str]]:
    if not STATE_FILE.exists():
        return {}
    try:
        raw = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    state: dict[str, dict[str, float | str]] = {}
    if not isinstance(raw, dict):
        return state
    for key, value in raw.items():
        if isinstance(value, str):
            state[key] = {"digest": value, "cooldown_until": 0.0}
        elif isinstance(value, dict):
            digest = value.get("digest", "")
            cooldown_until = value.get("cooldown_until", 0.0)
            if isinstance(digest, str):
                try:
                    cooldown = float(cooldown_until)
                except (TypeError, ValueError):
                    cooldown = 0.0
                state[key] = {"digest": digest, "cooldown_until": cooldown}
    return state


def save_state(state: dict[str, dict[str, float | str]]) -> None:
    STATE_FILE.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    env = kwargs.pop("env", None)
    return subprocess.run(cmd, text=True, capture_output=True, env=env, **kwargs)


def find_cli(name: str) -> str | None:
    return shutil.which(name, path=CLI_PATH)


def cmux_tree() -> list[dict[str, str]]:
    proc = run(["cmux", "--json", "tree", "--all"], check=True, timeout=5)
    data = json.loads(proc.stdout)
    rows: list[dict[str, str]] = []
    for window in data.get("windows", []):
        for workspace in window.get("workspaces", []):
            for pane in workspace.get("panes", []):
                for surface in pane.get("surfaces", []):
                    if surface.get("type") != "terminal":
                        continue
                    rows.append(
                        {
                            "workspace": workspace.get("ref", ""),
                            "title": workspace.get("title", ""),
                            "surface": surface.get("ref", ""),
                            "surface_title": surface.get("title", ""),
                        }
                    )
    return rows


def matches_filter(value: str, flt: str) -> bool:
    return not flt or flt in value


def read_screen(workspace: str, surface: str) -> str:
    try:
        proc = run(
            ["cmux", "read-screen", "--workspace", workspace, "--surface", surface, "--lines", str(LINES)],
            timeout=3,
        )
        return proc.stdout
    except subprocess.TimeoutExpired:
        log(f"READ_TIMEOUT workspace={workspace} surface={surface}")
        return ""


def extract_decision_token(text: str) -> str:
    for token in text.split():
        if token in {"ENTER", "1", "y", "SKIP", "DENY"}:
            return token
    return "SKIP"


def classify_with_codex(
    prompt_path: str,
    out_path: str,
    exec_log_path: str,
    env: dict[str, str],
    timeout_seconds: int,
) -> str:
    codex_bin = find_cli("codex")
    if not codex_bin:
        raise FileNotFoundError("codex")
    cmd = [
        "/opt/homebrew/bin/timeout",
        str(timeout_seconds),
        codex_bin,
        "exec",
        "--skip-git-repo-check",
        "--ephemeral",
        "-s",
        "read-only",
        "--color",
        "never",
    ]
    if CODEX_MODEL:
        cmd.extend(["-m", CODEX_MODEL])
    cmd.extend(["-o", out_path, "-"])

    with open(prompt_path, "r", encoding="utf-8") as prompt_in, open(exec_log_path, "w", encoding="utf-8") as exec_log:
        subprocess.run(
            cmd,
            stdin=prompt_in,
            stdout=exec_log,
            stderr=subprocess.STDOUT,
            env=env,
            timeout=timeout_seconds + 2,
            check=True,
        )
    out_text = Path(out_path).read_text(encoding="utf-8").strip()
    return extract_decision_token(out_text)


def classify_with_claude(
    prompt_path: str,
    exec_log_path: str,
    env: dict[str, str],
    timeout_seconds: int,
) -> str:
    claude_bin = find_cli("claude")
    if not claude_bin:
        raise FileNotFoundError("claude")
    cmd = [
        "/opt/homebrew/bin/timeout",
        str(timeout_seconds),
        claude_bin,
        "--disable-slash-commands",
        "-p",
        "--output-format",
        "text",
        "--permission-mode",
        "dontAsk",
        "--tools",
        "",
    ]
    if CLAUDE_MODEL:
        cmd.extend(["--model", CLAUDE_MODEL])

    with open(prompt_path, "r", encoding="utf-8") as prompt_in, open(exec_log_path, "w+", encoding="utf-8") as exec_log:
        subprocess.run(
            cmd,
            stdin=prompt_in,
            stdout=exec_log,
            stderr=subprocess.STDOUT,
            env=env,
            timeout=timeout_seconds + 2,
            check=True,
        )
        exec_log.seek(0)
        return extract_decision_token(exec_log.read().strip())


def classify_tail(
    workspace: str,
    title: str,
    surface: str,
    surface_title: str,
    tail_text: str,
    extra_context: str = "",
    timeout_seconds: int | None = None,
) -> str:
    effective_timeout = timeout_seconds or CLASSIFY_TIMEOUT
    prompt = f"""You are classifying a live cmux terminal screen for an approval bot.

Return exactly one token from this set:
ENTER
1
y
SKIP
DENY

Decision rules:
- Return ENTER when the screen is an approval dialog and the affirmative choice is already highlighted or selected.
- Return 1 when the screen is an approval dialog with a numbered affirmative option but Enter is not clearly the right key.
- Return y when the screen expects a y/n style approval.
- Return DENY only for clearly dangerous or destructive requests.
- Return SKIP if this is not an approval dialog or if you are unsure.
- Do not explain.

Context:
workspace_ref: {workspace}
workspace_title: {title}
surface_ref: {surface}
surface_title: {surface_title}

{extra_context}

Screen:
{tail_text}
"""

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as prompt_fh, \
        tempfile.NamedTemporaryFile("w+", encoding="utf-8", delete=False) as out_fh, \
        tempfile.NamedTemporaryFile("w+", encoding="utf-8", delete=False) as log_fh:
        prompt_fh.write(prompt)
        prompt_path = prompt_fh.name
        out_path = out_fh.name
        exec_log_path = log_fh.name

    try:
        env = {
            "HOME": str(HOME),
            "PATH": CLI_PATH,
            "SSH_AUTH_SOCK": os.environ.get("SSH_AUTH_SOCK", ""),
        }
        if CODEX_MODEL:
            env["CODEX_MODEL"] = CODEX_MODEL
        if CLAUDE_MODEL:
            env["CLAUDE_MODEL"] = CLAUDE_MODEL

        providers: list[tuple[str, Callable[[], str]]] = []
        if find_cli("codex"):
            providers.append(
                ("codex", lambda: classify_with_codex(prompt_path, out_path, exec_log_path, env, effective_timeout))
            )
        if find_cli("claude"):
            providers.append(
                ("claude", lambda: classify_with_claude(prompt_path, exec_log_path, env, effective_timeout))
            )
        if not providers:
            log(f"CLASSIFY_UNAVAILABLE workspace={workspace} surface={surface} providers=none")
            return "SKIP"

        for provider_name, provider in providers:
            try:
                decision = provider()
                log(f"CLASSIFY_PROVIDER workspace={workspace} surface={surface} provider={provider_name}")
                return decision
            except FileNotFoundError:
                log(f"CLASSIFY_UNAVAILABLE workspace={workspace} surface={surface} provider={provider_name}")
                continue
            except subprocess.TimeoutExpired:
                log(f"CLASSIFY_TIMEOUT workspace={workspace} surface={surface} provider={provider_name}")
                return "SKIP"
            except subprocess.CalledProcessError as exc:
                exec_log = Path(exec_log_path).read_text(encoding="utf-8", errors="ignore")
                if exc.returncode == 127 or "command not found" in exec_log.lower():
                    log(f"CLASSIFY_UNAVAILABLE workspace={workspace} surface={surface} provider={provider_name} exit={exc.returncode}")
                    continue
                if "not logged in" in exec_log.lower():
                    log(f"CLASSIFY_UNAVAILABLE workspace={workspace} surface={surface} provider={provider_name} reason=not_logged_in")
                    continue
                if "rate_limit_error" in exec_log.lower() or "rate limit" in exec_log.lower():
                    log(f"CLASSIFY_RATE_LIMIT workspace={workspace} surface={surface} provider={provider_name}")
                    return "SKIP"
                log(f"CLASSIFY_ERROR workspace={workspace} surface={surface} provider={provider_name} exit={exc.returncode}")
                return "SKIP"

        return "SKIP"
    finally:
        for path in (prompt_path, out_path, exec_log_path):
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass


def approve(workspace: str, surface: str, decision: str) -> None:
    if decision == "ENTER":
        subprocess.run(["cmux", "send-key", "--workspace", workspace, "--surface", surface, "Enter"], check=True, timeout=3)
    elif decision == "1":
        subprocess.run(["cmux", "send", "--workspace", workspace, "--surface", surface, "1"], check=True, timeout=3)
    elif decision == "y":
        subprocess.run(["cmux", "send", "--workspace", workspace, "--surface", surface, "y"], check=True, timeout=3)
    log(f"APPROVE_SENT workspace={workspace} surface={surface} decision={decision}")


def digest_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def monitor_after_approve(
    workspace: str,
    title: str,
    surface: str,
    surface_title: str,
    prior_tail_text: str,
    prior_decision: str,
) -> tuple[str, float]:
    deadline = time.time() + POST_APPROVE_WATCH_SECONDS
    prior_digest = digest_text(prior_tail_text)
    latest_tail = prior_tail_text
    latest_digest = prior_digest

    while time.time() < deadline:
        time.sleep(POST_APPROVE_POLL_SECONDS)
        screen = read_screen(workspace, surface)
        if not screen:
            log(f"POST_APPROVE_PROGRESS workspace={workspace} surface={surface} status=screen_unreadable")
            return "", 0.0

        latest_tail = extract_screen_tail(screen)
        if not latest_tail:
            log(f"POST_APPROVE_PROGRESS workspace={workspace} surface={surface} status=prompt_cleared")
            return "", 0.0

        latest_digest = digest_text(latest_tail)
        if latest_digest != prior_digest:
            log(f"POST_APPROVE_PROGRESS workspace={workspace} surface={surface} status=prompt_changed")
            return latest_tail, 0.0

    log(
        f"POST_APPROVE_STUCK workspace={workspace} surface={surface} "
        f"previous_decision={prior_decision}"
    )
    followup_decision = classify_tail(
        workspace,
        title,
        surface,
        surface_title,
        latest_tail,
        extra_context=(
            "Important follow-up context:\n"
            f"- The bot already sent: {prior_decision}\n"
            "- The terminal did not continue after that action.\n"
            "- Choose the next key to try, or SKIP if human attention is required.\n"
        ),
        timeout_seconds=ESCALATION_TIMEOUT,
    )
    log(f"POST_APPROVE_ESCALATION workspace={workspace} surface={surface} decision={followup_decision}")
    if followup_decision in {"ENTER", "1", "y"} and followup_decision != prior_decision:
        approve(workspace, surface, followup_decision)
        return latest_tail, time.time() + STUCK_COOLDOWN_SECONDS

    return latest_tail, time.time() + STUCK_COOLDOWN_SECONDS


def process_surface(
    row: dict[str, str],
    state_entry: dict[str, float | str],
    now: float,
) -> tuple[str, dict[str, float | str] | None]:
    state_key = f'{row["workspace"]}:{row["surface"]}'

    screen = read_screen(row["workspace"], row["surface"])
    if not screen:
        return state_key, None

    tail_text = extract_screen_tail(screen)
    if not tail_text:
        return state_key, None

    digest = digest_text(tail_text)
    cooldown_until = float(state_entry.get("cooldown_until", 0.0) or 0.0)
    if state_entry.get("digest") == digest and cooldown_until > now:
        return state_key, {
            "digest": str(state_entry.get("digest", "")),
            "cooldown_until": cooldown_until,
        }

    log(
        f'CANDIDATE workspace={row["workspace"]} title={row["title"]} '
        f'surface={row["surface"]} surface_title={row["surface_title"]}'
    )
    decision = classify_tail(row["workspace"], row["title"], row["surface"], row["surface_title"], tail_text)
    log(f'DECISION workspace={row["workspace"]} surface={row["surface"]} decision={decision}')

    if decision in {"ENTER", "1", "y"}:
        approve(row["workspace"], row["surface"], decision)
        watched_tail, updated_cooldown_until = monitor_after_approve(
            row["workspace"],
            row["title"],
            row["surface"],
            row["surface_title"],
            tail_text,
            decision,
        )
        return state_key, {
            "digest": digest_text(watched_tail) if watched_tail else digest,
            "cooldown_until": updated_cooldown_until,
        }

    return state_key, {
        "digest": digest,
        "cooldown_until": time.time() + STUCK_COOLDOWN_SECONDS,
    }


def run_scan() -> int:
    log(
        "cmux-codex-launchd-python start "
        f"lines={LINES} tail_lines={TAIL_LINES} timeout={CLASSIFY_TIMEOUT}s "
        f"model={CODEX_MODEL or 'default'} workspace_filter={WORKSPACE_FILTER or '*'} "
        f"surface_filter={SURFACE_FILTER or '*'} surface_title_filter={SURFACE_TITLE_FILTER or '*'} "
        f"workers={WORKER_POOL_SIZE} escalation_timeout={ESCALATION_TIMEOUT}s"
    )
    state = load_state()
    now = time.time()
    rows_to_process: list[tuple[dict[str, str], dict[str, float | str]]] = []
    for row in cmux_tree():
        state_key = f'{row["workspace"]}:{row["surface"]}'
        if not (matches_filter(row["workspace"], WORKSPACE_FILTER) or matches_filter(row["title"], WORKSPACE_FILTER)):
            continue
        if not matches_filter(row["surface"], SURFACE_FILTER):
            continue
        if not matches_filter(row["surface_title"], SURFACE_TITLE_FILTER):
            continue
        rows_to_process.append((row, state.get(state_key, {"digest": "", "cooldown_until": 0.0})))

    next_state: dict[str, dict[str, float | str]] = {}
    with ThreadPoolExecutor(max_workers=min(WORKER_POOL_SIZE, max(1, len(rows_to_process)))) as executor:
        futures = [executor.submit(process_surface, row, state_entry, now) for row, state_entry in rows_to_process]
        for future in as_completed(futures):
            state_key, state_update = future.result()
            if state_update is not None:
                next_state[state_key] = state_update

    save_state(next_state)
    return 0


def main() -> int:
    return run_scan()


if __name__ == "__main__":
    raise SystemExit(main())
