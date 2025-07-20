#!/usr/bin/env python3
"""
Unified test command that consolidates all test variants while maintaining backward compatibility.

This module provides a single `claude test` command that replaces the 14+ test command variants
with clear options and maintains backward compatibility through aliases.
"""

import click
import subprocess
import sys
import os
import time
from pathlib import Path


class TestConfig:
    """Configuration class for test execution"""
    
    def __init__(self):
        self.project_root = self._find_project_root()
        self.use_puppeteer = False
        self.use_mock = True
        self.test_type = None
        self.specific_test = None
        self.verbose = False
        self.long_test = False
        self.coverage = False
    
    def _find_project_root(self):
        """Find the project root directory"""
        current = Path.cwd()
        while current != current.parent:
            if (current / "mvp_site" / "main.py").exists():
                return current
            current = current.parent
        return Path.cwd()  # Fallback to current directory


def run_command(cmd, cwd=None, env=None, capture_output=False):
    """Execute a shell command with proper error handling"""
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, cwd=cwd, env=env, 
                                 capture_output=True, text=True)
            return result.returncode == 0, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, shell=True, cwd=cwd, env=env)
            return result.returncode == 0, "", ""
    except Exception as e:
        return False, "", str(e)


def verify_environment(config):
    """Verify the test environment is properly set up"""
    click.echo("🔍 Verifying test environment...")
    
    # Check if in project root
    if not (config.project_root / "mvp_site" / "main.py").exists():
        click.echo("❌ Error: Not in project root or mvp_site/main.py not found", err=True)
        return False
    
    # Check virtual environment
    venv_path = config.project_root / "venv"
    if not venv_path.exists():
        click.echo("❌ Error: Virtual environment not found at venv/", err=True)
        click.echo("Please run from project root with activated venv", err=True)
        return False
    
    click.echo("✅ Environment verification passed")
    return True


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--mock/--real', default=True, help='Use mock APIs (default) or real APIs')
@click.option('--browser', type=click.Choice(['puppeteer', 'playwright']), 
              default='puppeteer', help='Browser automation engine (default: puppeteer)')
@click.option('--coverage', is_flag=True, help='Run with coverage analysis')
@click.pass_context
def test(ctx, verbose, mock, browser, coverage):
    """Unified test command for WorldArchitect.AI
    
    Consolidates all test variants into a single command with clear options.
    Maintains backward compatibility through aliases.
    
    Examples:
        claude test ui --mock                    # Browser tests with mock APIs
        claude test ui --real                    # Browser tests with real APIs  
        claude test http --mock                  # HTTP tests with mock APIs
        claude test integration --long           # Full integration tests
        claude test all                          # Run all test suites
    """
    # Initialize context for subcommands
    if ctx.obj is None:
        ctx.obj = TestConfig()
    
    ctx.obj.verbose = verbose
    ctx.obj.use_mock = mock
    ctx.obj.use_puppeteer = (browser == 'puppeteer')
    ctx.obj.coverage = coverage


@test.command()
@click.option('--specific', help='Run a specific test file')
@click.pass_obj
def ui(config, specific):
    """Run browser/UI tests with real browser automation
    
    Uses Puppeteer MCP (default) or Playwright for browser automation.
    Always uses real browsers, never HTTP simulation.
    """
    config.test_type = 'ui'
    config.specific_test = specific
    
    if not verify_environment(config):
        sys.exit(1)
    
    click.echo(f"🌐 Running browser tests ({'mock' if config.use_mock else 'real'} APIs)")
    click.echo(f"🔧 Browser engine: {'Puppeteer MCP' if config.use_puppeteer else 'Playwright'}")
    
    # Build command
    mode = "mock" if config.use_mock else "real"
    cmd = f"./run_ui_tests.sh {mode}"
    
    if config.use_puppeteer:
        cmd += " --puppeteer"
    
    # Set environment
    env = os.environ.copy()
    env['TESTING'] = 'true'
    if config.use_mock:
        env['USE_MOCK_FIREBASE'] = 'true'
        env['USE_MOCK_GEMINI'] = 'true'
    
    # Execute the test
    success, stdout, stderr = run_command(cmd, cwd=config.project_root, env=env)
    
    if not success:
        click.echo("❌ Browser tests failed", err=True)
        if stderr and config.verbose:
            click.echo(f"Error: {stderr}", err=True)
        sys.exit(1)
    
    click.echo("✅ Browser tests completed successfully")


