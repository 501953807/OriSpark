#!/bin/bash
# OriStudio backward-compatible startup wrapper
# Delegates to scripts/start-all.sh

set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

# Parse legacy arguments for backward compatibility
ARGS=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --frontend-port|-fp)
            export FRONTEND_PORT="$2"; shift 2 ;;
        --backend-port|-bp)
            export BACKEND_PORT="$2"; shift 2 ;;
        *)
            echo "Unknown argument: $1"
            echo "Usage: $0 [--frontend-port PORT] [--backend-port PORT]"
            exit 1
            ;;
    esac
done

exec "$DIR/scripts/start-all.sh"
