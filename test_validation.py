#!/usr/bin/env python3
"""Test file to validate inline import detection."""

def process_data():
    # This should trigger IMP002: inline import violation
    import json
    import os
    return json.dumps({"path": os.getcwd()})

class DataProcessor:
    def __init__(self):
        try:
            # This should trigger IMP001: try/except import violation
            import yaml
            self.yaml = yaml
        except ImportError:
            self.yaml = None

def another_function():
    import sys  # Another inline import violation
    return sys.version

if __name__ == "__main__":
    print(process_data())
