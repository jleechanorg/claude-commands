#!/usr/bin/env python3
"""
slack_mcp_post.py — post a message to Slack via the slack-mcp-server HTTP endpoint
with explicit thread_ts honoring. Use this when the gateway's send_message path
self-roots the thread (proven bug class) and you need a reliable, thread-correct
post.

Three durable post paths, in order of preference:
  1. mcp__slack__conversations_add_message(channel_id, thread_ts, text)
     — runtime must surface the tool. Verify with `tools/list`.
     LIMITATION (2026-06-09 /learn finding): the server's content_type enum is
     ONLY ["text/markdown"]. Slack renders markdown as Block Kit rich_text,
     which fragments emoji shortcodes like :large_green_circle: into
     character-by-character segments. If you need plain-text rendering,
     use path (3) with mrkdwn=False instead — the MCP server cannot post plain.
  2. HTTP-direct to http://127.0.0.1:8006/mcp via JSON-RPC 2.0 over streamable-http
     — use when (1) is not surfaced. Requires an MCP session id (initialize first).
     Same text/markdown limitation as (1).
  3. curl against https://slack.com/api/chat.postMessage with HERMES_SLACK_BOT_TOKEN
     and mrkdwn=False — last-resort fallback that DOES support plain rendering.
     Body must include thread_ts=<incoming's thread_ts or ts>. Use this when
     Block Kit rendering mangles your emoji/bullets/headers.

Verification step (always do this after posting): pull
mcp__slack__conversations_replies(thread_ts=<expected_parent_ts>) and confirm
the new message's MsgID appears with ThreadTs == expected_parent_ts. If not,
the post was routed somewhere else — surface that to the user, do not retry.

When to use text/plain (the plain-render escape hatch):
  The MCP server can't. Use chat.postMessage with `{"mrkdwn": false}` instead.
  Slack's chat.postMessage will then render the text field as a single literal
  string with no mrkdwn parsing — no bold/italic/emoji shortcode expansion, but
  also no Block Kit fragmentation.

Usage:
  # Post markdown (MCP server, default)
  python3 slack_mcp_post.py --channel C0AH3RY3DK6 --thread-ts 1781021369.023829 \\
      --text "*Reply text*"

  # Post plain text (chat.postMessage fallback, no Block Kit fragmentation)
  python3 slack_mcp_post.py --channel C0AH3RY3DK6 --thread-ts 1781021369.023829 \\
      --text "Reply text" --fallback slack-api

  # Top-level (no thread)
  python3 slack_mcp_post.py --channel C0AH3RY3DK6 \\
      --text "Top-level message"

  # Probe what the server offers
  python3 slack_mcp_post.py --probe-tools
  python3 slack_mcp_post.py --probe-session
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Optional

MCP_URL = os.environ.get("SLACK_MCP_URL", "http://127.0.0.1:8006/mcp")
SLACK_API_URL = "https://slack.com/api/chat.postMessage"
DEFAULT_CONTENT_TYPE = "text/markdown"  # only value the MCP server accepts
PLAIN_FALLBACK_FLAG = "mrkdwn=False"  # chat.postMessage path supports this


def _http_json_rpc(method: str, params: dict, session_id: Optional[str] = None,
                   raw: bool = False, expect_response: bool = True) -> dict:
    """Single JSON-RPC 2.0 call to the MCP server. Handles session id handshake.

    `expect_response=False` is for notifications (e.g. notifications/initialized)
    which the server acknowledges with 202 + empty body and no JSON-RPC response.
    """
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    req = urllib.request.Request(MCP_URL, data=json.dumps(body).encode(),
                                 headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        payload = resp.read().decode()
        # resp.headers is case-insensitive in real HTTP responses (urllib uses
        # email.message.Message). But our test fake uses a plain dict. Look
        # up case-insensitively so both work.
        sid = None
        for k, v in resp.headers.items():
            if k.lower() == "mcp-session-id":
                sid = v
                break
        if sid is None:
            sid = session_id
    if not expect_response or raw:
        return {"_raw": payload, "_session": sid}
    # streamable-http may include event-stream framing; strip it
    text = payload.strip()
    if not text:
        # Empty body — likely a notification ack
        return {"_session": sid, "result": None}
    if text.startswith("event:"):
        # last line should be the actual JSON
        for line in reversed(text.splitlines()):
            line = line.strip()
            if line.startswith("data:"):
                return {"_session": sid, **json.loads(line[5:].strip())}
    return {"_session": sid, **json.loads(text)}


def probe_tools() -> tuple:
    """Initialize a session and return (tool_names, session_id)."""
    init = _http_json_rpc("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "slack_mcp_post", "version": "1"},
    })
    sid = init.get("_session")
    # notifications/initialized is a notification — server returns 202 + empty
    # body, no JSON-RPC response. Don't try to parse it.
    _http_json_rpc("notifications/initialized", {}, session_id=sid,
                   expect_response=False)
    tools_resp = _http_json_rpc("tools/list", {}, session_id=sid)
    tools = tools_resp.get("result", {}).get("tools") or []
    return [t["name"] for t in tools], sid


def probe_session() -> str:
    """Just initialize a session and print the id (useful for chained calls)."""
    init = _http_json_rpc("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "slack_mcp_post", "version": "1"},
    })
    return init.get("_session", "")


def post_via_mcp(channel_id: str, thread_ts: Optional[str], text: str,
                content_type: str = DEFAULT_CONTENT_TYPE) -> dict:
    """Post via the MCP server's conversations_add_message tool. Honors thread_ts.
    content_type is forced to text/markdown because that is the ONLY enum value
    the server accepts (2026-06-09 /learn finding)."""
    tool_names, sid = probe_tools()
    if "conversations_add_message" not in tool_names:
        raise RuntimeError(
            f"slack-mcp-server does not expose conversations_add_message. "
            f"Registered: {tool_names}. Fall back to chat.postMessage."
        )
    args = {"channel_id": channel_id, "text": text,
            "content_type": content_type}  # server only accepts text/markdown
    if thread_ts:
        args["thread_ts"] = thread_ts
    resp = _http_json_rpc("tools/call",
                          {"name": "conversations_add_message", "arguments": args},
                          session_id=sid)
    if "error" in resp:
        raise RuntimeError(f"MCP tools/call error: {resp['error']}")
    return resp


def post_via_slack_api(channel_id: str, thread_ts: Optional[str], text: str,
                       content_type: str = DEFAULT_CONTENT_TYPE) -> dict:
    """Last-resort fallback: direct chat.postMessage with bot token from env."""
    token = os.environ.get("HERMES_SLACK_BOT_TOKEN") or os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        raise RuntimeError("HERMES_SLACK_BOT_TOKEN env var required for fallback")
    body = {"channel": channel_id, "text": text}
    if thread_ts:
        body["thread_ts"] = thread_ts
    # chat.postMessage accepts text in mrkdwn by default; for true plain, use blocks
    if content_type == "text/plain":
        body["mrkdwn"] = False
    req = urllib.request.Request(
        SLACK_API_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json; charset=utf-8",
                 "Authorization": f"Bearer {token}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def post_via_xoxp(channel_id: str, thread_ts: Optional[str], text: str,
                  content_type: str = DEFAULT_CONTENT_TYPE,
                  identity_disclosure: bool = True) -> dict:
    """Cross-workspace fallback: chat.postMessage with XOX-P user token.

    Used when the bot token is scoped to a different workspace than the channel
    lives in (Failure 5f in slack-thread-routing-investigation skill). The user
    token crosses workspace boundaries where the bot token cannot. The post
    appears as the user ($USER), not the hermes bot — pass
    identity_disclosure=False to suppress the disclaimer if you've already
    included one in the body text.
    """
    token = os.environ.get("SLACK_USER_TOKEN")
    if not token:
        # Fallback chain mirrors launchd-env-wrapper.sh:_extract_bashrc_var pattern.
        # Order matters: check ~/.bashrc BEFORE ~/.profile. .bashrc is the live
        # source of truth for tokens (especially ones defined after the interactive
        # guard `if [ -z "$PS1" ]; then return; fi`); .profile is sourced earlier
        # in the dotfile chain and may carry a stale token that would shadow the
        # rotated .bashrc value. This is the same failure mode that produced
        # bashrc-profile-xapp-drift-blocks-launchd (memory).
        for source_path in ("~/.bashrc", "~/.profile"):
            try:
                path = os.path.expanduser(source_path)
                if not os.path.exists(path):
                    continue
                with open(path) as f:
                    for line in f:
                        # match `export SLACK_USER_TOKEN=...` (with optional leading spaces)
                        stripped = line.lstrip()
                        if not stripped.startswith("export SLACK_USER_TOKEN="):
                            continue
                        val = stripped.split("=", 1)[1].strip()
                        # strip surrounding quotes (single or double) per bashrc convention
                        if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
                            val = val[1:-1]
                        if val:
                            token = val
                            break
                if token:
                    break
            except Exception:
                # Don't mask a found token in a later source due to an earlier source
                # failing to read; just continue to the next.
                continue
    if not token:
        raise RuntimeError(
            "SLACK_USER_TOKEN not found in env, ~/.profile, or ~/.bashrc. "
            "For xoxp cross-workspace fallback, set SLACK_USER_TOKEN (xoxp-...) in "
            "one of those locations. Launchd processes should use the "
            "~/.hermes/scripts/launchd-env-wrapper.sh _extract_bashrc_var pattern "
            "(see SOUL.md COMMIT `slack-cross-workspace-fallback-xoxp`)."
        )
    # Identity disclosure: prepend a one-line note that this came from user identity
    if identity_disclosure and not text.startswith("(posted via"):
        text = (
            "(posted via $USER identity — cross-workspace bot-token hard-block "
            "would have stalled this reply; using XOX-P user token per SOUL.md "
            "COMMIT `slack-cross-workspace-fallback-xoxp`.)\n\n"
            + text
        )
    body = {"channel": channel_id, "text": text}
    if thread_ts:
        body["thread_ts"] = thread_ts
    if content_type == "text/plain":
        body["mrkdwn"] = False
    req = urllib.request.Request(
        SLACK_API_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json; charset=utf-8",
                 "Authorization": f"Bearer {token}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def _is_slack_ok(payload: object) -> bool:
    """chat.postMessage returns HTTP 200 with {"ok": false, "error": "..."}
    on workspace-scope failures (not_in_channel, channel_not_found,
    missing_scope, etc.). Treat those as fallthrough triggers, not success."""
    if not isinstance(payload, dict):
        return False
    # ok=True is required; sometimes "warning" is also set alongside ok=True
    if payload.get("ok") is True:
        return True
    # Explicit "ok": false → definite fallthrough
    if payload.get("ok") is False:
        return False
    # Older payloads without "ok" field: assume success if we got a "ts"
    return "ts" in payload


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--channel", help="Slack channel id (Cxxxxx) or #name")
    p.add_argument("--thread-ts", default=None,
                   help="Parent thread_ts. Omit for top-level channel post.")
    p.add_argument("--text", help="Message body")
    p.add_argument("--content-type", default=DEFAULT_CONTENT_TYPE,
                   choices=["text/markdown"],
                   help="MCP server only accepts text/markdown. For plain text, "
                        "use --fallback slack-api (chat.postMessage with mrkdwn=False).")
    p.add_argument("--no-thread", action="store_true",
                   help="Force top-level (overrides --thread-ts)")
    p.add_argument("--probe-tools", action="store_true",
                   help="Initialize session + list server tools, then exit")
    p.add_argument("--probe-session", action="store_true",
                   help="Initialize session + print session id, then exit")
    p.add_argument("--fallback", choices=["mcp", "slack-api", "xoxp", "auto"],
                   default="auto",
                   help="Post path: mcp (HTTP-direct), slack-api (bot token chat.postMessage), "
                        "xoxp (user token cross-workspace fallback per Failure 5f), "
                        "or auto (try mcp then slack-api with xoxp fallthrough on ok=false)")
    return p


def _run(args: argparse.Namespace) -> int:
    """Run with an already-parsed Namespace. Testable entrypoint."""
    if args.probe_tools:
        names, sid = probe_tools()
        print(f"Session: {sid}")
        print(f"Tools ({len(names)}):")
        for n in names:
            print(f"  - {n}")
        return 0
    if args.probe_session:
        sid = probe_session()
        print(sid or "(no session id returned)")
        return 0

    if not args.channel or not args.text:
        print("ERROR: --channel and --text required (or use --probe-tools)", file=sys.stderr)
        return 2

    thread_ts = None if args.no_thread else args.thread_ts
    # Honor: incoming's thread_ts wins; if top-level, thread_ts == own ts post-facto
    # (caller's responsibility — the skill requires this verification step)

    try:
        if args.fallback in ("mcp", "auto"):
            try:
                result = post_via_mcp(args.channel, thread_ts, args.text,
                                      args.content_type)
                # post_via_mcp wraps in JSON-RPC; check the inner result
                inner = ((result.get("result") or {}).get("result")
                         if isinstance(result, dict) else None)
                if isinstance(inner, dict) and not _is_slack_ok(inner):
                    if args.fallback == "mcp":
                        raise RuntimeError(f"MCP returned Slack error: {inner}")
                    print(f"mcp path Slack error: {inner.get('error')}; falling back",
                          file=sys.stderr)
                else:
                    print(json.dumps({"path": "mcp", "result": result}, indent=2))
                    return 0
            except Exception as e:
                if args.fallback == "mcp":
                    raise
                print(f"mcp path failed: {e}; falling back to chat.postMessage",
                      file=sys.stderr)

        if args.fallback == "xoxp":
            result = post_via_xoxp(args.channel, thread_ts, args.text,
                                   args.content_type)
            print(json.dumps({"path": "xoxp", "result": result}, indent=2))
            return 0

        # --fallback auto OR --fallback slack-api: try bot-token chat.postMessage first
        result = post_via_slack_api(args.channel, thread_ts, args.text,
                                    args.content_type)
        if not _is_slack_ok(result):
            err = result.get("error", "unknown")
            # In --fallback auto mode, fall through to XOX-P ONLY for cross-workspace
            # bot-token hard-block signatures. Other bot/config errors (missing_scope,
            # invalid_auth, account_inactive, etc.) should surface normally — a token
            # rotation gap or a wrong-channel typo should not silently promote to
            # the user-identity post path.
            CROSS_WORKSPACE_ERRORS = {
                "not_in_channel",
                "channel_not_found",
                "restricted_action",
                "team_access_not_granted",
                "missing_scope",  # scope is workspace-scoped on free-tier bot tokens
            }
            if args.fallback == "auto" and err in CROSS_WORKSPACE_ERRORS:
                print(
                    f"slack-api path returned ok=false ({err}); "
                    f"auto-falling-back to xoxp (cross-workspace hard-block per "
                    f"SOUL.md COMMIT slack-cross-workspace-fallback-xoxp)",
                    file=sys.stderr,
                )
                result = post_via_xoxp(args.channel, thread_ts, args.text,
                                       args.content_type)
                print(json.dumps({"path": "xoxp", "result": result}, indent=2))
                return 0
            # slack-api mode OR non-cross-workspace error in auto mode: report loudly
            # (don't exit 0 on Slack error so callers can detect the wrong-channel case)
            print(
                f"slack-api returned ok=false: error={err} result={result}",
                file=sys.stderr,
            )
            return 3  # distinct exit code for Slack API error
        print(json.dumps({"path": "slack-api", "result": result}, indent=2))
        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint. Pass argv for testability; None uses sys.argv[1:]."""
    return _run(_build_parser().parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
