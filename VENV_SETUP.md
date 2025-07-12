# Virtual Environment Setup

This document explains how to set up the Python virtual environment for WorldArchitect.AI development.

## Quick Setup

If the virtual environment is missing or corrupted, recreate it with:

```bash
# From project root
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r mvp_site/requirements.txt

# Install development dependencies
pip install coverage pytest playwright
```

## Usage

The project provides several ways to use the virtual environment:

### 1. vpython Script (Recommended)
```bash
# The vpython script automatically activates venv and runs Python
./vpython mvp_site/main.py serve
./vpython -c "import flask; print('Flask works!')"
```

### 2. vpython Bash Function
```bash
# Available when ~/.bashrc is sourced
vpython mvp_site/main.py serve
```

### 3. Manual Activation
```bash
source venv/bin/activate
python mvp_site/main.py serve
```

## Expected Location

The virtual environment must be located at:
```
/home/jleechan/projects/worldarchitect.ai/worktree_claude_md_treatment/venv/
```

This path is hardcoded in:
- `~/.bashrc` vpython() function (lines 162-178)
- `./vpython` script (lines 8-16)
- `./run_tests.sh` script (line 102)

## Dependencies

Core dependencies from `mvp_site/requirements.txt`:
- Flask==3.0.0
- gunicorn==21.2.0  
- firebase-admin==6.5.0
- google-cloud-firestore==2.16.0
- google-genai
- protobuf==4.25.3
- Flask-Cors==4.0.0
- fpdf2
- python-docx
- google-cloud-secret-manager
- selenium

Development dependencies:
- coverage (for test coverage analysis)
- pytest (for running tests)
- playwright (for browser automation tests)

## Troubleshooting

### "ModuleNotFoundError: No module named 'flask'"
This indicates the virtual environment is missing or not activated. Run the Quick Setup steps above.

### "Virtual environment activate script not found"
The venv directory doesn't exist. Create it with `python3 -m venv venv` from project root.

### Script failures
Ensure you're running scripts from the project root directory, not from subdirectories.