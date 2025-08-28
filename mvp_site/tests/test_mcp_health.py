#!/usr/bin/env python3
"""
Test MCP server health checks to ensure all servers are properly configured.
Uses red-green methodology - write failing tests first, then make them pass.
"""

import unittest
import subprocess
import json
import os
import time
import socket
from unittest.mock import patch, MagicMock

class TestMCPServerHealth(unittest.TestCase):
    """Test that all MCP servers are healthy and properly configured."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_timeout = 5
        # Try multiple possible config paths
        possible_paths = [
            os.path.expanduser("~/.config/claude/claude_desktop_config.json"),
            os.path.expanduser("~/.claude/claude_desktop_config.json"),
            os.path.expanduser("~/claude_desktop_config.json")
        ]
        
        self.mcp_config_path = None
        for path in possible_paths:
            if os.path.exists(path):
                self.mcp_config_path = path
                break
        
        if not self.mcp_config_path:
            # Use default path even if it doesn't exist yet
            self.mcp_config_path = os.path.expanduser("~/.config/claude/claude_desktop_config.json")
        
    def test_react_mcp_server_exists(self):
        """Test that react-mcp server is properly installed and configured."""
        # Skip if React MCP is not enabled
        if os.environ.get('REACT_MCP_ENABLED') != 'true':
            self.skipTest("React MCP server disabled (set REACT_MCP_ENABLED=true to enable)")
            
        # Check if react-mcp directory exists
        react_mcp_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "react-mcp"
        )
        self.assertTrue(
            os.path.exists(react_mcp_path),
            f"React MCP directory not found at {react_mcp_path}"
        )
        
        # Check if index.js exists
        index_path = os.path.join(react_mcp_path, "index.js")
        self.assertTrue(
            os.path.exists(index_path),
            f"React MCP index.js not found at {index_path}"
        )
        
    def test_worldarchitect_game_server_running(self):
        """Test that worldarchitect-game server is running on port 7000."""
        # Try multiple IPs due to WSL2 localhost issues
        # Allow configuration via environment variable
        test_hosts_env = os.environ.get('MCP_TEST_HOSTS', '')
        
        if test_hosts_env:
            # Use comma-separated list from environment
            test_hosts = [host.strip() for host in test_hosts_env.split(',')]
        else:
            # Default hosts for local testing
            test_hosts = ['localhost', '127.0.0.1']
            
            # Add WSL2 IPs if they appear to be configured
            try:
                # Try to get WSL2 IP from hostname command
                result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    ips = result.stdout.strip().split()
                    # Add non-localhost IPs
                    for ip in ips:
                        if ip and not ip.startswith('127.'):
                            test_hosts.append(ip)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        connected = False
        for host in test_hosts:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, 7000))
            sock.close()
            
            if result == 0:
                connected = True
                break
        
        # Skip server connectivity check in CI environment
        if os.environ.get('CI') == 'true' or os.environ.get('GITHUB_ACTIONS') == 'true':
            self.skipTest("Skipping server connectivity check in CI environment - server not running")
        else:
            self.assertTrue(
                connected,
                f"WorldArchitect game server not running on port 7000 (tried: {', '.join(test_hosts)})"
            )
        
    def test_mcp_config_has_all_servers(self):
        """Test that MCP config contains all required servers."""
        # Skip test if config file doesn't exist (CI environment)
        if not os.path.exists(self.mcp_config_path):
            self.skipTest(f"MCP config not found at {self.mcp_config_path} - likely CI environment")
            
        # Core required servers (always enabled)
        required_servers = [
            'sequential-thinking',
            'context7',
            'gemini-cli-mcp',
            'github-server',
            'filesystem',
            'serena',
            'memory-server',
            'perplexity-ask',
            'worldarchitect'
        ]
        
        # Optional servers (enabled by environment variables)
        optional_servers = {
            'react-mcp': 'REACT_MCP_ENABLED',
            'playwright-mcp': 'PLAYWRIGHT_ENABLED', 
            'ios-simulator-mcp': 'IOS_SIMULATOR_ENABLED'
        }
        
        with open(self.mcp_config_path, 'r') as f:
            config = json.load(f)
            
        mcpServers = config.get('mcpServers', {})
        
        # Check required servers
        for server in required_servers:
            self.assertIn(
                server, mcpServers,
                f"Required server {server} not found in MCP config"
            )
        
        # Check optional servers only if environment variables are set
        for server, env_var in optional_servers.items():
            if os.environ.get(env_var) == 'true':
                self.assertIn(
                    server, mcpServers,
                    f"Optional server {server} not found in MCP config (enabled by {env_var}=true)"
                )
            
    def test_claude_mcp_script_success(self):
        """Test that claude_mcp.sh script runs successfully."""
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "claude_mcp.sh"
        )
        
        self.assertTrue(
            os.path.exists(script_path),
            f"claude_mcp.sh not found at {script_path}"
        )
        
        # Run the script in test mode (should complete without errors)
        result = subprocess.run(
            [script_path, "--test"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Script should exit with 0 for success
        self.assertEqual(
            result.returncode, 0,
            f"claude_mcp.sh failed with return code {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
        
    def test_react_mcp_dependencies_installed(self):
        """Test that react-mcp has all dependencies installed."""
        # Skip if React MCP is not enabled
        if os.environ.get('REACT_MCP_ENABLED') != 'true':
            self.skipTest("React MCP server disabled (set REACT_MCP_ENABLED=true to enable)")
            
        react_mcp_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "react-mcp"
        )
        
        # Check package.json exists
        package_json_path = os.path.join(react_mcp_path, "package.json")
        if os.path.exists(package_json_path):
            # Check node_modules exists (skip in CI environment)
            node_modules_path = os.path.join(react_mcp_path, "node_modules")
            if os.environ.get('CI') == 'true' or os.environ.get('GITHUB_ACTIONS') == 'true':
                self.skipTest("Skipping node_modules check in CI environment - dependencies not installed")
            else:
                self.assertTrue(
                    os.path.exists(node_modules_path),
                    f"React MCP node_modules not found - run npm install in {react_mcp_path}"
                )
            
    def test_worldarchitect_game_service_file(self):
        """Test that worldarchitect-game has proper service configuration."""
        # Check for service file or startup script - prefer real implementation
        service_paths = [
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "scripts", "start_game_server.sh"
            ),
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "mvp_site", "mcp_api.py"  # Real MCP server implementation
            )
        ]
        
        found = False
        for path in service_paths:
            if os.path.exists(path):
                found = True
                break
                
        self.assertTrue(
            found,
            f"No worldarchitect-game service file found in: {service_paths}"
        )


if __name__ == '__main__':
    unittest.main()