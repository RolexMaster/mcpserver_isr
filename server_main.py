"""
FastMCP 2.12.0 / Streamable-HTTP 서버 엔트리포인트
- 서버명: coastal-ptz-controller
- 엔드포인트: /mcp
- eots_tools_core 의 @app.tool 데코레이터가 'server_main.app' 를 참조하는 구조를 지원합니다.
"""

from __future__ import annotations

import os
import sys
import logging
from typing import Any

# FastMCP 2.12.0 기준
try:
    from fastmcp import FastMCP
except ImportError as e:
    raise RuntimeError("fastmcp 패키지가 필요합니다. pip install fastmcp") from e


# -----------------------------------------------------------------------------
# 애플리케이션 생성 (버전 차이 호환)
# -----------------------------------------------------------------------------
def create_app() -> FastMCP:
    name = os.getenv("MCP_APP_NAME", "coastal-ptz-controller")
    version = os.getenv("MCP_APP_VERSION", "1.0.0")
    try:
        # 신규 시그니처
        return FastMCP(name=name, version=version)
    except TypeError:
        # 구버전 호환
        return FastMCP(app_name=name, version=version)


# 전역 app (툴들이 from server_main import app 로 접근하므로 반드시 모듈 전역에 있어야 함)
app = create_app()

# 중요: __main__로 실행될 때도 툴 모듈에서 from server_main import app 가
# 동일 객체를 바라보도록 모듈 별칭을 주입 (이중 import로 다른 app 인스턴스 생기는 문제 방지)
sys.modules["server_main"] = sys.modules[__name__]

# -----------------------------------------------------------------------------
# 로깅 세팅
# -----------------------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("server_main")


# -----------------------------------------------------------------------------
# 툴 모듈 import
# - eots_tools_core 만 사용
# -----------------------------------------------------------------------------
import eots_tools_core  # noqa: F401

# 예전 구조 (여러 모듈 사용)는 전부 주석 처리
# import alert_tools  # noqa: F401
# import eots_tools   # noqa: F401
# import target_tools # noqa: F401
# import system_tools # noqa: F401
# import zone_tools   # noqa: F401

# register(app) 패턴도 현재는 사용하지 않음
# for _mod in (alert_tools, eots_tools, target_tools, system_tools, zone_tools):
#     if hasattr(_mod, "register") and callable(getattr(_mod, "register")):
#         try:
#             _mod.register(app)  # 필요 시만 사용 (중복 등록에 주의)
#             logger.info("Registered tools via %s.register(app)", _mod.__name__)
#         except Exception as ex:
#             logger.warning("register(app) 호출 중 경고: %s: %s", _mod.__name__, ex)


# -----------------------------------------------------------------------------
# (옵션) 최소 헬스체크 툴 하나 등록해 두면 점검에 편리
# -----------------------------------------------------------------------------
@app.tool(name="health", description="서버 헬스체크: 항상 ok=True 반환")
def health() -> dict[str, Any]:
    return {"ok": True}


# -----------------------------------------------------------------------------
# 서버 실행
# -----------------------------------------------------------------------------
def main() -> None:
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))
    path = os.getenv("MCP_PATH", "/mcp")  # 배너와 동일 엔드포인트

    logger.info("Starting FastMCP (HTTP Streamable) on %s:%d%s", host, port, path)

    # FastMCP 2.x 의 HTTP 실행 시그니처가 버전에 따라 path/route 명이 다를 수 있어 방어적으로 처리
    try:
        # 선호: transport 인자를 받는 런타임
        app.run(transport="http", host=host, port=port, path=path)
    except TypeError:
        try:
            # 일부 버전은 path 대신 route 사용
            app.run(transport="http", host=host, port=port, route=path)
        except TypeError:
            # 더 구버전일 경우 전용 러너가 있을 수 있음
            try:
                # hypothetically: app.run_http(...)
                run_http = getattr(app, "run_http")
                run_http(host=host, port=port, path=path)  # type: ignore[attr-defined]
            except Exception:
                # 최후의 수단: uvicorn 직접 구동 (FastMCP가 ASGI 앱 제공 시)
                try:
                    import uvicorn  # type: ignore
                except Exception as e:
                    logger.error("HTTP 실행 실패: fastmcp/uvicorn 실행 경로를 확인하세요. %s", e)
                    raise
                # FastMCP가 ASGI 앱을 노출하는 속성명은 버전에 따라 다를 수 있음
                # 가장 흔한 이름들을 시도
                for attr in ("asgi", "app", "http_app"):
                    if hasattr(app, attr):
                        asgi_app = getattr(app, attr)
                        logger.warning("Fallback to uvicorn.run(%s)", attr)
                        uvicorn.run(asgi_app, host=host, port=port)  # type: ignore[misc]
                        return
                raise RuntimeError(
                    "FastMCP HTTP 실행 경로를 찾지 못했습니다. fastmcp 버전과 run 파라미터(path/route)를 확인하세요."
                )


if __name__ == "__main__":
    main()
