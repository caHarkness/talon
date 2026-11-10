#!/bin/bash

SAVED_DIRECTORY="$(pwd)"

cd "$(dirname "$0")"

CREATE_VENV=0

if [[ ! -d venv ]]
then
    python3 -m venv venv || python -m venv venv
    CREATE_VENV=1
fi

source ./venv/bin/activate > /dev/null 2>/dev/null
source ./venv/Scripts/activate > /dev/null 2>/dev/null

export IS_LINUX=0
export IS_WINDOWS=0

if [[ -d ./venv/Scripts ]]
then
    export IS_LINUX=0
    export IS_WINDOWS=1
else
    export IS_LINUX=1
    export IS_WINDOWS=0
fi

if [[ $CREATE_VENV -eq 1 ]]
then
    # For the FastMCP server:
    pip install fastmcp
    # Removed experimental packages for now:
    # pip install requests pillow pyautogui discord
fi

cd "${SAVED_DIRECTORY}"
