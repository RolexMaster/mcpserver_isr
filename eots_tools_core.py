# eots_tools_core.py
from __future__ import annotations

from typing import Dict, Any, List, Optional, Literal, Annotated
from pydantic import Field
from server_main import app  # fastmcp 앱 인스턴스

# 내부 상태: 단일 클라이언트 데모용
_STATE: Dict[str, Any] = {
    "mode": "eo",
    "zoom": 1,
    "pan": 0.0,
    "tilt": 0.0,
    "tracking": False,
}


# =========================
# 공통 유틸
# =========================
def _set_mode_internal(mode: Literal["eo", "ir", "swir"]) -> Dict[str, Any]:
    _STATE["mode"] = mode
    return {"ok": True, "mode": _STATE["mode"]}


def _set_zoom_internal(sensor: Literal["eo", "ir"], level: int) -> Dict[str, Any]:
    _STATE["mode"] = sensor  # 센서 모드도 같이 갱신(EO/IR 줌질의용)
    _STATE["zoom"] = level
    return {"ok": True, "mode": _STATE["mode"], "zoom": _STATE["zoom"]}


# =========================
# 모드 / 줌 / 폴라리티
# =========================

@app.tool(
    name="eots.set_mode",
    description="Set EO/IR/SWIR sensor mode. (core logic only, see ko/en files for localized descriptions.)",
)
def eots_set_mode(
    mode: Literal["eo", "ir", "swir"]
):
    """
    PRESET: 1, 2, 13, 14, 15
      - EO 카메라 3배 확대 (EO mode + zoom)
      - IR 카메라 5배 확대 (IR mode + zoom)
      - 열상 모드로 전환
      - 주간 모드로 전환
      - SWIR 모드로 전환
    """
    return _set_mode_internal(mode)


@app.tool(
    name="eots.zoom",
    description="Change zoom level on EO/IR sensor.",
)
def eots_zoom(
    sensor: Literal["eo", "ir"],
    level: Annotated[int, Field(ge=1, le=30)],
):
    """
    PRESET: 1, 2
      - EO 카메라 3배 확대
      - IR 카메라 5배 확대
    """
    return _set_zoom_internal(sensor, level)


@app.tool(
    name="eots.set_ir_polarity",
    description="Set IR polarity: black-hot / white-hot.",
)
def eots_set_ir_polarity(
    polarity: Literal["black_hot", "white_hot"]
):
    """
    PRESET: 3, 4
      - IR 카메라 흑상 전환
      - IR 카메라 백상 전환
    """
    _STATE["ir_polarity"] = polarity
    return {"ok": True, "ir_polarity": _STATE["ir_polarity"]}


# =========================
# 팬 / 틸트 / 방위각
# =========================

@app.tool(
    name="eots.set_pan",
    description="Set pan angle in degrees (-180 ~ 180).",
)
def eots_set_pan(
    pan_deg: Annotated[float, Field(ge=-180, le=180)]
):
    """
    PRESET: 5, 6
      - 좌로 20도 회전
      - 우로 30도 회전
    PRESET(연계): 9 (방위각 30도로 이동 시 내부적으로 pan과 매핑될 수 있음)
    """
    _STATE["pan"] = pan_deg
    return {"ok": True, "pan_deg": _STATE["pan"]}


@app.tool(
    name="eots.set_tilt",
    description="Set tilt angle in degrees (-90 ~ 90).",
)
def eots_set_tilt(
    tilt_deg: Annotated[float, Field(ge=-90, le=90)]
):
    """
    PRESET: 7, 8, 10
      - 상으로 5도 회전
      - 하로 3도 회전
      - 고저각 3도로 이동
    """
    _STATE["tilt"] = tilt_deg
    return {"ok": True, "tilt_deg": _STATE["tilt"]}


@app.tool(
    name="eots.set_azimuth",
    description="Set absolute azimuth/bearing (0~360 degrees).",
)
def eots_set_azimuth(
    bearing_deg: Annotated[float, Field(ge=0, le=360)]
):
    """
    PRESET: 9
      - 방위각 30도로 이동
    """
    _STATE["bearing"] = bearing_deg
    # 0~360 -> -180~180 pan 매핑
    pan_deg = bearing_deg if bearing_deg <= 180 else bearing_deg - 360
    _STATE["pan"] = pan_deg
    return {"ok": True, "bearing_deg": _STATE["bearing"], "pan_deg": _STATE["pan"]}


