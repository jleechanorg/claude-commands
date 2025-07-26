#!/usr/bin/env python3
"""
Test real A2A flow with fixed response correlation
"""

import asyncio
import sys
import os
import time
import json
from datetime import datetime

import traceback

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from redis_a2a_bridge import RedisA2ABridge
from message_broker import MessageBroker


async def test_real_task_execution():
    """Test that tasks actually get executed and responses are received"""
    print("=== Testing Real A2A Task Execution ===\n")

    # Initialize bridge
    broker = MessageBroker()
    bridge = RedisA2ABridge(broker)

    # First check for active agents
    print("1. Discovering active agents...")
    agents = await bridge.discover_agents_real()

    if not agents:
        print("❌ No active agents found!")
        print("\nPlease start a test worker in another terminal:")
        print("  cd orchestration && python3 test_agent_worker.py test-worker-1")
        return False

    print(f"✅ Found {len(agents)} active agents:")
    for agent in agents:
        print(f"   - {agent['id']} (type: {agent['type']}, queue: {agent['queue_size']} tasks)")

    # Test task execution
    print("\n2. Testing task execution...")
    task_description = "Test task from real A2A flow test"
    context_id = "test-context-123"

    # Use a specific test agent
    test_agent = agents[0]['id']
    print(f"   Sending task to agent: {test_agent}")

    try:
        # Reduce timeout for testing
        bridge.task_timeout = 10.0

        start_time = time.time()
        result = await bridge.execute_task_real(
            task_description=task_description,
            context_id=context_id,
            target_agent=test_agent
        )
        end_time = time.time()

        print(f"\n✅ Task completed successfully in {end_time - start_time:.2f} seconds!")
        print(f"   Result: {json.dumps(result, indent=2)}")

        # Verify result structure
        assert result.get('status') == 'completed', f"Expected status 'completed', got {result.get('status')}"
        assert result.get('task_id') is not None, "Missing task_id in result"
        assert result.get('processed_by') == test_agent, f"Expected processed_by '{test_agent}', got {result.get('processed_by')}"

        return True

    except asyncio.TimeoutError:
        print(f"\n❌ Task timed out after {bridge.task_timeout} seconds!")
        print("   This means the response correlation is still not working.")

        # Debug: Check what's in the queues
        print("\n3. Debugging queue contents...")
        a2a_queue = broker.redis_client.lrange("queue:a2a_bridge", 0, -1)
        print(f"   queue:a2a_bridge has {len(a2a_queue)} messages")

        for i, msg in enumerate(a2a_queue):
            try:
                data = json.loads(msg)
                print(f"\n   Message {i}:")
                print(f"     Type: {data.get('type')}")
                print(f"     From: {data.get('from_agent')}")
                print(f"     Payload: {data.get('payload')}")
            except Exception as e:
                print(f"     Error parsing: {e}")

        return False

    except Exception as e:
        print(f"\n❌ Task execution failed: {e}")

        traceback.print_exc()
        return False


async def test_workflow_execution():
    """Test workflow orchestration"""
    print("\n\n=== Testing Workflow Orchestration ===\n")

    bridge = RedisA2ABridge()

    # Test workflow
    workflow_desc = "Analyze requirements, implement solution, and test"
    context_id = "workflow-test-456"

    try:
        print("1. Creating workflow...")
        result = await bridge.orchestrate_workflow_real(
            workflow_description=workflow_desc,
            context_id=context_id
        )

        print(f"\n✅ Workflow completed!")
        print(f"   Workflow ID: {result['workflow_id']}")
        print(f"   Status: {result['status']}")
        print(f"   Steps completed: {result['steps_completed']}/{result['total_steps']}")

        # Check workflow state in Redis
        workflow_key = f"a2a_workflow:{result['workflow_id']}"
        workflow_state = bridge.message_broker.redis_client.hgetall(workflow_key)
        print(f"\n   Workflow state in Redis:")
        for key, value in workflow_state.items():
            if key in ['steps', 'results']:
                print(f"     {key}: <json data>")
            else:
                print(f"     {key}: {value}")

        return True

    except Exception as e:
        print(f"\n❌ Workflow execution failed: {e}")

        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print(f"Starting Real A2A Integration Tests at {datetime.now().isoformat()}")
    print("=" * 50)

    # Run tests
    task_success = await test_real_task_execution()

    if task_success:
        workflow_success = await test_workflow_execution()
    else:
        print("\n⚠️  Skipping workflow test since task execution failed")
        workflow_success = False

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"  Task Execution: {'✅ PASSED' if task_success else '❌ FAILED'}")
    print(f"  Workflow Orchestration: {'✅ PASSED' if workflow_success else '❌ FAILED' if task_success else '⏭️  SKIPPED'}")

    if task_success and workflow_success:
        print("\n🎉 All tests passed! A2A integration is functional.")
    else:
        print("\n❌ Some tests failed. Please check the output above.")

    return task_success and workflow_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
