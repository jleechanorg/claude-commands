"""
Tests for task_impl module.
Covers greet, add, subtract, multiply, divide, modulo, power functions.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from task_impl import greet, add, subtract, multiply, divide, modulo, power


class TestGreet:
    def test_default_greeting(self):
        assert greet() == "Hello, World!"

    def test_custom_name(self):
        assert greet("Alice") == "Hello, Alice!"


class TestAdd:
    def test_add_integers(self):
        assert add(2, 3) == 5

    def test_add_floats(self):
        assert add(1.5, 2.5) == 4.0

    def test_add_identity(self):
        assert add(7, 0) == 7


class TestSubtract:
    def test_subtract_integers(self):
        assert subtract(5, 3) == 2

    def test_subtract_floats(self):
        assert subtract(3.5, 1.5) == 2.0

    def test_subtract_identity(self):
        assert subtract(7, 0) == 7


class TestMultiply:
    def test_multiply_integers(self):
        assert multiply(3, 4) == 12

    def test_multiply_floats(self):
        assert multiply(2.5, 4.0) == 10.0

    def test_multiply_identity(self):
        assert multiply(7, 1) == 7


class TestDivide:
    def test_divide_integers(self):
        assert divide(10, 2) == 5.0

    def test_divide_floats(self):
        assert divide(7.5, 2.5) == 3.0

    def test_divide_identity(self):
        assert divide(7, 1) == 7.0

    def test_divide_by_zero_raises(self):
        with pytest.raises(ZeroDivisionError):
            divide(5, 0)


class TestModulo:
    def test_modulo_integers(self):
        assert modulo(10, 3) == 1

    def test_modulo_even(self):
        assert modulo(10, 2) == 0

    def test_modulo_identity(self):
        assert modulo(7, 1) == 0

    def test_modulo_by_zero_raises(self):
        with pytest.raises(ZeroDivisionError):
            modulo(5, 0)


class TestPower:
    def test_power_integers(self):
        assert power(2, 3) == 8

    def test_power_zero_exponent(self):
        assert power(5, 0) == 1

    def test_power_one_exponent(self):
        assert power(7, 1) == 7

    def test_power_floats(self):
        assert power(4.0, 0.5) == 2.0

    def test_power_zero_base(self):
        assert power(0, 5) == 0
