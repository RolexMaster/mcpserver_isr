# system_tools.py (System Management)
from server_main import app

@app.tool(name="system.status", description="System/Camera status")
def system_status():
    return {"ok": True, "cpu":"9%","mem":"43%","uptime":"1h 12m","camera":"ready"}

@app.tool(name="system.reboot", description="Reboot system/camera")
def system_reboot():
    return {"ok": True, "message": "rebooting..."}
