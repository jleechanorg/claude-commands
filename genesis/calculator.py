#!/usr/bin/env python3
"""
Simple Calculator with Error Handling
=====================================

A command-line calculator that performs basic arithmetic operations
with comprehensive error handling and input validation.
"""

import sys


class Calculator:
    """Simple calculator with error handling."""

    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        return a + b

    def subtract(self, a: float, b: float) -> float:
        """Subtract second number from first."""
        return a - b

    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b

    def divide(self, a: float, b: float) -> float:
        """Divide first number by second with zero division handling."""
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return a / b

    def calculate(self, num1: float, operator: str, num2: float) -> float:
        """Perform calculation based on operator."""
        operations = {
            '+': self.add,
            '-': self.subtract,
            '*': self.multiply,
            '/': self.divide
        }

        if operator not in operations:
            raise ValueError(f"Invalid operator: {operator}. Use +, -, *, /")

        return operations[operator](num1, num2)


def get_number_input(prompt: str) -> float:
    """Get and validate numeric input from user."""
    while True:
        try:
            value = input(prompt).strip()
            if not value:
                print("Error: Please enter a number")
                continue
            return float(value)
        except ValueError:
            print("Error: Invalid number format. Please enter a valid number.")
        except KeyboardInterrupt:
            print("\nCalculation cancelled.")
            sys.exit(0)


def get_operator_input() -> str:
    """Get and validate operator input from user."""
    valid_operators = ['+', '-', '*', '/']
    while True:
        try:
            operator = input("Enter operator (+, -, *, /): ").strip()
            if not operator:
                print("Error: Please enter an operator")
                continue
            if operator not in valid_operators:
                print(f"Error: Invalid operator '{operator}'. Use +, -, *, /")
                continue
            return operator
        except KeyboardInterrupt:
            print("\nCalculation cancelled.")
            sys.exit(0)


def run_calculator():
    """Main calculator interface."""
    print("=== Simple Calculator ===")
    print("Perform basic arithmetic operations with error handling")
    print("Press Ctrl+C to exit\n")

    calculator = Calculator()

    while True:
        try:
            print("-" * 30)
            num1 = get_number_input("Enter first number: ")
            operator = get_operator_input()
            num2 = get_number_input("Enter second number: ")

            result = calculator.calculate(num1, operator, num2)
            print(f"\nResult: {num1} {operator} {num2} = {result}")

            # Ask if user wants to continue
            while True:
                try:
                    continue_calc = input("\nContinue? (y/n): ").strip().lower()
                    if continue_calc in ['y', 'yes']:
                        break
                    if continue_calc in ['n', 'no']:
                        print("Calculator closing. Goodbye!")
                        return
                    print("Please enter 'y' for yes or 'n' for no.")
                except KeyboardInterrupt:
                    print("\nCalculator closing. Goodbye!")
                    return

        except ZeroDivisionError as e:
            print(f"Error: {e}")
        except ValueError as e:
            print(f"Error: {e}")
        except KeyboardInterrupt:
            print("\nCalculator closing. Goodbye!")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")


def run_tests():
    """Test calculator functionality with edge cases."""
    print("=== Running Calculator Tests ===\n")

    calculator = Calculator()
    test_cases = [
        # (num1, operator, num2, expected_result, should_raise_exception)
        (10, '+', 5, 15, None),
        (10, '-', 3, 7, None),
        (4, '*', 6, 24, None),
        (15, '/', 3, 5, None),
        (10, '/', 0, None, ZeroDivisionError),
        (5.5, '+', 2.3, 7.8, None),
        (-10, '+', 5, -5, None),
        (-4, '*', -3, 12, None),
        (0, '*', 100, 0, None),
        (7, '%', 3, None, ValueError),  # Invalid operator
    ]

    passed = 0
    total = len(test_cases)

    for i, (num1, op, num2, expected, expected_exception) in enumerate(test_cases, 1):
        try:
            result = calculator.calculate(num1, op, num2)
            if expected_exception:
                print(f"Test {i}: FAILED - Expected {expected_exception.__name__} but got result {result}")
            elif abs(result - expected) < 1e-10:  # Handle floating point precision
                print(f"Test {i}: PASSED - {num1} {op} {num2} = {result}")
                passed += 1
            else:
                print(f"Test {i}: FAILED - Expected {expected}, got {result}")

        except Exception as e:
            if expected_exception and isinstance(e, expected_exception):
                print(f"Test {i}: PASSED - Correctly raised {type(e).__name__}: {e}")
                passed += 1
            else:
                print(f"Test {i}: FAILED - Unexpected exception: {type(e).__name__}: {e}")

    print("\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")

    return passed == total


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        success = run_tests()
        sys.exit(0 if success else 1)
    else:
        run_calculator()
