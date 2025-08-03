#!/usr/bin/env python3
"""
Timeout Command - Performance Optimizer

Automatically applies timeout mitigation strategies to prevent Claude Code CLI timeouts.
Implements three modes: standard, strict, emergency for different optimization levels.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Optional

# Timeout modes and their configurations
TIMEOUT_MODES = {
    "standard": {
        "name": "STANDARD",
        "icon": "🚀",
        "thinking_limit": 5,
        "response_format": "bullet",
        "context_lines": 3,
        "tool_batching": True,
        "multiedit_threshold": 2,
        "max_file_lines": 100,
        "explanation_level": "minimal",
    },
    "strict": {
        "name": "STRICT",
        "icon": "⚡",
        "thinking_limit": 3,
        "response_format": "single_line",
        "context_lines": 1,
        "tool_batching": True,
        "multiedit_threshold": 1,
        "max_file_lines": 50,
        "explanation_level": "none",
    },
    "emergency": {
        "name": "EMERGENCY",
        "icon": "🚨",
        "thinking_limit": 2,
        "response_format": "actions_only",
        "context_lines": 0,
        "tool_batching": True,
        "multiedit_threshold": 1,
        "max_file_lines": 25,
        "explanation_level": "none",
    },
}


class TimeoutOptimizer:
    """Manages timeout optimization modes and behavior modifications"""

    def __init__(self):
        self.config_file = Path.home() / ".claude" / "timeout_config.json"
        self.current_mode = None
        self.load_config()

    def load_config(self):
        """Load current timeout configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    self.current_mode = config.get("mode")
        except Exception:
            self.current_mode = None

    def save_config(self, mode: Optional[str]):
        """Save timeout configuration"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w") as f:
                json.dump({"mode": mode}, f)
            self.current_mode = mode
        except PermissionError:
            print(
                "Error: Insufficient permissions to save the timeout configuration file."
            )
        except FileNotFoundError:
            print(
                "Error: The specified path for the timeout configuration file is invalid."
            )
        except OSError as e:
            print(
                f"Error: An OS-related error occurred while saving the timeout configuration: {e}"
            )
        except Exception as e:
            print(
                f"Warning: An unexpected error occurred while saving the timeout configuration: {type(e).__name__}: {e}"
            )

    def set_mode(self, mode: str) -> str:
        """Set timeout optimization mode"""
        if mode == "off":
            self.save_config(None)
            return "Timeout optimizations disabled"

        if mode not in TIMEOUT_MODES:
            return f"Invalid mode: {mode}. Use: standard, strict, emergency, off"

        self.save_config(mode)
        config = TIMEOUT_MODES[mode]

        # Generate mode indicator
        indicator = self.generate_mode_indicator(mode, config)

        # Generate optimization summary
        optimizations = self.generate_optimization_summary(config)

        return f"{indicator}\n{optimizations}"

    def generate_mode_indicator(self, mode: str, config: Dict) -> str:
        """Generate mode indicator display"""
        if mode == "emergency":
            return f"{config['icon']} TIMEOUT MODE: {config['name']}\nCrisis-mode: Actions-only | No-explain | Think-limit {config['thinking_limit']}"
        else:
            return f"{config['icon']} TIMEOUT MODE: {config['name']}\nOptimizations: Batching ON | Brevity ON | Think-limit {config['thinking_limit']}"

    def generate_optimization_summary(self, config: Dict) -> str:
        """Generate optimization summary"""
        optimizations = []

        if config["tool_batching"]:
            optimizations.append("Tool batching enabled")

        if config["multiedit_threshold"] <= 2:
            optimizations.append(
                f"MultiEdit enforced for >{config['multiedit_threshold']} edits"
            )

        if config["max_file_lines"] < 100:
            optimizations.append(
                f"File reads limited to {config['max_file_lines']} lines"
            )

        if config["explanation_level"] in ["minimal", "none"]:
            optimizations.append("Verbose explanations disabled")

        return "Active optimizations: " + " | ".join(optimizations)

    def get_current_status(self) -> str:
        """Get current timeout mode status"""
        if not self.current_mode:
            return "Timeout optimizations: OFF"

        config = TIMEOUT_MODES[self.current_mode]
        return self.generate_mode_indicator(self.current_mode, config)

    def generate_behavior_prompt(self) -> str:
        """Generate prompt modifications for current mode"""
        if not self.current_mode:
            return ""

        config = TIMEOUT_MODES[self.current_mode]

        prompt_parts = [
            f"🚨 TIMEOUT OPTIMIZATION MODE: {config['name']} ACTIVE",
            "",
            "MANDATORY BEHAVIOR MODIFICATIONS:",
        ]

        # Thinking constraints
        prompt_parts.append(
            f"- Thinking limit: {config['thinking_limit']} thoughts maximum"
        )
        prompt_parts.append("- No branching or revision thoughts")
        prompt_parts.append("- Linear problem-solving only")

        # Tool usage optimization
        if config["tool_batching"]:
            prompt_parts.append("- ALWAYS batch tool calls in single message")
            prompt_parts.append(
                f"- Use MultiEdit for >{config['multiedit_threshold']} file edits"
            )
            prompt_parts.append("- Use Task tool for >3 file operations")

        # File operation limits
        prompt_parts.append(f"- Read max {config['max_file_lines']} lines per file")
        prompt_parts.append("- Use offset/limit parameters for large files")
        prompt_parts.append("- Trust edit success, don't re-read files")

        # Response format constraints
        if config["response_format"] == "actions_only":
            prompt_parts.append("- ACTIONS ONLY: No explanations or context")
            prompt_parts.append("- Tool invocations + results only")
            prompt_parts.append("- Single word confirmations")
        elif config["response_format"] == "single_line":
            prompt_parts.append("- Single-line responses preferred")
            prompt_parts.append("- No code blocks unless essential")
            prompt_parts.append("- Abbreviations acceptable")
        elif config["response_format"] == "bullet":
            prompt_parts.append("- Bullet points for lists")
            prompt_parts.append("- File:line references > code quotes")
            prompt_parts.append(
                f"- Max {config['context_lines']} lines context per item"
            )

        # Explanation level
        if config["explanation_level"] == "none":
            prompt_parts.append("- Zero explanatory text")
            prompt_parts.append("- No unsolicited explanations")
        elif config["explanation_level"] == "minimal":
            prompt_parts.append("- Minimal explanations only")
            prompt_parts.append("- Focus on essential information")

        prompt_parts.extend(
            ["", "TIMEOUT PREVENTION IS CRITICAL - FOLLOW ALL CONSTRAINTS", ""]
        )

        return "\n".join(prompt_parts)


def main():
    """Main timeout command handler"""
    args = sys.argv[1:]  # Remove script name

    optimizer = TimeoutOptimizer()

    # Parse arguments
    if not args:
        # No arguments - set standard mode
        result = optimizer.set_mode("standard")
        print(result)

        # Output behavior prompt for Claude
        behavior_prompt = optimizer.generate_behavior_prompt()
        if behavior_prompt:
            print("\n" + behavior_prompt)

    elif args[0] in ["standard", "strict", "emergency", "off"]:
        # Set specific mode
        result = optimizer.set_mode(args[0])
        print(result)

        # Output behavior prompt for Claude (except for 'off')
        if args[0] != "off":
            behavior_prompt = optimizer.generate_behavior_prompt()
            if behavior_prompt:
                print("\n" + behavior_prompt)

    elif args[0] == "status":
        # Show current status
        print(optimizer.get_current_status())

    else:
        # Invalid argument
        print("Usage: /timeout [standard|strict|emergency|off|status]")
        print("Default: standard mode if no argument provided")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
