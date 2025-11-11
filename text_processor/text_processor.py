#!/usr/bin/env python3
"""
Text Processor CLI - Command-line interface for text processing operations.

This script provides a CLI for common text processing tasks including
word/character/line counting, text replacement, and case conversion.
"""

import argparse
import os
import sys

from .operations import (
    convert_case,
    count_characters,
    count_lines,
    count_words,
    get_text_stats,
    replace_text,
)


def read_input(file_path: str | None = None) -> str:
    """
    Read text input from file or stdin.

    Args:
        file_path: Path to input file, None for stdin

    Returns:
        Input text content

    Raises:
        FileNotFoundError: If specified file doesn't exist
        PermissionError: If file cannot be read
    """
    try:
        if file_path:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            with open(file_path, encoding='utf-8') as f:
                return f.read()
        else:
            # Read from stdin
            return sys.stdin.read()
    except PermissionError:
        raise PermissionError(f"Permission denied reading file: {file_path}")
    except UnicodeDecodeError:
        raise ValueError(f"Unable to decode file as UTF-8: {file_path}")


def handle_count_command(args) -> None:
    """Handle count operations."""
    try:
        text = read_input(args.file)

        if args.type == 'words':
            result = count_words(text)
            print(f"Words: {result}")
        elif args.type == 'characters':
            include_spaces = not args.no_spaces
            result = count_characters(text, include_spaces=include_spaces)
            spaces_label = "with" if include_spaces else "without"
            print(f"Characters ({spaces_label} spaces): {result}")
        elif args.type == 'lines':
            result = count_lines(text)
            print(f"Lines: {result}")
        elif args.type == 'all':
            stats = get_text_stats(text)
            print("Text Statistics:")
            print(f"  Words: {stats['words']}")
            print(f"  Characters (with spaces): {stats['characters_with_spaces']}")
            print(f"  Characters (without spaces): {stats['characters_without_spaces']}")
            print(f"  Lines: {stats['lines']}")
            print(f"  Paragraphs: {stats['paragraphs']}")

    except (FileNotFoundError, PermissionError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def handle_replace_command(args) -> None:
    """Handle text replacement operations."""
    try:
        text = read_input(args.file)

        result = replace_text(
            text,
            args.old,
            args.new,
            case_sensitive=not args.ignore_case
        )

        if args.output:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(result)
                print(f"Output written to: {args.output}")
            except PermissionError:
                print(f"Error: Permission denied writing to file: {args.output}", file=sys.stderr)
                sys.exit(1)
        else:
            print(result, end='')

    except (FileNotFoundError, PermissionError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def handle_case_command(args) -> None:
    """Handle case conversion operations."""
    try:
        text = read_input(args.file)

        result = convert_case(text, args.type)

        if args.output:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(result)
                print(f"Output written to: {args.output}")
            except PermissionError:
                print(f"Error: Permission denied writing to file: {args.output}", file=sys.stderr)
                sys.exit(1)
        else:
            print(result, end='')

    except (FileNotFoundError, PermissionError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Text Processor - CLI utility for text processing operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Count words in a file
  python text_processor.py count words -f input.txt

  # Count characters from stdin (excluding spaces)
  echo "Hello World" | python text_processor.py count characters --no-spaces

  # Get all statistics
  python text_processor.py count all -f document.txt

  # Replace text (case insensitive)
  python text_processor.py replace "hello" "hi" -f input.txt -i

  # Convert to uppercase and save to file
  python text_processor.py case upper -f input.txt -o output.txt
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Count command
    count_parser = subparsers.add_parser('count', help='Count words, characters, or lines')
    count_parser.add_argument(
        'type',
        choices=['words', 'characters', 'lines', 'all'],
        help='Type of count to perform'
    )
    count_parser.add_argument(
        '-f', '--file',
        help='Input file (default: read from stdin)'
    )
    count_parser.add_argument(
        '--no-spaces',
        action='store_true',
        help='Exclude spaces from character count'
    )

    # Replace command
    replace_parser = subparsers.add_parser('replace', help='Replace text')
    replace_parser.add_argument('old', help='Text to replace')
    replace_parser.add_argument('new', help='Replacement text')
    replace_parser.add_argument(
        '-f', '--file',
        help='Input file (default: read from stdin)'
    )
    replace_parser.add_argument(
        '-o', '--output',
        help='Output file (default: print to stdout)'
    )
    replace_parser.add_argument(
        '-i', '--ignore-case',
        action='store_true',
        help='Ignore case when replacing'
    )

    # Case command
    case_parser = subparsers.add_parser('case', help='Convert text case')
    case_parser.add_argument(
        'type',
        choices=['upper', 'lower', 'title', 'capitalize'],
        help='Type of case conversion'
    )
    case_parser.add_argument(
        '-f', '--file',
        help='Input file (default: read from stdin)'
    )
    case_parser.add_argument(
        '-o', '--output',
        help='Output file (default: print to stdout)'
    )

    return parser


def main() -> None:
    """Main entry point for the CLI."""
    parser = create_parser()

    # Show help if no arguments provided
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == 'count':
            handle_count_command(args)
        elif args.command == 'replace':
            handle_replace_command(args)
        elif args.command == 'case':
            handle_case_command(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
