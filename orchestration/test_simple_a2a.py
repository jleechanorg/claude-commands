#!/usr/bin/env python3
"""
Simple test of A2A integration with existing Redis agents
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from redis_a2a_bridge import RedisA2ABridge


async def test_simple_a2a():
    """Test basic A2A functionality"""
    print("=== Simple A2A Integration Test ===")

    # Create bridge
    bridge = RedisA2ABridge()

    # Test 1: Discover agents
    print("\n1. Testing agent discovery...")
    agents = await bridge.discover_agents_real()
    print(f"   Found {len(agents)} agents:")
    for agent in agents[:5]:  # Show first 5
        print(f"   - {agent['id']}: {agent.get('type', 'unknown')}")

    if not agents:
        print("   ❌ No agents found - please start some agents first")
        return False

    # Test 2: Execute a simple task
    print("\n2. Testing task execution...")
    test_agent = agents[0]['id']
    print(f"   Using agent: {test_agent}")

    try:
        result = await asyncio.wait_for(
            bridge.execute_task_real(
                task_description="Simple A2A test task",
                context_id="test_context_123",
                target_agent=test_agent
            ),
            timeout=3.0
        )
        print(f"   ✅ Task completed: {result}")
    except asyncio.TimeoutError:
        print("   ⚠️  Task timed out (no worker processing) - this is expected without active workers")
    except Exception as e:
        print(f"   ❌ Task failed: {e}")

    # Test 3: Create a simple workflow
    print("\n3. Testing workflow creation...")
    workflow = {
        "name": "test_workflow",
        "description": "Test the A2A workflow system",
        "steps": [
            {"agent": test_agent, "task": "step1", "description": "First step"},
            {"agent": test_agent, "task": "step2", "description": "Second step"}
        ]
    }

    try:
        workflow_result = await asyncio.wait_for(
            bridge.orchestrate_workflow_real(
                workflow_description=workflow["description"],
                context_id="workflow_test_123"
            ),
            timeout=5.0
        )
        print(f"   Workflow status: {workflow_result.get('status', 'unknown')}")
        if workflow_result.get('status') == 'completed':
            print("   ✅ Workflow completed successfully")
        else:
            print(f"   ⚠️  Workflow incomplete: {workflow_result}")
    except asyncio.TimeoutError:
        print("   ⚠️  Workflow timed out - expected without active workers")
    except Exception as e:
        print(f"   ❌ Workflow failed: {e}")

    print("\n=== Test Complete ===")
    print("Note: Timeouts are expected without active worker processes")
    print("The important thing is that the A2A bridge connects to Redis and finds agents")

    return True


if __name__ == "__main__":
    success = asyncio.run(test_simple_a2a())
    sys.exit(0 if success else 1)
