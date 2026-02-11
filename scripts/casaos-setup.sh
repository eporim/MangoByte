#!/bin/bash

# CasaOS Setup Script for MangoByte
# Run this script from the MangoByte repository directory

set -e

echo "=== MangoByte CasaOS Setup ==="

# Auto-detect paths (script is in scripts/ folder)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DATA_DIR="$APP_DIR/data"
BACKUP_DIR="$APP_DIR/backups"

echo "App directory: $APP_DIR"

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
  "odota": "YOUR_OPENDOTA_API_KEY_HERE",
  "test_guilds": [YOUR_DISCORD_SERVER_ID_HERE]
}
EOF
    echo ""
    echo "⚠️  IMPORTANT: Edit $DATA_DIR/settings.json with your actual values!"
    echo "   - Discord bot token: https://discord.com/developers/applications"
    echo "   - OpenDota API key (optional): https://www.opendota.com/api-keys"
    echo "   - Server ID: Right-click server name in Discord (with Developer Mode on) → Copy Server ID"
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
echo "1. Edit $DATA_DIR/settings.json with your Discord bot token and server ID"
echo "2. Run: cd $APP_DIR && docker compose up -d --build"
echo "3. Check logs: docker logs -f mangobyte"
echo "4. In Discord, run /setupranks to configure rank roles"
echo ""
echo "To rebuild after code changes (data is preserved):"
echo "  cd $APP_DIR && docker compose down && docker compose up -d --build"
echo ""
