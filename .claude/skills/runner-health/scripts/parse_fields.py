#!/usr/bin/env python3
"""parse_fields.py — JSON parser for runner-health.sh master script.

Usage:
  python3 parse_fields.py api "$API_JSON"   # extract api fields
  python3 parse_fields.py docker "$JSON"    # extract docker line
  python3 parse_fields.py lima "$JSON"      # extract lima line
  python3 parse_fields.py verdict "$API" "$DOCKER" "$LIMA" "$JEFF"  # compute verdict

Reads JSON from argv[2], outputs formatted text to stdout.
"""
import json
import sys


def api_fields(api_json: str) -> str:
    api = json.loads(api_json)
    on = api.get("runners", {}).get("online", "?")
    bu = api.get("runners", {}).get("busy", "?")
    lb = api.get("runners", {}).get("by_arch", {}).get("linux_x64", {}).get("busy", "?")
    return f"{on} {bu} {lb}"


def docker_line(docker_json: str) -> str:
    d = json.loads(docker_json)
    if d.get("error"):
        return f"error: {d['error']}"
    c = d.get("containers", {})
    up = c.get("up", "?")
    re_ = c.get("restarting", "?")
    return f"{up} up, {re_} restarting"


def lima_line(lima_json: str) -> str:
    d = json.loads(lima_json)
    if d.get("error"):
        return f"error: {d['error']}"
    i = d.get("instances", [])
    if not i:
        return "(no instances)"
    parts = ", ".join(f"{x.get('name')}={x.get('status')}" for x in i)
    return f"{len(i)} instance(s) — {parts}"


def jeff_line(jeff_json: str) -> str:
    d = json.loads(jeff_json)
    r = d.get("reachable", "?")
    if r is True:
        return "reachable"
    if r is False:
        return "UNREACHABLE (different wifi)"
    return "?"


def compute_verdict(api_json: str, docker_json: str, lima_json: str, jeff_json: str) -> str:
    api = json.loads(api_json)
    docker = json.loads(docker_json)
    lima = json.loads(lima_json)
    jeff = json.loads(jeff_json)

    on = api.get("runners", {}).get("online", "?")
    bu = api.get("runners", {}).get("busy", "?")
    lb = api.get("runners", {}).get("by_arch", {}).get("linux_x64", {}).get("busy", "?")
    de = docker.get("error") or ""
    jr = jeff.get("reachable", "?")

    if isinstance(on, int) and on < 22:
        return f"RED|Only {on}/22 runners online on GitHub"
    if isinstance(bu, int) and bu < 1:
        return "AMBER|0 runners busy (no active jobs)"
    if isinstance(lb, int) and lb < 1:
        verdict = "AMBER|0 Linux runners busy (jeff-ubuntu may be down)"
        if jr is False:
            return "GREEN|jeff-ubuntu unreachable (different wifi) but Linux runners busy=true — host is up, this network can't route"
        return verdict
    if de:
        return f"AMBER|Docker error: {de}"
    return "GREEN|All signals nominal"


def main():
    if len(sys.argv) < 2:
        print("usage: parse_fields.py {api|docker|lima|jeff|verdict} <json> [more json]", file=sys.stderr)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "api":
        print(api_fields(sys.argv[2]))
    elif cmd == "docker":
        print(docker_line(sys.argv[2]))
    elif cmd == "lima":
        print(lima_line(sys.argv[2]))
    elif cmd == "jeff":
        print(jeff_line(sys.argv[2]))
    elif cmd == "verdict":
        result = compute_verdict(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
        print(result)
    else:
        print(f"unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
