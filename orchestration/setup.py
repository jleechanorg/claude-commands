#!/usr/bin/env python3
"""
Setup script for ai_orch package.

This packages the orchestration directory as 'ai_orch' for PyPI distribution.
"""

from setuptools import setup
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="ai_orch",
    version="0.1.0",
    description="AI Orchestration - tmux-based interactive AI CLI wrapper and multi-agent orchestration system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="jleechan",
    author_email="jlee@jleechan.org",
    url="https://github.com/jleechanorg/worldarchitect.ai",
    license="MIT",

    # Package the orchestration directory
    # PyPI package name is 'ai_orch' but Python package name is 'orchestration'
    # This allows 'pip install ai_orch' while using 'from orchestration import ...'
    packages=["orchestration"],
    package_dir={},

    # Include package data
    package_data={
        "orchestration": [
            "*.md",
            "*.txt",
            "*.yaml",
            "*.conf",
            "config/*.yaml",
        ]
    },

    # Python version requirement
    python_requires=">=3.10",

    # No external dependencies - uses only stdlib
    install_requires=[],

    # Entry points for CLI commands
    # CLI commands are 'ai_orch' and 'orch' but import from 'orchestration' package
    entry_points={
        "console_scripts": [
            "ai_orch=orchestration.live_mode:main",
            "orch=orchestration.live_mode:main",
        ]
    },

    # PyPI classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Shells",
        "Topic :: Terminals",
        "License :: OSI Approved :: MIT License",
    ],

    keywords=[
        "ai",
        "orchestration",
        "tmux",
        "claude",
        "codex",
        "cli",
        "automation",
        "agents",
        "terminal",
        "interactive",
    ],

    project_urls={
        "Homepage": "https://github.com/jleechanorg/worldarchitect.ai",
        "Repository": "https://github.com/jleechanorg/worldarchitect.ai",
        "Issues": "https://github.com/jleechanorg/worldarchitect.ai/issues",
        "Documentation": "https://github.com/jleechanorg/worldarchitect.ai/tree/main/orchestration",
    },
)
