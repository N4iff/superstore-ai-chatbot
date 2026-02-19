#!/bin/bash
# Backup Script for n8n BI Chatbot
# Creates backups of workflows and n8n database

set -e

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "========================================="
echo "Creating Backup..."
echo "========================================="
echo ""
echo "Backup location: $BACKUP_DIR"
echo ""

# Backup n8n database
echo "Step 1: Backing up n8n database..."
docker-compose exec -T n8n_db pg_dump -U n8n n8n > "$BACKUP_DIR/n8n_database.sql"
echo "✅ Database backup complete"

# Copy workflow files
echo ""
echo "Step 2: Backing up workflows..."
cp workflows/*.json "$BACKUP_DIR/" 2>/dev/null || echo "⚠️  No workflow files found"
echo "✅ Workflow backup complete"

# Copy environment file (without sensitive data)
echo ""
echo "Step 3: Creating environment template..."
grep -v "PASSWORD\|KEY" .env > "$BACKUP_DIR/.env.template" 2>/dev/null || echo "⚠️  No .env file found"
echo "✅ Environment template created"

echo ""
echo "========================================="
echo "✅ Backup Complete!"
echo "========================================="
echo ""
echo "Backup saved to: $BACKUP_DIR"
echo ""
echo "Contents:"
ls -lh "$BACKUP_DIR"
echo ""