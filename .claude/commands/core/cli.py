#!/usr/bin/env python3
"""
Main CLI entry point using Click framework.
"""

import click
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from .execute import execute
    from .test import test, testui, testuif, testhttp, testhttpf, testi, tester
except ImportError:
    # Fallback to direct imports when running as script
    from execute import execute
    from test import test, testui, testuif, testhttp, testhttpf, testi, tester


@click.group()
@click.version_option(version='1.0.0', prog_name='claude-commands')
def cli():
    """Claude AI Assistant Command Line Interface"""
    pass


# Add command groups
cli.add_command(execute)
cli.add_command(test)

# Add backward compatibility aliases
cli.add_command(testui)
cli.add_command(testuif)
cli.add_command(testhttp)
cli.add_command(testhttpf)
cli.add_command(testi)
cli.add_command(tester)


if __name__ == '__main__':
    cli()