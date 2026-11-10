import os
import uvicorn
import argparse

from fastmcp                    import FastMCP
from fastmcp.server.providers   import FileSystemProvider
from starlette.middleware       import Middleware
from starlette.middleware.cors  import CORSMiddleware

script_dir      = os.path.dirname(os.path.abspath(__file__))
fs_providers    = []
for dir in [f"{script_dir}/tools", f"{script_dir}/tools_extra"]:
    if os.path.isdir(dir):
        fs_providers.append(FileSystemProvider(dir))

mcp = FastMCP(
    "Talon",
    providers=fs_providers)

# Hidden tools:
# mcp.disable(names={"change_directory"})
# mcp.disable(names={"git_apply"})
# No longer available, will remove

# Allow accessing this FastMCP server from your browser locally:
# https://github.com/PrefectHQ/fastmcp/issues/840

app = mcp.http_app(path="/mcp")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["mcp-session-id"])

if __name__ == "__main__":
    ARG_PARSER = argparse.ArgumentParser(description="Simple MCP Server")
    ARG_PARSER.add_argument("--port", type=int, help="The port to run this MCP server on", default=4470)
    ARGS = ARG_PARSER.parse_args()

    # Required to include CORS functionality:
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=ARGS.port)
