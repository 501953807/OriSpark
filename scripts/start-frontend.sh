#!/usr/bin/env bash
# Start OriStudio Web frontend dev server

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.env"

cd "$FRONTEND_WEB_DIR"

# Install deps if needed
if [ ! -d "node_modules" ]; then
    echo -e "${CYAN}Installing frontend dependencies...${RESET}"
    npm install
fi

echo -e "${GREEN}Starting frontend at http://localhost:${FRONTEND_PORT}${RESET}"
FRONTEND_PORT="$FRONTEND_PORT" BACKEND_PORT="$BACKEND_PORT" npx vite --port "$FRONTEND_PORT"
