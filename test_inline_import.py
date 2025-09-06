#!/usr/bin/env python3
"""Test file to verify import validation hook works"""

def some_function():
    """Function that contains inline import - should be detected"""
    import os  # IMP002: This should trigger validation failure
    return os.getcwd()

# Module level assignment
DEBUG = True

def another_function():
    """Another function with inline import"""
    try:
        import json  # IMP001: This should also trigger validation failure
        return json.dumps({"test": True})
    except ImportError:
        return "{}"

if __name__ == "__main__":
    print(some_function())
    print(another_function())
