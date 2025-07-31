"""
Performance Benchmark: MCP vs Direct Calls

Compares performance between:
1. Direct function calls (current main.py approach)
2. MCP protocol calls (new architecture)

This helps validate that MCP architecture doesn't introduce
significant performance overhead.
"""

import asyncio
import json
import logging
import os
import statistics
import sys
import time
from collections.abc import Callable
from typing import Any

# Performance testing configuration
SIMULATED_AI_DELAY = 0.050  # 50ms simulated AI API delay

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))

from helpers import mock_environment, patch_firestore, patch_gemini

logger = logging.getLogger(__name__)


class MockDirectCalls:
    """Mock implementation of direct function calls (current architecture)."""

    def __init__(self):
        self.call_count = 0

    def create_campaign(self, name: str, description: str, user_id: str) -> dict[str, Any]:
        """Direct campaign creation (simulates current main.py)."""
        self.call_count += 1

        # Simulate database operation delay
        time.sleep(0.001)  # 1ms simulated DB delay

        import uuid
        campaign_id = str(uuid.uuid4())

        return {
            'success': True,
            'data': {
                'campaign_id': campaign_id,
                'name': name,
                'description': description,
                'dm_user_id': user_id,
                'created_at': time.time()
            }
        }

    def get_campaigns(self, user_id: str) -> dict[str, Any]:
        """Direct campaigns retrieval."""
        self.call_count += 1

        # Simulate database query delay
        time.sleep(0.002)  # 2ms simulated DB query

        return {
            'success': True,
            'data': {
                'campaigns': [
                    {
                        'id': 'campaign-1',
                        'name': 'Test Campaign 1',
                        'dm_user_id': user_id
                    },
                    {
                        'id': 'campaign-2',
                        'name': 'Test Campaign 2',
                        'dm_user_id': user_id
                    }
                ]
            }
        }

    def process_action(self, session_id: str, action_type: str, action_data: dict[str, Any]) -> dict[str, Any]:
        """Direct action processing (includes AI call simulation)."""
        self.call_count += 1

        # Simulate AI API call delay (this is the expensive operation)
        time.sleep(SIMULATED_AI_DELAY)

        return {
            'success': True,
            'data': {
                'action_id': f'action-{self.call_count}',
                'session_id': session_id,
                'action_type': action_type,
                'result': 'Action processed successfully',
                'narrative': f'The {action_type} action was completed.',
                'timestamp': time.time()
            }
        }


