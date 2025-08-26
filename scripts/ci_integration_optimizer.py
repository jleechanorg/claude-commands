#!/usr/bin/env python3
"""
CI Integration Optimizer - GitHub Actions matrix optimization for 15-minute CI target

Optimizes GitHub Actions workflow configuration for parallel test execution,
intelligent test grouping, and performance monitoring to achieve 15-minute CI target.
"""

import json
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Tuple


logger = logging.getLogger(__name__)


class CIIntegrationOptimizer:
    def __init__(self, target_time_minutes=15):
        self.target_time = target_time_minutes

    def optimize_github_actions_matrix(self, test_files):
        # Optimize GitHub Actions matrix for parallel execution
        matrix_entries = []
        for test_file in test_files:
            matrix_entries.append({
                'test_file': test_file
            })
        return {'matrix': {'include': matrix_entries}}

    def generate_workflow_yaml(self):
        # Generate optimized workflow YAML
        return """name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include: []
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python -m pytest ${{ matrix.test_file }}
"""

    def create_intelligent_test_groups(self, test_files: List[str], worker_count: int = 4) -> List[List[str]]:
        """Group tests intelligently for parallel execution."""
        logger.info(f"Creating {worker_count} intelligent test groups from {len(test_files)} tests")
        
        # Analyze test complexity and group accordingly
        test_complexity = {}
        for test_file in test_files:
            test_complexity[test_file] = self._estimate_test_complexity(test_file)
        
        # Sort by complexity (descending) for load balancing
        sorted_tests = sorted(test_complexity.items(), key=lambda x: x[1], reverse=True)
        
        # Distribute tests across workers using round-robin with load balancing
        groups = [[] for _ in range(worker_count)]
        group_loads = [0] * worker_count
        
        for test_file, complexity in sorted_tests:
            # Find group with minimum load
            min_load_index = group_loads.index(min(group_loads))
            groups[min_load_index].append(test_file)
            group_loads[min_load_index] += complexity
        
        logger.info(f"Test groups created with loads: {group_loads}")
        return groups

    def generate_optimized_workflow(self, test_groups: List[List[str]]) -> str:
        """Generate optimized GitHub Actions workflow YAML."""
        
        workflow = {
            'name': 'Optimized Test Suite',
            'on': {
                'push': {'branches': ['main']},
                'pull_request': {'branches': ['main']}
            },
            'jobs': {
                'test-matrix': {
                    'runs-on': 'ubuntu-latest',
                    'strategy': {
                        'fail-fast': False,
                        'matrix': {
                            'test-group': list(range(len(test_groups)))
                        }
                    },
                    'steps': [
                        {'uses': 'actions/checkout@v4'},
                        {
                            'name': 'Set up Python',
                            'uses': 'actions/setup-python@v4',
                            'with': {'python-version': '3.11'}
                        },
                        {
                            'name': 'Install dependencies',
                            'run': 'pip install -r requirements.txt'
                        },
                        {
                            'name': 'Run test group',
                            'run': self._generate_test_command(),
                            'env': {
                                'TEST_GROUP': '${{ matrix.test-group }}',
                                'PARALLEL_WORKERS': '4'
                            }
                        }
                    ]
                },
                'coverage-report': {
                    'needs': 'test-matrix',
                    'runs-on': 'ubuntu-latest',
                    'if': 'always()',
                    'steps': [
                        {'uses': 'actions/checkout@v4'},
                        {
                            'name': 'Generate coverage report',
                            'run': 'python scripts/generate_coverage_report.py'
                        }
                    ]
                }
            }
        }
        
        return yaml.dump(workflow, default_flow_style=False, sort_keys=False)

    def estimate_ci_time(self, test_files: List[str], worker_count: int = 4) -> Dict:
        """Estimate CI execution time with optimization."""
        
        total_complexity = sum(self._estimate_test_complexity(f) for f in test_files)
        avg_complexity_per_worker = total_complexity / worker_count
        
        # Time estimation based on complexity (1 complexity unit ≈ 2 seconds)
        estimated_time_minutes = (avg_complexity_per_worker * 2) / 60
        
        # Add overhead (setup, teardown, reporting)
        overhead_minutes = 5
        total_estimated_time = estimated_time_minutes + overhead_minutes
        
        return {
            'estimated_time_minutes': round(total_estimated_time, 1),
            'target_time_minutes': self.target_time,
            'meets_target': total_estimated_time <= self.target_time,
            'time_savings': max(0, (len(test_files) * 0.5) - total_estimated_time),
            'parallel_efficiency': round(worker_count / max(1, total_estimated_time / 5), 2)
        }

    def _estimate_test_complexity(self, test_file: str) -> float:
        """Estimate complexity score for a test file."""
        try:
            path = Path(test_file)
            if not path.exists():
                return 1.0  # Default complexity
            
            # File size based complexity
            size_kb = path.stat().st_size / 1024
            size_score = min(size_kb / 10, 5)  # Max 5 points for size
            
            # Content analysis
            with open(path, 'r') as f:
                content = f.read()
            
            # Complexity indicators
            line_count = len(content.split('\n'))
            line_score = min(line_count / 50, 3)  # Max 3 points for lines
            
            # Test type complexity
            type_score = 1
            if 'integration' in path.name.lower():
                type_score = 3
            elif 'api' in path.name.lower() or 'database' in path.name.lower():
                type_score = 2
            
            return size_score + line_score + type_score
            
        except Exception as e:
            logger.warning(f"Error estimating complexity for {test_file}: {e}")
            return 1.0

    def _generate_test_command(self) -> str:
        """Generate the test execution command for CI."""
        return """
python3 scripts/run_test_group.py --group=$TEST_GROUP --workers=$PARALLEL_WORKERS --cache-optimizer
        """.strip()

    def create_test_group_runner(self, test_groups: List[List[str]], output_file: str = "scripts/run_test_group.py"):
        """Create the test group runner script for CI."""
        
        runner_script = f'''#!/usr/bin/env python3
"""
Test Group Runner - Execute specific test groups in CI
Generated by CIIntegrationOptimizer for parallel execution
"""

import argparse
import sys
import subprocess
from pathlib import Path

TEST_GROUPS = {test_groups}

def main():
    parser = argparse.ArgumentParser(description="Run specific test group")
    parser.add_argument("--group", type=int, required=True, help="Test group index")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers")
    parser.add_argument("--cache-optimizer", action="store_true", help="Enable cache optimization")
    
    args = parser.parse_args()
    
    if args.group >= len(TEST_GROUPS):
        print(f"Error: Group {{args.group}} not found. Available groups: 0-{{len(TEST_GROUPS)-1}}")
        sys.exit(1)
    
    test_files = TEST_GROUPS[args.group]
    print(f"Running test group {{args.group}} with {{len(test_files)}} tests")
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    if args.cache_optimizer:
        cmd.extend(["--cache-optimizer", f"--num-workers={{args.workers}}"])
    
    cmd.extend(test_files)
    
    # Execute tests
    result = subprocess.run(cmd, capture_output=False)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
'''
        
        with open(output_file, 'w') as f:
            f.write(runner_script)
        
        # Make executable
        Path(output_file).chmod(0o755)
        logger.info(f"Created test group runner: {output_file}")