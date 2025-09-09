"""
Test Helpers for MCP Testing

Common utilities, fixtures, and helper functions for MCP testing.
"""

import json
import logging
import os
import shutil
import socket
import subprocess
import tempfile
import time
import uuid
from collections.abc import Generator
from contextlib import asynccontextmanager, contextmanager, suppress
from typing import Any
from unittest.mock import patch

import psutil
import requests

from mcp_test_client import WorldArchitectMCPClient
from mock_mcp_server import MockMCPServer, run_mock_server_background

logger = logging.getLogger(__name__)


class TestEnvironment:
    """Manages test environment setup and cleanup."""

    def __init__(self):
        self.processes: list[subprocess.Popen] = []
        self.temp_dirs: list[str] = []
        self.mock_server_threads: list = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def cleanup(self):
        """Clean up all test resources."""
        # Kill processes
        for proc in self.processes:
            try:
                if proc.poll() is None:  # Still running
                    proc.terminate()
                    proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            except Exception as e:
                logger.warning(f"Error cleaning up process: {e}")

        # Clean up temp directories
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Error cleaning up temp dir {temp_dir}: {e}")

        self.processes.clear()
        self.temp_dirs.clear()
        self.mock_server_threads.clear()

    def start_mock_server(self, port: int = 8001) -> MockMCPServer:
        """Start a mock MCP server in background."""
        thread = run_mock_server_background(port)
        self.mock_server_threads.append(thread)

        # Wait for server to be ready
        for _ in range(30):  # 30 second timeout
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=1)
                if response.status_code == 200:
                    logger.info(f"Mock MCP server started on port {port}")
                    return MockMCPServer(port)
            except requests.RequestException:
                time.sleep(1)

        raise RuntimeError(f"Mock MCP server failed to start on port {port}")

    def start_real_mcp_server(
        self, script_path: str, port: int = 8000
    ) -> subprocess.Popen:
        """Start a real MCP server process."""
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"MCP server script not found: {script_path}")

        env = os.environ.copy()
        env.update(
            {
                "MCP_SERVER_PORT": str(port),
                "TESTING": "true",
                "FIRESTORE_EMULATOR_HOST": "localhost:8080",  # Use emulator for testing
            }
        )

        proc = subprocess.Popen(
            ["python", script_path, "--port", str(port)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.processes.append(proc)

        # Wait for server to be ready
        if not self._wait_for_process_health(port):
            proc.kill()
            raise RuntimeError(f"Real MCP server failed to start on port {port}")

        logger.info(f"Real MCP server started on port {port}")
        return proc

    def start_translation_layer(
        self, script_path: str, port: int = 8080, mcp_url: str = "http://localhost:8000"
    ) -> subprocess.Popen:
        """Start the translation layer (main.py) process."""
        if not os.path.exists(script_path):
            raise FileNotFoundError(
                f"Translation layer script not found: {script_path}"
            )

        env = os.environ.copy()
        env.update(
            {
                "FLASK_PORT": str(port),
                "MCP_SERVER_URL": mcp_url,
                "TESTING": "true",
                "JWT_SECRET_KEY": "test-secret-key",
            }
        )

        proc = subprocess.Popen(
            ["python", script_path, "--port", str(port)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.processes.append(proc)

        # Wait for Flask server to be ready
        if not self._wait_for_process_health(port, path="/api/health"):
            proc.kill()
            raise RuntimeError(f"Translation layer failed to start on port {port}")

        logger.info(f"Translation layer started on port {port}")
        return proc

    def _wait_for_process_health(
        self, port: int, path: str = "/health", timeout: int = 30
    ) -> bool:
        """Wait for a process to respond to health checks."""
        for _ in range(timeout):
            try:
                response = requests.get(f"http://localhost:{port}{path}", timeout=1)
                if response.status_code == 200:
                    return True
            except requests.RequestException:
                time.sleep(1)
        return False

    def create_temp_dir(self) -> str:
        """Create a temporary directory that will be cleaned up."""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        return temp_dir


@contextmanager
def mock_environment(mock_port: int = 8001) -> Generator[dict[str, Any], None, None]:
    """
    Context manager for mock testing environment.

    Args:
        mock_port: Port for mock MCP server

    Yields:
        Dict containing test environment components
    """
    with TestEnvironment() as env:
        mock_server = env.start_mock_server(mock_port)

        yield {
            "mock_server": mock_server,
            "client": WorldArchitectMCPClient(f"http://localhost:{mock_port}"),
            "environment": env,
        }


@contextmanager
def integration_environment(
    mcp_script: str,
    translation_script: str,
    mcp_port: int = 8000,
    translation_port: int = 8080,
) -> Generator[dict[str, Any], None, None]:
    """
    Context manager for integration testing environment.

    Args:
        mcp_script: Path to MCP server script (world_logic.py)
        translation_script: Path to translation layer script (main.py)
        mcp_port: Port for MCP server
        translation_port: Port for translation layer

    Yields:
        Dict containing test environment components
    """
    with TestEnvironment() as env:
        # Start MCP server
        mcp_proc = env.start_real_mcp_server(mcp_script, mcp_port)

        # Start translation layer
        translation_proc = env.start_translation_layer(
            translation_script, translation_port, f"http://localhost:{mcp_port}"
        )

        yield {
            "mcp_process": mcp_proc,
            "translation_process": translation_proc,
            "mcp_client": WorldArchitectMCPClient(f"http://localhost:{mcp_port}"),
            "http_client": requests.Session(),
            "translation_url": f"http://localhost:{translation_port}",
            "environment": env,
        }


class MockFirestore:
    """Mock Firestore client for testing."""

    def __init__(self):
        self.data: dict[str, dict[str, Any]] = {}

    def collection(self, collection_name: str):
        """Get a collection reference."""
        return MockCollection(self, collection_name)

    def document(self, path: str):
        """Get a document reference."""
        return MockDocument(self, path)


class MockCollection:
    """Mock Firestore collection."""

    def __init__(self, firestore: MockFirestore, name: str):
        self.firestore = firestore
        self.name = name

    def add(self, data: dict[str, Any]) -> tuple:
        """Add a document to the collection."""
        doc_id = str(uuid.uuid4())
        self.firestore.data[f"{self.name}/{doc_id}"] = data
        return None, MockDocument(self.firestore, f"{self.name}/{doc_id}")

    def document(self, doc_id: str):
        """Get a document in this collection."""
        return MockDocument(self.firestore, f"{self.name}/{doc_id}")

    def where(self, field: str, operator: str, value: Any):
        """Add a where clause (returns self for chaining)."""
        return self

    def get(self) -> list[Any]:
        """Get all documents in collection."""
        docs = []
        for path, data in self.firestore.data.items():
            if path.startswith(f"{self.name}/"):
                doc = MockDocument(self.firestore, path)
                doc._data = data
                docs.append(doc)
        return docs


class MockDocument:
    """Mock Firestore document."""

    def __init__(self, firestore: MockFirestore, path: str):
        self.firestore = firestore
        self.path = path
        self._data = None

    @property
    def id(self) -> str:
        """Get document ID."""
        return self.path.split("/")[-1]

    def get(self):
        """Get document data."""
        self._data = self.firestore.data.get(self.path)
        return self

    def to_dict(self) -> dict[str, Any] | None:
        """Convert document to dict."""
        return self._data

    def exists(self) -> bool:
        """Check if document exists."""
        return self.path in self.firestore.data

    def set(self, data: dict[str, Any]):
        """Set document data."""
        self.firestore.data[self.path] = data

    def update(self, updates: dict[str, Any]):
        """Update document data."""
        if self.path in self.firestore.data:
            self.firestore.data[self.path].update(updates)
        else:
            self.firestore.data[self.path] = updates

    def delete(self):
        """Delete document."""
        if self.path in self.firestore.data:
            del self.firestore.data[self.path]


class MockGeminiClient:
    """Mock Gemini AI client for testing."""

    def __init__(self):
        self.call_count = 0
        self.responses = [
            "The ancient dragon stirs as you approach its lair...",
            "Your character successfully performs the action.",
            "The spell takes effect, illuminating the dark corridor.",
            "The merchant eyes you suspiciously but agrees to the trade.",
        ]

    def generate_content(self, prompt: str) -> dict[str, Any]:
        """Mock content generation."""
        self.call_count += 1
        response_text = self.responses[self.call_count % len(self.responses)]

        return {
            "text": response_text,
            "candidates": [{"content": {"parts": [{"text": response_text}]}}],
            "usage_metadata": {
                "prompt_token_count": len(prompt.split()),
                "candidates_token_count": len(response_text.split()),
                "total_token_count": len(prompt.split()) + len(response_text.split()),
            },
        }


def create_test_campaign_data() -> dict[str, Any]:
    """Create test campaign data."""
    return {
        "name": "Test Campaign",
        "description": "A test campaign for automated testing",
        "dm_user_id": "test-user-123",
        "created_at": "2024-01-01T00:00:00",
        "status": "active",
    }


def create_test_character_data() -> dict[str, Any]:
    """Create test character data."""
    return {
        "name": "Test Character",
        "class": "Fighter",
        "level": 1,
        "user_id": "test-user-123",
        "attributes": {
            "strength": 15,
            "dexterity": 13,
            "constitution": 14,
            "intelligence": 12,
            "wisdom": 10,
            "charisma": 8,
        },
    }


def create_test_action_data() -> dict[str, Any]:
    """Create test action data."""
    return {
        "action_type": "attack",
        "target": "goblin",
        "weapon": "sword",
        "description": "Swing sword at the goblin",
    }


async def assert_mcp_response_format(response: dict[str, Any]):
    """Assert that an MCP response has the correct format."""
    assert "status" in response, "MCP response must have 'status' field"
    assert response["status"] in ["success", "error"], (
        "Status must be 'success' or 'error'"
    )

    if response["status"] == "success":
        assert "data" in response, "Success response must have 'data' field"
    else:
        assert "error" in response, "Error response must have 'error' field"
        assert "error_type" in response, "Error response must have 'error_type' field"


def find_free_port(start_port: int = 8000) -> int:
    """Find a free port starting from the given port."""
    for port in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("localhost", port))
                return port
            except OSError:
                continue

    raise RuntimeError(f"No free port found in range {start_port}-{start_port + 100}")


def kill_process_on_port(port: int):
    """Kill any process running on the specified port."""
    try:
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                try:
                    process = psutil.Process(conn.pid)
                    process.terminate()
                    process.wait(timeout=5)
                except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                    with suppress(psutil.NoSuchProcess):
                        process.kill()
    except (ImportError, AttributeError) as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"psutil not available. Cannot kill process on port {port}: {e}")


@asynccontextmanager
async def temporary_mcp_client(server_url: str):
    """Async context manager for MCP client."""
    client = WorldArchitectMCPClient(server_url)
    try:
        await client.connect()
        yield client
    finally:
        await client.disconnect()


def load_test_data(filename: str) -> dict[str, Any]:
    """Load test data from JSON file."""
    test_data_dir = os.path.join(os.path.dirname(__file__), "..", "mock_data")
    file_path = os.path.join(test_data_dir, filename)

    with open(file_path) as f:
        return json.load(f)


def patch_firestore():
    """Patch Firestore for testing."""
    return patch("firebase_admin.firestore.client", return_value=MockFirestore())


def patch_gemini():
    """Patch Gemini client for testing."""
    return patch("google.genai.Client", return_value=MockGeminiClient())
