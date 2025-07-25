#!/usr/bin/env python3
"""Test real workflow orchestration"""

import asyncio
import subprocess
import time
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from redis_a2a_bridge import RedisA2ABridge
from message_broker import MessageBroker


async def test_real_workflow():
    """Test workflow orchestration with debug workers"""
    print("=== Testing Real Workflow Orchestration ===\n")
    
    # Start multiple debug workers
    print("1. Starting debug workers...")
    workers = []
    for i in range(3):
        worker_id = f"workflow-worker-{i}"
        proc = subprocess.Popen(
            ["python3", "debug_worker.py", worker_id],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        workers.append((worker_id, proc))
        print(f"   Started {worker_id}")
    
    # Give them time to start
    time.sleep(2)
    
    try:
        # Initialize bridge
        bridge = RedisA2ABridge()
        bridge.task_timeout = 10.0  # Reasonable timeout
        
        # Verify workers are ready
        print("\n2. Verifying workers...")
        agents = await bridge.discover_agents_real()
        worker_count = sum(1 for a in agents if 'workflow-worker' in a['id'])
        print(f"   Found {worker_count} workflow workers")
        
        # Create workflow
        print("\n3. Creating workflow...")
        workflow_desc = "Analyze the requirements, implement the solution, and test the implementation"
        context_id = "workflow-test-real"
        
        start_time = time.time()
        result = await bridge.orchestrate_workflow_real(
            workflow_description=workflow_desc,
            context_id=context_id
        )
        end_time = time.time()
        
        print(f"\n✅ Workflow completed in {end_time - start_time:.2f} seconds!")
        print(f"   Workflow ID: {result['workflow_id']}")
        print(f"   Status: {result['status']}")
        print(f"   Steps completed: {result['steps_completed']}/{result['total_steps']}")
        
        # Show step results
        print("\n4. Step Results:")
        for step_id, step_result in result['results'].items():
            print(f"\n   {step_id}:")
            print(f"     Status: {step_result.get('status')}")
            if step_result.get('status') == 'completed':
                print(f"     Result: {step_result.get('result')}")
            else:
                print(f"     Error: {step_result.get('error')}")
        
        # Verify workflow state in Redis
        print("\n5. Verifying Redis state...")
        broker = MessageBroker()
        workflow_key = f"a2a_workflow:{result['workflow_id']}"
        workflow_state = broker.redis_client.hgetall(workflow_key)
        
        print(f"   Workflow exists in Redis: {'✅' if workflow_state else '❌'}")
        if workflow_state:
            print(f"   Status in Redis: {workflow_state.get('status')}")
            print(f"   Created at: {workflow_state.get('created_at')}")
            print(f"   Completed at: {workflow_state.get('completed_at', 'N/A')}")
        
        # Success if all steps completed
        success = result['status'] == 'completed' and result['steps_completed'] == result['total_steps']
        
        return success
        
    finally:
        # Clean up workers
        print("\n6. Cleaning up workers...")
        for worker_id, proc in workers:
            proc.terminate()
            proc.wait()
            print(f"   Stopped {worker_id}")


async def main():
    success = await test_real_workflow()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Workflow orchestration is working correctly!")
        print("✅ All workflow steps were executed by real Redis agents")
    else:
        print("❌ Workflow orchestration test failed")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)