#!/usr/bin/env python3
"""
Command Wrapper Integration System
==================================

This module provides the integration layer between the enhanced command wrappers
and the existing .claude/commands/ infrastructure. It creates a bridge that
allows memory-enhanced commands to work alongside standard commands.

Features:
- Seamless integration with existing command structure
- Command routing with memory enhancement options
- Backward compatibility maintenance
- Command alias management
"""

import os
import sys
from dataclasses import dataclass

# Import the cognitive enhancement framework
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from enhanced_execute_wrapper import EnhancedExecuteWrapper
from memory_aware_commands import MemoryAwareCommandProcessor


@dataclass
class CommandMapping:
    """Mapping between standard and enhanced commands."""

    standard_command: str
    enhanced_command: str
    aliases: list[str]
    memory_enabled: bool
    description: str


class CommandWrapperIntegration:
    """Integration system for enhanced command wrappers."""

    def __init__(self, claude_commands_dir: str | None = None):
        self.claude_commands_dir = (
            claude_commands_dir or self._find_claude_commands_dir()
        )
        self.processor = MemoryAwareCommandProcessor()
        self.execute_wrapper = EnhancedExecuteWrapper()

        # Define command mappings
        self.command_mappings = {
            "execute": CommandMapping(
                standard_command="execute",
                enhanced_command="execute-enhanced",
                aliases=["ee", "e+"],
                memory_enabled=True,
                description="Memory-enhanced execution with pattern guidance",
            ),
            "plan": CommandMapping(
                standard_command="plan",
                enhanced_command="plan-enhanced",
                aliases=["plan+", "pe"],
                memory_enabled=True,
                description="Memory-informed planning with pattern consultation",
            ),
            "testui": CommandMapping(
                standard_command="testui",
                enhanced_command="testui-enhanced",
                aliases=["testui+", "tue"],
                memory_enabled=True,
                description="Pattern-aware UI testing with learned preferences",
            ),
            "learn": CommandMapping(
                standard_command="learn",
                enhanced_command="learn-enhanced",
                aliases=["learn+", "le"],
                memory_enabled=True,
                description="Enhanced learning with pattern analysis",
            ),
        }

    def _find_claude_commands_dir(self) -> str:
        """Find the .claude/commands directory."""
        current_dir = os.getcwd()

        # Search up the directory tree
        while current_dir != "/":
            claude_dir = os.path.join(current_dir, ".claude", "commands")
            if os.path.exists(claude_dir):
                return claude_dir
            current_dir = os.path.dirname(current_dir)

        # Fallback to current directory
        return os.path.join(os.getcwd(), ".claude", "commands")

    def route_command(self, command: str, args: str, enhanced: bool = True) -> str:
        """Route command to appropriate handler."""

        # Check if this is an enhanced command alias
        enhanced_command = self._resolve_enhanced_alias(command)
        if enhanced_command:
            return self._execute_enhanced_command(enhanced_command, args)

        # Check if standard command has enhancement available
        if enhanced and command in self.command_mappings:
            return self._execute_enhanced_command(command, args)

        # Fall back to standard command
        return self._execute_standard_command(command, args)

    def _resolve_enhanced_alias(self, command: str) -> str | None:
        """Resolve enhanced command aliases to base commands."""
        for base_cmd, mapping in self.command_mappings.items():
            if command in mapping.aliases or command == mapping.enhanced_command:
                return base_cmd
        return None

    def _execute_enhanced_command(self, command: str, args: str) -> str:
        """Execute enhanced version of command."""

        if command in ["execute", "e"]:
            return self.processor.process_command("execute", args)

        if command == "plan":
            return self.processor.process_command("plan", args)

        if command in ["testui", "testuif", "testhttp", "testhttpf", "testi"]:
            return self.processor.process_command(command, args)

        if command == "learn":
            return self.processor.process_command("learn", args)

        # Generic enhanced processing
        return self.processor.process_command(command, args)

    def _execute_standard_command(self, command: str, args: str) -> str:
        """Execute standard version of command (fallback)."""

        # Try to read standard command file
        command_file = os.path.join(self.claude_commands_dir, f"{command}.md")

        if os.path.exists(command_file):
            with open(command_file) as f:
                content = f.read()

            return (
                f"Standard `/{command}` command:\n{content[:500]}...\n\n"
                f"(Use `/{command}+` or `/ee` for memory-enhanced version)"
            )

        return f"Command `/{command}` not found. Available enhanced commands: {list(self.command_mappings.keys())}"

    def create_enhanced_command_files(self):
        """Create enhanced command files in .claude/commands/ directory."""

        if not os.path.exists(self.claude_commands_dir):
            os.makedirs(self.claude_commands_dir, exist_ok=True)

        # Create enhanced execute command file
        execute_enhanced_path = os.path.join(
            self.claude_commands_dir, "execute-enhanced.md"
        )
        if not os.path.exists(execute_enhanced_path):
            # Copy from our enhanced file
            source_path = os.path.join(os.path.dirname(__file__), "execute-enhanced.md")
            if os.path.exists(source_path):
                with open(source_path) as src, open(execute_enhanced_path, "w") as dst:
                    dst.write(src.read())

        # Create command integration documentation
        integration_doc = self._generate_integration_documentation()
        integration_path = os.path.join(
            self.claude_commands_dir, "MEMORY_INTEGRATION.md"
        )
        with open(integration_path, "w") as f:
            f.write(integration_doc)

        # Create command aliases file
        aliases_doc = self._generate_aliases_documentation()
        aliases_path = os.path.join(self.claude_commands_dir, "ENHANCED_ALIASES.md")
        with open(aliases_path, "w") as f:
            f.write(aliases_doc)

    def _generate_integration_documentation(self) -> str:
        """Generate documentation for command integration."""

        doc = """# Memory Integration for Slash Commands

## Overview
Enhanced command wrappers provide memory pattern integration for improved execution quality and consistency.

## Enhanced Commands Available

"""

        for _base_cmd, mapping in self.command_mappings.items():
            doc += f"### /{mapping.enhanced_command}\n"
            doc += f"**Aliases**: {', '.join(['/' + alias for alias in mapping.aliases])}\n"
            doc += f"**Description**: {mapping.description}\n"
            doc += (
                f"**Memory Enabled**: {'Yes' if mapping.memory_enabled else 'No'}\n\n"
            )

        doc += """
## Memory Integration Features

### Pattern Consultation
- Automatic query of learned patterns before execution
- Relevance scoring and pattern categorization
- Context-aware decision making

### Pattern Application
- Critical corrections applied automatically
- User preferences incorporated
- Workflow patterns followed
- Technical insights applied

### Learning Integration
- Execution outcomes feed back to memory
- User corrections captured as patterns
- Continuous improvement of command behavior

## Usage Examples

### Standard vs Enhanced
```bash
# Standard execution
/execute implement user auth

# Enhanced execution with memory
/ee implement user auth
/execute-enhanced implement user auth
```

### Memory Consultation Results
Enhanced commands show memory consultation results:
```
🧠 MEMORY CONSULTATION RESULTS:
Found 3 relevant patterns

🚨 CRITICAL CORRECTIONS (1):
  ⚠️ Always use --puppeteer for browser tests

🎯 USER PREFERENCES (1):
  • Prefer subagent coordination for complex tasks

💡 RECOMMENDATIONS (1):
  • Apply defensive programming patterns
```

## Backward Compatibility
- All standard commands continue to work unchanged
- Enhanced versions provide additional memory features
- Users can choose between standard and enhanced
- Gradual migration path available

## Integration Points
- `.claude/commands/` - Enhanced command documentation
- `roadmap/cognitive_enhancement/` - Memory system implementation
- Existing slash command infrastructure - Seamless integration
"""

        return doc

    def _generate_aliases_documentation(self) -> str:
        """Generate documentation for command aliases."""

        doc = """# Enhanced Command Aliases

Quick reference for enhanced command aliases with memory integration.

## Command Mappings

| Standard | Enhanced | Aliases | Description |
|----------|----------|---------|-------------|
"""

        for base_cmd, mapping in self.command_mappings.items():
            aliases_str = ", ".join([f"`/{alias}`" for alias in mapping.aliases])
            doc += f"| `/{base_cmd}` | `/{mapping.enhanced_command}` | {aliases_str} | {mapping.description} |\n"

        doc += """
## Quick Start

### Most Common Enhanced Commands
```bash
/ee [task]          # Enhanced execute with memory
/plan+ [task]       # Enhanced planning with patterns
/testui+ [test]     # Pattern-aware UI testing
/learn+ [learning]  # Enhanced learning capture
```

### Memory Features
All enhanced commands provide:
- 🧠 **Pattern Consultation**: Automatic memory query
- 🚨 **Critical Corrections**: High-confidence fixes applied
- 🎯 **User Preferences**: Personal workflow preferences
- 💡 **Recommendations**: Learned best practices

### Example Usage
```bash
# Enhanced execution with memory guidance
/ee implement user authentication system

# Enhanced testing with learned preferences
/testui+ test login form validation

# Enhanced learning with pattern analysis
/learn+ always use headless=True for CI tests
```

## Memory Consultation Process

1. **Pattern Query**: Search learned patterns for relevance
2. **Categorization**: Group by type (corrections, preferences, workflows)
3. **Application**: Apply relevant patterns to execution strategy
4. **Enhancement**: Improve command execution with memory insights

## Integration Benefits

✅ **Consistency**: User preferences applied across commands
✅ **Learning**: Commands improve with each interaction
✅ **Efficiency**: Avoid repeating past mistakes
✅ **Personalization**: AI behavior adapts to user style
✅ **Quality**: Better execution decisions through memory
"""

        return doc

    def get_available_commands(self) -> dict[str, list[str]]:
        """Get list of available standard and enhanced commands."""

        standard_commands = []
        enhanced_commands = []

        # Scan .claude/commands directory for standard commands
        if os.path.exists(self.claude_commands_dir):
            for file in os.listdir(self.claude_commands_dir):
                if file.endswith(".md"):
                    cmd_name = file[:-3]  # Remove .md extension
                    if "-enhanced" in cmd_name:
                        enhanced_commands.append(cmd_name)
                    else:
                        standard_commands.append(cmd_name)

        return {
            "standard": sorted(standard_commands),
            "enhanced": sorted(enhanced_commands),
            "aliases": {
                cmd: mapping.aliases for cmd, mapping in self.command_mappings.items()
            },
        }

    def install_integration(self):
        """Install the command integration system."""

        print("🔧 Installing Enhanced Command Integration...")

        # Create enhanced command files
        self.create_enhanced_command_files()
        print(f"✅ Enhanced command files created in {self.claude_commands_dir}")

        # Display integration summary
        commands = self.get_available_commands()
        print(f"✅ {len(commands['standard'])} standard commands available")
        print(f"✅ {len(commands['enhanced'])} enhanced commands available")
        print(
            f"✅ {sum(len(aliases) for aliases in commands['aliases'].values())} command aliases configured"
        )

        print("\n🚀 Enhanced commands ready!")
        print("Try: /ee [task] for memory-enhanced execution")


def main():
    """Demonstrate command wrapper integration."""

    integration = CommandWrapperIntegration()

    # Install integration
    integration.install_integration()

    print("\n" + "=" * 60)
    print("COMMAND INTEGRATION DEMO")
    print("=" * 60)

    # Test command routing
    test_commands = [
        ("execute", "implement user auth"),
        ("ee", "implement user auth"),
        ("plan+", "build dashboard"),
        ("testui", "test login form"),
    ]

    for cmd, args in test_commands:
        print(f"\nTesting: /{cmd} {args}")
        print("-" * 40)
        result = integration.route_command(cmd, args)
        # Show first 200 chars of result
        print(result[:200] + "..." if len(result) > 200 else result)


if __name__ == "__main__":
    main()
