#!/bin/bash

# Infrastructure Test Runner
# Tests Docker Compose services: api, db, redis, worker, flower

set -e

echo "🚀 Genesis Infrastructure Test Suite"
echo "===================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found. Please run from project root."
    exit 1
fi

# Install test dependencies
echo "📦 Installing test dependencies..."
pip install -r tests/requirements-test.txt

# Start services if not already running
echo "🐳 Checking Docker Compose services..."
if ! docker-compose ps | grep -q "Up"; then
    echo "Starting Docker Compose services..."
    docker-compose up -d
    echo "⏳ Waiting 30 seconds for services to initialize..."
    sleep 30
else
    echo "✅ Docker Compose services are already running"
fi

# Show service status
echo ""
echo "📋 Service Status:"
docker-compose ps

# Run the infrastructure tests
echo ""
echo "🧪 Running Infrastructure Tests..."
echo "================================="

# Run with pytest
python -m pytest tests/test_infrastructure.py -v -s --tb=short

# Show final service status
echo ""
echo "📋 Final Service Status:"
docker-compose ps

echo ""
echo "✅ Infrastructure test suite completed!"
