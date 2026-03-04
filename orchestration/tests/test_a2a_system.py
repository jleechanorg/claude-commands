#!/usr/bin/env python3
"""
Test suite for A2A system integration
"""

import contextlib
import os
import shutil
import signal
import sys
import tempfile
import time

from orchestration.a2a_agent_wrapper import create_a2a_wrapper
from orchestration.a2a_integration import (
    A2A_BASE_DIR,
    create_a2a_client,
    get_a2a_status,
)
from orchestration.a2a_monitor import A2AMonitor
from orchestration.task_dispatcher import TaskDispatcher

# Set test A2A directory after imports
test_dir = tempfile.mkdtemp()
os.environ["A2A_BASE_DIR"] = f"{test_dir}/a2a"


def test_basic_a2a_functionality():
    """Test basic A2A message and task functionality"""
    print("Testing basic A2A functionality...")

    try:
        # Create two test agents with secure temporary directories
        agent1_workspace = tempfile.mkdtemp(prefix="test-agent-1-")
        agent2_workspace = tempfile.mkdtemp(prefix="test-agent-2-")
        agent1 = create_a2a_client("test-agent-1", "frontend", ["javascript", "react"], agent1_workspace)
        agent2 = create_a2a_client("test-agent-2", "backend", ["python", "api"], agent2_workspace)

        # Test agent discovery
        agents = agent1.discover_agents()
        print(f"✓ Agent discovery: Found {len(agents)} agents")
        assert len(agents) >= 2, "Should find both agents"

        # Test task publishing and claiming
        task_id = agent1.publish_task("Build login form", ["javascript"])
        print(f"✓ Task publishing: Created task {task_id}")
        assert task_id is not None, "Task should be created"

        # Wait for task propagation in A2A system (CI needs more time)
        max_retries = 5
        available_tasks = []
        for attempt in range(max_retries):
            time.sleep(1 + attempt * 0.5)  # Progressive backoff
            available_tasks = agent2.task_pool.get_available_tasks()
            if len(available_tasks) >= 1:
                break
            print(f"⏳ Attempt {attempt + 1}/{max_retries}: Found {len(available_tasks)} tasks, retrying...")

        print(f"✓ Task discovery: Found {len(available_tasks)} available tasks")
        assert len(available_tasks) >= 1, f"Should find published task after {max_retries} attempts"

        # Test messaging
        success = agent1.send_message("test-agent-2", "status", {"message": "Hello from agent 1"})
        print(f"✓ Messaging: Send success = {success}")
        assert success, "Message should be sent successfully"

        messages = agent2.receive_messages()
        print(f"✓ Message reception: Received {len(messages)} messages")
        assert len(messages) >= 1, "Should receive message"

        # Test system status
        status = get_a2a_status()
        print(f"✓ System status: {status['agents_online']} agents online, {status['available_tasks']} tasks available")

        print("✅ Basic A2A functionality test PASSED")

    except Exception as e:
        print(f"❌ Basic A2A functionality test FAILED: {e}")
        raise
    finally:
        # Cleanup temporary workspaces
        try:
            shutil.rmtree(agent1_workspace, ignore_errors=True)
            shutil.rmtree(agent2_workspace, ignore_errors=True)
        except Exception:
            pass


def test_a2a_wrapper():
    """Test A2A agent wrapper functionality"""
    print("\nTesting A2A wrapper functionality...")

    try:
        # Create wrapper with secure temporary directory
        wrapper_workspace = tempfile.mkdtemp(prefix="wrapper-test-1-")
        wrapper = create_a2a_wrapper(
            agent_id="wrapper-test-1",
            agent_type="testing",
            capabilities=["python", "testing"],
            workspace=wrapper_workspace,
        )

        # Start wrapper
        wrapper.start()
        print("✓ Wrapper started successfully")

        # Test wrapper methods
        agents = wrapper.discover_agents()
        print(f"✓ Wrapper discovery: Found {len(agents)} agents")

        task_id = wrapper.publish_task("Run tests", ["testing"])
        print(f"✓ Wrapper task publishing: Created task {task_id}")

        # Let wrapper process for a bit
        time.sleep(2)

        # Stop wrapper
        wrapper.stop()
        print("✓ Wrapper stopped successfully")

        print("✅ A2A wrapper test PASSED")

    except Exception as e:
        print(f"❌ A2A wrapper test FAILED: {e}")
        raise
    finally:
        # Cleanup temporary workspace
        with contextlib.suppress(Exception):
            shutil.rmtree(wrapper_workspace, ignore_errors=True)


def test_a2a_monitor():
    """Test A2A monitoring functionality"""
    print("\nTesting A2A monitor functionality...")

    try:
        # Create monitor
        monitor = A2AMonitor(cleanup_interval=60, stale_threshold=30)
        monitor.start()
        print("✓ Monitor started successfully")

        # Test health reporting
        health = monitor.get_system_health()
        print(f"✓ System health: {health['health_status']}")
        print(f"  - Active agents: {health['agents']['active']}")
        print(f"  - Available tasks: {health['tasks']['available']}")

        # Test cleanup
        cleanup_result = monitor.force_cleanup()
        print(f"✓ Cleanup completed: {cleanup_result}")

        monitor.stop()
        print("✓ Monitor stopped successfully")

        print("✅ A2A monitor test PASSED")

    except Exception as e:
        print(f"❌ A2A monitor test FAILED: {e}")
        raise


def test_task_dispatcher_integration():
    """Test task dispatcher A2A integration"""
    print("\nTesting task dispatcher A2A integration...")

    try:
        # Create dispatcher
        dispatcher = TaskDispatcher()
        print(f"✓ Task dispatcher created: A2A enabled = {dispatcher.a2a_enabled}")

        if dispatcher.a2a_enabled:
            # Test A2A task broadcasting
            task_id = dispatcher.broadcast_task_to_a2a("Test orchestration task", ["orchestration"])
            print(f"✓ Task broadcast: {task_id}")

            # Test A2A status
            status = dispatcher.get_a2a_status()
            print(f"✓ A2A status retrieved: {status.get('a2a_enabled', False)}")

            print("✅ Task dispatcher A2A integration test PASSED")
        else:
            print("⚠️  Task dispatcher A2A integration test SKIPPED (A2A not available)")

    except Exception as e:
        print(f"❌ Task dispatcher A2A integration test FAILED: {e}")
        raise


def run_all_tests():
    """Run all A2A tests"""
    print("🚀 Starting A2A System Tests")
    print(f"Test A2A directory: {A2A_BASE_DIR}")

    tests = [
        test_basic_a2a_functionality,
        test_a2a_wrapper,
        test_a2a_monitor,
        test_task_dispatcher_integration,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            test()
            passed += 1
        except Exception:
            pass

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All A2A tests PASSED!")
        return True
    print("💥 Some A2A tests FAILED!")
    return False


if __name__ == "__main__":

    def timeout_handler(signum, frame):
        print("⏰ Test timed out after 30 seconds - A2A tests may be hanging")
        sys.exit(3)

    try:
        # Set 30-second timeout for the entire test suite
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)

        success = run_all_tests()
        signal.alarm(0)  # Cancel timeout
        exit_code = 0 if success else 1
    except Exception as e:
        print(f"💥 Test suite crashed: {e}")
        exit_code = 2
    finally:
        # Cleanup test directory
        try:
            shutil.rmtree(test_dir, ignore_errors=True)
            print(f"🧹 Cleaned up test directory: {test_dir}")
        except Exception as e:
            print(f"Warning: Could not clean up test directory: {e}")

    sys.exit(exit_code)
