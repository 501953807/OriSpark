#!/usr/bin/env bash
# Start WeChat mini-program development

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.env"

# Check if mini-program project is initialized
if [ ! -f "$MINIPROGRAM_DIR/project.config.json" ]; then
    echo -e "${YELLOW}WeChat mini-program project not initialized yet.${RESET}"
    echo -e "${YELLOW}This is a Phase 3 feature. See frontend-miniprogram/README.md${RESET}"
    exit 1
fi

cd "$MINIPROGRAM_DIR"

# Check for WeChat DevTools
if command -v wechatdevtools &>/dev/null; then
    wechatdevtools open .
elif [ -f "package.json" ]; then
    # Try uni-app or other framework
    npm run dev:mp-weixin
else
    echo -e "${YELLOW}Open WeChat DevTools manually and load: $MINIPROGRAM_DIR${RESET}"
fi
