# eots_tools.py (Electro-Optical Tracking System)
from typing import Optional
from pydantic import BaseModel, Field
from server_main import app

_DEF = {"mode":"eo", "zoom": 1, "pan": 0.0, "tilt": 0.0, "tracking": False}

class EotsModeParams(BaseModel):
    mode: str = Field(..., pattern=r"^(eo|ir|auto)$")

class EotsPanTiltParams(BaseModel):
    pan_deg: float = Field(..., ge=-180, le=180)
    tilt_deg: float = Field(..., ge=-90, le=90)

class EotsZoomParams(BaseModel):
    level: int = Field(..., ge=1, le=30)

class EotsTrackParams(BaseModel):
    enable: bool
    target_id: Optional[str] = None

@app.tool(name="eots.set_mode", description="Set EO/IR/auto mode")
def eots_set_mode(params: EotsModeParams):
    _DEF["mode"] = params.mode
    return {"ok": True, "mode": _DEF["mode"]}

@app.tool(name="eots.pan_tilt", description="Pan/Tilt to degrees")
def eots_pan_tilt(params: EotsPanTiltParams):
    _DEF["pan"], _DEF["tilt"] = params.pan_deg, params.tilt_deg
    return {"ok": True, "pan_deg": _DEF["pan"], "tilt_deg": _DEF["tilt"]}

@app.tool(name="eots.zoom", description="Set zoom level")
def eots_zoom(params: EotsZoomParams):
    _DEF["zoom"] = params.level
    return {"ok": True, "zoom": _DEF["zoom"]}

@app.tool(name="eots.track", description="Enable/Disable tracking")
def eots_track(params: EotsTrackParams):
    _DEF["tracking"] = params.enable
    return {"ok": True, "tracking": _DEF["tracking"], "target_id": params.target_id}
