# server_main.py
import os
import sys
from fastmcp import FastMCP

def create_app():
    try:
        return FastMCP(name="coastal-ptz-controller", version="1.0.0")
    except TypeError:
        return FastMCP(app_name="coastal-ptz-controller", version="1.0.0")

app = create_app()

# 도구 모듈 등록(데코레이터)
import target_tools  # noqa: F401
import zone_tools    # noqa: F401
import eots_tools    # noqa: F401
import alert_tools   # noqa: F401
import system_tools  # noqa: F401

if __name__ == "__main__":
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))

    # 1) 공식 HTTP 러너가 있으면 그걸로
    try:
        app.run_http(host=HOST, port=PORT)
        sys.exit(0)
    except Exception:
        pass

    # 2) run(transport="http") 지원 버전
    try:
        app.run(transport="http", host=HOST, port=PORT)
        sys.exit(0)
    except Exception:
        pass

    # 3) ASGI 노출되어 있으면 uvicorn으로
    asgi = getattr(app, "asgi", None) or getattr(app, "app", None) or getattr(app, "asgi_app", None)
    if asgi is not None:
        import uvicorn
        uvicorn.run(asgi, host=HOST, port=PORT)
    else:
        # 4) 최후 수단: STDIO (포트 사용 안 함)
        app.run()
