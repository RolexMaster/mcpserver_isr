# alert_tools.py (Alert Management)
from pydantic import BaseModel, Field
from server_main import app

class AlertRaiseParams(BaseModel):
    level: str = Field(..., pattern=r"^(info|warning|critical)$")
    message: str
    zone_id: str | None = None
    target_id: str | None = None

@app.tool(name="alert.raise", description="Raise alert")
def alert_raise(params: AlertRaiseParams):
    return {"ok": True, "alert": params.dict()}

@app.tool(name="alert.clear", description="Clear current alert")
def alert_clear():
    return {"ok": True, "cleared": True}
