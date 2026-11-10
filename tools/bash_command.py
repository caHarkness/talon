import sys
import subprocess

from fastmcp.tools import tool

@tool
def bash_command(command: str) -> dict:
    """
    Run a command with bash only if the command being run is known to exit within a reasonable amount of time. Do not use absolute paths in commands unless explicitly told to do so. Assume the user wants to work within the current working directory and use relative pathing by default.
    """
    try:
        kwargs = dict(
            stdin=subprocess.DEVNULL,
            timeout=30,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace")

        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(["bash", "-c", command], **kwargs)

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }

    except Exception as x:
        return {
            "exception": str(x)
        }