class PerformanceBenchmark:
    """Performance benchmark suite for MCP vs Direct calls."""

    def __init__(self, mock_port: int = 8001):
        self.mock_port = mock_port
        self.direct_calls = MockDirectCalls()
        self.results: dict[str, Any] = {}

    async def benchmark_function(self, func: Callable, *args, iterations: int = 100, **kwargs) -> dict[str, Any]:
        """Benchmark a function over multiple iterations."""
        times = []
        errors = 0

        for i in range(iterations):
            start_time = time.perf_counter()

            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)  # Convert to milliseconds

            except Exception as e:
                errors += 1
                logger.error(f"Error in iteration {i}: {e}")

        if not times:
            return {
                'error': 'All iterations failed',
                'errors': errors,
                'iterations': iterations
            }

        return {
            'mean_ms': statistics.mean(times),
            'median_ms': statistics.median(times),
            'min_ms': min(times),
            'max_ms': max(times),
            'std_dev_ms': statistics.stdev(times) if len(times) > 1 else 0,
            'p95_ms': self._percentile(times, 95),
            'p99_ms': self._percentile(times, 99),
            'total_time_ms': sum(times),
            'iterations': len(times),
            'errors': errors,
            'success_rate': len(times) / iterations
        }

    def _percentile(self, data: list[float], percentile: int) -> float:
        """Calculate percentile of data."""
        sorted_data = sorted(data)
        index = int((percentile / 100.0) * len(sorted_data))
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        return sorted_data[index]

    @patch_firestore()
    @patch_gemini()
    async def benchmark_campaign_creation(self, mock_gemini, mock_firestore) -> dict[str, Any]:
        """Benchmark campaign creation: Direct vs MCP."""
        results = {}

        # Benchmark direct calls
        logger.info("Benchmarking direct campaign creation...")
        direct_result = await self.benchmark_function(
            self.direct_calls.create_campaign,
            "Benchmark Campaign",
            "Campaign for performance testing",
            "benchmark-user-123",
            iterations=50
        )
        results['direct'] = direct_result

        # Benchmark MCP calls
        logger.info("Benchmarking MCP campaign creation...")
        with mock_environment(self.mock_port) as env:
            client = env['client']

            async def mcp_create_campaign():
                async with client:
                    return await client.create_campaign(
                        name="Benchmark Campaign",
                        description="Campaign for performance testing",
                        user_id="benchmark-user-123"
                    )

            mcp_result = await self.benchmark_function(
                mcp_create_campaign,
                iterations=50
            )
            results['mcp'] = mcp_result

        # Calculate overhead
        if 'mean_ms' in direct_result and 'mean_ms' in mcp_result:
            overhead_ms = mcp_result['mean_ms'] - direct_result['mean_ms']
            overhead_percent = (overhead_ms / direct_result['mean_ms']) * 100

            results['overhead'] = {
                'absolute_ms': overhead_ms,
                'percent': overhead_percent
            }

        return results

    @patch_firestore()
    @patch_gemini()
    async def benchmark_campaign_retrieval(self, mock_gemini, mock_firestore) -> dict[str, Any]:
        """Benchmark campaign retrieval: Direct vs MCP."""
        results = {}

        # Benchmark direct calls
        logger.info("Benchmarking direct campaign retrieval...")
        direct_result = await self.benchmark_function(
            self.direct_calls.get_campaigns,
            "benchmark-user-123",
            iterations=100
        )
        results['direct'] = direct_result

        # Benchmark MCP calls
        logger.info("Benchmarking MCP campaign retrieval...")
        with mock_environment(self.mock_port) as env:
            client = env['client']

            async def mcp_get_campaigns():
                async with client:
                    return await client.get_campaigns(user_id="benchmark-user-123")

            mcp_result = await self.benchmark_function(
                mcp_get_campaigns,
                iterations=100
            )
            results['mcp'] = mcp_result

        # Calculate overhead
        if 'mean_ms' in direct_result and 'mean_ms' in mcp_result:
            overhead_ms = mcp_result['mean_ms'] - direct_result['mean_ms']
            overhead_percent = (overhead_ms / direct_result['mean_ms']) * 100

            results['overhead'] = {
                'absolute_ms': overhead_ms,
                'percent': overhead_percent
            }

        return results

    @patch_firestore()
    @patch_gemini()
    async def benchmark_action_processing(self, mock_gemini, mock_firestore) -> dict[str, Any]:
        """Benchmark action processing: Direct vs MCP (includes AI calls)."""
        results = {}

        # Benchmark direct calls
        logger.info("Benchmarking direct action processing...")
        direct_result = await self.benchmark_function(
            self.direct_calls.process_action,
            "benchmark-session-123",
            "attack",
            {"target": "goblin", "weapon": "sword"},
            iterations=20  # Fewer iterations due to AI delay
        )
        results['direct'] = direct_result

        # Benchmark MCP calls
        logger.info("Benchmarking MCP action processing...")
        with mock_environment(self.mock_port) as env:
            client = env['client']

            async def mcp_process_action():
                async with client:
                    return await client.process_action(
                        session_id="benchmark-session-123",
                        action_type="attack",
                        action_data={"target": "goblin", "weapon": "sword"}
                    )

            mcp_result = await self.benchmark_function(
                mcp_process_action,
                iterations=20
            )
            results['mcp'] = mcp_result

        # Calculate overhead
        if 'mean_ms' in direct_result and 'mean_ms' in mcp_result:
            overhead_ms = mcp_result['mean_ms'] - direct_result['mean_ms']
            overhead_percent = (overhead_ms / direct_result['mean_ms']) * 100

            results['overhead'] = {
                'absolute_ms': overhead_ms,
                'percent': overhead_percent
            }

        return results

    async def run_full_benchmark(self) -> dict[str, Any]:
        """Run complete performance benchmark suite."""
        logger.info("Starting comprehensive performance benchmark...")

        benchmark_results = {
            'timestamp': time.time(),
            'benchmarks': {}
        }

        # Campaign creation benchmark
        campaign_creation = await self.benchmark_campaign_creation()
        benchmark_results['benchmarks']['campaign_creation'] = campaign_creation

        # Campaign retrieval benchmark
        campaign_retrieval = await self.benchmark_campaign_retrieval()
        benchmark_results['benchmarks']['campaign_retrieval'] = campaign_retrieval

        # Action processing benchmark
        action_processing = await self.benchmark_action_processing()
        benchmark_results['benchmarks']['action_processing'] = action_processing

        # Overall summary
        overheads = []
        for benchmark_name, benchmark_data in benchmark_results['benchmarks'].items():
            if 'overhead' in benchmark_data and 'percent' in benchmark_data['overhead']:
                overheads.append(benchmark_data['overhead']['percent'])

        if overheads:
            benchmark_results['summary'] = {
                'average_overhead_percent': statistics.mean(overheads),
                'max_overhead_percent': max(overheads),
                'min_overhead_percent': min(overheads),
                'acceptable_overhead': all(o < 20 for o in overheads),  # < 20% overhead acceptable
                'performance_verdict': 'PASS' if all(o < 20 for o in overheads) else 'FAIL'
            }

        return benchmark_results

    def generate_report(self, results: dict[str, Any]) -> str:
        """Generate human-readable performance report."""
        report = []
        report.append("=" * 60)
        report.append("MCP ARCHITECTURE PERFORMANCE BENCHMARK REPORT")
        report.append("=" * 60)
        report.append("")

        if 'summary' in results:
            summary = results['summary']
            report.append(f"OVERALL VERDICT: {summary['performance_verdict']}")
            report.append(f"Average Overhead: {summary['average_overhead_percent']:.2f}%")
            report.append(f"Max Overhead: {summary['max_overhead_percent']:.2f}%")
            report.append("")

        for benchmark_name, benchmark_data in results['benchmarks'].items():
            report.append(f"--- {benchmark_name.upper().replace('_', ' ')} ---")

            if 'direct' in benchmark_data:
                direct = benchmark_data['direct']
                report.append("Direct Call Performance:")
                report.append(f"  Mean: {direct['mean_ms']:.2f}ms")
                report.append(f"  Median: {direct['median_ms']:.2f}ms")
                report.append(f"  P95: {direct['p95_ms']:.2f}ms")
                report.append(f"  Success Rate: {direct['success_rate']*100:.1f}%")

            if 'mcp' in benchmark_data:
                mcp = benchmark_data['mcp']
                report.append("MCP Call Performance:")
                report.append(f"  Mean: {mcp['mean_ms']:.2f}ms")
                report.append(f"  Median: {mcp['median_ms']:.2f}ms")
                report.append(f"  P95: {mcp['p95_ms']:.2f}ms")
                report.append(f"  Success Rate: {mcp['success_rate']*100:.1f}%")

            if 'overhead' in benchmark_data:
                overhead = benchmark_data['overhead']
                status = "✓ ACCEPTABLE" if overhead['percent'] < 20 else "✗ TOO HIGH"
                report.append(f"MCP Overhead: {overhead['absolute_ms']:.2f}ms ({overhead['percent']:.1f}%) {status}")

            report.append("")

        return "\n".join(report)


async def main():
    """Main benchmark execution."""
    logging.basicConfig(level=logging.INFO)

    benchmark = PerformanceBenchmark()

    print("Starting MCP Architecture Performance Benchmark...")
    print("This will compare direct function calls vs MCP protocol calls")
    print("=" * 60)

    try:
        results = await benchmark.run_full_benchmark()

        # Generate and display report
        report = benchmark.generate_report(results)
        print(report)

        # Save results to file
        output_file = f"benchmark_results_{int(time.time())}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"Detailed results saved to: {output_file}")

        # Exit with appropriate code
        if results.get('summary', {}).get('performance_verdict') == 'PASS':
            print("\n✓ BENCHMARK PASSED: MCP overhead is acceptable")
            return 0
        print("\n✗ BENCHMARK FAILED: MCP overhead is too high")
        return 1

    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        print(f"\n✗ BENCHMARK ERROR: {e}")
        return 1


if __name__ == '__main__':
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
