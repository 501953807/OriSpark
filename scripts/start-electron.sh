#!/usr/bin/env bash
# Start OriStudio Electron desktop app

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.env"

# Check if electron project is initialized
if [ ! -f "$ELECTRON_DIR/package.json" ]; then
    echo -e "${YELLOW}Electron project not initialized yet.${RESET}"
    echo -e "${YELLOW}This script will scaffold it when ready.${RESET}"
    exit 1
fi

cd "$ELECTRON_DIR"

# Install deps if needed
if [ ! -d "node_modules" ]; then
    npm install
fi

# Build frontend-web assets for Electron bundling
if [ ! -d "$FRONTEND_WEB_DIR/dist" ]; then
    cd "$FRONTEND_WEB_DIR" && npm run build && cd -
fi

echo -e "${GREEN}Starting Electron app...${RESET}"
npx electron .
