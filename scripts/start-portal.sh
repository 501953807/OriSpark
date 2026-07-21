#!/usr/bin/env bash
# Start OriSpark Nuxt 3 portal

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.env"

# Check if Nuxt project is initialized
if [ ! -f "$FRONTEND_NUXT_DIR/nuxt.config.ts" ]; then
    echo -e "${YELLOW}Nuxt portal project not initialized yet.${RESET}"
    echo -e "${YELLOW}Run: make portal-init${RESET}"
    exit 1
fi

cd "$FRONTEND_NUXT_DIR"

# Install deps if needed
if [ ! -d "node_modules" ]; then
    npm install
fi

echo -e "${GREEN}Starting Nuxt portal at http://localhost:${PORTAL_PORT}${RESET}"
PORT="$PORTAL_PORT" npx nuxt dev
