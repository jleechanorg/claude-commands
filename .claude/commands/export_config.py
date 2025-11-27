#!/usr/bin/env python3
"""
Shared Export Configuration for Claude Code
Used by both /localexportcommands and /exportcommands to ensure consistency
"""

import json

# 🚨 SINGLE SOURCE OF TRUTH: Export Component List
# This list defines ALL components that should be exported by both local and remote export commands
# Both commands MUST use this list to maintain consistency

# EXPORTABLE_COMPONENTS: Standard Claude Code directories and files that should be exported
# - These are the core components that make up a Claude Code configuration
# - Modifications to this list automatically affect both export commands
# - Based on official Claude Code documentation and standard directory structure

EXPORTABLE_COMPONENTS = [
    "commands",      # Slash commands (.md and .py files) - STANDARD
    "hooks",         # Lifecycle hooks (.sh, .py, .md files) - STANDARD
    "agents",        # Subagents/specialized AI assistants (.md files) - STANDARD
    "scripts",       # Claude Code utility scripts (.sh, .py files) - STANDARD
    "skills",        # Skill documentation and guides (.md files) - STANDARD
    "settings.json", # Configuration file - STANDARD
    "workflows"      # GitHub Actions workflows (.yml files) - EXAMPLES ONLY
]

# 📝 NOTE: MCP Server Script Locations (export-time consolidation)
# - MCP launchers and utilities live in project root/scripts for backward compatibility
#   (e.g., claude_mcp.sh, codex_mcp.sh, mcp_common.sh, mcp_dual_background.sh,
#   mcp_stdio_wrapper.py, start_mcp_production.sh, start_mcp_server.sh)
# - Export commands consolidate these into the scripts component so the bundle exposes
#   them under .claude/scripts without relocating files inside the repository

# EXCLUDED_COMPONENTS: Project-specific directories that should NOT be exported
# - These are custom directories specific to individual projects
# - They are not part of the standard Claude Code structure
# - Export commands should skip these directories

EXCLUDED_COMPONENTS = [
    "config",            # Project-specific configuration (not user config)
    "framework",         # Project development frameworks
    "guides",            # Project-specific guides
    "learnings",         # Project-specific learnings
    "memory_templates",  # Project-specific memory templates
    "research",          # Project-specific research
    "schemas",           # Project-specific schemas
    "templates",         # Project-specific templates
    "triggers",          # Project-specific triggers
    "learnings.md",      # Project-specific learnings file
    "principal_engineer_review_prompt.md",  # Project-specific prompts
    "settings.toml",     # Deprecated/alternative config format
    "settings.json.backup"  # Backup files
]

# Component descriptions for documentation
COMPONENT_DESCRIPTIONS = {
    "commands": "Slash commands that provide CLI-like interface to Claude Code",
    "hooks": "Lifecycle hooks that run at specific points in Claude Code workflow",
    "agents": "Specialized AI agent configurations for different tasks",
    "scripts": "Utility scripts including MCP server scripts and automation helpers",
    "skills": "Skill documentation and guides for Claude Code capabilities",
    "settings.json": "Claude Code configuration and preferences",
    "workflows": "GitHub Actions workflow examples (require integration into your codebase)"
}


def get_exportable_components():
    """Return the list of exportable components."""
    return EXPORTABLE_COMPONENTS.copy()


def get_excluded_components():
    """Return the list of excluded components."""
    return EXCLUDED_COMPONENTS.copy()


def get_component_description(component):
    """Get description for a specific component."""
    return COMPONENT_DESCRIPTIONS.get(component, "No description available")


def get_all_descriptions():
    """Return all component descriptions."""
    return COMPONENT_DESCRIPTIONS.copy()


if __name__ == "__main__":
    # When run directly, print the configuration for debugging
    config = {
        "exportable_components": EXPORTABLE_COMPONENTS,
        "excluded_components": EXCLUDED_COMPONENTS,
        "component_descriptions": COMPONENT_DESCRIPTIONS
    }

    print(json.dumps(config, indent=2))
