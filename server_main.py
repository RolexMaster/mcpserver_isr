# server_main.py
from fastmcp import FastMCP

# 호환 래퍼: 최신 fastmcp(name=...) / 구버전(app_name=...)
def create_app():
    try:
        return FastMCP(name="coastal-ptz-controller", version="1.0.0")
    except TypeError:
        # 구버전 fastmcp 대응
        return FastMCP(app_name="coastal-ptz-controller", version="1.0.0")

# Single MCP app (all tools register on this instance)
app = create_app()

# Import tool modules (registration happens via decorators)
import target_tools
import zone_tools
import eots_tools
import alert_tools
import system_tools

if __name__ == "__main__":
    # 코랩은 외부 포트 접근이 어려워 STDIO 권장
    USE_HTTP = True  # ← 코랩에서는 False
    if USE_HTTP:
        if hasattr(app, "run_http"):
            app.run_http(host="0.0.0.0", port=8765)
        else:
            app.run(host="0.0.0.0", port=8765)
    else:
        if hasattr(app, "run_stdio"):
            app.run_stdio()
        else:
            app.run()
