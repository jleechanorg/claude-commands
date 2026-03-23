"""
Smoke test for pair session test task (pair-1771583524-25943).
Tests the greeting utility added as part of the test task.
"""
import sys
import importlib.util
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent
TASK_MODULE = SCRIPTS_DIR / "task_impl.py"


def _load():
    spec = importlib.util.spec_from_file_location("task_impl_smoke", TASK_MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_greet_returns_string():
    mod = _load()
    result = mod.greet("World")
    assert isinstance(result, str), "greet() should return a string"


def test_greet_contains_name():
    mod = _load()
    result = mod.greet("Alice")
    assert "Alice" in result, "greet() should include the name in the output"


def test_greet_default_name():
    mod = _load()
    result = mod.greet()
    assert isinstance(result, str)
    assert len(result) > 0, "greet() with no args should return non-empty string"


def test_add_integers():
    mod = _load()
    assert mod.add(2, 3) == 5
    assert mod.add(0, 0) == 0
    assert mod.add(-1, 1) == 0


def test_add_floats():
    mod = _load()
    assert abs(mod.add(1.5, 2.5) - 4.0) < 1e-9


def test_subtract_integers():
    mod = _load()
    assert mod.subtract(5, 3) == 2
    assert mod.subtract(0, 0) == 0
    assert mod.subtract(-1, -1) == 0
    assert mod.subtract(1, -1) == 2


def test_subtract_floats():
    mod = _load()
    assert abs(mod.subtract(3.5, 1.5) - 2.0) < 1e-9


def test_multiply_integers():
    mod = _load()
    assert mod.multiply(3, 4) == 12
    assert mod.multiply(0, 5) == 0
    assert mod.multiply(-2, 3) == -6


def test_multiply_floats():
    mod = _load()
    assert abs(mod.multiply(2.5, 4.0) - 10.0) < 1e-9


def test_multiply_identity():
    mod = _load()
    assert mod.multiply(7, 1) == 7
    assert mod.multiply(1, 7) == 7
