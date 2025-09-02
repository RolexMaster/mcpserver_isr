# server_main.py
from fastmcp import FastMCP

# Single MCP app (all tools register on this instance)
app = FastMCP(app_name="coastal-ptz-controller", version="1.0.0")

# Import tool modules (registration happens via decorators)
import target_tools
import zone_tools
import eots_tools
import alert_tools
import system_tools

if __name__ == "__main__":
    USE_HTTP = True  # flip to False for stdio
    if USE_HTTP:
        app.run_http(host="0.0.0.0", port=8765)
    else:
        app.run_stdio()
