#!/usr/bin/env python3
"""
/list - Display all available slash commands with descriptions

Reads all .md files in the commands directory and displays their purposes.
"""

import glob
import os
import sys


def read_command_info(md_file):
    """Extract command name and purpose from markdown file"""
    try:
        with open(md_file, "r") as f:
            content = f.read()

        # Extract title (first line starting with #)
        lines = content.split("\n")
        title = ""
        purpose = ""

        for line in lines:
            if line.startswith("# ") and not title:
                title = line[2:].strip()
            elif line.startswith("**Purpose**:") and not purpose:
                purpose = line.replace("**Purpose**:", "").strip()
                break

        return title, purpose
    except (OSError, IOError, ValueError) as e:
        print(f"Error reading file {md_file}: {e}", file=sys.stderr)
        return None, None


def main():
    """Main function to list all commands"""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Find all .md files in the commands directory
    md_files = glob.glob(os.path.join(script_dir, "*.md"))

    commands = []

    for md_file in md_files:
        filename = os.path.basename(md_file)
        command_name = filename.replace(".md", "")

        # Skip the list command itself to avoid recursion
        if command_name == "list":
            continue

        title, purpose = read_command_info(md_file)

        if title and purpose:
            commands.append({"name": command_name, "title": title, "purpose": purpose})

    # Sort commands alphabetically
    commands.sort(key=lambda x: x["name"])

    # Display the commands
    print("# Available Slash Commands")
    print()

    for cmd in commands:
        print(f"- `/{cmd['name']}` - {cmd['purpose']}")

    print()
    print("Use `/command_name` to execute any of these commands.")
    print("Add `--help` to any command for detailed usage information.")


if __name__ == "__main__":
    main()