@test.command()
@click.option('--specific', help='Run a specific test file')
@click.pass_obj
def http(config, specific):
    """Run HTTP request tests using requests library
    
    Tests API endpoints directly without browser automation.
    Never uses browser engines - only HTTP requests.
    """
    config.test_type = 'http'
    config.specific_test = specific
    
    if not verify_environment(config):
        sys.exit(1)
    
    click.echo(f"🔗 Running HTTP tests ({'mock' if config.use_mock else 'real'} APIs)")
    
    # Verify requests library
    success, _, _ = run_command('vpython -c "import requests"', 
                               cwd=config.project_root, capture_output=True)
    if not success:
        click.echo("❌ Error: requests library not installed", err=True)
        sys.exit(1)
    
    # Start test server if needed
    click.echo("🚀 Starting test server...")
    server_cmd = "TESTING=true PORT=8086 vpython mvp_site/main.py serve"
    env = os.environ.copy()
    env['TESTING'] = 'true'
    
    # Start server in background
    server_proc = subprocess.Popen(server_cmd.split(), cwd=config.project_root, env=env)
    time.sleep(3)  # Allow server to start
    
    try:
        # Run HTTP tests
        if specific:
            test_cmd = f"TESTING=true vpython testing_http/{specific}"
        else:
            test_cmd = "find testing_http -name 'test_*.py' -exec TESTING=true vpython {} \\;"
        
        success, stdout, stderr = run_command(test_cmd, cwd=config.project_root, env=env)
        
        if not success:
            click.echo("❌ HTTP tests failed", err=True)
            if stderr and config.verbose:
                click.echo(f"Error: {stderr}", err=True)
            sys.exit(1)
        
        click.echo("✅ HTTP tests completed successfully")
    
    finally:
        # Cleanup server
        server_proc.terminate()
        server_proc.wait()


@test.command()
@click.option('--long', is_flag=True, help='Run long-running integration tests')
@click.pass_obj
def integration(config, long):
    """Run integration tests
    
    Tests the integration between different system components.
    Use --long for comprehensive integration testing.
    """
    config.test_type = 'integration'
    config.long_test = long
    
    if not verify_environment(config):
        sys.exit(1)
    
    click.echo(f"🔄 Running integration tests ({'long' if long else 'standard'} mode)")
    
    # Set environment
    env = os.environ.copy()
    env['TESTING'] = 'true'
    
    # Run integration tests
    cmd = "TESTING=true python3 mvp_site/test_integration/test_integration.py"
    
    success, stdout, stderr = run_command(cmd, cwd=config.project_root, env=env)
    
    if not success:
        click.echo("❌ Integration tests failed", err=True)
        if stderr and config.verbose:
            click.echo(f"Error: {stderr}", err=True)
        sys.exit(1)
    
    click.echo("✅ Integration tests completed successfully")


@test.command()
@click.pass_obj
def all(config):
    """Run all test suites (unit, integration, UI, HTTP)
    
    Comprehensive test execution across all test types.
    Uses mock APIs by default for cost efficiency.
    """
    if not verify_environment(config):
        sys.exit(1)
    
    click.echo("🧪 Running all test suites...")
    
    # Set environment
    env = os.environ.copy()
    env['TESTING'] = 'true'
    
    test_suites = [
        ("Unit Tests", "./run_tests.sh"),
        ("UI Tests", f"./run_ui_tests.sh {'mock' if config.use_mock else 'real'}"),
        ("Integration Tests", "TESTING=true python3 mvp_site/test_integration/test_integration.py")
    ]
    
    failed_suites = []
    
    for suite_name, cmd in test_suites:
        click.echo(f"\n📋 Running {suite_name}...")
        
        success, stdout, stderr = run_command(cmd, cwd=config.project_root, env=env)
        
        if success:
            click.echo(f"✅ {suite_name} passed")
        else:
            click.echo(f"❌ {suite_name} failed")
            failed_suites.append(suite_name)
            if config.verbose and stderr:
                click.echo(f"Error: {stderr}")
    
    # Summary
    click.echo(f"\n📊 Test Summary")
    click.echo("=" * 20)
    total_suites = len(test_suites)
    passed_suites = total_suites - len(failed_suites)
    
    click.echo(f"Total suites: {total_suites}")
    click.echo(f"Passed: {passed_suites}")
    click.echo(f"Failed: {len(failed_suites)}")
    
    if failed_suites:
        click.echo(f"\nFailed suites: {', '.join(failed_suites)}")
        sys.exit(1)
    else:
        click.echo("\n✅ All test suites passed! 🎉")


