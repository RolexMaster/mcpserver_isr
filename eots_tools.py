# eots_tools.py (Electro-Optical Tracking System)
from typing import Optional, Literal, Annotated, Any
from pydantic import Field
from server_main import app  # 기존 구조 유지

# 내부 상태 (단일 클라이언트 환경이라 락 불필요)
_STATE: dict[str, Any] = {"mode": "eo", "zoom": 1, "pan": 0.0, "tilt": 0.0, "tracking": False}


@app.tool(name="eots.set_mode", description="Set EO/IR/auto mode")
def eots_set_mode(
    mode: Literal["eo", "ir", "auto"]
):
    _STATE["mode"] = mode
    return {"ok": True, "mode": _STATE["mode"]}


@app.tool(name="eots.pan_tilt", description="Pan/Tilt to degrees")
def eots_pan_tilt(
    pan_deg: Annotated[float, Field(ge=-180, le=180)],
    tilt_deg: Annotated[float, Field(ge=-90, le=90)],
):
    _STATE["pan"], _STATE["tilt"] = pan_deg, tilt_deg
    return {"ok": True, "pan_deg": _STATE["pan"], "tilt_deg": _STATE["tilt"]}


@app.tool(name="eots.zoom", description="Set zoom level")
def eots_zoom(
    level: Annotated[int, Field(ge=1, le=30)]
):
    _STATE["zoom"] = level
    return {"ok": True, "zoom": _STATE["zoom"]}


@app.tool(name="eots.track", description="Enable/Disable tracking")
def eots_track(
    enable: bool,
    target_id: Optional[str] = None,
):
    if enable and not target_id:
        raise ValueError("target_id is required when enable=True")

    _STATE["tracking"] = enable
    return {"ok": True, "tracking": _STATE["tracking"], "target_id": target_id}