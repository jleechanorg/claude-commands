#!/usr/bin/env python3
"""Parse `claude --verbose --output-format=json` JSONL output.

Used to verify a Claude-Code wrapper against a third-party provider actually
completes end-to-end (model returned an answer) even when stdout looks empty
in non-TTY bash contexts. Emits ASSISTANT_TEXT + RESULT metrics.

Usage: python3 parse_claude_verbose.py < /tmp/claudeor.out
"""
import sys, json


def emit(d):
    if d.get("type") == "assistant":
        for c in d.get("message", {}).get("content", []):
            if c.get("type") == "text":
                t = c.get("text", "").strip()
                if t:
                    print("ASSISTANT_TEXT:", repr(t))
            if c.get("type") == "thinking":
                th = c.get("thinking", "").strip()
                if th:
                    print("THINKING:", repr(th)[:160])
    if d.get("type") == "result":
        print("COST=", d.get("total_cost_usd"),
              "IS_ERROR=", d.get("is_error"),
              "STOP_REASON=", d.get("stop_reason"))
        print("MODEL_USAGE=", json.dumps(d.get("modelUsage", {})))
        print("SESSION_ID=", d.get("session_id"))
        return True  # signal end
    return False


def main():
    finished = False
    for line in sys.stdin:
        line = line.strip().lstrip("\r")
        if not line:
            continue
        if line.startswith("["):
            inner = line[1:-1]
            for obj in inner.split("},{"):
                if not obj.startswith("{"):
                    obj = "{" + obj
                if not obj.endswith("}"):
                    obj = obj + "}"
                try:
                    if emit(json.loads(obj)):
                        finished = True
                        return
                except Exception:
                    continue
        elif line.startswith("{") and line.endswith("}"):
            try:
                if emit(json.loads(line)):
                    finished = True
                    return
            except Exception:
                continue
    if not finished:
        print("(no result event — did the wrapper actually run?)")
        sys.exit(1)


if __name__ == "__main__":
    main()
