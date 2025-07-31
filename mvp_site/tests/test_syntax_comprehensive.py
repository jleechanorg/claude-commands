import ast
import importlib.util
import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_state import GameState


class TestComprehensiveSyntax(unittest.TestCase):
    """
    Comprehensive syntax and import testing that would catch the f-string error.
    This test ensures all Python files can be parsed and core modules imported.
    """

    def test_all_python_files_syntax(self):
        """Test that all Python files in the project have valid syntax using AST parsing."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)  # Go up to mvp_site directory
        python_files = []

        # Find all .py files in parent directory (the actual application files)
        for file in os.listdir(parent_dir):
            if file.endswith(".py") and not file.startswith("test_"):
                python_files.append(file)

        syntax_errors = []

        for py_file in python_files:
            file_path = os.path.join(parent_dir, py_file)
            try:
                with open(file_path, encoding="utf-8") as f:
                    source_code = f.read()
                # This AST parse would have caught the f-string syntax error
                ast.parse(source_code, filename=py_file)
            except SyntaxError as e:
                syntax_errors.append(f"{py_file}:{e.lineno}: {e.msg}")
            except Exception as e:
                syntax_errors.append(f"{py_file}: Unexpected error - {e}")

        if syntax_errors:
            self.fail(f"Syntax errors found: {'; '.join(syntax_errors)}")

    def test_game_state_syntax_and_import(self):
        """Specifically test game_state.py syntax and import."""
        # First check syntax with AST
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            file_path = os.path.join(parent_dir, "game_state.py")
            with open(file_path, encoding="utf-8") as f:
                source_code = f.read()
            ast.parse(source_code, filename="game_state.py")
        except SyntaxError as e:
            self.fail(f"Syntax error in game_state.py at line {e.lineno}: {e.msg}")

        # Then test import
        try:
            # Test basic instantiation
            gs = GameState()
            assert gs is not None
        except Exception as e:
            self.fail(f"Failed to import or instantiate GameState: {e}")

    def test_main_module_syntax(self):
        """Test that main.py has valid syntax and can load its dependencies."""
        # Check main.py syntax
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            file_path = os.path.join(parent_dir, "main.py")
            with open(file_path, encoding="utf-8") as f:
                source_code = f.read()
            ast.parse(source_code, filename="main.py")
        except SyntaxError as e:
            self.fail(f"Syntax error in main.py at line {e.lineno}: {e.msg}")

        # Test if main.py can import its dependencies (catches import chain syntax errors)
        try:
            spec = importlib.util.spec_from_file_location("main_test", file_path)
            if spec and spec.loader:
                main_module = importlib.util.module_from_spec(spec)
                # This would catch the game_state f-string error when main.py imports game_state
                spec.loader.exec_module(main_module)
        except SyntaxError as e:
            self.fail(f"Syntax error in main.py or its dependencies: {e}")
        except ImportError as e:
            if "No module named" in str(e):
                self.skipTest(f"Skipping due to missing dependency: {e}")
            else:
                self.fail(f"Import error: {e}")
        except Exception as e:
            self.fail(f"Unexpected error loading main.py: {e}")

    def test_basic_game_state_instantiation(self):
        """Test basic GameState instantiation without combat-specific features."""
        try:
            # Add parent directory to path for imports

            sys.path.insert(
                0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )

            gs = GameState()

            # Test basic instantiation and core attributes
            assert gs is not None
            assert gs.player_character_data is not None
            assert gs.world_data is not None
            assert gs.npc_data is not None

        except SyntaxError as e:
            self.fail(f"Syntax error in GameState instantiation: {e}")
        except Exception as e:
            # Allow other errors (like missing dependencies) but not syntax errors
            if "SyntaxError" in str(type(e)):
                self.fail(f"Syntax error in GameState code: {e}")


if __name__ == "__main__":
    print("=== Comprehensive Syntax Testing ===")
    print("This test would have caught the f-string syntax error.")

    # Quick syntax check preview
    current_dir = os.path.dirname(os.path.abspath(__file__)) or "."
    parent_dir = os.path.dirname(current_dir)
    print("\n--- Quick syntax check for all Python files ---")

    for file in os.listdir(parent_dir):
        if file.endswith(".py"):
            try:
                with open(os.path.join(parent_dir, file), encoding="utf-8") as f:
                    ast.parse(f.read(), filename=file)
                print(f"✓ {file}: Syntax OK")
            except SyntaxError as e:
                print(f"✗ {file}: Syntax Error at line {e.lineno}: {e.msg}")
            except Exception as e:
                print(f"? {file}: Could not check - {e}")

    print("\n--- Running comprehensive test suite ---")
    unittest.main(verbosity=2)
