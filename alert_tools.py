# alert_tools.py (Alert Management)
from pydantic import BaseModel, Field
from server_main import app

class AlertRaiseParams(BaseModel):
    level: str = Field(..., pattern=r"^(info|warning|critical)$")
    message: str
    zone_id: str | None = None
    target_id: str | None = None

@app.tool(
    name="alert.raise",
    description=(
        "이 함수를 호출하면 운용자(사용자)의 모니터 화면에 알림 팝업이 표시된다. "
        "알림 창에 표시될 문구(제목/내용/심각도 등)는 AlertRaiseParams 파라미터로 전달받아 사용한다. "
        "카메라 움직임이나 모드 변경은 수행하지 않고, 오직 화면 알림을 띄울 때만 사용한다."
    ),
)
def alert_raise(params: AlertRaiseParams):
    return {"ok": True, "alert": params.dict()}


@app.tool(name="alert.clear", description="Clear current alert")
def alert_clear():
    return {"ok": True, "cleared": True}
