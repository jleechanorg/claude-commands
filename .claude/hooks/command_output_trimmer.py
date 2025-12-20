#!/usr/bin/env python3
"""
Command Output Trimmer Hook - OPTIMIZED VERSION
Reduces slash command token consumption by 50-70% with <5ms overhead.
"""

import contextlib
import json
import os
import re
import sys
import threading
import time
import traceback
from collections import deque
from dataclasses import dataclass
from typing import Any


@dataclass
class CompressionStats:
    """Statistics about output compression performance."""
    original_size: int = 0
    compressed_size: int = 0
    bytes_saved: int = 0
    compression_ratio: float = 0.0
    original_lines: int = 0
    compressed_lines: int = 0
    lines_saved: int = 0
    processing_time_ms: float = 0.0
    command_type: str = 'unknown'

    def __post_init__(self):
        """Calculate derived metrics."""
        self.bytes_saved = max(0, self.original_size - self.compressed_size)
        self.lines_saved = max(0, self.original_lines - self.compressed_lines)
        if self.original_size > 0:
            self.compression_ratio = min(1.0, self.bytes_saved / self.original_size)

    @classmethod
    def from_compression(cls, original_output: str, compressed_output: str,
                        processing_time_ms: float = 0.0, command_type: str = 'unknown') -> 'CompressionStats':
        """Create CompressionStats from original and compressed output."""
        original_size = len(original_output.encode('utf-8'))
        compressed_size = len(compressed_output.encode('utf-8'))
        original_lines = len(original_output.splitlines())
        compressed_lines = len(compressed_output.splitlines())

        return cls(
            original_size=original_size,
            compressed_size=compressed_size,
            original_lines=original_lines,
            compressed_lines=compressed_lines,
            processing_time_ms=processing_time_ms,
            command_type=command_type
        )

# Configuration constants to replace magic numbers
class Config:
    # Sample size for command detection (chars)
    DETECTION_SAMPLE_SIZE = 500
    # Threshold for aggressive trimming (lines)
    AGGRESSIVE_TRIM_THRESHOLD = 100
    # Default max lines for fast trim
    FAST_TRIM_MAX_LINES = 50
    # First N lines to keep in fast trim
    FAST_TRIM_KEEP_FIRST = 25
    # Last N lines to keep in fast trim
    FAST_TRIM_KEEP_LAST = 25
    # Maximum input size to prevent DoS (10MB)
    MAX_INPUT_SIZE = 10 * 1024 * 1024
    # Performance warning threshold in ms
    PERFORMANCE_WARNING_THRESHOLD = 10
    # Maximum stats entries to keep
    MAX_STATS_ENTRIES = 1000
    # Stats reset threshold
    STATS_RESET_THRESHOLD = 10000
    # Argument length limit to prevent DoS
    ARG_LENGTH_LIMIT = 1000

