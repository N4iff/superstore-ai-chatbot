#!/bin/bash
# Start n8n BI Chatbot Services

set -e

echo "========================================="
echo "Starting n8n BI Chatbot..."
echo "========================================="
echo ""

if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "Please run ./ops/setup.sh first"
    exit 1
fi

docker-compose up -d

echo ""
echo "✅ Services started successfully"
echo ""
echo "n8n UI: http://localhost:5678"
echo ""
echo "To view logs: docker-compose logs -f n8n"
echo "To stop: ./ops/stop.sh"
echo ""