#!/usr/bin/env bash
# Start all OriStudio services

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.env"

PIDS=()

cleanup() {
    echo -e "${YELLOW}Shutting down all services...${RESET}"
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null
    exit
}
trap cleanup INT TERM EXIT

echo -e "${GREEN}=== OriStudio Starting ===${RESET}"
echo ""

# 1. Backend
echo -e "${CYAN}[1/4] Backend API${RESET}"
scripts/start-backend.sh &
PIDS+=($!)

# Wait for backend to be ready
echo -e "${YELLOW}Waiting for backend to start...${RESET}"
for i in {1..30}; do
    if curl -s "http://${BACKEND_HOST}:${BACKEND_PORT}/api/health" &>/dev/null; then
        echo -e "${GREEN}Backend ready!${RESET}"
        break
    fi
    sleep 1
done

# 2. Frontend Web
echo -e "${CYAN}[2/4] Frontend Web${RESET}"
scripts/start-frontend.sh &
PIDS+=($!)

# 3. Celery (optional)
if command -v celery &>/dev/null; then
    echo -e "${CYAN}[3/4] Celery${RESET}"
    scripts/start-celery.sh &
    PIDS+=($!)
else
    echo -e "${YELLOW}Celery not installed, skipping${RESET}"
fi

# 4. Portal (if initialized)
if [ -f "$FRONTEND_NUXT_DIR/nuxt.config.ts" ]; then
    echo -e "${CYAN}[4/4] Nuxt Portal${RESET}"
    scripts/start-portal.sh &
    PIDS+=($!)
fi

echo ""
echo -e "${GREEN}=== All Services Started ===${RESET}"
echo "  Backend:  http://${BACKEND_HOST}:${BACKEND_PORT}"
echo "  Frontend: http://localhost:${FRONTEND_PORT}"
echo "  API Docs: http://${BACKEND_HOST}:${BACKEND_PORT}/docs"
echo ""
echo "Press Ctrl+C to stop all services"

wait
