# server_main.py
import os
import sys
from fastmcp import FastMCP

# 🔌 ngrok 추가
try:
    from pyngrok import ngrok
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyngrok"])
    from pyngrok import ngrok


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

    # ngrok 터널 열기
    public_url = ngrok.connect(PORT)
    print("🌍 External URL (ngrok):", public_url)

    # FastMCP 서버 실행
    try:
        app.run_http(host=HOST, port=PORT)
    except Exception:
        try:
            app.run(transport="http", host=HOST, port=PORT)
        except Exception:
            asgi = getattr(app, "asgi", None) or getattr(app, "app", None) or getattr(app, "asgi_app", None)
            if asgi is not None:
                import uvicorn
                uvicorn.run(asgi, host=HOST, port=PORT)
            else:
                app.run()
