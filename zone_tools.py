# zone_tools.py (Zone Management)
from typing import Optional, Literal
from pydantic import BaseModel, Field
from server_main import app

_ZONES = {}
_RULES = {}

class ZoneDefineParams(BaseModel):
    zone_id: str
    type: Literal["restricted","harbor","lane","anchor"] = "restricted"
    polygon: list = Field(..., description="[[lat,lon], ...] closed polygon")

class ZoneListParams(BaseModel):
    type: Optional[str] = None

class ZoneRuleParams(BaseModel):
    zone_id: str
    rule: Literal["no_entry","speed_limit","night_ir_only","zoom_cap"]
    value: Optional[float] = None

@app.tool(name="zone.define", description="Create/update a geofence zone")
def zone_define(params: ZoneDefineParams):
    _ZONES[params.zone_id] = params.dict()
    return {"ok": True, "zone": _ZONES[params.zone_id]}

@app.tool(name="zone.list", description="List zones")
def zone_list(params: ZoneListParams):
    zs = list(_ZONES.values())
    if params.type:
        zs = [z for z in zs if z["type"] == params.type]
    return {"ok": True, "zones": zs}

@app.tool(name="zone.set_rule", description="Attach policy to a zone")
def zone_set_rule(params: ZoneRuleParams):
    if params.zone_id not in _ZONES:
        return {"ok": False, "error": "zone_not_found"}
    _RULES[params.zone_id] = {"rule": params.rule, "value": params.value}
    return {"ok": True, "zone_id": params.zone_id, "rule": _RULES[params.zone_id]}
