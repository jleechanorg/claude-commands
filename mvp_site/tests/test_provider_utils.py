from __future__ import annotations

from mvp_site.llm_providers.provider_utils import (
    build_tool_results_prompt,
    execute_openai_tool_calls,
    run_json_first_tool_requests_flow,
    run_openai_json_first_tool_requests_flow,
    run_openai_native_two_phase_flow,
    stringify_chat_parts,
)


def test_execute_openai_tool_calls():
    calls: list[tuple[str, dict]] = []

    def executor(name: str, args: dict) -> dict:
        calls.append((name, args))
        return {"ok": True, "name": name, "args": args}

    tool_calls = [
        {
            "id": "call_1",
            "type": "function",
            "function": {"name": "roll_dice", "arguments": "{\"notation\":\"1d20+5\"}"},
        }
    ]

    results = execute_openai_tool_calls(tool_calls, execute_tool_fn=executor, logger=None)
    assert len(results) == 1
    assert results[0]["tool_call_id"] == "call_1"
    assert results[0]["tool"] == "roll_dice"
    assert results[0]["args"]["notation"] == "1d20+5"
    assert calls[0][0] == "roll_dice"


def test_run_openai_json_first_tool_requests_flow_runs_phase2():
    class Resp:
        def __init__(self, text: str):
            self.text = text

    calls: list[dict] = []

    def gen(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return Resp(
                "{\"tool_requests\":[{\"tool\":\"roll_dice\",\"args\":{\"notation\":\"1d20\"}}]}"
            )
        return Resp("{\"narrative\":\"ok\"}")

    def exec_tool_requests(tool_requests):
        return [
            {
                "tool": tool_requests[0]["tool"],
                "args": tool_requests[0]["args"],
                "result": {"total": 7},
            }
        ]

    def format_results(_results):
        return "- roll_dice: total=7"

    class Logger:
        def info(self, _m): ...

        def warning(self, _m): ...

        def error(self, _m): ...

    out = run_openai_json_first_tool_requests_flow(
        generate_content_fn=gen,
        prompt_contents=["hi"],
        model_name="m",
        system_instruction_text="sys",
        temperature=0.0,
        max_output_tokens=10,
        provider_no_tool_requests_log_prefix="X",
        execute_tool_requests_fn=exec_tool_requests,
        format_tool_results_text_fn=format_results,
        logger=Logger(),
    )
    assert out.text == "{\"narrative\":\"ok\"}"
    assert len(calls) == 2
    phase2_messages = calls[1].get("messages", [])
    assert phase2_messages, "Phase 2 should pass messages"
    assert "Tool results" in phase2_messages[-1]["content"]


def test_run_json_first_tool_requests_flow_runs_phase2():
    class Resp:
        def __init__(self, text: str):
            self.text = text

    phase2_calls: list[object] = []

    def phase1():
        return Resp(
            "{\"tool_requests\":[{\"tool\":\"roll_dice\",\"args\":{\"notation\":\"1d20\"}}]}"
        )

    def extract_text(resp: Resp) -> str:
        return resp.text

    def exec_tool_requests(tool_requests):
        return [
            {
                "tool": tool_requests[0]["tool"],
                "args": tool_requests[0]["args"],
                "result": {"total": 7},
            }
        ]

    def format_results(_results):
        return "- roll_dice: total=7"

    def build_history(*, prompt_contents, phase1_text, tool_results_prompt):
        return {
            "prompt_contents": prompt_contents,
            "phase1_text": phase1_text,
            "tool_results_prompt": tool_results_prompt,
        }

    def phase2(history):
        phase2_calls.append(history)
        return Resp("{\"narrative\":\"ok\"}")

    class Logger:
        def info(self, _m): ...

        def warning(self, _m): ...

        def error(self, _m): ...

    out = run_json_first_tool_requests_flow(
        phase1_generate_fn=phase1,
        extract_text_fn=extract_text,
        prompt_contents=["hi"],
        execute_tool_requests_fn=exec_tool_requests,
        format_tool_results_text_fn=format_results,
        build_history_fn=build_history,
        phase2_generate_fn=phase2,
        logger=Logger(),
        no_tool_requests_log_msg="no tool requests",
    )

    assert out.text == "{\"narrative\":\"ok\"}"
    assert len(phase2_calls) == 1
    history = phase2_calls[0]
    assert history["prompt_contents"] == ["hi"]
    assert "Tool results" in history["tool_results_prompt"]


def test_run_json_first_tool_requests_flow_extracts_json_boundaries_from_wrapped_text():
    class Resp:
        def __init__(self, text: str):
            self.text = text

    phase2_calls: list[object] = []

    def phase1():
        return Resp(
            """```json
{"tool_requests":[{"tool":"roll_dice","args":{"notation":"1d20"}}]}
```"""
        )

    def extract_text(resp: Resp) -> str:
        return resp.text

    def exec_tool_requests(tool_requests):
        return [
            {
                "tool": tool_requests[0]["tool"],
                "args": tool_requests[0]["args"],
                "result": {"total": 7},
            }
        ]

    def format_results(_results):
        return "- roll_dice: total=7"

    def build_history(*, prompt_contents, phase1_text, tool_results_prompt):
        return {
            "prompt_contents": prompt_contents,
            "phase1_text": phase1_text,
            "tool_results_prompt": tool_results_prompt,
        }

    def phase2(history):
        phase2_calls.append(history)
        return Resp('{"narrative":"ok"}')

    class Logger:
        def info(self, _m): ...

        def warning(self, _m): ...

        def error(self, _m): ...

    out = run_json_first_tool_requests_flow(
        phase1_generate_fn=phase1,
        extract_text_fn=extract_text,
        prompt_contents=["hi"],
        execute_tool_requests_fn=exec_tool_requests,
        format_tool_results_text_fn=format_results,
        build_history_fn=build_history,
        phase2_generate_fn=phase2,
        logger=Logger(),
        no_tool_requests_log_msg="no tool requests",
    )

    assert out.text == '{"narrative":"ok"}'
    assert len(phase2_calls) == 1
    assert phase2_calls[0]["phase1_text"].startswith("{")
    assert phase2_calls[0]["phase1_text"].endswith("}")


def test_run_json_first_tool_requests_flow_returns_phase1_when_no_tools():
    class Resp:
        def __init__(self, text: str):
            self.text = text

    phase2_calls: list[object] = []

    def phase1():
        return Resp("{\"narrative\":\"ok\"}")

    def extract_text(resp: Resp) -> str:
        return resp.text

    def exec_tool_requests(_tool_requests):
        raise AssertionError("should not execute tools")

    def format_results(_results):
        raise AssertionError("should not format results")

    def build_history(*, prompt_contents, phase1_text, tool_results_prompt):
        raise AssertionError("should not build history")

    def phase2(history):
        phase2_calls.append(history)
        return Resp("{\"narrative\":\"phase2\"}")

    class Logger:
        def info(self, _m): ...

        def warning(self, _m): ...

        def error(self, _m): ...

    out = run_json_first_tool_requests_flow(
        phase1_generate_fn=phase1,
        extract_text_fn=extract_text,
        prompt_contents=["hi"],
        execute_tool_requests_fn=exec_tool_requests,
        format_tool_results_text_fn=format_results,
        build_history_fn=build_history,
        phase2_generate_fn=phase2,
        logger=Logger(),
        no_tool_requests_log_msg="no tool requests",
    )

    assert out.text == "{\"narrative\":\"ok\"}"
    assert phase2_calls == []


def test_run_openai_native_two_phase_flow_injects_tool_messages():
    class Resp:
        def __init__(self, text: str, tool_calls=None):
            self.text = text
            self._tool_calls = tool_calls

        @property
        def tool_calls(self):
            return self._tool_calls

    calls: list[dict] = []

    tool_calls = [
        {
            "id": "call_1",
            "type": "function",
            "function": {"name": "roll_dice", "arguments": "{\"notation\":\"1d20\"}"},
        }
    ]

    def gen(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return Resp("", tool_calls=tool_calls)
        return Resp("{\"narrative\":\"ok\"}", tool_calls=None)

    def exec_tool(name: str, args: dict):
        return {"tool": name, "args": args, "total": 3}

    class Logger:
        def info(self, _m): ...

        def warning(self, _m): ...

        def error(self, _m): ...

    out = run_openai_native_two_phase_flow(
        generate_content_fn=gen,
        prompt_contents=["hi"],
        model_name="m",
        system_instruction_text="sys",
        temperature=0.0,
        max_output_tokens=10,
        dice_roll_tools=[{"function": {"name": "roll_dice"}}],
        execute_tool_fn=exec_tool,
        logger=Logger(),
    )
    assert out.text == "{\"narrative\":\"ok\"}"
    assert len(calls) == 2
    phase2_messages = calls[1].get("messages", [])
    assert any(m.get("role") == "tool" for m in phase2_messages)
    tool_msgs = [m for m in phase2_messages if m.get("role") == "tool"]
    assert tool_msgs[0]["tool_call_id"] == "call_1"


def test_stringify_chat_parts():
    assert stringify_chat_parts([]) == ""
    assert stringify_chat_parts(["a", "b"]) == "a\n\nb"
    text = stringify_chat_parts([{"x": 1}])
    assert '"x"' in text


def test_build_tool_results_prompt():
    base = build_tool_results_prompt("- roll_dice({}): {\"total\": 1}")
    assert "Tool results" in base
    assert "Do NOT include tool_requests" in base

    with_extra = build_tool_results_prompt("X", extra_instructions="EXTRA")
    assert "EXTRA" in with_extra
