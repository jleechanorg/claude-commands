#!/bin/bash
# WorldArchitect.AI MCP Server Deployment Script for Google Cloud Run
# Deploys the Game MCP server alongside the main web application

set -euo pipefail

source "$(dirname "$0")/scripts/deploy_common.sh"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
YELLOW='\033[1;33m'

ENVIRONMENT="dev" # Default environment
MCP_SERVICE_NAME="worldarchitect-mcp"

# Parse arguments
if [[ "${1:-}" == "stable" ]]; then
    ENVIRONMENT="stable"
fi

PROJECT_ID=$(deploy_common::get_project_id)
SERVICE_NAME="$MCP_SERVICE_NAME-$ENVIRONMENT"
IMAGE_TAG="gcr.io/$PROJECT_ID/$MCP_SERVICE_NAME:$ENVIRONMENT-latest"

echo -e "${BLUE}--- Deploying WorldArchitect MCP Server ---${NC}"
echo "Environment:      $ENVIRONMENT"
echo "Service Name:     $SERVICE_NAME"
echo "Project ID:       $PROJECT_ID"
echo "Image Tag:        $IMAGE_TAG"
echo "--------------------------"

SECRET_BINDINGS=()

if gcloud secrets describe gemini-api-key --project "$PROJECT_ID" >/dev/null 2>&1; then
    SECRET_BINDINGS+=("GEMINI_API_KEY=gemini-api-key:latest")
else
    echo -e "${YELLOW}Warning: Secret 'gemini-api-key' not found; Gemini integration will be disabled.${NC}"
fi

if gcloud secrets describe firestore-sa --project "$PROJECT_ID" >/dev/null 2>&1; then
    SECRET_BINDINGS+=("FIREBASE_CREDENTIALS_JSON=firestore-sa:latest")
else
    echo -e "${YELLOW}Warning: Secret 'firestore-sa' not found; deploying without Firestore credentials.${NC}"
fi

SECRET_SPEC=""
if ((${#SECRET_BINDINGS[@]} > 0)); then
    SECRET_SPEC=$(IFS=','; printf '%s' "${SECRET_BINDINGS[*]}")
fi

# Create temporary deployment directory
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT
echo -e "${BLUE}Creating deployment package in $TEMP_DIR${NC}"

# Copy full package to preserve import structure (excluding venv symlink)
rsync -a --exclude='venv' mvp_site "$TEMP_DIR/"

# Copy world directory if it exists
if [ -d "world" ]; then
    echo -e "${BLUE}Copying world directory...${NC}"
    cp -r world "$TEMP_DIR/"
fi

# Create MCP-specific requirements.txt by extending the app's baseline set
cp mvp_site/requirements.txt "$TEMP_DIR/requirements.txt"
runtime_requirements="$TEMP_DIR/requirements.txt"
python3 - "$runtime_requirements" <<'PY'
import pathlib
import re
import sys

req_path = pathlib.Path(sys.argv[1])
patterns = re.compile(r"^(ruff|isort|mypy|bandit|types-|pytest|playwright)", re.IGNORECASE)
lines = [line.rstrip() for line in req_path.read_text().splitlines()]
filtered = [line for line in lines if line and not patterns.match(line.strip())]
req_path.write_text("\n".join(filtered) + "\n")
PY
cat << 'EOF' >> "$TEMP_DIR/requirements.txt"

# MCP transport dependencies
httpx-sse>=0.4
jsonschema>=4.20.0
pydantic-settings>=2.5.2
python-multipart>=0.0.9
sse-starlette>=1.6.1
starlette>=0.27
uvicorn>=0.23.1

# Ensure MCP server tooling stays current
mcp>=1.12.2
EOF

# Create startup script for Cloud Run
cat > "$TEMP_DIR/startup.py" << 'EOF'
#!/usr/bin/env python3
"""
Cloud Run startup wrapper for MCP API server.
Handles environment variable configuration and port binding.
"""

import os
import sys

def main():
    # Get port from Cloud Run environment
    port = os.environ.get("PORT", "8080")
    host = "0.0.0.0"

    # Set up environment
    os.environ["PYTHONPATH"] = "/app"

    # Start MCP server with correct module path
    cmd = [
        sys.executable,
        "mvp_site/mcp_api.py",
        "--port",
        port,
        "--host",
        host,
        "--http-only",
    ]
    print(f"Starting MCP server: {' '.join(cmd)}")

    # Replace current process with MCP server
    os.execvp(sys.executable, cmd)

if __name__ == "__main__":
    main()
EOF

# Update Dockerfile to use startup script
cat > "$TEMP_DIR/Dockerfile" << EOF
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set environment variables
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \\
    CMD curl -f http://localhost:8080/health || exit 1

# Run startup script
CMD ["python", "startup.py"]
EOF

chmod +x "$TEMP_DIR/startup.py"

echo -e "${BLUE}Building container image...${NC}"
deploy_common::submit_build "$TEMP_DIR" "$IMAGE_TAG"

echo -e "${BLUE}Deploying to Cloud Run...${NC}"
deploy_common::deploy_service \
    "$SERVICE_NAME" \
    "$IMAGE_TAG" \
    "$SECRET_SPEC" \
    "1Gi" \
    "300" \
    "0" \
    "5" \
    "10" \
    "us-central1" \
    "8080"

echo -e "${BLUE}Configuring service...${NC}"
deploy_common::update_service_timeout "$SERVICE_NAME" "300" "us-central1"

# Get service URL
SERVICE_URL=$(deploy_common::service_url "$SERVICE_NAME" "us-central1")

echo -e "${GREEN}--- MCP Server Deployment Complete ---${NC}"
echo -e "${GREEN}Service URL: $SERVICE_URL${NC}"
echo -e "${GREEN}Health Check: $SERVICE_URL/health${NC}"
echo -e "${GREEN}JSON-RPC Endpoint: $SERVICE_URL/mcp${NC}"
echo ""
echo -e "${BLUE}Available Tools:${NC}"
echo "  • create_campaign - Create D&D campaigns"
echo "  • get_campaign_state - Retrieve campaign data"
echo "  • process_action - Handle game actions"
echo "  • export_campaign - Export to PDF/DOCX/TXT"
echo "  • get_campaigns_list - List user campaigns"
echo ""
echo -e "${BLUE}💡 To use this MCP server in Claude Code:${NC}"
echo "claude mcp add-json --scope user \"worldarchitect-cloud\" '{\"type\": \"http\", \"url\": \"$SERVICE_URL/mcp\"}'"

echo -e "${GREEN}✅ MCP server successfully deployed to Google Cloud Run!${NC}"
