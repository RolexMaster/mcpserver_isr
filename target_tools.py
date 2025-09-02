# target_tools.py (Target Information Management)
from typing import Optional
from pydantic import BaseModel, Field
from server_main import app

_TARGETS = {}

class TargetRegisterParams(BaseModel):
    target_id: str = Field(..., description="Unique target identifier")
    cls: str = Field(..., description="Class: vessel/speedboat/fishing/etc.")
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    speed_kn: float = Field(0.0, ge=0)
    heading_deg: float = Field(0.0, ge=0, le=359.9)

class TargetUpdateParams(BaseModel):
    target_id: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    speed_kn: Optional[float] = None
    heading_deg: Optional[float] = None

class TargetQueryNearestParams(BaseModel):
    lat: float
    lon: float
    radius_km: float = Field(5.0, gt=0)
    limit: int = Field(5, ge=1, le=50)

@app.tool(name="target.register", description="Register a target with initial kinematics")
def target_register(params: TargetRegisterParams):
    _TARGETS[params.target_id] = params.dict()
    return {"ok": True, "stored": _TARGETS[params.target_id]}

@app.tool(name="target.update_track", description="Update target kinematics")
def target_update(params: TargetUpdateParams):
    if params.target_id not in _TARGETS:
        return {"ok": False, "error": "target_not_found"}
    for k, v in params.dict(exclude={"target_id"}).items():
        if v is not None:
            _TARGETS[params.target_id][k] = v
    return {"ok": True, "updated": _TARGETS[params.target_id]}

from math import cos, radians, sqrt
def _km(a_lat,a_lon,b_lat,b_lon):
    kx = 111 * cos(radians((a_lat+b_lat)/2))
    ky = 111
    return sqrt(((a_lon-b_lon)*kx)**2 + ((a_lat-b_lat)*ky)**2)

@app.tool(name="target.query_nearest", description="Find nearest targets within radius")
def target_query_nearest(params: TargetQueryNearestParams):
    items = []
    for t in _TARGETS.values():
        d = _km(params.lat, params.lon, t["lat"], t["lon"])
        if d <= params.radius_km:
            items.append({"target_id": t["target_id"], "cls": t["cls"], "km": round(d,2),
                          "speed_kn": t["speed_kn"], "heading_deg": t["heading_deg"]})
    items.sort(key=lambda x: x["km"])
    return {"ok": True, "count": len(items[:params.limit]), "results": items[:params.limit]}
