#!/usr/bin/env python3
"""
Example: How to change ports with centralized configuration

This demonstrates how future port changes will require editing only 1-2 files
instead of 26+ files like we had to do before.
"""

from .testing_config import TestConfig, TestType


def show_current_ports():
    """Show current port configuration"""
    print("Current Test Server Ports:")
    print(f"  Browser tests: {TestConfig.get_server_config(TestType.BROWSER).base_port}")
    print(f"  HTTP tests:    {TestConfig.get_server_config(TestType.HTTP).base_port}")
    print(f"  Integration:   {TestConfig.get_server_config(TestType.INTEGRATION).base_port}")
    print(f"  Development:   {TestConfig.get_server_config(TestType.DEVELOPMENT).base_port}")

def demonstrate_url_generation():
    """Show how URLs are generated from centralized config"""
    print("\nGenerated URLs:")
    print(f"  Browser test URL: {TestConfig.get_test_url(TestType.BROWSER)}")
    print(f"  HTTP test URL:    {TestConfig.get_base_url(TestType.HTTP)}")
    print(f"  Integration URL:  {TestConfig.get_test_url(TestType.INTEGRATION)}")

if __name__ == "__main__":
    print("🎯 Centralized Test Configuration Demo")
    print("=" * 40)

    show_current_ports()
    demonstrate_url_generation()

    print("\n✅ Future Changes:")
    print("   To change ALL browser test ports: Edit 1 line in testing_config.py")
    print("   To change ALL HTTP test ports:    Edit 1 line in testing_config.py")
    print("   To change timeout values:         Edit 1 line in testing_config.py")
    print("   To add new test type:             Add 1 entry to SERVERS dict")

    print("\n❌ Before (what we just fixed):")
    print("   To change ports: Edit 26+ files across multiple directories")
    print("   Risk of missing files and inconsistent configuration")
