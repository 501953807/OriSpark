#!/usr/bin/env bash
# Start Celery worker and beat

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.env"

cd "$BACKEND_DIR"

# Check Redis availability
if ! redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping &>/dev/null; then
    echo -e "${YELLOW}Warning: Redis not responding at ${REDIS_HOST}:${REDIS_PORT}${RESET}"
    echo -e "${YELLOW}Starting Celery anyway (tasks will queue until Redis is available)${RESET}"
fi

export CELERY_BROKER_URL="redis://${CELERY_REDIS_URL}"
export CELERY_RESULT_BACKEND="redis://${CELERY_REDIS_URL}"

echo -e "${GREEN}Starting Celery worker...${RESET}"
celery -A app.tasks.celery_app worker --loglevel=info &
WORKER_PID=$!

echo -e "${GREEN}Starting Celery beat...${RESET}"
celery -A app.tasks.celery_app beat --loglevel=info &
BEAT_PID=$!

trap "kill $WORKER_PID $BEAT_PID 2>/dev/null; exit" INT TERM EXIT
wait
