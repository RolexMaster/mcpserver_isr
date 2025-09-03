# mcpclient_test.py
import os
import json
import asyncio
from typing import Any, Optional

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

# 터널 URL은 환경변수로도 바꿀 수 있게
MCP_URL = os.getenv("MCP_URL", "https://distributors-fy-dome-bosnia.trycloudflare.com/mcp")


# ---------- 유틸 ----------
def pretty(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except TypeError:
        # pydantic v2 model or similar
        dump = getattr(obj, "model_dump", None)
        if callable(dump):
            return json.dumps(dump(), ensure_ascii=False, indent=2)
        dct = getattr(obj, "__dict__", None)
        if isinstance(dct, dict):
            return json.dumps(dct, ensure_ascii=False, indent=2)
        return str(obj)


def first_attr(obj: Any, names: list[str], default=None):
    for n in names:
        if hasattr(obj, n):
            return getattr(obj, n)
    return default


def to_schema_json(schema_obj: Any) -> Optional[dict]:
    """툴의 입력 스키마를 dict로 변환 (가능한 여러 케이스 방어)"""
    if schema_obj is None:
        return None
    # pydantic model?
    dump = getattr(schema_obj, "model_dump", None)
    if callable(dump):
        return dump()
    # dataclass-like
    if hasattr(schema_obj, "__dict__"):
        try:
            json.dumps(schema_obj.__dict__)  # serializable?
            return schema_obj.__dict__
        except Exception:
            pass
    # 이미 dict인 경우
    if isinstance(schema_obj, dict):
        return schema_obj
    # 마지막 수단: 문자열화
    return {"raw": str(schema_obj)}


async def main():
    transport = StreamableHttpTransport(url=MCP_URL)
    client = Client(transport)

    async with client:
        # 연결 확인
        await client.ping()
        print("[OK] ping")

        # ----------- Tools -----------
        tools = await client.list_tools()
        tool_names = [getattr(t, "name", "<noname>") for t in tools]
        print("\n[tools]", tool_names)

        # 각 툴의 설명/스키마 출력
        print("\n[tool schemas]")
        for t in tools:
            name = first_attr(t, ["name", "tool", "id"], "<noname>")
            desc = first_attr(t, ["description", "desc"], "")
            # 스키마 후보 속성들: input_schema / inputSchema / schema / parameters ...
            schema_obj = first_attr(t, ["input_schema", "inputSchema", "schema", "parameters"], None)
            schema_json = to_schema_json(schema_obj)

            print(f"\n== {name}")
            if desc:
                print(f" - description: {desc}")
            if schema_json is not None:
                print(pretty(schema_json))
            else:
                print(" (no input schema)")

        # ----------- Resources -----------
        resources = await client.list_resources()
        res_uris = [first_attr(r, ["uri"], "") for r in resources]
        print("\n[resources]", res_uris)

        # 있으면 첫 리소스를 읽어서 보여주기
        if res_uris:
            uri0 = res_uris[0]
            try:
                content = await client.read_resource(uri0)
                print(f"\n[read_resource] {uri0}")
                print(pretty(content))
            except Exception as e:
                print(f"[read_resource error] {uri0}: {e}")

        # ----------- 샘플 툴 호출 (있을 때만 안전 호출) -----------
        async def try_call(name: str, args: dict):
            if name in tool_names:
                try:
                    res = await client.call_tool(name, args)
                    print(f"\n[call_tool] {name} {args}")
                    # fastmcp ToolResult는 .data 등을 가질 수 있음
                    data = getattr(res, "data", res)
                    print(pretty(data))
                except Exception as e:
                    print(f"[call_tool error] {name}: {e}")

        # 파라미터 없는 것으로 추정되는 기본 툴들 먼저
        await try_call("health", {})
        await try_call("system.status", {})
        await try_call("zone.list", {})

        # EOTS 예시 (스키마에 맞춰 조정하세요)
        await try_call("eots.set_mode", {"mode": "ir"})
        await try_call("eots.pan_tilt", {"pan_deg": 10.0, "tilt_deg": -5.0})
        await try_call("eots.zoom", {"level": 3})
        await try_call("eots.track", {"enable": False})

        # 필요 시 target.* / alert.* / zone.* 등도 try_call로 이어서 호출하면 됩니다.


if __name__ == "__main__":
    asyncio.run(main())