class OptimizedCommandOutputTrimmer:
    # Pre-compiled regex patterns for performance
    COMMAND_PATTERNS: dict[str, re.Pattern] = {
        'test': re.compile(r'(Running tests|PASSED|FAILED|test_\w+|pytest|unittest)', re.IGNORECASE),
        'pushl': re.compile(r'(git push|PR #\d+|Labels applied|Pushing to|origin/)', re.IGNORECASE),
        'copilot': re.compile(r'(Phase \d+|COPILOT|Comment coverage|⏱️ EXECUTION TIMING)', re.IGNORECASE),
        'coverage': re.compile(r'(Coverage report|TOTAL.*\d+%|\.py\s+\d+\s+\d+\s+\d+%)', re.IGNORECASE),
        'execute': re.compile(r'(TODO:|✅ COMPLETED|🔄 IN PROGRESS|TodoWrite tool)', re.IGNORECASE),
        'cerebras': re.compile(r'(Cerebras|🚀 SPEED|Token generation)', re.IGNORECASE),
        'orchestrate': re.compile(r'(orchestration|tmux|task-agent-|Redis coordination)', re.IGNORECASE)
    }

    # Thread-safe singleton pattern
    _instance = None
    _config = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # Double-check pattern
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    @classmethod
    def _reset_singleton_for_testing(cls):
        """Reset singleton for testing purposes only"""
        with cls._lock:
            cls._instance = None
            cls._config = None

    def _initialize(self):
        """One-time initialization with bounded statistics"""
        self.config = self._load_config_once()
        # Use bounded collections to prevent memory leaks
        self.recent_stats = deque(maxlen=Config.MAX_STATS_ENTRIES)
        self.stats_summary = {'total_saved': 0, 'count': 0, 'total_original': 0, 'total_trimmed': 0}
        self.perf_stats = deque(maxlen=Config.MAX_STATS_ENTRIES)

    def _load_config_once(self) -> dict:
        """Load configuration once and cache it"""
        if OptimizedCommandOutputTrimmer._config is None:
            settings_path = os.path.expanduser('~/.claude/settings.json')
            default_config = {
                'enabled': True,
                'compression_threshold': 0.2,
                'log_statistics': False,  # Disabled by default for performance
                'preserve_errors': True,
                'max_output_lines': 100,
                'performance_mode': True,  # New flag for aggressive optimization
                'passthrough_markers': [
                    '[claude:show-full-output]',
                    '[claude:full-output]',
                    '[claude:no-trim]'
                ],
                'passthrough_requests': [
                    'show full output',
                    'show the full output',
                    'show output',
                    'display full output',
                    'need the full output',
                    'full command output'
                ],
                'custom_rules': {
                    'test': {'max_passed_tests': 3, 'preserve_failures': True},
                    'pushl': {'max_git_lines': 5, 'preserve_pr_links': True},
                    'copilot': {'max_timing_lines': 2, 'preserve_phases': True},
                    'coverage': {'max_file_lines': 10, 'preserve_summary': True},
                    'execute': {'max_explanation_lines': 5, 'preserve_todos': True}
                }
            }

            try:
                if os.path.exists(settings_path):
                    with open(settings_path) as f:
                        settings = json.load(f)
                        if 'output_trimmer' in settings:
                            user_config = settings['output_trimmer']
                            # Validate config for solo dev debugging efficiency
                            validated_config = self._validate_config(user_config, settings_path)
                            default_config.update(validated_config)
            except FileNotFoundError:
                # Settings file doesn't exist - use defaults (normal case)
                pass
            except json.JSONDecodeError as e:
                # Malformed JSON - help solo dev debug quickly
                sys.stderr.write(f"⚠️ CONFIG ERROR: {settings_path} has invalid JSON at line {e.lineno}: {e.msg}\n")
                sys.stderr.write("Using default configuration. Fix JSON syntax to customize output trimmer.\n")
            except Exception as e:
                # Other errors - provide helpful context for debugging
                sys.stderr.write(f"⚠️ CONFIG WARNING: Error loading {settings_path}: {e}\n")
                sys.stderr.write("Using default configuration. Check file permissions and format.\n")

            OptimizedCommandOutputTrimmer._config = default_config

        return OptimizedCommandOutputTrimmer._config

    def _validate_config(self, user_config: dict, settings_path: str) -> dict:
        """Validate user configuration with helpful error messages for solo dev debugging"""
        validated = {}

        # Define expected types for key config values
        expected_types = {
            'enabled': bool,
            'compression_threshold': (int, float),
            'log_statistics': bool,
            'preserve_errors': bool,
            'max_output_lines': int,
            'performance_mode': bool
        }

        for key, value in user_config.items():
            if key in expected_types:
                expected_type = expected_types[key]
                # Handle both single type and tuple of types
                if isinstance(expected_type, tuple):
                    if not isinstance(value, expected_type):
                        sys.stderr.write(f"⚠️ CONFIG: {settings_path} - '{key}' should be {' or '.join(t.__name__ for t in expected_type)}, got {type(value).__name__}. Using default.\n")
                        continue
                elif not isinstance(value, expected_type):
                    sys.stderr.write(f"⚠️ CONFIG: {settings_path} - '{key}' should be {expected_type.__name__}, got {type(value).__name__}. Using default.\n")
                    continue

                # Additional validation for specific keys
                if key == 'compression_threshold' and not (0.0 <= value <= 1.0):
                    sys.stderr.write(f"⚠️ CONFIG: {settings_path} - 'compression_threshold' should be between 0.0 and 1.0, got {value}. Using default.\n")
                    continue
                if key == 'max_output_lines' and value < 1:
                    sys.stderr.write(f"⚠️ CONFIG: {settings_path} - 'max_output_lines' should be positive, got {value}. Using default.\n")
                    continue

            # Accept the validated value
            validated[key] = value

        return validated

    def detect_command_type(self, output: str) -> str:
        """Detect command type using pre-compiled patterns"""
        # Quick check on first N chars for performance
        sample = output[:Config.DETECTION_SAMPLE_SIZE] if len(output) > Config.DETECTION_SAMPLE_SIZE else output

        for cmd_type, pattern in self.COMMAND_PATTERNS.items():
            if pattern.search(sample):
                return cmd_type
        return 'generic'

    def fast_trim(self, lines: list[str], max_lines: int = None) -> list[str]:
        """Ultra-fast generic trimming with intelligent middle summarization"""
        if max_lines is None:
            max_lines = Config.FAST_TRIM_MAX_LINES

        if len(lines) <= max_lines:
            return lines

        # Keep first N and last M lines based on config
        trimmed = lines[:Config.FAST_TRIM_KEEP_FIRST]

        # Summarize the middle section instead of just excluding it
        middle_lines = lines[Config.FAST_TRIM_KEEP_FIRST:-Config.FAST_TRIM_KEEP_LAST]
        summary = self._summarize_middle_content(middle_lines)
        trimmed.extend(summary)

        trimmed.extend(lines[-Config.FAST_TRIM_KEEP_LAST:])
        return trimmed


    def _collect_middle_summary_items(
        self,
        middle_lines: list[str],
        *,
        max_collected_items: int,
        max_line_chars: int,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        """Collect key items (errors/urls/status/refs) from middle content."""
        errors: list[str] = []
        urls: list[str] = []
        status_updates: list[str] = []
        important_info: list[str] = []

        for line in middle_lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue

            if len(line_stripped) > max_line_chars:
                line_stripped = line_stripped[:max_line_chars] + "..."

            upper = line_stripped.upper()
            if (
                len(errors) < max_collected_items
                and any(p in upper for p in ("ERROR", "FAILED", "EXCEPTION", "WARNING"))
            ):
                errors.append(line_stripped)

            if (
                len(urls) < max_collected_items
                and "http" in line_stripped
                and "://" in line_stripped
            ):
                urls.append(line_stripped)

            if len(status_updates) < max_collected_items and any(
                p in line_stripped for p in ("✅", "❌", "🔄", "PASSED", "SUCCESS", "COMPLETED")
            ):
                status_updates.append(line_stripped)

            if len(important_info) < max_collected_items and any(
                p in line_stripped for p in ("PR #", "commit", "merge", "branch")
            ):
                important_info.append(line_stripped)

        return errors, urls, status_updates, important_info

    @staticmethod
    def _append_bulleted_section(
        summary_lines: list[str],
        *,
        header: str,
        items: list[str],
        max_items: int,
        indent: str = "    • ",
    ) -> None:
        summary_lines.append(header)
        for item in items[:max_items]:
            summary_lines.append(f"{indent}{item}")
        if len(items) > max_items:
            summary_lines.append(f"    ... and {len(items) - max_items} more")

    @staticmethod
    def _append_basic_middle_stats(summary_lines: list[str], middle_lines: list[str]) -> None:
        unique_patterns: set[str] = set()
        for line in middle_lines[:20]:
            words = line.strip().split()[:3]
            if not words:
                continue
            unique_patterns.add(" ".join(words))

        summary_lines.append(f"  Content types found: {len(unique_patterns)} different patterns")
        if unique_patterns:
            summary_lines.append("  Sample patterns:")
            for pattern in list(unique_patterns)[:3]:
                summary_lines.append(f"    • {pattern}...")

    def _summarize_middle_content(self, middle_lines: list[str], max_summary_lines: int = 25) -> list[str]:
        """Create an intelligent summary of middle content with bounded memory usage."""
        if not middle_lines:
            return []

        summary_lines: list[str] = [f"\n... [SUMMARY of {len(middle_lines)} middle lines] ..."]

        errors, urls, status_updates, important_info = self._collect_middle_summary_items(
            middle_lines,
            max_collected_items=10,
            max_line_chars=200,
        )

        if errors:
            self._append_bulleted_section(
                summary_lines,
                header="  Errors/Warnings found:",
                items=errors,
                max_items=3,
            )
        if urls:
            self._append_bulleted_section(
                summary_lines,
                header="  URLs found:",
                items=urls,
                max_items=2,
            )
        if status_updates:
            self._append_bulleted_section(
                summary_lines,
                header="  Status updates:",
                items=status_updates,
                max_items=5,
            )
        if important_info:
            self._append_bulleted_section(
                summary_lines,
                header="  Important references:",
                items=important_info,
                max_items=3,
            )

        if not (errors or urls or status_updates or important_info):
            self._append_basic_middle_stats(summary_lines, middle_lines)

        summary_lines.append("... [END SUMMARY] ...\n")

        if max_summary_lines > 0 and len(summary_lines) > max_summary_lines:
            summary_lines = summary_lines[: max_summary_lines - 1]
            summary_lines.append("... [SUMMARY TRUNCATED] ...\n")

        return summary_lines

    def _is_passthrough_disabled(self) -> bool:
        if not self.config.get("enabled", True):
            return True

        env_toggle = os.environ.get("CLAUDE_TRIMMER_DISABLE", "")
        if env_toggle.lower() in {"1", "true", "yes", "on"}:
            return True

        env_mode = os.environ.get("CLAUDE_TRIMMER_MODE", "").strip().lower()
        return env_mode in {"off", "disable", "disabled", "passthrough", "raw", "full"}

    def _contains_passthrough_markers(self, output: str) -> bool:
        markers = self.config.get("passthrough_markers", [])
        if not markers:
            return False

        lowered = output.lower()
        return any(marker and marker.lower() in lowered for marker in markers)

    def _contains_passthrough_requests(self, output: str) -> bool:
        requests = self.config.get("passthrough_requests", [])
        if not requests:
            return False

        collapsed = re.sub(r"\s+", " ", output)
        collapsed_lowered = collapsed.lower()
        for request in requests:
            if not request:
                continue
            if isinstance(request, str):
                if request.lower() in collapsed_lowered:
                    return True
                continue
            if not (isinstance(request, dict) and "regex" in request):
                continue
            pattern = request.get("regex")
            if not isinstance(pattern, str):
                continue
            try:
                compiled = re.compile(pattern, re.IGNORECASE)
            except re.error:
                continue
            if compiled.search(output) or compiled.search(collapsed):
                return True

        return False

    def _should_bypass(self, output: str) -> bool:
        """Determine if trimming should be skipped entirely."""
        if self._is_passthrough_disabled():
            return True
        if self._contains_passthrough_markers(output):
            return True
        return self._contains_passthrough_requests(output)

    def process_output(self, output: str) -> str:
        """Main processing with performance tracking"""
        if self._should_bypass(output):
            return output

        # Performance tracking
        start_time = time.perf_counter() if self.config.get('performance_mode') else 0

        lines = output.split('\n')
        original_count = len(lines)

        # Quick exit for small outputs
        if original_count < 20:
            return output

        # Performance mode: aggressive trimming
        if self.config.get('performance_mode') and original_count > Config.AGGRESSIVE_TRIM_THRESHOLD:
            trimmed_lines = self.fast_trim(lines, Config.FAST_TRIM_MAX_LINES)
        else:
            # Standard mode: smart trimming
            cmd_type = self.detect_command_type(output)

            if cmd_type == 'test':
                trimmed_lines = self.trim_test_output(lines)
            elif cmd_type == 'pushl':
                trimmed_lines = self.trim_pushl_output(lines)
            elif cmd_type == 'copilot':
                trimmed_lines = self.trim_copilot_output(lines)
            else:
                trimmed_lines = self.fast_trim(lines)

        # Calculate compression
        trimmed_count = len(trimmed_lines)
        compression_ratio = 1 - (trimmed_count / original_count) if original_count > 0 else 0

        # Track performance with bounded collection
        if self.config.get('performance_mode'):
            elapsed = (time.perf_counter() - start_time) * 1000  # Convert to ms
            # Store in bounded deque to prevent memory leak
            self.perf_stats.append({
                'time': elapsed,
                'lines': original_count,
                'compression': compression_ratio
            })

            # Add performance footer only if very slow
            if elapsed > Config.PERFORMANCE_WARNING_THRESHOLD:
                trimmed_lines.append(f"[Trimmer: {elapsed:.1f}ms]")

        if compression_ratio >= self.config['compression_threshold']:
            # Update bounded statistics to prevent memory leak
            self._update_stats(original_count, trimmed_count)

            # Store recent stat for analysis
            self.recent_stats.append({
                'original': original_count,
                'trimmed': trimmed_count,
                'ratio': compression_ratio
            })

            return '\n'.join(trimmed_lines)
        return output

    def _update_stats(self, original_count: int, trimmed_count: int):
        """Update statistics with automatic reset to prevent memory leaks"""
        self.stats_summary['total_original'] += original_count
        self.stats_summary['total_trimmed'] += trimmed_count
        self.stats_summary['count'] += 1

        # Calculate and update saved lines
        lines_saved = original_count - trimmed_count
        if lines_saved > 0:
            self.stats_summary['total_saved'] += lines_saved

        # Reset summary periodically to prevent unbounded growth
        if self.stats_summary['count'] > Config.STATS_RESET_THRESHOLD:
            self.stats_summary = {
                'total_original': 0,
                'total_trimmed': 0,
                'count': 0,
                'total_saved': 0
            }

    def trim_test_output(self, lines: list[str]) -> list[str]:
        """Optimized test output compression"""
        config = self.config['custom_rules']['test']
        trimmed = []
        passed_count = 0
        total_passed = sum(1 for line in lines if 'PASSED' in line.upper())

        for line in lines:
            # Fast check for important lines
            line_upper = line.upper()
            if 'FAILED' in line_upper or 'ERROR' in line_upper:
                trimmed.append(line)
            elif 'PASSED' in line_upper:
                if passed_count < config['max_passed_tests']:
                    trimmed.append(line)
                    passed_count += 1
            elif len(trimmed) < 20:  # Keep early context
                trimmed.append(line)

        # Add compression indicator if we limited passed tests
        if total_passed > config['max_passed_tests']:
            suppressed = total_passed - config['max_passed_tests']
            trimmed.append(f"... [{suppressed} more passed tests compressed] ...")

        return trimmed

    def trim_pushl_output(self, lines: list[str]) -> list[str]:
        """Optimized pushl output compression"""
        config = self.config['custom_rules']['pushl']
        trimmed = []
        git_lines = 0

        for line in lines:
            # Fast check for PR links
            if 'PR #' in line or 'github.com' in line:
                trimmed.append(line)
            elif 'git' in line.lower() and git_lines < config['max_git_lines']:
                trimmed.append(line)
                git_lines += 1
            elif len(trimmed) < 10:
                trimmed.append(line)

        return trimmed

    def trim_copilot_output(self, lines: list[str]) -> list[str]:
        """Optimized copilot output compression"""
        trimmed = []

        for line in lines:
            # Keep only phase markers and status
            if 'Phase' in line or '✅' in line or '❌' in line or 'WARNING' in line or len(trimmed) < 5:
                trimmed.append(line)

        return trimmed

    def get_performance_report(self):
        """Get performance statistics from bounded collection"""
        if len(self.perf_stats) > 0:
            recent_times = [stat['time'] for stat in self.perf_stats if 'time' in stat]
            if recent_times:
                avg_time = sum(recent_times) / len(recent_times)
                return f"Avg: {avg_time:.2f}ms over last {len(recent_times)} calls"
        return "No performance data"

    def compress_output(self, output: str) -> tuple[str, 'CompressionStats']:
        """
        Compress the output and return both the compressed output and statistics.

        Args:
            output: The output string to compress

        Returns:
            A tuple containing the compressed output string and CompressionStats object
        """
        compressed_output = self.process_output(output)

        stats = CompressionStats.from_compression(
            original_output=output,
            compressed_output=compressed_output
        )

        return compressed_output, stats


    def _trim_args_list(self, args_list: list[Any]) -> list[Any]:
        trimmed_list: list[Any] = []
        for arg in args_list:
            if isinstance(arg, (list, dict)):
                trimmed_list.append(self.trim_args(arg))
                continue

            arg_str = str(arg)
            if len(arg_str) > Config.ARG_LENGTH_LIMIT:
                trimmed_list.append(arg_str[: Config.ARG_LENGTH_LIMIT])
            else:
                trimmed_list.append(arg)

        return trimmed_list

    def _trim_args_dict(self, args_dict: dict[Any, Any]) -> dict[Any, Any]:
        trimmed_dict: dict[Any, Any] = {}
        collision_counter: dict[str, int] = {}

        for key, value in args_dict.items():
            if isinstance(value, (list, dict)):
                final_value = self.trim_args(value)
            else:
                value_str = str(value)
                final_value = (
                    value_str[: Config.ARG_LENGTH_LIMIT]
                    if len(value_str) > Config.ARG_LENGTH_LIMIT
                    else value
                )

            key_str = str(key)
            base_key = key_str[: Config.ARG_LENGTH_LIMIT] if len(key_str) > Config.ARG_LENGTH_LIMIT else key_str

            if base_key in trimmed_dict:
                collision_counter[base_key] = collision_counter.get(base_key, 0) + 1
                suffix = f"__dup{collision_counter[base_key]}"
                max_base_length = max(1, Config.ARG_LENGTH_LIMIT - len(suffix))
                final_key = base_key[:max_base_length] + suffix
            else:
                collision_counter.setdefault(base_key, 0)
                final_key = base_key

            trimmed_dict[final_key] = final_value

        return trimmed_dict

    def trim_args(self, args: Any) -> Any:
        """Trim argument length to prevent DoS attacks."""
        if args is None:
            return None

        if isinstance(args, list):
            return self._trim_args_list(args)

        if isinstance(args, dict):
            return self._trim_args_dict(args)

        if isinstance(args, str):
            return args[: Config.ARG_LENGTH_LIMIT] if len(args) > Config.ARG_LENGTH_LIMIT else args

        arg_str = str(args)
        if len(arg_str) > Config.ARG_LENGTH_LIMIT:
            return arg_str[: Config.ARG_LENGTH_LIMIT]

        return args

    def process_command_output(self, output: str) -> str:
        """
        Alias for process_output method.

        Args:
            output: The output string to process

        Returns:
            The processed output string
        """
        return self.process_output(output)

    def compress_test_output(self, lines: list[str]) -> list[str]:
        """
        Compress test output lines.

        Args:
            lines: List of output lines to compress

        Returns:
            List of compressed output lines
        """
        return self.trim_test_output(lines)

    def compress_pushl_output(self, lines: list[str]) -> list[str]:
        """
        Compress pushl output lines.

        Args:
            lines: List of output lines to compress

        Returns:
            List of compressed output lines
        """
        return self.trim_pushl_output(lines)

    def compress_copilot_output(self, lines: list[str]) -> list[str]:
        """
        Compress copilot output lines.

        Args:
            lines: List of output lines to compress

        Returns:
            List of compressed output lines
        """
        return self.trim_copilot_output(lines)

    def compress_coverage_output(self, lines: list[str]) -> list[str]:
        """
        Compress coverage output lines.

        Args:
            lines: List of output lines to compress

        Returns:
            List of compressed output lines
        """
        # Coverage compression logic - preserve totals and percentages
        trimmed = []
        for line in lines:
            if 'TOTAL' in line or '%' in line or len(trimmed) < 5:
                trimmed.append(line)
        return trimmed

    def compress_execute_output(self, lines: list[str]) -> list[str]:
        """
        Compress execute output lines.

        Args:
            lines: List of output lines to compress

        Returns:
            List of compressed output lines
        """
        # Execute compression logic - preserve TODO states and checklists
        trimmed = []
        for line in lines:
            if '✅' in line or '🔄' in line or '❌' in line or 'TODO:' in line or '- [' in line or len(trimmed) < 10:
                trimmed.append(line)
        return trimmed

    def compress_generic_output(self, lines: list[str]) -> list[str]:
        """
        Compress generic output lines.

        Args:
            lines: List of output lines to compress

        Returns:
            List of compressed output lines
        """
        if len(lines) <= Config.FAST_TRIM_MAX_LINES:
            return lines

        # Preserve important patterns and first/last lines
        trimmed = []

        # Keep first few lines
        trimmed.extend(lines[:Config.FAST_TRIM_KEEP_FIRST])

        # Summarize middle content instead of just excluding it
        middle_lines = lines[Config.FAST_TRIM_KEEP_FIRST:-Config.FAST_TRIM_KEEP_LAST]
        summary = self._summarize_middle_content(middle_lines)
        trimmed.extend(summary)

        # Keep last few lines
        trimmed.extend(lines[-Config.FAST_TRIM_KEEP_LAST:])

        return trimmed


def main():
    """Hook entry point with error handling and input validation"""
    try:
        trimmer = OptimizedCommandOutputTrimmer()

        # Note: trim_args is for API function arguments, not command-line arguments
        # Command-line arguments for this hook don't need sanitization

        # Read input with size limit to prevent DoS (byte-aware)
        stdin_buffer = getattr(sys.stdin, "buffer", None)
        truncated = False

        if stdin_buffer is not None:
            raw_input = stdin_buffer.read(Config.MAX_INPUT_SIZE + 1)
            truncated = len(raw_input) > Config.MAX_INPUT_SIZE
            if truncated:
                raw_input = raw_input[:Config.MAX_INPUT_SIZE]
        else:
            byte_buffer = bytearray()
            while True:
                chunk = sys.stdin.read(1024)
                if not chunk:
                    break

                chunk_bytes = chunk.encode("utf-8")
                remaining = Config.MAX_INPUT_SIZE - len(byte_buffer)

                if remaining <= 0:
                    truncated = True
                    break

                if len(chunk_bytes) > remaining:
                    byte_buffer.extend(chunk_bytes[:remaining])
                    truncated = True
                    break

                byte_buffer.extend(chunk_bytes)

            if not truncated:
                extra_char = sys.stdin.read(1)
                if extra_char:
                    truncated = True

            raw_input = bytes(byte_buffer[:Config.MAX_INPUT_SIZE])

        if truncated:
            sys.stderr.write(f"Warning: Input exceeds {Config.MAX_INPUT_SIZE} bytes, truncating\n")

        input_data = raw_input.decode("utf-8", errors="replace")

        # Process command output directly (trim_args is for function arguments, not output)
        trimmed_output = trimmer.process_output(input_data)

        # Write output
        sys.stdout.write(trimmed_output)
        return 0

    except Exception as e:
        # On any error, pass through original output with full stack trace for debugging
        sys.stderr.write(f"Trimmer error: {e}\n")
        sys.stderr.write(f"Stack trace: {traceback.format_exc()}\n")
        # Attempt to write original data if available
        with contextlib.suppress(NameError):
            sys.stdout.write(input_data)
        return 1

if __name__ == '__main__':
    sys.exit(main())
