#!/usr/bin/env python3
"""
Enhanced /header command with Memory MCP integration
Provides header compliance checking with historical context
"""

import os
import sys
import argparse
from typing import Dict, Any

# Add the current directory to sys.path to import modules
sys.path.insert(0, os.path.dirname(__file__))
from compliance_checker import HeaderComplianceChecker, LearningRetriever


def enhanced_header_command(args: argparse.Namespace) -> None:
    """Enhanced /header command with Memory MCP integration"""
    
    # Initialize checkers
    header_checker = HeaderComplianceChecker()
    learning_retriever = LearningRetriever()
    
    # Get compliance analysis
    results = header_checker.check_header_compliance(verbose=args.verbose)
    
    # Get additional context if requested
    if args.context:
        context_results = learning_retriever.get_context_learnings(args.context)
        print(f"\n📚 Context Learnings for '{args.context}':")
        print(f"   {context_results['summary']}")
    
    # Always show the header format (this is the primary purpose)
    print(f"\n✅ Required Header Format:")
    print(f"   {results['header_format']}")
    
    # Show violations if any exist and not in quiet mode
    if not args.quiet and results['violation_count'] > 0:
        print(f"\n⚠️ Header Violation History: {results['violation_count']} violations")
        print("   Use --verbose for detailed analysis")
    
    # Show recommendations if any exist
    if results['recommendations'] and not args.quiet:
        print(f"\n💡 Recommendations:")
        for rec in results['recommendations']:
            print(f"   {rec}")
    
    # Show quick stats
    if not args.quiet:
        print(f"\n📊 Quick Stats:")
        print(f"   Branch: {results['git_info']['local_branch']}")
        print(f"   Upstream: {results['git_info']['upstream']}")
        print(f"   PR: {results['git_info']['pr_status']}")
        print(f"   Violations: {results['violation_count']}")
        print(f"   Learnings: {len(results['learnings'])}")


def main():
    """Main entry point for enhanced header command"""
    parser = argparse.ArgumentParser(
        description="Enhanced /header command with Memory MCP integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Show header format with basic compliance info
  %(prog)s --verbose          # Show detailed compliance analysis
  %(prog)s --quiet            # Show only header format
  %(prog)s --context branch   # Show header + branch-related learnings
  %(prog)s --context header --verbose  # Full analysis with header context
        """
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed compliance analysis"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Show only header format, no additional info"
    )
    
    parser.add_argument(
        "--context", "-c",
        type=str,
        help="Show learnings related to specific context (e.g., 'branch', 'header', 'git')"
    )
    
    args = parser.parse_args()
    
    # Run the enhanced header command
    enhanced_header_command(args)


if __name__ == "__main__":
    main()