import unittest
import logging
from unittest.mock import patch, MagicMock
from io import StringIO
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from decorators import log_exceptions


class TestLogExceptionsDecorator(unittest.TestCase):
    """Test the log_exceptions decorator."""
    
    def setUp(self):
        """Set up test logging environment."""
        # Create a test logger
        self.test_logger = logging.getLogger('decorators')
        self.test_logger.setLevel(logging.ERROR)
        
        # Create a string stream to capture log output
        self.log_stream = StringIO()
        self.handler = logging.StreamHandler(self.log_stream)
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
        self.assertEqual(sample_function.__name__, 'sample_function')
        self.assertEqual(sample_function.__doc__, 'Sample docstring.')
    
    def test_decorator_successful_execution(self):
        """Test decorator with successful function execution."""
        @log_exceptions
        def successful_function(x, y):
            return x + y
        
        result = successful_function(2, 3)
        self.assertEqual(result, 5)
        
        # No error should be logged for successful execution
        log_output = self.log_stream.getvalue()
        self.assertEqual(log_output, "")
    
    def test_decorator_logs_exception_and_reraises(self):
        """Test that decorator logs exceptions and re-raises them."""
        @log_exceptions
        def failing_function(x):
            if x < 0:
                raise ValueError("Negative values not allowed")
            return x * 2
        
        # Test that exception is logged and re-raised
        with self.assertRaises(ValueError) as context:
            failing_function(-1)
        
        self.assertEqual(str(context.exception), "Negative values not allowed")
        
        # Check that error was logged
        log_output = self.log_stream.getvalue()
        self.assertIn("EXCEPTION IN: failing_function", log_output)
        self.assertIn("Args: (-1,)", log_output)
        self.assertIn("Kwargs: {}", log_output)
        self.assertIn("Error: Negative values not allowed", log_output)
        self.assertIn("Traceback:", log_output)
        self.assertIn("END EXCEPTION", log_output)
    
    def test_decorator_logs_function_arguments(self):
        """Test that decorator logs function arguments in error messages."""
        @log_exceptions
        def function_with_args(a, b, c=None, d="default"):
            raise RuntimeError("Test error")
        
        with self.assertRaises(RuntimeError):
            function_with_args("arg1", "arg2", c="kwarg1", d="kwarg2")
        
        log_output = self.log_stream.getvalue()
        self.assertIn("Args: ('arg1', 'arg2')", log_output)
        self.assertIn("Kwargs: {'c': 'kwarg1', 'd': 'kwarg2'}", log_output)
    
    def test_decorator_with_different_exception_types(self):
        """Test decorator behavior with different exception types."""
        @log_exceptions
        def multi_exception_function(error_type):
            if error_type == "value":
                raise ValueError("Value error occurred")
            elif error_type == "type":
                raise TypeError("Type error occurred")
            elif error_type == "runtime":
                raise RuntimeError("Runtime error occurred")
            else:
                raise Exception("Generic error occurred")
        
        # Test ValueError
        with self.assertRaises(ValueError):
            multi_exception_function("value")
        
        # Test TypeError
        with self.assertRaises(TypeError):
            multi_exception_function("type")
        
        # Test RuntimeError
        with self.assertRaises(RuntimeError):
            multi_exception_function("runtime")
        
        # Test generic Exception
        with self.assertRaises(Exception):
            multi_exception_function("other")
        
        # Verify all exceptions were logged
        log_output = self.log_stream.getvalue()
        self.assertIn("Value error occurred", log_output)
        self.assertIn("Type error occurred", log_output)
        self.assertIn("Runtime error occurred", log_output)
        self.assertIn("Generic error occurred", log_output)
    
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
        self.assertEqual(return_dict(), {"key": "value", "number": 42})
        self.assertEqual(return_list(), [1, 2, 3, "four"])
        self.assertIsNone(return_none())
        self.assertTrue(return_boolean())
    
    def test_decorator_with_complex_arguments(self):
        """Test decorator with complex argument types."""
        @log_exceptions
        def complex_args_function(list_arg, dict_arg, **kwargs):
            raise ValueError("Error with complex args")
        
        test_list = [1, 2, {"nested": "dict"}]
        test_dict = {"key1": "value1", "key2": [1, 2, 3]}
        
        with self.assertRaises(ValueError):
            complex_args_function(test_list, test_dict, extra_kwarg="test")
        
        log_output = self.log_stream.getvalue()
        # Verify that complex arguments are logged (exact format may vary)
        self.assertIn("EXCEPTION IN: complex_args_function", log_output)
        self.assertIn("Args:", log_output)
        self.assertIn("Kwargs:", log_output)
        self.assertIn("extra_kwarg", log_output)
    
    @patch('decorators.logger')
    def test_decorator_uses_module_logger(self, mock_logger):
        """Test that decorator uses the correct logger instance."""
        @log_exceptions
        def function_that_fails():
            raise Exception("Test exception")
        
        with self.assertRaises(Exception):
            function_that_fails()
        
        # Verify that the module logger's error method was called
        mock_logger.error.assert_called_once()
        
        # Get the logged message
        logged_message = mock_logger.error.call_args[0][0]
        self.assertIn("EXCEPTION IN: function_that_fails", logged_message)
        self.assertIn("Test exception", logged_message)
    
    def test_nested_decorated_functions(self):
        """Test behavior when decorated functions call other decorated functions."""
        @log_exceptions
        def inner_function():
            raise ValueError("Inner function error")
        
        @log_exceptions
        def outer_function():
            inner_function()
        
        with self.assertRaises(ValueError):
            outer_function()
        
        log_output = self.log_stream.getvalue()
        # Both functions should log their exceptions
        self.assertIn("EXCEPTION IN: inner_function", log_output)
        self.assertIn("EXCEPTION IN: outer_function", log_output)
        self.assertIn("Inner function error", log_output)


if __name__ == '__main__':
    unittest.main()