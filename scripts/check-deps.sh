#!/usr/bin/env bash
# OriStudio dependency checker

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.env"

RED=$ANSI_RED; GREEN=$ANSI_GREEN; YELLOW=$ANSI_YELLOW; RESET=$ANSI_RESET

check_cmd() {
    if command -v "$1" &>/dev/null; then
        echo -e "${GREEN}✓${RESET} $1 found: $(command -v "$1")"
    else
        echo -e "${RED}✗${RESET} $1 not found"
    fi
}

echo "=== OriStudio Environment Check ==="
echo ""

check_cmd "$PYTHON_BIN"
check_cmd "$NODE_BIN"
check_cmd "$NPM_BIN"
check_cmd pip || true

if command -v redis-server &>/dev/null; then
    echo -e "${GREEN}✓${RESET} redis-server found: $(command -v redis-server)"
else
    echo -e "${YELLOW}!${RESET} redis-server not found (optional, use Docker or install: brew install redis)"
fi

if command -v electron &>/dev/null || [ -d "$ELECTRON_DIR/node_modules/electron" ]; then
    echo -e "${GREEN}✓${RESET} Electron available"
else
    echo -e "${YELLOW}!${RESET} Electron not installed (frontend-electron/) — skip make electron until initialized"
fi

if [ -d "$FRONTEND_NUXT_DIR/.nuxt" ] || [ -f "$FRONTEND_NUXT_DIR/nuxt.config.ts" ]; then
    echo -e "${GREEN}✓${RESET} Nuxt portal project initialized"
else
    echo -e "${YELLOW}!${RESET} Nuxt portal is a skeleton — run make portal-init first"
fi

if [ -f "$MINIPROGRAM_DIR/project.config.json" ]; then
    echo -e "${GREEN}✓${RESET} WeChat mini-program project initialized"
else
    echo -e "${YELLOW}!${RESET} WeChat mini-program is a skeleton — not ready for local dev"
fi

echo ""
echo "Configuration:"
echo "  Backend:  http://${BACKEND_HOST}:${BACKEND_PORT}"
echo "  Frontend: http://localhost:${FRONTEND_PORT}"
echo "  Portal:   http://localhost:${PORTAL_PORT}"
