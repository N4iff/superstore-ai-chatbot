#!/bin/bash
# Stop n8n BI Chatbot Services

echo "========================================="
echo "Stopping n8n BI Chatbot..."
echo "========================================="
echo ""

docker-compose down

echo ""
echo "✅ Services stopped successfully"
echo ""