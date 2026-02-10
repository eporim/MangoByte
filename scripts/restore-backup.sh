#!/bin/bash

# Backup Restoration Script for MangoByte
# Usage: ./restore-backup.sh [backup_timestamp]
# Example: ./restore-backup.sh 20260210_120000

set -e

APP_DIR="/DATA/AppData/mangobyte"
DATA_DIR="$APP_DIR/data"
BACKUP_DIR="$APP_DIR/backups"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== MangoByte Backup Restoration ==="

# List available backups
echo ""
echo "Available backups:"
ls -la "$BACKUP_DIR"/botdata_*.json 2>/dev/null | awk '{print $NF}' | sed 's/.*botdata_/  /' | sed 's/.json//' || echo "  No backups found"
echo ""

if [ -z "$1" ]; then
    echo "Usage: $0 <timestamp>"
    echo "Example: $0 20260210_120000"
    exit 1
fi

TIMESTAMP=$1
BOTDATA_BACKUP="$BACKUP_DIR/botdata_${TIMESTAMP}.json"
SETTINGS_BACKUP="$BACKUP_DIR/settings_${TIMESTAMP}.json"

# Check if backup exists
if [ ! -f "$BOTDATA_BACKUP" ]; then
    echo "❌ Backup not found: $BOTDATA_BACKUP"
    exit 1
fi

echo "Stopping containers..."
cd "$SCRIPT_DIR/.." 2>/dev/null || cd "$APP_DIR/app"
docker compose down

echo "Restoring botdata.json from $BOTDATA_BACKUP..."
cp "$BOTDATA_BACKUP" "$DATA_DIR/botdata.json"

if [ -f "$SETTINGS_BACKUP" ]; then
    echo "Restoring settings.json from $SETTINGS_BACKUP..."
    cp "$SETTINGS_BACKUP" "$DATA_DIR/settings.json"
fi

echo "Starting containers..."
docker compose up -d

echo ""
echo "✅ Restoration complete!"
echo "Check logs: docker logs -f mangobyte"
