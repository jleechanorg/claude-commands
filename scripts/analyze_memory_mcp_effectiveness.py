#!/usr/bin/env python3
"""
Memory MCP Effectiveness Analyzer
Analyzes conversation logs to measure Memory MCP search effectiveness and consultation patterns.

Based on investigation showing:
- Need to track search success rates
- Measure consultation frequency and decision correlation
- Identify patterns for optimization improvements
"""

import argparse
import json
import sys
import os
from typing import Dict, List, Any, Optional, Tuple
import re
from pathlib import Path

# Add mvp_site to path for logging_util import
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mvp_site'))
import logging_util

# Use project logging utility
logger = logging_util.getLogger(__name__)

# Constants for analysis thresholds
MIN_LINE_THRESHOLD = 10  # Minimum lines to consider a substantial conversation
EMPTY_RESULT_INDICATORS = ['no entities', 'empty result', 'no results found', '[]', '{}']
SUCCESS_INDICATORS = ['found', 'entities', 'discovered', 'retrieved', 'located']
CONSULTATION_PATTERNS = [r'memory.?search', r'mcp.*memory', r'memory.*query', r'search.*pattern']


class MemoryMCPAnalyzer:
    """
    Analyzer for Memory MCP effectiveness in conversation logs.
    Tracks search patterns, success rates, and decision correlations.
    """

    def __init__(self, log_directory: Optional[str] = None) -> None:
        """
        Initialize the analyzer with optional log directory.

        Args:
            log_directory: Path to conversation logs directory
        """
        self.log_directory = log_directory or self._find_log_directory()
        self.consultation_frequency = 0
        self.successful_consultations = 0
        self.total_searches = 0
        self.decision_correlations = []
        self.search_patterns = {}

        logger.info(f"Initialized Memory MCP Analyzer with log directory: {self.log_directory}")

    def _find_log_directory(self) -> str:
        """
        Find the conversation logs directory using project conventions.

        Returns:
            Path to conversation logs directory
        """
        # Check common locations for conversation logs
        possible_paths = [
            os.path.expanduser("~/.claude/projects"),
            os.path.join(os.getcwd(), "logs"),
            os.path.join(os.getcwd(), "tmp", "logs"),
            "/tmp/claude_logs"
        ]

        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found log directory: {path}")
                return path

        # Default fallback
        default_path = os.path.expanduser("~/.claude/projects")
        logger.warning(f"No log directory found, using default: {default_path}")
        return default_path

    def parse_conversation_log(self, log_file: str) -> Dict[str, Any]:
        """
        Parse a single conversation log file (JSONL format).

        Args:
            log_file: Path to the conversation log file

        Returns:
            Dictionary containing parsed conversation data and metrics
        """
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                line_count = len(lines)

            if line_count < MIN_LINE_THRESHOLD:
                logger.debug(f"Skipping short conversation log: {log_file} ({line_count} lines)")
                return {'skipped': True, 'reason': 'too_short', 'line_count': line_count}

            conversation_data = []
            memory_consultations = 0
            successful_searches = 0
            total_message_searches = 0

            for line_num, line in enumerate(lines, 1):
                try:
                    if line.strip():  # Skip empty lines
                        entry = json.loads(line.strip())
                        conversation_data.append(entry)

                        # Analyze for memory MCP patterns
                        content = str(entry.get('content', ''))

                        # Check for memory consultations
                        if self._has_memory_consultation(content):
                            memory_consultations += 1
                            total_message_searches += 1

                            # Check if consultation was successful
                            if self._is_successful_result(content):
                                successful_searches += 1

                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON on line {line_num} in {log_file}: {e}")
                    continue

            # Calculate effectiveness metrics
            consultation_frequency = memory_consultations / line_count if line_count > 0 else 0.0
            success_rate = successful_searches / total_message_searches if total_message_searches > 0 else 0.0

            result = {
                'file': log_file,
                'line_count': line_count,
                'total_entries': len(conversation_data),
                'memory_consultations': memory_consultations,
                'successful_searches': successful_searches,
                'total_searches': total_message_searches,
                'consultation_frequency': consultation_frequency,
                'success_rate': success_rate,
                'skipped': False
            }

            logger.debug(f"Parsed {log_file}: {memory_consultations} consultations, {success_rate:.2%} success rate")
            return result

        except UnicodeDecodeError as e:
            logger.error(f"UTF-8 encoding error reading {log_file}: {e}")
            return {'skipped': True, 'reason': 'encoding_error', 'error': str(e)}
        except FileNotFoundError:
            logger.error(f"Log file not found: {log_file}")
            return {'skipped': True, 'reason': 'file_not_found'}
        except Exception as e:
            logger.error(f"Unexpected error parsing {log_file}: {e}")
            return {'skipped': True, 'reason': 'parse_error', 'error': str(e)}

    def _has_memory_consultation(self, content: str) -> bool:
        """
        Check if content indicates a memory MCP consultation.

        Args:
            content: Message content to analyze

        Returns:
            True if content contains memory consultation patterns
        """
        content_lower = content.lower()

        # Check for explicit consultation patterns
        for pattern in CONSULTATION_PATTERNS:
            if re.search(pattern, content_lower):
                return True

        # Check for memory-related keywords
        memory_keywords = ['memory search', 'mcp search', 'search memory', 'recall pattern']
        return any(keyword in content_lower for keyword in memory_keywords)

    def _is_successful_result(self, content: str) -> bool:
        """
        Determine if a memory consultation resulted in successful results.
        Make this robust to handle non-string content and various result formats.

        Args:
            content: Content to analyze for success indicators

        Returns:
            True if content indicates successful memory retrieval
        """
        try:
            # Handle non-string content robustly
            if not isinstance(content, str):
                content = str(content) if content is not None else ""

            content_lower = content.lower()

            # Check for explicit empty result indicators first
            if any(indicator in content_lower for indicator in EMPTY_RESULT_INDICATORS):
                return False

            # Check for success indicators
            has_success_indicators = any(indicator in content_lower for indicator in SUCCESS_INDICATORS)

            # Look for entity/relationship counts
            entity_count_match = re.search(r'(\d+)\s*entit', content_lower)
            if entity_count_match:
                count = int(entity_count_match.group(1))
                return count > 0

            # Look for JSON-like structures with content
            if re.search(r'\{.*"entities".*\[.*\].*\}', content, re.DOTALL):
                # Check if the entities array is not empty
                if not re.search(r'"entities":\s*\[\s*\]', content):
                    return True

            return has_success_indicators

        except Exception as e:
            logger.warning(f"Error analyzing result content: {e}")
            # Default to False for robustness
            return False

    def analyze_directory(self, directory: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze all conversation logs in a directory.

        Args:
            directory: Directory to analyze (uses self.log_directory if None)

        Returns:
            Comprehensive analysis results
        """
        target_dir = directory or self.log_directory

        if not os.path.exists(target_dir):
            logger.error(f"Directory does not exist: {target_dir}")
            return {'error': 'directory_not_found', 'directory': target_dir}

        log_files = []
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                if file.endswith('.jsonl') or 'conversation' in file.lower():
                    log_files.append(os.path.join(root, file))

        if not log_files:
            logger.warning(f"No conversation log files found in {target_dir}")
            return {'error': 'no_log_files', 'directory': target_dir}

        logger.info(f"Analyzing {len(log_files)} log files in {target_dir}")

        # Analyze each log file
        results = []
        total_consultations = 0
        total_successful = 0
        total_searches = 0
        skipped_files = 0

        for log_file in log_files:
            result = self.parse_conversation_log(log_file)
            results.append(result)

            if result.get('skipped'):
                skipped_files += 1
                continue

            total_consultations += result['memory_consultations']
            total_successful += result['successful_searches']
            total_searches += result['total_searches']

        # Calculate overall metrics
        analyzed_files = len(log_files) - skipped_files
        overall_success_rate = total_successful / total_searches if total_searches > 0 else 0.0

        summary = {
            'directory': target_dir,
            'total_files': len(log_files),
            'analyzed_files': analyzed_files,
            'skipped_files': skipped_files,
            'total_consultations': total_consultations,
            'total_successful_searches': total_successful,
            'total_searches': total_searches,
            'overall_success_rate': overall_success_rate,
            'average_consultations_per_file': total_consultations / analyzed_files if analyzed_files > 0 else 0.0,
            'file_results': results
        }

        logger.info(f"Analysis complete: {overall_success_rate:.2%} success rate across {analyzed_files} files")
        return summary

    def generate_report(self, analysis_results: Dict[str, Any], output_format: str = 'text') -> str:
        """
        Generate a formatted report from analysis results.

        Args:
            analysis_results: Results from analyze_directory()
            output_format: Format for output ('text', 'json', 'markdown')

        Returns:
            Formatted report as string
        """
        if output_format == 'json':
            return json.dumps(analysis_results, indent=2)

        # Generate text/markdown report
        report_lines = []

        if output_format == 'markdown':
            report_lines.extend([
                "# Memory MCP Effectiveness Analysis Report",
                "",
                f"**Directory Analyzed:** `{analysis_results['directory']}`",
                f"**Analysis Date:** {os.popen('date').read().strip()}",
                "",
                "## Summary Statistics",
                "",
                f"- **Total Files:** {analysis_results['total_files']}",
                f"- **Analyzed Files:** {analysis_results['analyzed_files']}",
                f"- **Skipped Files:** {analysis_results['skipped_files']}",
                f"- **Total Memory Consultations:** {analysis_results['total_consultations']}",
                f"- **Successful Searches:** {analysis_results['total_successful_searches']}",
                f"- **Overall Success Rate:** {analysis_results['overall_success_rate']:.2%}",
                f"- **Avg Consultations/File:** {analysis_results['average_consultations_per_file']:.1f}",
                ""
            ])
        else:
            report_lines.extend([
                "Memory MCP Effectiveness Analysis Report",
                "=" * 50,
                "",
                f"Directory: {analysis_results['directory']}",
                f"Analysis Date: {os.popen('date').read().strip()}",
                "",
                "Summary Statistics:",
                f"  Total Files: {analysis_results['total_files']}",
                f"  Analyzed Files: {analysis_results['analyzed_files']}",
                f"  Skipped Files: {analysis_results['skipped_files']}",
                f"  Total Memory Consultations: {analysis_results['total_consultations']}",
                f"  Successful Searches: {analysis_results['total_successful_searches']}",
                f"  Overall Success Rate: {analysis_results['overall_success_rate']:.2%}",
                f"  Avg Consultations/File: {analysis_results['average_consultations_per_file']:.1f}",
                ""
            ])

        # Add detailed file analysis if requested
        successful_files = [r for r in analysis_results['file_results']
                          if not r.get('skipped') and r.get('success_rate', 0) > 0.5]

        if successful_files:
            if output_format == 'markdown':
                report_lines.extend([
                    "## High-Performing Files",
                    "",
                    "| File | Consultations | Success Rate | Line Count |",
                    "|------|---------------|--------------|------------|"
                ])
                for result in successful_files[:10]:  # Top 10
                    filename = os.path.basename(result['file'])
                    report_lines.append(
                        f"| {filename} | {result['memory_consultations']} | "
                        f"{result['success_rate']:.1%} | {result['line_count']} |"
                    )
            else:
                report_lines.extend([
                    "High-Performing Files (Success Rate > 50%):",
                ])
                for result in successful_files[:10]:
                    filename = os.path.basename(result['file'])
                    report_lines.append(
                        f"  {filename}: {result['memory_consultations']} consultations, "
                        f"{result['success_rate']:.1%} success rate, {result['line_count']} lines"
                    )

        return "\n".join(report_lines)


def main() -> None:
    """
    CLI interface for Memory MCP effectiveness analysis.
    """
    parser = argparse.ArgumentParser(
        description='Analyze Memory MCP effectiveness from conversation logs'
    )
    parser.add_argument(
        '--directory',
        type=str,
        help='Directory containing conversation logs (default: auto-detect)'
    )
    parser.add_argument(
        '--output',
        choices=['text', 'json', 'markdown'],
        default='text',
        help='Output format for the report'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Analyze a single log file instead of directory'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--save-report',
        type=str,
        help='Save report to specified file'
    )

    args = parser.parse_args()

    if args.verbose:
        logging_util.getLogger().setLevel(logging_util.DEBUG)

    analyzer = MemoryMCPAnalyzer(args.directory)

    try:
        if args.file:
            # Analyze single file
            logger.info(f"Analyzing single file: {args.file}")
            result = analyzer.parse_conversation_log(args.file)

            if result.get('skipped'):
                print(f"File skipped: {result.get('reason', 'unknown')}")
                sys.exit(1)

            # Create summary format for single file
            analysis_results = {
                'directory': os.path.dirname(args.file),
                'total_files': 1,
                'analyzed_files': 1,
                'skipped_files': 0,
                'total_consultations': result['memory_consultations'],
                'total_successful_searches': result['successful_searches'],
                'total_searches': result['total_searches'],
                'overall_success_rate': result['success_rate'],
                'average_consultations_per_file': result['memory_consultations'],
                'file_results': [result]
            }
        else:
            # Analyze directory
            logger.info("Starting Memory MCP effectiveness analysis...")
            analysis_results = analyzer.analyze_directory()

            if 'error' in analysis_results:
                logger.error(f"Analysis failed: {analysis_results['error']}")
                sys.exit(1)

        # Generate and output report
        report = analyzer.generate_report(analysis_results, args.output)

        if args.save_report:
            with open(args.save_report, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Report saved to: {args.save_report}")
        else:
            print(report)

        # Exit with appropriate code
        success_rate = analysis_results['overall_success_rate']
        if success_rate >= 0.7:
            logger.info(f"Analysis complete: Excellent performance ({success_rate:.2%})")
            sys.exit(0)
        elif success_rate >= 0.5:
            logger.info(f"Analysis complete: Good performance ({success_rate:.2%})")
            sys.exit(0)
        else:
            logger.warning(f"Analysis complete: Performance needs improvement ({success_rate:.2%})")
            sys.exit(0)

    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
