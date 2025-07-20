#!/usr/bin/env python3
"""
Integration test for the unified test command.
Verifies that the command structure works correctly.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a command and return success status and output"""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, 
            capture_output=True, text=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def test_command_help():
    """Test that the main command shows help correctly"""
    print("🧪 Testing main command help...")
    
    success, stdout, stderr = run_command("python3 test.py --help")
    
    if not success:
        print(f"❌ Command help failed: {stderr}")
        return False
    
    # Check for expected content
    expected_content = [
        "Unified test command for WorldArchitect.AI",
        "claude test ui --mock",
        "claude test http --mock", 
        "claude test integration --long",
        "Commands:",
        "ui", "http", "integration", "all", "end2end"
    ]
    
    for content in expected_content:
        if content not in stdout:
            print(f"❌ Missing expected content: {content}")
            return False
    
    print("✅ Main command help test passed")
    return True


def test_subcommand_help():
    """Test that subcommands show help correctly"""
    print("🧪 Testing subcommand help...")
    
    subcommands = ["ui", "http", "integration", "all", "end2end"]
    
    for subcmd in subcommands:
        success, stdout, stderr = run_command(f"python3 test.py {subcmd} --help")
        
        if not success:
            print(f"❌ Subcommand {subcmd} help failed: {stderr}")
            return False
        
        # Basic check that help is shown
        if "Usage:" not in stdout or "Options:" not in stdout:
            print(f"❌ Subcommand {subcmd} help format incorrect")
            return False
    
    print("✅ Subcommand help test passed")
    return True


def test_alias_imports():
    """Test that backward compatibility aliases can be imported"""
    print("🧪 Testing alias imports...")
    
    aliases = ["testui", "testuif", "testhttp", "testhttpf", "testi", "tester"]
    
    for alias in aliases:
        try:
            # Try to import the alias
            exec(f"from test import {alias}")
            print(f"✓ {alias} imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import {alias}: {e}")
            return False
    
    print("✅ Alias import test passed")
    return True


def test_config_initialization():
    """Test that TestConfig initializes correctly"""
    print("🧪 Testing configuration initialization...")
    
    try:
        # Import and create TestConfig
        exec("""
from test import TestConfig
config = TestConfig()
assert config.use_mock == True
assert config.use_puppeteer == False
assert config.test_type == None
assert config.verbose == False
assert config.coverage == False
print("✓ TestConfig initialized with correct defaults")
""")
    except Exception as e:
        print(f"❌ TestConfig initialization failed: {e}")
        return False
    
    print("✅ Configuration initialization test passed")
    return True


def test_environment_detection():
    """Test that project root detection works"""
    print("🧪 Testing environment detection...")
    
    try:
        # Test project root detection
        exec("""
from test import TestConfig
config = TestConfig()
project_root = config.project_root
print(f"✓ Project root detected: {project_root}")
assert project_root.name in ['worktree_roadmap', 'worldarchitect.ai'], f"Unexpected project root: {project_root}"
""")
    except Exception as e:
        print(f"❌ Environment detection failed: {e}")
        return False
    
    print("✅ Environment detection test passed")
    return True


def main():
    """Run all tests"""
    print("🚀 Running unified test command integration tests")
    print("=" * 50)
    
    # Change to the command directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    tests = [
        test_command_help,
        test_subcommand_help,
        test_alias_imports,
        test_config_initialization,
        test_environment_detection
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()  # Add spacing between tests
    
    # Summary
    total = passed + failed
    print("📊 Test Summary")
    print("=" * 20)
    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n✅ All integration tests passed! 🎉")
        return True
    else:
        print(f"\n❌ {failed} integration tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)