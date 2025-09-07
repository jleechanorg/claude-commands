def test_function():
    import os  # This should trigger IMP002: inline import violation
    return os.getcwd()

def another_function():
    try:
        import sys  # This should trigger IMP001: try/except import violation
        return sys.version
    except ImportError:
        return "unknown"
