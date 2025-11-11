#!/usr/bin/env python3
"""Simple test for inline import detection"""

import ast
import sys


def test_simple():
    code = '''
import os
import sys

def test_func():
    import json
    return json.dumps({})

if True:
    import logging
    logging.info("test")
'''

    try:
        tree = ast.parse(code)
        print("AST parsing successful")

        # Simple visitor
        class SimpleVisitor(ast.NodeVisitor):
            def __init__(self):
                self.imports = []
                self.depth = 0

            def visit_Import(self, node):
                print(f"Found import at line {node.lineno}, depth {self.depth}")
                for alias in node.names:
                    self.imports.append((alias.name, node.lineno, self.depth))
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                print(f"Found from-import at line {node.lineno}, depth {self.depth}")
                self.generic_visit(node)

            def visit_FunctionDef(self, node):
                self.depth += 1
                print(f"Entering function {node.name} at depth {self.depth}")
                self.generic_visit(node)
                self.depth -= 1

            def visit_If(self, node):
                self.depth += 1
                print(f"Entering if block at depth {self.depth}")
                self.generic_visit(node)
                self.depth -= 1

        visitor = SimpleVisitor()
        visitor.visit(tree)

        print("Imports found:", visitor.imports)

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(test_simple())
