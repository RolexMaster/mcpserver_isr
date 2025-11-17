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

# =========================
# 도구: 특정 구역으로 카메라 이동
# =========================
@app.tool(
    name="zone.move_camera",
    description=(
        "Move EOTS camera view to a predefined zone by its zone_id. "
        "사용자가 \"A 구역 확인해\", \"B 구역으로 카메라 돌려\"처럼 특정 구역을 언급할 때, "
        "해당 zone_id로 카메라 시야를 그 구역으로 전환할 때 사용하는 도구이다. "
        "예: zone_id='A', 'B', 'HarborEntrance' 등."
    ),
)
def zone_move_camera(
    zone_id: str,
):
    """
    EOTS 카메라 시야를 zone_id로 정의된 구역을 바라보도록 이동시키는 도구.

    - zone_id: 'A', 'B', 'HarborEntrance' 등 미리 정의된 구역 ID 문자열
    - 내부에서는 이 zone_id를 이용해 사전에 정의된 구역 정보를 찾아
      카메라를 해당 구역 방향으로 이동시키는 로직을 구현하면 된다.
    """
