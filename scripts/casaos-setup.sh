#!/bin/bash

# CasaOS Setup Script for MangoByte

set -e

echo "=== MangoByte CasaOS Setup ==="

# Define paths
APP_DIR="/DATA/AppData/mangobyte"
DATA_DIR="$APP_DIR/data"
BACKUP_DIR="$APP_DIR/backups"

# Create directories
echo "Creating directories..."
mkdir -p "$DATA_DIR"
mkdir -p "$BACKUP_DIR"

# Check if settings.json exists
if [ ! -f "$DATA_DIR/settings.json" ]; then
    echo ""
    echo "Creating settings.json template..."
    cat > "$DATA_DIR/settings.json" << 'EOF'
{
  "token": "YOUR_DISCORD_BOT_TOKEN_HERE",
  "odota": "YOUR_OPENDOTA_API_KEY_HERE"
}
EOF
    echo ""
    echo "⚠️  IMPORTANT: Edit $DATA_DIR/settings.json with your actual tokens!"
    echo "   - Discord bot token: https://discord.com/developers/applications"
    echo "   - OpenDota API key (optional): https://www.opendota.com/api-keys"
else
    echo "settings.json already exists, skipping..."
fi

# Create empty botdata.json if it doesn't exist
if [ ! -f "$DATA_DIR/botdata.json" ]; then
    echo "Creating empty botdata.json..."
    echo '{}' > "$DATA_DIR/botdata.json"
else
    echo "botdata.json already exists, skipping..."
fi

# Set permissions
echo "Setting permissions..."
chmod 644 "$DATA_DIR/settings.json"
chmod 644 "$DATA_DIR/botdata.json"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit $DATA_DIR/settings.json with your Discord bot token"
echo "2. Run: docker compose up -d --build"
echo "3. Check logs: docker logs -f mangobyte"
echo "4. In Discord, run /setupranks to configure rank roles"
echo ""
