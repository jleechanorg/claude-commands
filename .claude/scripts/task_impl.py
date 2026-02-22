"""
Task implementation for pair session test task.
Provides greeting and arithmetic utilities.
"""


def greet(name: str = "World") -> str:
    """Return a greeting string including the given name."""
    return f"Hello, {name}!"


def add(a, b):
    """Return the sum of a and b."""
    return a + b


def subtract(a, b):
    """Return the difference of a and b."""
    return a - b


def multiply(a, b):
    """Return the product of a and b."""
    return a * b


def divide(a, b):
    """Return the quotient of a divided by b. Raises ZeroDivisionError if b is zero."""
    if b == 0:
        raise ZeroDivisionError("division by zero")
    return a / b


def modulo(a, b):
    """Return a modulo b. Raises ZeroDivisionError if b is zero."""
    if b == 0:
        raise ZeroDivisionError("division by zero")
    return a % b


def power(a, b):
    """Return a raised to the power of b."""
    return a ** b
