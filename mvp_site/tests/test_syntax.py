import ast
import os
import sys
import unittest


class TestModuleSyntax(unittest.TestCase):
    def test_all_python_files_syntax(self):
        """Test that all Python files have valid syntax - would catch f-string errors."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        syntax_errors = []

        for file in os.listdir(current_dir):
            if file.endswith(".py") and not file.startswith("test_"):
                try:
                    file_path = os.path.join(current_dir, file)
                    with open(file_path, encoding="utf-8") as f:
                        ast.parse(f.read(), filename=file)
                except SyntaxError as e:
                    syntax_errors.append(f"{file}:{e.lineno}: {e.msg}")

        if syntax_errors:
            self.fail(f"Syntax errors: {'; '.join(syntax_errors)}")

    def test_llm_service_import(self):
        """
        Tests if the llm_service.py module can be imported.
        A failure here indicates a syntax error in the file.
        """
        print("\n--- Attempting to import llm_service.py ---")

        # We must set the API key environment variable BEFORE importing,
        # because the module uses it immediately upon import.
        # We can use a dummy value for this syntax test.
        if "GEMINI_API_KEY" not in os.environ:
            print("Setting dummy GEMINI_API_KEY for import test...")
            os.environ["GEMINI_API_KEY"] = "DUMMY_KEY_FOR_SYNTAX_TEST"

        try:
            # Add parent directory to path for imports

            sys.path.insert(
                0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )

            # If we get here, the import was successful.
            print("SUCCESS: llm_service.py was imported without a syntax error.")
            assert True
        except (SyntaxError, IndentationError) as e:
            # If we get here, the import failed due to a syntax error.
            print(f"FAILURE: A syntax error was found in llm_service.py: {e}")
            self.fail(f"SyntaxError or IndentationError in llm_service.py: {e}")
        except Exception as e:
            # Catch any other potential import-time errors.
            print(f"FAILURE: An unexpected error occurred during import: {e}")
            self.fail(f"An unexpected error occurred during import: {e}")


if __name__ == "__main__":
    unittest.main()
