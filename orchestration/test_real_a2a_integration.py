#!/usr/bin/env python3
"""
Real A2A Integration Test Suite - NO FAKE SIMULATIONS
Tests actual message flow and agent processing
"""

import asyncio
import json
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Any

from redis_a2a_bridge import RedisA2ABridge
from message_broker import MessageBroker

import sys


class RealA2AIntegrationTest:
    """Test suite that validates REAL A2A functionality - no simulations"""

    def __init__(self):
        self.bridge = RedisA2ABridge()
        self.broker = MessageBroker()
        self.test_results = {}
        self.debug_workers = []

    async def setup(self):
        """Start real debug workers for testing"""
        print("Starting 3 test workers on Redis...")

        # Start 3 debug workers
        for i in range(3):
            worker_id = f"test-worker-real-{i}"
            proc = subprocess.Popen(
                ["python3", "debug_worker.py", worker_id],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.debug_workers.append((worker_id, proc))
            print(f"  Started {worker_id}")

        # Give them time to register
        await asyncio.sleep(2)

    async def teardown(self):
        """Clean up test workers"""
        print("\nCleaning up test workers...")
        for worker_id, proc in self.debug_workers:
            proc.terminate()
            proc.wait()
            print(f"  Stopped {worker_id}")

    async def test_agent_discovery_real(self):
        """Test that we can discover REAL running agents"""
        test_name = "Agent Discovery (Real)"
        print(f"\nTesting {test_name}...")

        try:
            agents = await self.bridge.discover_agents_real()

            # Verify we found our test workers
            test_worker_count = sum(1 for a in agents if 'test-worker-real' in a['id'])

            if test_worker_count >= 3 and len(agents) >= 3:
                self.test_results[test_name] = {
                    "status": "PASS",
                    "message": f"Found {len(agents)} real agents including {test_worker_count} test workers",
                    "details": {
                        "total_agents": len(agents),
                        "test_workers": test_worker_count,
                        "agent_ids": [a['id'] for a in agents if 'test-worker-real' in a['id']]
                    }
                }
            else:
                self.test_results[test_name] = {
                    "status": "FAIL",
                    "message": f"Expected 3+ test workers, found {test_worker_count}",
                    "details": {"agents": agents}
                }

        except Exception as e:
            self.test_results[test_name] = {
                "status": "FAIL",
                "message": f"Exception: {str(e)}",
                "details": {}
            }

    async def test_task_execution_real(self):
        """Test REAL task execution with actual agent response"""
        test_name = "Task Execution (Real)"
        print(f"\nTesting {test_name}...")

        try:
            # Use shorter timeout for testing
            self.bridge.task_timeout = 5.0

            # Execute real task
            task_desc = "Test task for real execution validation"
            context_id = "real-test-context"

            start_time = time.time()
            result = await self.bridge.execute_task_real(
                task_description=task_desc,
                context_id=context_id,
                target_agent="test-worker-real-0"
            )
            end_time = time.time()

            # Validate REAL response
            if (result.get('status') == 'completed' and
                result.get('processed_by') == 'test-worker-real-0' and
                result.get('result') is not None):

                self.test_results[test_name] = {
                    "status": "PASS",
                    "message": f"Task completed in {end_time - start_time:.2f}s",
                    "details": {
                        "task_id": result.get('task_id'),
                        "status": result.get('status'),
                        "processed_by": result.get('processed_by'),
                        "result": result.get('result')
                    }
                }
            else:
                self.test_results[test_name] = {
                    "status": "FAIL",
                    "message": "Task did not complete successfully",
                    "details": result
                }

        except Exception as e:
            self.test_results[test_name] = {
                "status": "FAIL",
                "message": f"Exception: {str(e)}",
                "details": {}
            }

    async def test_workflow_orchestration_real(self):
        """Test REAL workflow execution across multiple agents"""
        test_name = "Workflow Orchestration (Real)"
        print(f"\nTesting {test_name}...")

        try:
            # Create a multi-step workflow
            workflow_desc = "Analyze requirements, implement solution, and test implementation"
            context_id = "real-workflow-test"

            start_time = time.time()
            result = await self.bridge.orchestrate_workflow_real(
                workflow_description=workflow_desc,
                context_id=context_id
            )
            end_time = time.time()

            # Validate all steps completed
            all_completed = all(
                step_result.get('status') == 'completed'
                for step_result in result['results'].values()
            )

            if (result['status'] == 'completed' and
                all_completed and
                result['steps_completed'] == result['total_steps']):

                self.test_results[test_name] = {
                    "status": "PASS",
                    "message": f"Workflow completed in {end_time - start_time:.2f}s",
                    "details": {
                        "workflow_id": result['workflow_id'],
                        "steps_completed": result['steps_completed'],
                        "total_steps": result['total_steps'],
                        "execution_time": f"{end_time - start_time:.2f}s"
                    }
                }
            else:
                self.test_results[test_name] = {
                    "status": "FAIL",
                    "message": "Workflow did not complete all steps successfully",
                    "details": result
                }

        except Exception as e:
            self.test_results[test_name] = {
                "status": "FAIL",
                "message": f"Exception: {str(e)}",
                "details": {}
            }

    async def test_concurrent_tasks_real(self):
        """Test REAL concurrent task execution"""
        test_name = "Concurrent Tasks (Real)"
        print(f"\nTesting {test_name}...")

        try:
            # Send multiple tasks concurrently
            tasks = []
            for i in range(3):
                task = self.bridge.execute_task_real(
                    task_description=f"Concurrent task {i}",
                    context_id=f"concurrent-test-{i}",
                    target_agent=f"test-worker-real-{i}"
                )
                tasks.append(task)

            # Wait for all to complete
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            # Check results
            successful = sum(1 for r in results
                           if isinstance(r, dict) and r.get('status') == 'completed')

            if successful == 3:
                self.test_results[test_name] = {
                    "status": "PASS",
                    "message": f"All 3 tasks completed in {end_time - start_time:.2f}s",
                    "details": {
                        "successful": successful,
                        "total": len(results),
                        "parallel_time": f"{end_time - start_time:.2f}s"
                    }
                }
            else:
                self.test_results[test_name] = {
                    "status": "FAIL",
                    "message": f"Only {successful}/3 tasks completed",
                    "details": {"results": results}
                }

        except Exception as e:
            self.test_results[test_name] = {
                "status": "FAIL",
                "message": f"Exception: {str(e)}",
                "details": {}
            }

    async def test_error_handling_real(self):
        """Test REAL error handling with non-existent agent"""
        test_name = "Error Handling (Real)"
        print(f"\nTesting {test_name}...")

        try:
            # Try to send task to non-existent agent
            result = await self.bridge.execute_task_real(
                task_description="Task for non-existent agent",
                context_id="error-test",
                target_agent="non-existent-agent-12345"
            )

            # Should get a failed status
            if result.get('status') == 'failed':
                self.test_results[test_name] = {
                    "status": "PASS",
                    "message": "Correctly handled non-existent agent",
                    "details": result
                }
            else:
                self.test_results[test_name] = {
                    "status": "FAIL",
                    "message": "Did not properly handle error",
                    "details": result
                }

        except Exception as e:
            # Timeout is expected for non-existent agent
            if "timed out" in str(e):
                self.test_results[test_name] = {
                    "status": "PASS",
                    "message": "Correctly timed out for non-existent agent",
                    "details": {"error": str(e)}
                }
            else:
                self.test_results[test_name] = {
                    "status": "FAIL",
                    "message": f"Unexpected exception: {str(e)}",
                    "details": {}
                }

    def print_results(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("REAL A2A INTEGRATION TEST RESULTS")
        print("=" * 60)

        passed = 0
        failed = 0

        for test_name, result in self.test_results.items():
            status = result['status']
            message = result['message']

            if status == "PASS":
                print(f"✅ {test_name}: {message}")
                passed += 1
            else:
                print(f"❌ {test_name}: {message}")
                failed += 1

            # Show details for failures
            if status == "FAIL" and result.get('details'):
                print(f"   Details: {json.dumps(result['details'], indent=2)}")

        print("\n" + "-" * 60)
        print(f"Total: {len(self.test_results)} tests")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print("-" * 60)

        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! A2A integration is fully functional.")
        else:
            print(f"\n❌ {failed} tests failed. See details above.")

        return failed == 0

    async def run_all_tests(self):
        """Run all real integration tests"""
        await self.setup()

        try:
            # Run tests in order
            await self.test_agent_discovery_real()
            await self.test_task_execution_real()
            await self.test_workflow_orchestration_real()
            await self.test_concurrent_tasks_real()
            await self.test_error_handling_real()

        finally:
            await self.teardown()

        return self.print_results()


async def main():
    """Run the real integration test suite"""
    print(f"Starting REAL A2A Integration Tests with {len(sys.argv)-1} test modules")
    print("This validates actual message flow, no simulations!")
    print("=" * 60)

    test_suite = RealA2AIntegrationTest()
    success = await test_suite.run_all_tests()

    return success


if __name__ == "__main__":

    success = asyncio.run(main())
    sys.exit(0 if success else 1)
