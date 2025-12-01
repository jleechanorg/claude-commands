import os
import sys
import unittest
from io import StringIO
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import pytest

from mvp_site import logging_util
from mvp_site.decorators import log_exceptions


class TestLogExceptionsDecorator(unittest.TestCase):
    """Test the log_exceptions decorator."""

    def setUp(self):
        """Set up test logging environment."""
        # Create a test logger - must match the logger name used in decorators.py
        self.test_logger = logging_util.getLogger("mvp_site.decorators")
        self.test_logger.setLevel(logging_util.ERROR)

        # Create a string stream to capture log output
        self.log_stream = StringIO()
        self.handler = logging_util.StreamHandler(self.log_stream)
        self.test_logger.addHandler(self.handler)

    def tearDown(self):
        """Clean up test logging environment."""
        self.test_logger.removeHandler(self.handler)
        self.handler.close()

    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves original function metadata."""

        @log_exceptions
        def sample_function():
            """Sample docstring."""
            return "success"

        # Test that function metadata is preserved
        assert sample_function.__name__ == "sample_function"
        assert sample_function.__doc__ == "Sample docstring."

    def test_decorator_successful_execution(self):
        """Test decorator with successful function execution."""

        @log_exceptions
        def successful_function(x, y):
            return x + y

        result = successful_function(2, 3)
        assert result == 5

        # No error should be logged for successful execution
        log_output = self.log_stream.getvalue()
        assert log_output == ""

    def test_decorator_logs_exception_and_reraises(self):
        """Test that decorator logs exceptions and re-raises them."""

        @log_exceptions
        def failing_function(x):
            if x < 0:
                raise ValueError("Negative values not allowed")
            return x * 2

        # Test that exception is logged and re-raised
        with pytest.raises(ValueError, match="Negative values not allowed") as context:
            failing_function(-1)

        assert str(context.value) == "Negative values not allowed"

        # Check that error was logged (args trimmed for security)
        log_output = self.log_stream.getvalue()
        assert "EXCEPTION IN: failing_function" in log_output
        assert "Args: (1 args)" in log_output  # Trimmed: count only, not content
        assert "Kwargs: {}" in log_output
        assert "Error: Negative values not allowed" in log_output
        assert "Traceback:" in log_output
        assert "END EXCEPTION" in log_output

    def test_decorator_logs_function_arguments(self):
        """Test that decorator logs function argument counts (trimmed for security)."""

        @log_exceptions
        def function_with_args(a, b, c=None, d="default"):
            raise RuntimeError("Test error")

        with pytest.raises(RuntimeError, match="Test error"):
            function_with_args("arg1", "arg2", c="kwarg1", d="kwarg2")

        # Args trimmed for security - shows count only, kwargs shows keys only
        log_output = self.log_stream.getvalue()
        assert "Args: (2 args)" in log_output  # Count only, not content
        assert "Kwargs: ['c', 'd']" in log_output  # Keys only, not values

    def test_decorator_with_different_exception_types(self):
        """Test decorator behavior with different exception types."""

        @log_exceptions
        def multi_exception_function(error_type):
            if error_type == "value":
                raise ValueError("Value error occurred")
            if error_type == "type":
                raise TypeError("Type error occurred")
            if error_type == "runtime":
                raise RuntimeError("Runtime error occurred")
            raise Exception("Generic error occurred")

        # Test ValueError
        with pytest.raises(ValueError, match="Value error occurred"):
            multi_exception_function("value")

        # Test TypeError
        with pytest.raises(TypeError, match="Type error occurred"):
            multi_exception_function("type")

        # Test RuntimeError
        with pytest.raises(RuntimeError, match="Runtime error occurred"):
            multi_exception_function("runtime")

        # Test generic Exception
        with pytest.raises(Exception, match="Generic error occurred"):
            multi_exception_function("other")

        # Verify all exceptions were logged
        log_output = self.log_stream.getvalue()
        assert "Value error occurred" in log_output
        assert "Type error occurred" in log_output
        assert "Runtime error occurred" in log_output
        assert "Generic error occurred" in log_output

    def test_decorator_preserves_return_values(self):
        """Test that decorator preserves various return value types."""

        @log_exceptions
        def return_dict():
            return {"key": "value", "number": 42}

        @log_exceptions
        def return_list():
            return [1, 2, 3, "four"]

        @log_exceptions
        def return_none():
            return None

        @log_exceptions
        def return_boolean():
            return True

        # Test that return values are preserved
        assert return_dict() == {"key": "value", "number": 42}
        assert return_list() == [1, 2, 3, "four"]
        assert return_none() is None
        assert return_boolean()

    def test_decorator_with_complex_arguments(self):
        """Test decorator with complex argument types."""

        @log_exceptions
        def complex_args_function(list_arg, dict_arg, **kwargs):
            raise ValueError("Error with complex args")

        test_list = [1, 2, {"nested": "dict"}]
        test_dict = {"key1": "value1", "key2": [1, 2, 3]}

        with pytest.raises(ValueError, match="Error with complex args"):
            complex_args_function(test_list, test_dict, extra_kwarg="test")

        log_output = self.log_stream.getvalue()
        # Verify that complex arguments are logged (exact format may vary)
        assert "EXCEPTION IN: complex_args_function" in log_output
        assert "Args:" in log_output
        assert "Kwargs:" in log_output
        assert "extra_kwarg" in log_output

    @patch("mvp_site.logging_util.error")
    def test_decorator_uses_module_logger(self, mock_error):
        """Test that decorator uses logging_util.error for exception logging."""

        @log_exceptions
        def function_that_fails():
            raise Exception("Test exception")

        with pytest.raises(Exception, match="Test exception"):
            function_that_fails()

        # Verify that logging_util.error was called
        mock_error.assert_called_once()

        # Get the logged message from the call args
        logged_message = mock_error.call_args[0][0]
        assert "EXCEPTION IN: function_that_fails" in logged_message
        assert "Test exception" in logged_message

    def test_nested_decorated_functions(self):
        """Test behavior when decorated functions call other decorated functions."""

        @log_exceptions
        def inner_function():
            raise ValueError("Inner function error")

        @log_exceptions
        def outer_function():
            inner_function()

        with pytest.raises(ValueError, match="Inner function error"):
            outer_function()

        log_output = self.log_stream.getvalue()
        # Both functions should log their exceptions
        assert "EXCEPTION IN: inner_function" in log_output
        assert "EXCEPTION IN: outer_function" in log_output
        assert "Inner function error" in log_output


if __name__ == "__main__":
    unittest.main()
