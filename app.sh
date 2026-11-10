#!/bin/bash
printf "\033]0;%s\a" "Talon MCP Server"

export PYTHONDONTWRITEBYTECODE=1

TALON_PROJECT_DIR="$(dirname "$(realpath "$0")")"

source "${TALON_PROJECT_DIR}/venv.sh"
python -uB "${TALON_PROJECT_DIR}/app.py" "$@"
