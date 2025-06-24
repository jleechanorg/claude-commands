import unittest
import sys
import os
import ast
import importlib.util

class TestComprehensiveSyntax(unittest.TestCase):
    """
    Comprehensive syntax and import testing that would catch the f-string error.
    This test ensures all Python files can be parsed and core modules imported.
    """
    
    def test_all_python_files_syntax(self):
        """Test that all Python files in the project have valid syntax using AST parsing."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        python_files = []
        
        # Find all .py files in current directory (excluding test files for this specific test)
        for file in os.listdir(current_dir):
            if file.endswith('.py') and not file.startswith('test_'):
                python_files.append(file)
        
        syntax_errors = []
        
        for py_file in python_files:
            file_path = os.path.join(current_dir, py_file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
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
            with open('game_state.py', 'r', encoding='utf-8') as f:
                source_code = f.read()
            ast.parse(source_code, filename='game_state.py')
        except SyntaxError as e:
            self.fail(f"Syntax error in game_state.py at line {e.lineno}: {e.msg}")
        
        # Then test import
        try:
            from game_state import GameState
            # Test basic instantiation
            gs = GameState()
            self.assertIsNotNone(gs)
        except Exception as e:
            self.fail(f"Failed to import or instantiate GameState: {e}")
    
    def test_main_module_syntax(self):
        """Test that main.py has valid syntax and can load its dependencies."""
        # Check main.py syntax
        try:
            with open('main.py', 'r', encoding='utf-8') as f:
                source_code = f.read()
            ast.parse(source_code, filename='main.py')
        except SyntaxError as e:
            self.fail(f"Syntax error in main.py at line {e.lineno}: {e.msg}")
        
        # Test if main.py can import its dependencies (catches import chain syntax errors)
        try:
            spec = importlib.util.spec_from_file_location("main_test", "main.py")
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

    def test_combat_logging_syntax(self):
        """Specifically test the new combat logging code that caused the syntax error."""
        try:
            from game_state import GameState
            gs = GameState()
            
            # Test the start_combat method that had the f-string syntax error
            combatants = [
                {'name': 'Test Player', 'initiative': 15, 'type': 'pc', 'hp_current': 30, 'hp_max': 30},
                {'name': 'Test Enemy', 'initiative': 10, 'type': 'enemy', 'hp_current': 20, 'hp_max': 20}
            ]
            
            # This would fail if the logging line had syntax errors
            gs.start_combat(combatants)
            gs.end_combat()
            
        except SyntaxError as e:
            self.fail(f"Syntax error in combat logging code: {e}")
        except Exception as e:
            # Allow other errors (like missing dependencies) but not syntax errors
            if "SyntaxError" in str(type(e)):
                self.fail(f"Syntax error in combat code: {e}")

if __name__ == '__main__':
    print("=== Comprehensive Syntax Testing ===")
    print("This test would have caught the f-string syntax error.")
    
    # Quick syntax check preview
    current_dir = os.path.dirname(os.path.abspath(__file__)) or '.'
    print("\n--- Quick syntax check for all Python files ---")
    
    for file in os.listdir(current_dir):
        if file.endswith('.py'):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    ast.parse(f.read(), filename=file)
                print(f"✓ {file}: Syntax OK")
            except SyntaxError as e:
                print(f"✗ {file}: Syntax Error at line {e.lineno}: {e.msg}")
            except Exception as e:
                print(f"? {file}: Could not check - {e}")
    
    print("\n--- Running comprehensive test suite ---")
    unittest.main(verbosity=2)