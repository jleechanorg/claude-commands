#!/usr/bin/env python3
"""
Command-line interface for capture analysis and mock validation.
"""

import argparse
import json
import os
import sys
from typing import Dict

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from capture_analysis import CaptureAnalyzer, create_mock_baseline


def analyze_command(args):
    """Analyze captured data."""
    analyzer = CaptureAnalyzer(args.capture_dir)
    analysis = analyzer.analyze_captures(days_back=args.days)
    
    if args.output:
        report = analyzer.generate_report(analysis, args.output)
        print(f"Analysis report saved to: {args.output}")
    else:
        report = analyzer.generate_report(analysis)
        print(report)


def compare_command(args):
    """Compare captured data with mock responses."""
    if not os.path.exists(args.capture_file):
        print(f"Error: Capture file not found: {args.capture_file}")
        return
    
    if not os.path.exists(args.mock_file):
        print(f"Error: Mock file not found: {args.mock_file}")
        return
    
    # Load mock responses
    with open(args.mock_file, 'r') as f:
        mock_responses = json.load(f)
    
    analyzer = CaptureAnalyzer(os.path.dirname(args.capture_file))
    comparison = analyzer.compare_with_mock(args.capture_file, mock_responses)
    
    print(f"Mock Validation Results:")
    print(f"Total comparisons: {comparison['total_comparisons']}")
    print(f"Matches: {comparison['matches']}")
    print(f"Accuracy score: {comparison['accuracy_score']:.2%}")
    print(f"Missing mocks: {len(comparison['missing_mocks'])}")
    print(f"Differences found: {len(comparison['differences'])}")
    
    if args.verbose:
        if comparison['missing_mocks']:
            print("\n## Missing Mock Responses:")
            for missing in comparison['missing_mocks']:
                print(f"- {missing['service']}.{missing['operation']}")
        
        if comparison['differences']:
            print("\n## Differences Found:")
            for diff in comparison['differences'][:5]:  # Show first 5
                print(f"- {diff['service']}.{diff['operation']}: {len(diff['differences'])} differences")
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(comparison, f, indent=2)
        print(f"\nDetailed comparison saved to: {args.output}")


def baseline_command(args):
    """Create mock baseline from captured data."""
    if not os.path.exists(args.capture_file):
        print(f"Error: Capture file not found: {args.capture_file}")
        return
    
    try:
        count = create_mock_baseline(args.capture_file, args.output)
        print(f"Created mock baseline with {count} responses")
        print(f"Saved to: {args.output}")
    except Exception as e:
        print(f"Error creating baseline: {e}")


def cleanup_command(args):
    """Clean up old capture files."""
    if not os.path.exists(args.capture_dir):
        print(f"Error: Capture directory not found: {args.capture_dir}")
        return
    
    from capture import cleanup_old_captures
    
    print(f"Cleaning up captures older than {args.days} days...")
    cleanup_old_captures(args.capture_dir, args.days)
    print("Cleanup completed")


def list_command(args):
    """List available capture files."""
    if not os.path.exists(args.capture_dir):
        print(f"Capture directory not found: {args.capture_dir}")
        return
    
    capture_files = []
    for filename in os.listdir(args.capture_dir):
        if filename.startswith('capture_') and filename.endswith('.json'):
            filepath = os.path.join(args.capture_dir, filename)
            stat = os.stat(filepath)
            size_kb = stat.st_size / 1024
            capture_files.append((filename, size_kb, stat.st_mtime))
    
    if not capture_files:
        print("No capture files found")
        return
    
    # Sort by modification time (newest first)
    capture_files.sort(key=lambda x: x[2], reverse=True)
    
    print(f"Found {len(capture_files)} capture files:")
    print(f"{'Filename':<40} {'Size (KB)':<10} {'Modified'}")
    print("-" * 70)
    
    for filename, size, mtime in capture_files:
        from datetime import datetime
        mod_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        print(f"{filename:<40} {size:<10.1f} {mod_time}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze and validate captured service interactions"
    )
    
    # Global options
    parser.add_argument(
        '--capture-dir', 
        default=os.environ.get('TEST_CAPTURE_DIR', '/tmp/test_captures'),
        help='Directory containing capture files'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze captured data')
    analyze_parser.add_argument('--days', type=int, default=7, 
                              help='Number of days back to analyze')
    analyze_parser.add_argument('--output', help='Output file for report')
    analyze_parser.set_defaults(func=analyze_command)
    
    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare with mock responses')
    compare_parser.add_argument('capture_file', help='Capture file to analyze')
    compare_parser.add_argument('mock_file', help='Mock responses file')
    compare_parser.add_argument('--output', help='Output file for detailed results')
    compare_parser.add_argument('--verbose', action='store_true', 
                               help='Show detailed differences')
    compare_parser.set_defaults(func=compare_command)
    
    # Baseline command
    baseline_parser = subparsers.add_parser('baseline', help='Create mock baseline')
    baseline_parser.add_argument('capture_file', help='Capture file to use as baseline')
    baseline_parser.add_argument('output', help='Output file for mock responses')
    baseline_parser.set_defaults(func=baseline_command)
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old captures')
    cleanup_parser.add_argument('--days', type=int, default=7,
                               help='Keep captures newer than this many days')
    cleanup_parser.set_defaults(func=cleanup_command)
    
    # List command
    list_parser = subparsers.add_parser('list', help='List capture files')
    list_parser.set_defaults(func=list_command)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        args.func(args)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()