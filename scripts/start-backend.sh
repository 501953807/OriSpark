#!/usr/bin/env bash
# Start OriStudio backend API server

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.env"

cd "$BACKEND_DIR"

# Ensure venv exists
if [ ! -d "venv" ]; then
    echo -e "${CYAN}Creating Python virtual environment...${RESET}"
    "$PYTHON_BIN" -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt

echo -e "${GREEN}Starting backend at http://${BACKEND_HOST}:${BACKEND_PORT}${RESET}"
echo -e "${CYAN}API docs: http://${BACKEND_HOST}:${BACKEND_PORT}/docs${RESET}"
uvicorn app.main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" --reload
