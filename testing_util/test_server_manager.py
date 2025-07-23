#!/usr/bin/env python3
"""
Centralized Test Server Manager for WorldArchitect.AI

Manages Flask test server lifecycle across different test types.
Provides unified server startup, health checks, and cleanup.
"""

import os
import socket
import subprocess
import sys
import time
import signal
import logging
from contextlib import contextmanager
from typing import Optional, Generator, Dict, Any
from dataclasses import dataclass

import requests
import psutil

from .testing_config import TestConfig, TestType, TestMode


@dataclass
class ServerInstance:
    """Information about a running test server"""
    process: subprocess.Popen
    port: int
    test_type: TestType
    base_url: str
    pid: int


class TestServerManager:
    """Manages test server instances across different test types"""
    
    def __init__(self):
        self.running_servers: Dict[TestType, ServerInstance] = {}
        self.cleanup_registered = False
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up logging for server manager"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def find_available_port(self, test_type: TestType, preferred_port: Optional[int] = None) -> int:
        """Find an available port for the test server"""
        server_config = TestConfig.get_server_config(test_type)
        
        # Try preferred port first
        if preferred_port and self._is_port_available(preferred_port):
            return preferred_port
        
        # Try base port
        if self._is_port_available(server_config.base_port):
            return server_config.base_port
        
        # Search in port range
        min_port, max_port = server_config.port_range
        for port in range(min_port, max_port + 1):
            if self._is_port_available(port):
                return port
        
        raise RuntimeError(f"No available ports found for {test_type} in range {server_config.port_range}")
    
    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                return result != 0
        except Exception:
            return False
    
    def start_server(self, test_type: TestType, test_mode: TestMode = TestMode.MOCK, 
                    port: Optional[int] = None, timeout: int = 30) -> ServerInstance:
        """Start a test server instance"""
        
        # Check if server is already running
        if test_type in self.running_servers:
            existing = self.running_servers[test_type]
            if self._is_server_healthy(existing):
                self.logger.info(f"Server already running for {test_type} on port {existing.port}")
                return existing
            else:
                self.logger.warning(f"Existing server for {test_type} is unhealthy, stopping...")
                self.stop_server(test_type)
        
        # Find available port
        actual_port = self.find_available_port(test_type, port)
        self.logger.info(f"Starting {test_type} server on port {actual_port}")
        
        # Set up environment for server
        env = self._setup_server_environment(test_mode, actual_port)
        
        # Start server process
        server_cmd = self._build_server_command(actual_port)
        try:
            process = subprocess.Popen(
                server_cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self._get_project_root(),
                preexec_fn=os.setsid  # Create process group for easier cleanup
            )
            
            # Wait for server to become healthy
            base_url = TestConfig.get_base_url(test_type, actual_port)
            if not self._wait_for_server_health(base_url, timeout):
                process.terminate()
                process.wait(timeout=5)
                raise RuntimeError(f"Server failed to start within {timeout} seconds")
            
            # Create server instance
            server_instance = ServerInstance(
                process=process,
                port=actual_port,
                test_type=test_type,
                base_url=base_url,
                pid=process.pid
            )
            
            self.running_servers[test_type] = server_instance
            self._register_cleanup()
            
            self.logger.info(f"✓ {test_type} server started successfully on {base_url}")
            return server_instance
            
        except Exception as e:
            self.logger.error(f"Failed to start {test_type} server: {e}")
            raise
    
    def stop_server(self, test_type: TestType, timeout: int = 10) -> bool:
        """Stop a test server instance"""
        if test_type not in self.running_servers:
            return True
        
        server = self.running_servers[test_type]
        self.logger.info(f"Stopping {test_type} server (PID: {server.pid})")
        
        try:
            # Try graceful shutdown first
            server.process.terminate()
            server.process.wait(timeout=timeout // 2)
        except subprocess.TimeoutExpired:
            # Force kill if graceful shutdown fails
            self.logger.warning(f"Force killing {test_type} server (PID: {server.pid})")
            try:
                os.killpg(server.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass  # Process already dead
        
        # Clean up
        del self.running_servers[test_type]
        self.logger.info(f"✓ {test_type} server stopped")
        return True
    
    def stop_all_servers(self) -> None:
        """Stop all running test servers"""
        self.logger.info("Stopping all test servers...")
        for test_type in list(self.running_servers.keys()):
            self.stop_server(test_type)
    
    def _setup_server_environment(self, test_mode: TestMode, port: int) -> Dict[str, str]:
        """Set up environment variables for server"""
        env = os.environ.copy()
        env["PORT"] = str(port)
        env["FLASK_ENV"] = "testing"
        
        if test_mode == TestMode.MOCK:
            env.update(TestConfig.MOCK_ENV_VARS)
        
        return env
    
    def _build_server_command(self, port: int) -> list[str]:
        """Build command to start Flask server"""
        return [
            sys.executable, "-m", "mvp_site.main", "serve"
        ]
    
    def _get_project_root(self) -> str:
        """Get project root directory using hardcoded path for reliability"""
        project_root = os.path.expanduser("~/projects/worldarchitect.ai")
        if os.path.exists(project_root):
            return project_root
        # Fallback to current working directory if hardcoded path doesn't exist
        return os.getcwd()
    
    def _wait_for_server_health(self, base_url: str, timeout: int) -> bool:
        """Wait for server to become healthy"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(base_url, timeout=2)
                if response.status_code == 200:
                    return True
            except requests.RequestException:
                pass
            time.sleep(0.5)
        return False
    
    def _is_server_healthy(self, server: ServerInstance) -> bool:
        """Check if server instance is healthy"""
        try:
            # Check if process is still alive
            if server.process.poll() is not None:
                return False
            
            # Check if server responds to requests
            response = requests.get(server.base_url, timeout=2)
            return response.status_code == 200
        except Exception:
            return False
    
    def _register_cleanup(self) -> None:
        """Register cleanup handlers"""
        if self.cleanup_registered:
            return
        
        import atexit
        atexit.register(self.stop_all_servers)
        
        def signal_handler(signum, frame):
            self.stop_all_servers()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        self.cleanup_registered = True


# Global server manager instance
_server_manager = TestServerManager()

# Convenience functions
def start_test_server(test_type: TestType, test_mode: TestMode = TestMode.MOCK,
                     port: Optional[int] = None, timeout: int = 30) -> ServerInstance:
    """Start a test server - convenience function"""
    return _server_manager.start_server(test_type, test_mode, port, timeout)

def stop_test_server(test_type: TestType) -> bool:
    """Stop a test server - convenience function"""
    return _server_manager.stop_server(test_type)

def get_server_instance(test_type: TestType) -> Optional[ServerInstance]:
    """Get running server instance"""
    return _server_manager.running_servers.get(test_type)

@contextmanager
def test_server(test_type: TestType, test_mode: TestMode = TestMode.MOCK,
               port: Optional[int] = None) -> Generator[ServerInstance, None, None]:
    """Context manager for test server lifecycle"""
    server = start_test_server(test_type, test_mode, port)
    try:
        yield server
    finally:
        stop_test_server(test_type)

# Backward compatibility functions
def start_browser_server(port: Optional[int] = None) -> ServerInstance:
    """Start browser test server - backward compatibility"""
    return start_test_server(TestType.BROWSER, TestMode.MOCK, port)

def start_http_server(port: Optional[int] = None) -> ServerInstance:
    """Start HTTP test server - backward compatibility"""
    return start_test_server(TestType.HTTP, TestMode.MOCK, port)