@app.tool(
    name="eots.stop",
    description="Stop camera motion and tracking.",
)
def eots_stop():
    """
    PRESET: 12
      - 정지
    """
    _STATE["moving"] = False
    _STATE["tracking"] = False
    return {"ok": True, "stopped": True, "moving": False, "tracking": False}


# =========================
# 흔들림 보정 / 속도 제어
# =========================

@app.tool(
    name="eots.stabilization",
    description="Enable or disable image stabilization for EO/IR.",
)
def eots_stabilization(
    sensor: Literal["eo", "ir"],
    enable: bool,
):
    """
    PRESET: 21, 22, 23, 24
      - 주간 카메라 흔들림 보정 시작/종료
      - 열상 카메라 흔들림 보정 시작/종료
    """
    key = f"{sensor}_stab"
    _STATE[key] = enable
    return {"ok": True, "sensor": sensor, "stabilization": enable}


@app.tool(
    name="eots.pan_speed",
    description="Increase or decrease pan speed.",
)
def eots_pan_speed(
    delta: Annotated[float, Field(ge=-1.0, le=1.0)]
):
    """
    PRESET: 17, 18
      - 팬 속도 증가 (양수)
      - 팬 속도 감소 (음수)
    """
    cur = _STATE.get("pan_speed", 0.0)
    _STATE["pan_speed"] = cur + delta
    return {"ok": True, "pan_speed": _STATE["pan_speed"]}


@app.tool(
    name="eots.tilt_speed",
    description="Increase or decrease tilt speed.",
)
def eots_tilt_speed(
    delta: Annotated[float, Field(ge=-1.0, le=1.0)]
):
    """
    PRESET: 19, 20
      - 틸트 속도 증가 (양수)
      - 틸트 속도 감소 (음수)
    """
    cur = _STATE.get("tilt_speed", 0.0)
    _STATE["tilt_speed"] = cur + delta
    return {"ok": True, "tilt_speed": _STATE["tilt_speed"]}


# =========================
# 전원 제어 / LRF
# =========================

@app.tool(
    name="eots.power",
    description="Power on/off EO/IR sensors and LRF.",
)
def eots_power(
    target: Literal["eo", "ir", "lrf"],
    on: bool,
):
    """
    PRESET: 25, 26, 27, 28, 29, 30
      - 열상 카메라 전원 켜기/끄기
      - 주간 카메라 전원 켜기/끄기
      - LRF 켜기/끄기 (필요시)
    """
    key = f"power_{target}"
    _STATE[key] = on
    return {"ok": True, "target": target, "on": on}


@app.tool(
    name="eots.lrf_fire",
    description=(
        "[LRF] Fire the laser range finder ONCE to measure distance and target coordinates "
        "for the object currently under the crosshair. "
        "Use this when the user asks to show or update the current target distance/position, "
        "e.g. 'Show target position', 'Measure the current target', 'Give me the range to the target'."
    ),
)
def eots_lrf_fire():
    """
    PRESET: 33, 32 (예: 거리 측정 시작, 타겟 위치 알려줘)
    """
    _STATE["lrf_fired"] = True
    # 실제 시스템에서는 측정 거리/좌표를 채워 넣으면 됨
    _STATE["lrf_last_distance_m"] = 1234.5
    _STATE["lrf_last_target_coord"] = {"lat": 37.2322, "lon": 129.5403}
    return {
        "ok": True,
        "fired": True,
        "distance_m": _STATE["lrf_last_distance_m"],
        "target_coord": _STATE["lrf_last_target_coord"],
    }


# =========================
# 자동초점 / 영상 향상
# =========================

@app.tool(
    name="eots.autofocus",
    description="Run autofocus on selected sensor.",
)
def eots_autofocus(
    sensor: Literal["eo", "ir"]
):
    """
    PRESET: 11
      - 열상 자동초점 / 주간 자동초점
    """
    _STATE["autofocus_fired"] = True
    _STATE["autofocus_sensor"] = sensor
    return {"ok": True, "sensor": sensor, "autofocus_fired": True}


