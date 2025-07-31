#!/bin/bash
# WorldArchitect.AI MCP Server Deployment Script for Google Cloud Run
# Deploys the Game MCP server alongside the main web application

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ENVIRONMENT="dev" # Default environment
MCP_SERVICE_NAME="worldarchitect-mcp"

# Parse arguments
if [[ "$1" == "stable" ]]; then
    ENVIRONMENT="stable"
fi

PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="$MCP_SERVICE_NAME-$ENVIRONMENT"
IMAGE_TAG="gcr.io/$PROJECT_ID/$MCP_SERVICE_NAME:$ENVIRONMENT-latest"

echo -e "${BLUE}--- Deploying WorldArchitect MCP Server ---${NC}"
echo "Environment:      $ENVIRONMENT"
echo "Service Name:     $SERVICE_NAME"
echo "Project ID:       $PROJECT_ID"
echo "Image Tag:        $IMAGE_TAG"
echo "--------------------------"

# Create temporary deployment directory
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT
echo -e "${BLUE}Creating deployment package in $TEMP_DIR${NC}"

# Copy full package to preserve import structure
cp -r mvp_site "$TEMP_DIR/"

# Copy world directory if it exists
if [ -d "world" ]; then
    echo -e "${BLUE}Copying world directory...${NC}"
    cp -r world "$TEMP_DIR/"
fi

# Create MCP-specific requirements.txt
cat > "$TEMP_DIR/requirements.txt" << EOF
# Core MCP Server Dependencies
mcp>=1.12.2
httpx-sse>=0.4
jsonschema>=4.20.0
pydantic-settings>=2.5.2
python-multipart>=0.0.9
sse-starlette>=1.6.1
starlette>=0.27
uvicorn>=0.23.1

# WorldArchitect Dependencies
google-genai>=1.0.0
google-cloud-firestore>=2.16.0
google-auth>=2.0.0
pydantic>=2.8.0
requests>=2.31.0
flask>=3.0.0
gunicorn>=21.2.0
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
import subprocess

def main():
    # Get port from Cloud Run environment
    port = os.environ.get("PORT", "8080")
    host = "0.0.0.0"

    # Set up environment
    os.environ["PYTHONPATH"] = "/app"

    # Start MCP server with correct module path
    cmd = [sys.executable, "mvp_site/mcp_api.py", "--port", port, "--host", host]
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
(cd "$TEMP_DIR" && gcloud builds submit . --tag "$IMAGE_TAG")

echo -e "${BLUE}Deploying to Cloud Run...${NC}"
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_TAG" \
    --platform managed \
    --allow-unauthenticated \
    --set-secrets="GEMINI_API_KEY=gemini-api-key:latest,FIREBASE_CREDENTIALS_JSON=firestore-sa:latest" \
    --memory=1Gi \
    --timeout=300 \
    --min-instances=0 \
    --max-instances=5 \
    --concurrency=10 \
    --port=8080

echo -e "${BLUE}Configuring service...${NC}"
gcloud run services update "$SERVICE_NAME" \
    --platform managed \
    --timeout=300

# Get service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --platform managed --format 'value(status.url)')

echo -e "${GREEN}--- MCP Server Deployment Complete ---${NC}"
echo -e "${GREEN}Service URL: $SERVICE_URL${NC}"
echo -e "${GREEN}Health Check: $SERVICE_URL/health${NC}"
echo -e "${GREEN}JSON-RPC Endpoint: $SERVICE_URL/rpc${NC}"
echo ""
echo -e "${BLUE}Available Tools:${NC}"
echo "  • create_campaign - Create D&D campaigns"
echo "  • get_campaign_state - Retrieve campaign data"
echo "  • process_action - Handle game actions"
echo "  • export_campaign - Export to PDF/DOCX/TXT"
echo "  • get_campaigns_list - List user campaigns"
echo ""
echo -e "${BLUE}💡 To use this MCP server in Claude Code:${NC}"
echo "claude mcp add-json --scope user \"worldarchitect-cloud\" '{\"type\": \"http\", \"url\": \"$SERVICE_URL/rpc\"}'"

echo -e "${GREEN}✅ MCP server successfully deployed to Google Cloud Run!${NC}"
