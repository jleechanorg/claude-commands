import types

from mvp_site.llm_providers.gemini_provider import (
    extract_code_execution_evidence,
    extract_code_execution_parts_summary,
)


class _FakeExecutableCode:
    def __init__(self, *, language: str = "python", code: str = "print('hi')"):
        self.language = language
        self.code = code


class _FakeCodeExecutionResult:
    def __init__(self, *, outcome: str = "SUCCESS", output: str = "hi\n"):
        self.outcome = outcome
        self.output = output


class _FakePart:
    def __init__(self, *, executable_code=None, code_execution_result=None):
        self.executable_code = executable_code
        self.code_execution_result = code_execution_result


class _FakeContent:
    def __init__(self, parts):
        self.parts = parts


class _FakeCandidate:
    def __init__(self, content):
        self.content = content


def test_extract_code_execution_evidence_detects_parts():
    resp = types.SimpleNamespace(
        candidates=[
            _FakeCandidate(
                _FakeContent(
                    parts=[
                        _FakePart(executable_code=_FakeExecutableCode()),
                        _FakePart(code_execution_result=_FakeCodeExecutionResult()),
                    ]
                )
            )
        ]
    )

    evidence = extract_code_execution_evidence(resp)
    assert evidence["code_execution_used"] is True
    assert evidence["executable_code_parts"] == 1
    assert evidence["code_execution_result_parts"] == 1


def test_extract_code_execution_parts_summary_truncates():
    big_code = "x=" + ("1" * 2000)
    resp = types.SimpleNamespace(
        candidates=[
            _FakeCandidate(
                _FakeContent(
                    parts=[
                        _FakePart(executable_code=_FakeExecutableCode(code=big_code)),
                        _FakePart(code_execution_result=_FakeCodeExecutionResult(output="y" * 2000)),
                    ]
                )
            )
        ]
    )

    summary = extract_code_execution_parts_summary(resp, max_parts=2, max_chars=50)
    assert summary["candidates"] == 1
    assert summary["parts"] == 2
    assert len(summary["executable_code_samples"]) == 1
    assert len(summary["code_execution_result_samples"]) == 1
    assert summary["executable_code_samples"][0]["code"].endswith("...(truncated)")
    assert summary["code_execution_result_samples"][0]["output"].endswith("...(truncated)")

