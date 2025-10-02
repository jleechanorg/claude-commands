import os

from setuptools import setup

# Read long description from README
with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements from mvp_site/requirements.txt
requirements_path = os.path.join("mvp_site", "requirements.txt")
with open(requirements_path, encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]

# Note: mcp>=1.0.0 already declared in mvp_site/requirements.txt (no duplication needed)

setup(
    name="worldarchitect-mcp",
    version="1.0.0",
    author="WorldArchitect.AI",
    author_email="support@worldarchitect.ai",
    description="WorldArchitect.AI MCP Server - Complete D&D 5e Campaign Management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jleechanorg/worldarchitect.ai",
    packages=["mvp_site", "mvp_site.schemas"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "worldarchitect-mcp=mvp_site.mcp_api:run_server",
        ],
    },
    include_package_data=True,
    package_data={
        "mvp_site": [
            "*.json",
            "*.md",
            "*.txt",
            "prompts/*.md",
            "schemas/*.json",
            "config/*.py",
            "static/**/*",
            "templates/**/*",
        ],
    },
    exclude=["tests*", "testing_*", "*.pyc", "__pycache__"],
)
