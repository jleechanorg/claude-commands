#!/bin/bash

# Script to run campaign selector with proper environment

# Define vpython function locally
vpython() {
    PROJECT_ROOT_PATH="$HOME/projects/worldarchitect.ai"
    VENV_ACTIVATE_SCRIPT="$PROJECT_ROOT_PATH/venv/bin/activate"

    if [ ! -f "$VENV_ACTIVATE_SCRIPT" ]; then
        echo "Error: Virtual environment not found"
        return 1
    fi

    if [[ "$VIRTUAL_ENV" != "$PROJECT_ROOT_PATH/venv" ]]; then
        echo "Activating virtual environment..."
        source "$VENV_ACTIVATE_SCRIPT"
    fi

    python "$@"
}

# Set Firebase credentials
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.firebase/worldarchitect-ai-firebase-adminsdk.json"

# Run the campaign selector
vpython scripts/campaign_selector_0.4.py
