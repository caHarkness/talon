#!/bin/bash

TALON_PROJECT_DIR="$(dirname "$(realpath "$0")")"

source "${TALON_PROJECT_DIR}/venv.sh"

if [[ -z $1 ]]
then
    export USER_MODE=1
    cd

    export INFERENCE_URL="http://127.0.0.1:9931"
    export VERBOSE=1

    printf "\033]0;%s\a" "Talon MCP Server"
fi

if [[ ! -z $USER_MODE || "$@" =~ "--auto" ]]
then
    PORT=$(python -uB "${TALON_PROJECT_DIR}/port.py")

    python -uB "${TALON_PROJECT_DIR}/app.py" --port $PORT > "${TALON_PROJECT_DIR}/log.txt" 2>&1 &
    SERVER_PID=$!

    trap "kill -KILL $SERVER_PID" EXIT TERM QUIT

    export MCP_URL="http://127.0.0.1:$PORT/mcp"
    echo "Running MCP server on http://localhost:${PORT}/mcp"
fi

python -uB "${TALON_PROJECT_DIR}/cli.py" "$@"