@app.tool(
    name="eots.enhance",
    description="Start or stop image enhancement on EO/IR.",
)
def eots_enhance(
    sensor: Literal["eo", "ir"],
    action: Literal["start", "stop"],
):
    """
    PRESET: 34, 35, 36, 37
      - 열상/주간 카메라 영상 개선 시작/종료
    """
    key = f"enhance_{sensor}"
    _STATE[key] = (action == "start")
    return {"ok": True, "sensor": sensor, "enhance": _STATE[key]}


# =========================
# 위치 이동 / 프리셋 이동
# =========================

@app.tool(
    name="eots.goto_latlon",
    description="Move sensor to given latitude/longitude (if supported by system).",
)
def eots_goto_latlon(
    lat: float,
    lon: float,
):
    """
    PRESET: 38
      - 위도 37°13'56\"N 경도 129°32'25\"E 위치로 이동
    """
    _STATE["target_lat"] = lat
    _STATE["target_lon"] = lon
    return {"ok": True, "lat": lat, "lon": lon}


@app.tool(
    name="eots.goto_preset",
    description="Move sensor to named preset position.",
)
def eots_goto_preset(
    name: str,
):
    """
    PRESET: 39, 40
      - 좌측 빨간 등대 위치로 이동
      - 우측 방파제 프리셋 위치로 이동
    """
    _STATE["last_preset"] = name
    return {"ok": True, "preset": name}


# =========================
# AI 탐지 / 자동탐지/추적/감시 / 오토스캔
# =========================

@app.tool(
    name="eots.objects_list",
    description="Return list of currently detected objects (from last detection result).",
)
def eots_objects_list():
    """
    PRESET: 41
      - 탐지 객체 목록 가져오기
    """
    objects: List[Dict[str, Any]] = _STATE.get("objects", [])
    return {"ok": True, "objects": objects}


@app.tool(
    name="eots.auto_detect",
    description="Enable/disable automatic detection.",
)
def eots_auto_detect(
    enable: bool,
):
    """
    PRESET: 42, 43
      - 자동탐지 시작/종료
    """
    _STATE["auto_detect"] = enable
    return {"ok": True, "auto_detect": enable}


@app.tool(
    name="eots.auto_track",
    description="Enable/disable automatic tracking.",
)
def eots_auto_track(
    enable: bool,
):
    """
    PRESET: 44, 45
      - 자동추적 시작/종료
    """
    _STATE["auto_track_mode"] = enable
    return {"ok": True, "auto_track_mode": enable}


@app.tool(
    name="eots.auto_scan_list",
    description="Return list of available auto-scan patterns.",
)
def eots_auto_scan_list():
    """
    PRESET: 46
      - 오토 스캔 목록 보여줘
    """
    patterns = _STATE.get("auto_scan_patterns", ["pattern_A", "pattern_B"])
    return {"ok": True, "patterns": patterns}


@app.tool(
    name="eots.auto_scan",
    description="Start or stop auto scan / surveillance.",
)
def eots_auto_scan(
    enable: bool,
):
    """
    PRESET: 47, 48, 49, 50 (자동 감시/오토스캔 시작/중지 계열)
      - 오토 스캔 실행 / 오토 스캔 중지
      - 자동 감시 시작 / 자동 감시 중지
    """
    _STATE["auto_scan"] = enable
    return {"ok": True, "auto_scan": enable}


# =========================
# 녹화 / 캡처
# =========================

@app.tool(
    name="eots.record",
    description="Start or stop video recording.",
)
def eots_record(
    action: Literal["start", "stop"],
    mode: Literal["manual", "track_session"] = "manual",
    filename_hint: Optional[str] = None,
):
    """
    PRESET: 49, 50
      - 녹화 시작 / 녹화 중지
    """
    if action == "start":
        _STATE["recording"] = True
        _STATE["recording_mode"] = mode
        _STATE["recording_filename_hint"] = filename_hint
    else:
        _STATE["recording"] = False

    return {
        "ok": True,
        "action": action,
        "recording": _STATE.get("recording", False),
        "mode": _STATE.get("recording_mode"),
        "filename_hint": _STATE.get("recording_filename_hint"),
    }


@app.tool(
    name="eots.capture",
    description="Capture a still image frame.",
)
def eots_capture():
    """
    PRESET: (예: 캡처 시작)
    """
    import time as _time
    capture_id = f"capture_{int(_time.time())}"
    _STATE["last_capture_id"] = capture_id
    _STATE["last_capture_timestamp"] = _time.time()
    return {"ok": True, "capture_id": capture_id}