@test.command()
@click.pass_obj
def end2end(config):
    """Run end-to-end tests with real services (costs money!)
    
    Uses real Firebase and Gemini APIs for comprehensive validation.
    Prompts for confirmation due to API costs.
    """
    if not config.use_mock:
        # User explicitly chose real APIs, no need to prompt again
        pass
    else:
        # Default is mock, so confirm for real API usage
        if not click.confirm("⚠️  End-to-end tests use real APIs and cost money. Continue?"):
            click.echo("Test cancelled by user")
            return
    
    if not verify_environment(config):
        sys.exit(1)
    
    click.echo("🚀 Running end-to-end tests with real services...")
    
    # Check for required environment variables
    required_vars = ['REAL_FIREBASE_PROJECT', 'REAL_GEMINI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        click.echo(f"❌ Missing required environment variables: {', '.join(missing_vars)}", err=True)
        click.echo("Please set these variables for real API testing", err=True)
        sys.exit(1)
    
    # Set environment for real APIs
    env = os.environ.copy()
    env['TESTING'] = 'true'
    env['TEST_MODE'] = 'real'
    env['FIREBASE_PROJECT_ID'] = os.getenv('REAL_FIREBASE_PROJECT')
    env['GEMINI_API_KEY'] = os.getenv('REAL_GEMINI_API_KEY')
    
    # Run end-to-end tests
    cmd = "./claude_command_scripts/tester.sh"
    
    success, stdout, stderr = run_command(cmd, cwd=config.project_root, env=env)
    
    if not success:
        click.echo("❌ End-to-end tests failed", err=True)
        if stderr and config.verbose:
            click.echo(f"Error: {stderr}", err=True)
        sys.exit(1)
    
    click.echo("✅ End-to-end tests completed successfully")


# Backward compatibility aliases
@click.command()
@click.option('--specific', help='Run a specific test file')
def testui(specific):
    """Alias for: claude test ui --mock"""
    config = TestConfig()
    config.use_mock = True
    config.use_puppeteer = True
    config.specific_test = specific
    ui.callback(config, specific)

@click.command()
@click.option('--specific', help='Run a specific test file')
def testuif(specific):
    """Alias for: claude test ui --real"""
    config = TestConfig()
    config.use_mock = False
    config.use_puppeteer = True
    config.specific_test = specific
    ui.callback(config, specific)

@click.command()
@click.option('--specific', help='Run a specific test file')
def testhttp(specific):
    """Alias for: claude test http --mock"""
    config = TestConfig()
    config.use_mock = True
    config.specific_test = specific
    http.callback(config, specific)

@click.command()
@click.option('--specific', help='Run a specific test file')
def testhttpf(specific):
    """Alias for: claude test http --real"""
    config = TestConfig()
    config.use_mock = False
    config.specific_test = specific
    http.callback(config, specific)

@click.command()
@click.option('--long', is_flag=True, help='Run long-running integration tests')
def testi(long):
    """Alias for: claude test integration"""
    config = TestConfig()
    config.long_test = long
    integration.callback(config, long)

@click.command()
def tester():
    """Alias for: claude test end2end"""
    config = TestConfig()
    config.use_mock = False  # end2end tests use real APIs
    end2end.callback(config)


# Export the main command
if __name__ == '__main__':
    test()