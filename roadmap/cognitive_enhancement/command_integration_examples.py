#!/usr/bin/env python3
"""
Command Integration Examples
============================

This module demonstrates how enhanced command wrappers integrate with the
existing .claude/commands/ structure and shows before/after examples of
commands with memory integration.

Examples show:
- How patterns guide execution decisions
- Integration with existing slash command infrastructure
- Before/after command behavior comparisons
- Practical usage scenarios
"""

import os
import sys

# Import the cognitive enhancement framework
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from enhanced_learn import LearningPattern
from memory_aware_commands import MemoryAwareCommandProcessor


class CommandIntegrationDemo:
    """Demonstrates command integration with memory patterns."""

    def __init__(self):
        self.processor = MemoryAwareCommandProcessor()
        self.setup_example_patterns()

    def setup_example_patterns(self):
        """Set up example patterns for demonstration."""
        example_patterns = [
            LearningPattern(
                pattern_type="correction",
                content="Always use --puppeteer flag for browser tests in Claude Code CLI",
                context="Browser testing setup discussion",
                confidence=0.9,
                timestamp="2025-07-14T10:00:00",
                source="user_correction",
                examples=["--puppeteer for browser automation"],
                tags=["testing", "browser", "puppeteer", "critical"],
            ),
            LearningPattern(
                pattern_type="preference",
                content="User prefers TodoWrite checklist before any execution",
                context="Command execution workflow",
                confidence=0.8,
                timestamp="2025-07-14T09:30:00",
                source="user_feedback",
                examples=["TodoWrite circuit breaker"],
                tags=["workflow", "execution", "planning"],
            ),
            LearningPattern(
                pattern_type="workflow",
                content="For complex tasks, use subagent coordination with worktrees",
                context="Architecture implementation discussion",
                confidence=0.85,
                timestamp="2025-07-14T09:00:00",
                source="successful_execution",
                examples=["subagent parallel execution"],
                tags=["execution", "complexity", "subagents", "workflow"],
            ),
            LearningPattern(
                pattern_type="technical",
                content="Checkpoint frequency should be every 3-5 files for medium complexity tasks",
                context="Progress tracking discussion",
                confidence=0.75,
                timestamp="2025-07-14T08:30:00",
                source="process_improvement",
                examples=["checkpoint every 5 minutes"],
                tags=["checkpoints", "frequency", "progress"],
            ),
            LearningPattern(
                pattern_type="correction",
                content="Use test_mode=true&test_user_id=test-user-123 for UI tests",
                context="UI testing authentication bypass",
                confidence=0.9,
                timestamp="2025-07-14T08:00:00",
                source="user_correction",
                examples=["test mode URL parameters"],
                tags=["testing", "ui", "authentication", "critical"],
            ),
        ]

        # Add patterns to the learner
        for pattern in example_patterns:
            self.processor.learner.add_pattern(pattern)

    def demo_before_after_execute(self):
        """Demonstrate before/after for execute command."""
        task = "implement browser testing for login functionality"

        print("🔄 EXECUTE COMMAND ENHANCEMENT DEMO")
        print("=" * 60)

        print("\n📋 BEFORE (Standard /execute):")
        print("-" * 40)
        standard_response = """I'll implement browser testing for login functionality.

## EXECUTE PROTOCOL CHECKLIST
- [ ] Context check: 85% remaining
- [ ] Task complexity assessment: Medium
- [ ] Execution approach: Direct execution
- [ ] Checkpoint frequency: Every 5 minutes OR 3-5 files
- [ ] Scratchpad location: roadmap/scratchpad_[branch].md
- [ ] PR update strategy: Push at each checkpoint

Beginning implementation..."""
        print(standard_response)

        print("\n📋 AFTER (Memory-Enhanced /execute):")
        print("-" * 40)
        enhanced_response = self.processor.process_command("execute", task)
        print(enhanced_response)

    def demo_before_after_testui(self):
        """Demonstrate before/after for testui command."""
        task = "test the user registration form"

        print("\n🔄 TESTUI COMMAND ENHANCEMENT DEMO")
        print("=" * 60)

        print("\n📋 BEFORE (Standard /testui):")
        print("-" * 40)
        standard_response = """I'll test the user registration form using browser automation.

Running UI tests with mock backend...
Using Playwright for browser automation."""
        print(standard_response)

        print("\n📋 AFTER (Memory-Enhanced /testui):")
        print("-" * 40)
        enhanced_response = self.processor.process_command("testui", task)
        print(enhanced_response)

    def demo_pattern_guidance_impact(self):
        """Demonstrate how patterns guide specific decisions."""

        print("\n🔄 PATTERN GUIDANCE IMPACT DEMO")
        print("=" * 60)

        scenarios = [
            {
                "task": "create comprehensive authentication system",
                "pattern_impact": "High complexity → Subagent coordination recommended",
                "without_patterns": "Direct implementation approach",
                "with_patterns": "Subagent coordination with worktrees (learned pattern)",
            },
            {
                "task": "test browser functionality",
                "pattern_impact": "Critical correction → Must use --puppeteer flag",
                "without_patterns": "Default Playwright usage",
                "with_patterns": "--puppeteer flag applied (user correction)",
            },
            {
                "task": "build API endpoints",
                "pattern_impact": "Checkpoint frequency → Every 3-5 files",
                "without_patterns": "Standard 5-minute checkpoints",
                "with_patterns": "Pattern-informed checkpoint frequency",
            },
        ]

        for i, scenario in enumerate(scenarios, 1):
            print(f"\n📊 Scenario {i}: {scenario['task']}")
            print(f"Pattern Impact: {scenario['pattern_impact']}")
            print(f"❌ Without Memory: {scenario['without_patterns']}")
            print(f"✅ With Memory: {scenario['with_patterns']}")

    def demo_command_file_integration(self):
        """Show how enhanced commands integrate with .claude/commands/ structure."""

        print("\n🔄 COMMAND FILE INTEGRATION DEMO")
        print("=" * 60)

        print("\n📁 Integration Approach:")
        print("-" * 30)

        integration_plan = """
1. **Enhanced Command Files**:
   - execute-enhanced.md → Memory-aware execute command
   - testui-enhanced.md → Pattern-informed testing
   - learn-enhanced.md → Memory-integrated learning

2. **Command Wrapper Scripts**:
   - enhanced_execute_wrapper.py → Execute command enhancement
   - memory_aware_commands.py → Universal command processor
   - command_integration.py → Integration utilities

3. **Memory Integration Points**:
   - Pattern query before execution
   - Context-aware decision making
   - Learning feedback loop integration
   - Consistent memory consultation

4. **Backward Compatibility**:
   - Original commands still work
   - Enhanced versions provide additional value
   - Gradual migration possible
   - User choice between standard/enhanced
        """
        print(integration_plan)

    def demo_learning_feedback_loop(self):
        """Demonstrate the learning feedback loop."""

        print("\n🔄 LEARNING FEEDBACK LOOP DEMO")
        print("=" * 60)

        print("\n📝 Scenario: User corrects command execution approach")
        print("-" * 50)

        demo_flow = """
1. **Initial Command**: /execute implement user dashboard

2. **AI Response**: Uses direct execution approach

3. **User Correction**: "Actually, use subagent coordination for this"

4. **Learning Capture**: /learn command captures the correction
   - Pattern: "For dashboard implementation, use subagent coordination"
   - Type: "preference"
   - Context: "UI implementation projects"

5. **Future Commands**: /execute implement admin panel

6. **Enhanced Response**: Memory query finds dashboard pattern
   - Recommends subagent coordination
   - Cites previous user preference
   - Applies learned approach automatically

7. **Result**: Consistent with user preferences without re-correction
        """
        print(demo_flow)

        print("\n💡 Benefits:")
        print("- Reduces repeated corrections")
        print("- Builds user-specific preferences")
        print("- Improves response quality over time")
        print("- Creates personalized AI assistant behavior")

    def demo_real_usage_scenarios(self):
        """Show real-world usage scenarios."""

        print("\n🔄 REAL USAGE SCENARIOS")
        print("=" * 60)

        scenarios = [
            {
                "command": "/execute",
                "task": "fix the JSON parsing error in API",
                "memory_insights": [
                    "Previous JSON fixes used robust_json_parser.py",
                    "User prefers defensive programming for JSON",
                    "Test JSON edge cases thoroughly",
                ],
                "enhanced_approach": "Apply robust parsing + comprehensive tests",
            },
            {
                "command": "/testui",
                "task": "verify login form validation",
                "memory_insights": [
                    "Always use test_mode=true for auth bypass",
                    "User prefers headless=True for CI tests",
                    "Screenshot failures for debugging",
                ],
                "enhanced_approach": "Test mode + headless + screenshot capture",
            },
            {
                "command": "/learn",
                "task": "document new testing approach",
                "memory_insights": [
                    "User wants critical rules in CLAUDE.md",
                    "Technical details go in lessons.mdc",
                    "Create separate PR for learning updates",
                ],
                "enhanced_approach": "Categorize + appropriate file + clean PR",
            },
        ]

        for scenario in scenarios:
            print(f"\n📋 Command: {scenario['command']} {scenario['task']}")
            print("Memory Insights:")
            for insight in scenario["memory_insights"]:
                print(f"  • {insight}")
            print(f"Enhanced Approach: {scenario['enhanced_approach']}")

    def run_full_demo(self):
        """Run the complete demonstration."""
        print("🚀 ENHANCED COMMAND WRAPPERS DEMONSTRATION")
        print("=" * 80)
        print("Showing how memory pattern integration transforms command execution")

        self.demo_before_after_execute()
        self.demo_before_after_testui()
        self.demo_pattern_guidance_impact()
        self.demo_command_file_integration()
        self.demo_learning_feedback_loop()
        self.demo_real_usage_scenarios()

        print("\n🎯 SUMMARY")
        print("=" * 80)
        summary = """
The enhanced command wrappers provide:

✅ **Memory Integration**: Commands automatically consult learned patterns
✅ **Pattern-Guided Decisions**: Execution approaches informed by experience
✅ **Consistency**: User preferences applied across all commands
✅ **Learning Loop**: Continuous improvement through pattern accumulation
✅ **Backward Compatibility**: Works alongside existing command structure
✅ **User-Specific Adaptation**: AI behavior adapts to individual preferences

This transforms commands from static procedures into adaptive, learning-enabled
tools that improve with each interaction.
        """
        print(summary)


def main():
    """Run the command integration demonstration."""
    demo = CommandIntegrationDemo()
    demo.run_full_demo()


if __name__ == "__main__":
    main()
