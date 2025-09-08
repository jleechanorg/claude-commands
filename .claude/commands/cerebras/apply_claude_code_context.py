#!/usr/bin/env python3
"""
Claude Code CLI Context Management Integration

This script integrates the ClaudeCodeContextFilter with cerebras_direct.sh
to replicate Claude Code CLI's clean context management for external AI services.

Usage:
    python apply_claude_code_context.py --mode smart --raw-context "conversation text"
    python apply_claude_code_context.py --mode smart --quality-threshold 0.3 --raw-context "text"
"""

import sys
import argparse
import json
from typing import Dict, Any
from claude_code_context_filter import ClaudeCodeContextFilter, ContextQualityScorer


def main():
    """Main entry point for Claude Code CLI context management"""
    parser = argparse.ArgumentParser(
        description="Apply Claude Code CLI context management to external AI services"
    )
    parser.add_argument(
        "--mode",
        choices=["none", "smart", "semantic", "full"],
        default="smart",
        help="Context filtering mode (replicates cerebras_direct.sh flags)"
    )
    parser.add_argument(
        "--raw-context",
        required=True,
        help="Raw conversation context to filter"
    )
    parser.add_argument(
        "--quality-threshold",
        type=float,
        default=0.3,
        help="Minimum quality score (0.0-1.0) for context inclusion"
    )
    parser.add_argument(
        "--show-analysis",
        action="store_true",
        help="Show context analysis details"
    )
    parser.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="Output format"
    )

    args = parser.parse_args()

    # Initialize Claude Code CLI context management
    filter = ClaudeCodeContextFilter()
    scorer = ContextQualityScorer()

    # Apply context filtering based on mode
    if args.mode == "none":
        clean_context = ""
        quality_score = 0.0
        message_count = 0
    elif args.mode == "full":
        clean_context = args.raw_context
        quality_score = scorer.score_content_quality(args.raw_context)
        message_count = len(args.raw_context.split('\n'))
    else:  # smart or semantic mode
        clean_messages = filter.extract_clean_messages(args.raw_context)
        clean_context = filter._rebuild_conversation_context(clean_messages)
        quality_score = scorer.score_content_quality(clean_context) if clean_context else 0.0
        message_count = len(clean_messages)

        # Apply quality threshold
        if quality_score < args.quality_threshold:
            if args.show_analysis:
                print(f"⚠️ Context quality ({quality_score:.2f}) below threshold ({args.quality_threshold}), falling back to no-context mode", file=sys.stderr)
            clean_context = ""
            quality_score = 0.0

    # Show analysis if requested
    if args.show_analysis:
        print("🔍 Claude Code CLI Context Analysis:", file=sys.stderr)
        print(f"  Mode: {args.mode}", file=sys.stderr)
        print(f"  Quality Score: {quality_score:.2f}", file=sys.stderr)
        print(f"  Message Count: {message_count}", file=sys.stderr)
        print(f"  Context Length: {len(clean_context)} chars", file=sys.stderr)
        print(f"  Threshold: {args.quality_threshold}", file=sys.stderr)
        print("---", file=sys.stderr)

    # Output results
    if args.output_format == "json":
        result = {
            "clean_context": clean_context,
            "quality_score": quality_score,
            "message_count": message_count,
            "mode": args.mode,
            "threshold_met": quality_score >= args.quality_threshold,
            "original_length": len(args.raw_context),
            "filtered_length": len(clean_context)
        }
        print(json.dumps(result, indent=2))
    else:
        # Text output for direct use in scripts
        print(clean_context)


if __name__ == "__main__":
    main()
