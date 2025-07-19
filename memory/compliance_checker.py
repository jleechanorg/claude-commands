#!/usr/bin/env python3
"""
Compliance Checker for Memory MCP Integration
Provides compliance checking functionality for /header command and other tools
"""

import json
import os
import sys
from typing import Any

# Add the current directory to sys.path to import mock_mcp_reader
sys.path.insert(0, os.path.dirname(__file__))
from mock_mcp_reader import (
    ComplianceMemoryReader,
    LearningMemoryReader,
    MockMemoryMCPReader,
)


class HeaderComplianceChecker:
    """Enhanced /header command with Memory MCP compliance checking"""

    def __init__(self, memory_file: str = None):
        """Initialize with Memory MCP reader"""
        self.reader = MockMemoryMCPReader(memory_file)
        self.compliance_reader = ComplianceMemoryReader(self.reader)
        self.learning_reader = LearningMemoryReader(self.reader)

    def check_header_compliance(self, verbose: bool = False) -> dict[str, Any]:
        """Check header compliance with historical context"""
        # Get current git status
        git_info = self._get_git_info()

        # Get violation history
        header_violations = self.compliance_reader.get_violation_history("header")

        # Get related learnings
        header_learnings = self.learning_reader.get_related_learnings("header")

        # Analyze patterns
        results = {
            "git_info": git_info,
            "violation_count": len(header_violations),
            "violations": header_violations,
            "learnings": header_learnings,
            "recommendations": self._generate_recommendations(
                header_violations, header_learnings
            ),
            "header_format": self._get_header_format(git_info),
        }

        if verbose:
            self._print_detailed_analysis(results)

        return results

    def _get_repo_root(self) -> str:
        """Get the repository root directory"""
        import subprocess

        try:
            return subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except subprocess.CalledProcessError:
            # Fallback to parent directory of memory directory
            return os.path.dirname(os.path.dirname(__file__))

    def _get_git_info(self) -> dict[str, str]:
        """Get git information for header generation"""
        import subprocess

        # Get repository root
        repo_root = self._get_repo_root()

        try:
            # Get current branch
            current_branch = subprocess.check_output(
                ["git", "branch", "--show-current"], text=True, cwd=repo_root
            ).strip()

            # Get upstream branch
            try:
                upstream = subprocess.check_output(
                    ["git", "rev-parse", "--abbrev-ref", "@{upstream}"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                    cwd=repo_root,
                ).strip()
            except subprocess.CalledProcessError:
                upstream = "no upstream"

            # Get PR info
            try:
                pr_info = subprocess.check_output(
                    [
                        "gh",
                        "pr",
                        "list",
                        "--head",
                        current_branch,
                        "--json",
                        "number,url",
                    ],
                    text=True,
                    stderr=subprocess.DEVNULL,
                    cwd=repo_root,
                ).strip()

                if pr_info:
                    pr_data = json.loads(pr_info)
                    if pr_data:
                        pr_number = pr_data[0]["number"]
                        pr_url = pr_data[0]["url"]
                        pr_status = f"#{pr_number} {pr_url}"
                    else:
                        pr_status = "none"
                else:
                    pr_status = "none"
            except (subprocess.CalledProcessError, json.JSONDecodeError):
                pr_status = "none"

            return {
                "local_branch": current_branch,
                "upstream": upstream,
                "pr_status": pr_status,
            }
        except Exception as e:
            return {
                "local_branch": "unknown",
                "upstream": "unknown",
                "pr_status": "unknown",
                "error": str(e),
            }

    def _generate_recommendations(
        self, violations: list[dict], learnings: list[dict]
    ) -> list[str]:
        """Generate recommendations based on historical data"""
        recommendations = []

        # Check violation frequency
        if len(violations) >= 3:
            recommendations.append(
                f"⚠️ You've forgotten the header {len(violations)} times before! "
                "Consider setting up a reminder system."
            )

        # Check for specific patterns from learnings
        for learning in learnings:
            name = learning["name"]
            if "upstream-tracking" in name:
                recommendations.append(
                    "🔧 Remember to set upstream tracking: use `git push -u origin branch-name`"
                )
            elif "pr-tracking" in name:
                recommendations.append(
                    "🔍 Ensure header reflects actual PR context, not just branch name match"
                )

        # General compliance reminders
        if len(violations) > 0:
            recommendations.append(
                "📋 Header is MANDATORY for every response - no exceptions!"
            )

        return recommendations

    def _get_header_format(self, git_info: dict[str, str]) -> str:
        """Generate the properly formatted header"""
        local = git_info.get("local_branch", "unknown")
        upstream = git_info.get("upstream", "unknown")
        pr = git_info.get("pr_status", "unknown")

        return f"[Local: {local} | Remote: {upstream} | PR: {pr}]"

    def _print_detailed_analysis(self, results: dict[str, Any]) -> None:
        """Print detailed compliance analysis"""
        print("🔍 Header Compliance Analysis")
        print("=" * 50)

        # Current status
        print("📍 Current Status:")
        print(f"   Local Branch: {results['git_info']['local_branch']}")
        print(f"   Upstream: {results['git_info']['upstream']}")
        print(f"   PR Status: {results['git_info']['pr_status']}")
        print()

        # Violation history
        print(f"⚠️ Violation History: {results['violation_count']} violations found")
        if results["violations"]:
            for i, violation in enumerate(results["violations"][:3], 1):
                print(f"   {i}. {violation['name']}")
                if violation["observations"]:
                    print(f"      {violation['observations'][0][:100]}...")
        print()

        # Learnings
        print(f"📚 Related Learnings: {len(results['learnings'])} found")
        for learning in results["learnings"][:3]:
            print(f"   - {learning['name']}")
            if learning["observations"]:
                print(f"     {learning['observations'][0][:100]}...")
        print()

        # Recommendations
        print("💡 Recommendations:")
        for rec in results["recommendations"]:
            print(f"   {rec}")
        print()

        # Header format
        print("✅ Required Header Format:")
        print(f"   {results['header_format']}")
        print()


class LearningRetriever:
    """Retrieve relevant learnings for current context"""

    def __init__(self, memory_file: str = None):
        self.reader = MockMemoryMCPReader(memory_file)
        self.learning_reader = LearningMemoryReader(self.reader)

    def get_context_learnings(
        self, context: str, category: str = None
    ) -> dict[str, Any]:
        """Get learnings relevant to current context"""
        related_learnings = self.learning_reader.get_related_learnings(context)

        if category:
            category_learnings = self.learning_reader.get_learnings_by_category(
                category
            )
            # Combine and deduplicate
            all_learnings = {
                l["name"]: l for l in related_learnings + category_learnings
            }
            learnings = list(all_learnings.values())
        else:
            learnings = related_learnings

        return {
            "context": context,
            "category": category,
            "learnings": learnings,
            "summary": self._summarize_learnings(learnings),
        }

    def _summarize_learnings(self, learnings: list[dict[str, Any]]) -> str:
        """Create a concise summary of learnings"""
        if not learnings:
            return "No relevant learnings found"

        summaries = []
        for learning in learnings[:3]:  # Top 3
            name = learning["name"]
            if learning["observations"]:
                # Extract classification and key point
                first_obs = learning["observations"][0]
                if "Classification:" in first_obs:
                    classification = (
                        first_obs.split("Classification:")[1]
                        .split("Category:")[0]
                        .strip()
                    )
                    content = (
                        first_obs.split("Content:")[1].split("Context:")[0].strip()
                        if "Content:" in first_obs
                        else first_obs
                    )
                    summaries.append(f"{name}: {classification} - {content[:100]}")
                else:
                    summaries.append(f"{name}: {first_obs[:100]}")

        return "; ".join(summaries)


def main():
    """Test the compliance checker functionality"""
    print("Testing Compliance Checker...")

    # Test header compliance
    print("\n1. Testing HeaderComplianceChecker:")
    header_checker = HeaderComplianceChecker()
    results = header_checker.check_header_compliance(verbose=True)

    # Test learning retrieval
    print("\n2. Testing LearningRetriever:")
    learning_retriever = LearningRetriever()
    context_results = learning_retriever.get_context_learnings("header", "commands")
    print(f"   Found {len(context_results['learnings'])} relevant learnings")
    print(f"   Summary: {context_results['summary']}")

    print("\nCompliance Checker test complete!")


if __name__ == "__main__":
    main()
