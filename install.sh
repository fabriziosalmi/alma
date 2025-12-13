#!/bin/bash
set -e

echo "🐳 ALMA Zero-Config Installer"
echo "============================="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop first."
    exit 1
fi

echo "🚀 Building containers... (this may take a few minutes)"
docker compose -f compose.yml build

echo "✨ Starting ALMA Stack..."
docker compose -f compose.yml up -d

echo "============================="
echo "✅ ALMA is running!"
echo "👉 Dashboard: http://localhost"
echo "👉 API Docs:  http://localhost/api/v1/docs"
echo ""
echo "To stop: docker compose down"
echo "To view logs: docker compose logs -f"
