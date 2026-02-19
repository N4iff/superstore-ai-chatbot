#!/bin/bash
# Setup Script for n8n BI Chatbot
# This script initializes the entire project environment

set -e  # Exit on error

echo "========================================="
echo "n8n BI Chatbot - Project Setup"
echo "========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "Please copy .env.example to .env and configure your credentials"
    exit 1
fi

echo "✅ Found .env file"
echo ""

# Load environment variables
source .env

echo "Step 1: Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker is installed"
echo ""

echo "Step 2: Checking PostgreSQL connection to Project 1 database..."
if command -v psql &> /dev/null; then
    echo "Testing connection to ${PROJECT1_DB_HOST}:${PROJECT1_DB_PORT}/${PROJECT1_DB_NAME}..."
    
    if PGPASSWORD="${PROJECT1_DB_PASSWORD}" psql -h "${PROJECT1_DB_HOST}" -p "${PROJECT1_DB_PORT}" -U "${PROJECT1_DB_USER}" -d "${PROJECT1_DB_NAME}" -c "SELECT 1" > /dev/null 2>&1; then
        echo "✅ Connection successful"
        
        echo ""
        echo "Would you like to initialize the database (create chatbot_reader user and view)? (y/n)"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            echo "Running database initialization script..."
            PGPASSWORD="${PROJECT1_DB_PASSWORD}" psql -h "${PROJECT1_DB_HOST}" -p "${PROJECT1_DB_PORT}" -U "${PROJECT1_DB_USER}" -d "${PROJECT1_DB_NAME}" -f ops/init_db.sql
            echo "✅ Database initialized"
        else
            echo "⏭️  Skipping database initialization"
        fi
    else
        echo "⚠️  Warning: Could not connect to Project 1 database"
        echo "   Make sure your credentials in .env are correct"
        echo "   You can run ops/init_db.sql manually later"
    fi
else
    echo "⚠️  psql not found - skipping database initialization"
    echo "   You'll need to run ops/init_db.sql manually against your Project 1 database"
fi

echo ""
echo "Step 3: Starting n8n services..."
docker-compose up -d

echo ""
echo "Step 4: Waiting for n8n to be ready..."
sleep 10

echo ""
echo "Step 5: Importing workflow..."
if [ -f workflows/n8n_workflow_export.json ]; then
    echo "✅ Workflow file found"
    echo "   You'll need to import it manually:"
    echo "   1. Open http://localhost:5678"
    echo "   2. Click 'Import from File'"
    echo "   3. Select workflows/n8n_workflow_export.json"
else
    echo "⚠️  Warning: workflows/n8n_workflow_export.json not found"
fi

echo ""
echo "========================================="
echo " Setup Complete!"
echo "========================================="
echo ""
echo "n8n is now running at: http://localhost:5678"
echo ""
echo "Next steps:"
echo "  1. Import the workflow (see instructions above)"
echo "  2. Configure credentials in n8n:"
echo "     - OpenAI API"
echo "     - PostgreSQL (Project 1 database)"
echo "     - Discord Bot"
echo "     - Gmail OAuth"
echo "  3. Activate the workflow"
echo ""
echo "To stop services: ./ops/stop.sh"
echo "To view logs: docker-compose logs -f n8n"
echo ""