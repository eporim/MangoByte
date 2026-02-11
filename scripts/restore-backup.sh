#!/bin/bash

# Backup Restoration Script for MangoByte
# Usage: ./restore-backup.sh [backup_timestamp]
# Example: ./restore-backup.sh 20260210_120000

set -e

# Auto-detect paths
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DATA_DIR="$APP_DIR/data"
BACKUP_DIR="$APP_DIR/backups"

echo "=== MangoByte Backup Restoration ==="
echo "App directory: $APP_DIR"

# List available backups
echo ""
echo "Available backups:"
ls -1 "$BACKUP_DIR"/botdata_*.json 2>/dev/null | xargs -I {} basename {} .json | sed 's/botdata_/  /' || echo "  No backups found"
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
cd "$APP_DIR"
docker compose down

echo "Restoring botdata.json from $BOTDATA_BACKUP..."
cp "$BOTDATA_BACKUP" "$DATA_DIR/botdata.json"

if [ -f "$SETTINGS_BACKUP" ]; then
    read -p "Also restore settings.json? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Restoring settings.json from $SETTINGS_BACKUP..."
        cp "$SETTINGS_BACKUP" "$DATA_DIR/settings.json"
    fi
fi

echo "Starting containers..."
docker compose up -d

echo ""
echo "✅ Restoration complete!"
echo "Check logs: docker logs -f mangobyte"
