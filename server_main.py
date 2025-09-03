# server_main.py  — cloudflared Quick Tunnel 버전
import os
import re
import sys
import time
import threading
import subprocess
from shutil import which

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


HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

def run_app_blocking():
    """FastMCP 서버를 (가능한 러너로) 실행 — 블로킹 함수."""
    # 1) 공식 HTTP 러너
    try:
        app.run_http(host=HOST, port=PORT)
        return
    except Exception:
        pass

    # 2) transport="http"
    try:
        app.run(transport="http", host=HOST, port=PORT)
        return
    except Exception:
        pass

    # 3) ASGI -> uvicorn
    asgi = getattr(app, "asgi", None) or getattr(app, "app", None) or getattr(app, "asgi_app", None)
    if asgi is not None:
        import uvicorn
        uvicorn.run(asgi, host=HOST, port=PORT)
        return

    # 4) 최후 수단: STDIO
    app.run()


def ensure_cloudflared_installed():
    """cloudflared 바이너리를 보장 (없으면 pip 설치)."""
    if which("cloudflared"):
        return
    # 일부 환경에서는 패키지명이 cloudflared (python 래퍼가 바이너리 제공)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "cloudflared"])
    if not which("cloudflared"):
        raise RuntimeError("cloudflared 설치 실패 — 수동 설치가 필요합니다.")


def start_quicktunnel(local_port: int) -> str:
    """
    cloudflared Quick Tunnel 실행 후 공개 URL 반환.
    출력 로그에서 https://xxxx.trycloudflare.com 추출.
    """
    ensure_cloudflared_installed()

    # --no-autoupdate: Colab 등 임시 환경에서 자동업데이트 비활성
    cmd = [
        "cloudflared", "tunnel",
        "--url", f"http://127.0.0.1:{local_port}",
        "--no-autoupdate",
    ]
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1
    )

    public_url = None
    url_pat = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com", re.I)

    # 몇 초 동안 URL을 기다린다.
    start = time.time()
    while time.time() - start < 30:
        line = proc.stdout.readline()
        if not line:
            time.sleep(0.1)
            continue
        # print(line, end="")  # 필요 시 디버그
        m = url_pat.search(line)
        if m:
            public_url = m.group(0)
            break

        # 비정상 종료 체크
        if proc.poll() is not None:
            raise RuntimeError("cloudflared 프로세스가 예기치 않게 종료되었습니다.")

    if not public_url:
        raise TimeoutError("cloudflared 공개 URL을 얻지 못했습니다.")

    return public_url


if __name__ == "__main__":
    # 1) FastMCP 서버를 백그라운드 스레드로 실행
    t = threading.Thread(target=run_app_blocking, daemon=True)
    t.start()

    # 서버가 바인딩될 시간을 약간 준다 (짧게 대기)
    time.sleep(1.5)

    # 2) cloudflared Quick Tunnel 시작
    try:
        public_url = start_quicktunnel(PORT)
    except Exception as e:
        print(f"[cloudflared] 터널 시작 실패: {e}", file=sys.stderr)
        # 터널 없이도 로컬에서 계속 구동되도록 메인 스레드 block
        t.join()
        sys.exit(1)

    # 3) 접속 정보 출력
    print("\n" + "─" * 80)
    print("🌐 Cloudflared Quick Tunnel Ready")
    print(f"   • Local:   http://127.0.0.1:{PORT}")
    print(f"   • Public:  {public_url}")
    print(f"   • MCP URL: {public_url}/mcp")
    print("   (요청 시 반드시 Accept: application/json, text/event-stream 헤더 포함)")
    print("─" * 80 + "\n")

    # 4) 메인 스레드 대기 (서버 스레드 join)
    try:
        t.join()
    except KeyboardInterrupt:
        pass
