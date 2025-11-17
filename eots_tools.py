# eots_tools.py (Electro-Optical Tracking System)
import time
from typing import Dict, List, Optional, Literal, Annotated, Any
from pydantic import Field
from server_main import app  # 기존 구조 유지

# 내부 상태 (단일 클라이언트 환경이라 락 불필요)
_STATE: dict[str, Any] = {"mode": "eo", "zoom": 1, "pan": 0.0, "tilt": 0.0, "tracking": False}



# =========================
# 추가 도구: 특정 객체 존재 여부 확인 (탐지 결과 기반)
# =========================
@app.tool(
    name="eots.detection_object_exists",
    description=(
        "[SIDE-EFFECT FREE] Check whether the *current* EOTS detection results already contain "
        "any object with the given label (e.g. 'ship', 'boat', 'person'). "
        "Use this when the user asks yes/no style questions such as:\n"
        "- \"현재 화면에 선박 있냐?\"\n"
        "- \"지금 시야에 사람 있어?\"\n"
        "- \"이 구역에 보트가 한 척이라도 있으면 알려줘\"\n"
        "또한 한국어로 \"탐지\"/\"발견\"/\"포착\"/\"잡히다\" 같은 표현을 쓰면서\n"
        "단순히 '선박이 탐지되었는지', '사람이 발견되었는지'를 물어볼 때\n"
        "가장 먼저 사용해야 하는 도구이다. 예:\n"
        "- \"지금 선박 탐지된 거 있어?\"\n"
        "- \"이 화면에 사람 발견된 거 있냐?\"\n"
        "- \"현재 시야에 보트가 하나라도 잡혔어?\"\n"
        "This tool NEVER moves the camera and NEVER starts a new detection; "
        "it only inspects the latest detection results stored in _STATE['objects'] and "
        "returns exists/count/matched_objects. "
        "If the user instead requests detailed target information or coordinates "
        "(예: \"어디에 있는지 좌표를 알려줘\"), prefer using 'eots.objects_list' "
        "after detection is available."
    ),
)
def eots_detection_object_exists(
    object_name: str,
):
    """
    현재 화면(EO/IR 등)에서 **이미 수행된 탐지 결과**
    (_STATE['objects'])를 조회하여,
    주어진 이름(object_name)을 가진 객체가 존재하는지 여부를 반환하는 도구.

    _STATE['objects'] 예시:
    [
        {
            "id": "trk_001",
            "label": "ship",
            "confidence": 0.91,
            "bbox": [x_min, y_min, x_max, y_max],
            "distance_m": 1234.5
        },
        ...
    ]

    - object_name: "ship", "boat", "person" 등 label 이름
    - label 비교는 소문자로 변환하여 대소문자 무시하고 수행
    - 새로운 탐지를 수행하지 않고, 이미 저장된 탐지 결과만 조회한다.
    - 사용자의 발화에 '탐지', '발견', '포착', '잡히다' 등의 표현이 포함되어 있고
      단순히 존재 여부(있냐/없냐)를 묻는다면 이 도구 사용을 우선 고려한다.
    """
    objects: List[Dict[str, Any]] = _STATE.get("objects", [])
    q = (object_name or "").strip().lower()

    matched = [
        obj for obj in objects
        if str(obj.get("label", "")).lower() == q
    ]
    exists = len(matched) > 0

    return {
        "ok": True,
        "query": object_name,
        "exists": exists,
        "count": len(matched),
        "matched_objects": matched,
    }



@app.tool(name="eots.set_mode", description="Set EO/IR/auto mode")
def eots_set_mode(
    mode: Literal["eo", "ir", "auto"]
):
    _STATE["mode"] = mode
    return {"ok": True, "mode": _STATE["mode"]}

# =========================
# 추가 도구: Pan만 설정
# =========================
@app.tool(name="eots.set_pan", description="Set pan angle in degrees")
def eots_set_pan(
    pan_deg: Annotated[float, Field(ge=-180, le=180)]
):
    """
    수평(Pan) 각도만 단독으로 설정하는 도구.
    - 기존 eots.pan_tilt를 건드리지 않고, pan만 바꾸고 싶을 때 사용.
    """
    _STATE["pan"] = pan_deg
    return {
        "ok": True,
        "pan_deg": _STATE["pan"],
    }


# =========================
# 추가 도구: Tilt만 설정
# =========================
@app.tool(name="eots.set_tilt", description="Set tilt angle in degrees")
def eots_set_tilt(
    tilt_deg: Annotated[float, Field(ge=-90, le=90)]
):
    """
    수직(Tilt) 각도만 단독으로 설정하는 도구.
    - 기존 eots.pan_tilt를 건드리지 않고, tilt만 바꾸고 싶을 때 사용.
    """
    _STATE["tilt"] = tilt_deg
    return {
        "ok": True,
        "tilt_deg": _STATE["tilt"],
    }

# @app.tool(name="eots.pan_tilt", description="Pan/Tilt to degrees")
# def eots_pan_tilt(
#     pan_deg: Annotated[float, Field(ge=-180, le=180)],
#     tilt_deg: Annotated[float, Field(ge=-90, le=90)],
# ):
#     _STATE["pan"], _STATE["tilt"] = pan_deg, tilt_deg
#     return {"ok": True, "pan_deg": _STATE["pan"], "tilt_deg": _STATE["tilt"]}


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


# =========================
# 추가 도구 1: 방위각 설정
# =========================
@app.tool(name="eots.set_azimuth", description="Set absolute azimuth/bearing in degrees (0-360)")
def eots_set_azimuth(
    bearing_deg: Annotated[float, Field(ge=0, le=360)]
):
    """
    절대 방위각(0~360도)을 설정하는 도구.
    - _STATE["bearing"] 에 절대 방위각 저장
    - 필요시 pan(-180~180) 값으로도 변환해서 _STATE["pan"] 업데이트
    """
    # 절대 방위각 저장
    _STATE["bearing"] = bearing_deg

    # pan(-180~180)로 변환 (예: 270도 -> -90도)
    pan_deg = bearing_deg if bearing_deg <= 180 else bearing_deg - 360
    _STATE["pan"] = pan_deg

    return {
        "ok": True,
        "bearing_deg": _STATE["bearing"],
        "pan_deg": _STATE["pan"],
    }


# =========================
# 추가 도구 2: 카메라 정지
# =========================
@app.tool(name="eots.stop", description="Stop camera motion and tracking")
def eots_stop():
    """
    카메라 움직임 및 추적을 정지하는 도구.
    실제 구현에서는 모터 정지 명령, 트래킹 해제 등을 연동하면 됨.
    """
    # 새로운 상태 키들을 추가로 사용해도 무방
    _STATE["moving"] = False
    _STATE["tracking"] = False

    return {
        "ok": True,
        "stopped": True,
        "moving": _STATE["moving"],
        "tracking": _STATE["tracking"],
    }

# =========================
# 추가 도구: IR 흑상 / 백상 전환
# =========================
@app.tool(
    name="eots.set_ir_polarity",
    description="Set IR polarity: black-hot (흑상) / white-hot (백상)"
)
def eots_set_ir_polarity(
    polarity: Literal["black_hot", "white_hot"]
):
    """
    IR 카메라 폴라리티(흑상/백상)를 설정하는 도구.
    - black_hot : 흑상(뜨거운 객체가 검게 보이는 모드)
    - white_hot : 백상(뜨거운 객체가 밝게 보이는 모드)
    """
    _STATE["ir_polarity"] = polarity
    return {
        "ok": True,
        "ir_polarity": _STATE["ir_polarity"],
    }


# =========================
# 추가 도구: 자동 탐지 모드
# =========================
@app.tool(
    name="eots.auto_detect",
    description="Enable or disable automatic detection mode (자동 탐지 모드)"
)
def eots_auto_detect(
    enable: bool,
):
    """
    자동 탐지 모드를 켜거나 끄는 도구.
    - enable=True  : 자동 탐지 모드 활성화
    - enable=False : 자동 탐지 모드 비활성화
    """
    _STATE["auto_detect"] = enable
    return {
        "ok": True,
        "auto_detect": _STATE["auto_detect"],
    }


# =========================
# 추가 도구: 자동 추적 모드
# =========================
@app.tool(
    name="eots.auto_track",
    description="Enable or disable automatic tracking mode (자동 추적 모드)"
)
def eots_auto_track(
    enable: bool,
):
    """
    자동 추적 모드를 켜거나 끄는 도구.
    - enable=True  : 자동 추적 모드 활성화
    - enable=False : 자동 추적 모드 비활성화
    """
    _STATE["auto_track_mode"] = enable
    return {
        "ok": True,
        "auto_track_mode": _STATE["auto_track_mode"],
    }


# =========================
# 추가 도구: 자동 감시 모드
# =========================
@app.tool(
    name="eots.auto_surveillance",
    description="Enable or disable automatic surveillance mode (자동 감시, 스캔 모드)"
)
def eots_auto_surveillance(
    enable: bool,
):
    """
    자동 감시(스캔/패턴 감시 등) 모드를 켜거나 끄는 도구.
    - enable=True  : 자동 감시 모드 활성화
    - enable=False : 자동 감시 모드 비활성화
    """
    _STATE["auto_surveillance"] = enable
    return {
        "ok": True,
        "auto_surveillance": _STATE["auto_surveillance"],
    }


# =========================
# 추가 도구: LRF 발사
# =========================
@app.tool(
    name="eots.lrf_fire",
    description=(
        "Fire LRF (Laser Range Finder) once to measure distance and target coordinates "
        "(현재 조준선이 향하는 표적에 대해 LRF를 1회 발사하여 거리와 표적 좌표를 측정/갱신할 때 사용)"
    ),
)
def eots_lrf_fire():
    """
    LRF(레이저 거리 측정기)를 1회 발사하는 도구.

    - 이 도구는 현재 EO/IR 조준선이 향하는 표적을 기준으로 LRF를 발사하여
      해당 표적까지의 거리와 표적 좌표(예: 위·경도 또는 로컬 좌표)를 측정하는 용도로 사용된다.
    - 실제 시스템에서는 여기서 하드웨어 LRF 발사 명령을 호출하고,
      측정된 거리 및 좌표 값을 받아서 _STATE 에 저장하도록 연동하면 된다.

    예: 
    _STATE["lrf_last_distance_m"] = measured_distance
    _STATE["lrf_last_target_coord"] = {
        "lat": ...,
        "lon": ...,
        "x": ...,
        "y": ...,
    }
    """
    # 발사 플래그만 간단히 상태에 기록 (필요하면 timestamp, distance, coords 등 추가)
    _STATE["lrf_fired"] = True

    # 추후에 실제 거리/좌표 측정 결과를 저장하고 싶다면 예시처럼 필드를 추가:
    # _STATE["lrf_last_distance_m"] = measured_distance
    # _STATE["lrf_last_target_coord"] = {"lat": ..., "lon": ...}

    return {
        "ok": True,
        "fired": True,
    }


# =========================
# 추가 도구: 자동초점 (Autofocus)
# =========================
@app.tool(
    name="eots.autofocus",
    description="Run autofocus on the current sensor (자동초점 실행)"
)
def eots_autofocus():
    """
    현재 선택된 센서(예: EO 또는 IR)에 대해 자동초점을 한 번 실행하는 도구.
    실제 시스템에서는 여기에서 카메라 오토포커스 명령을 호출하면 된다.
    """
    # 현재 모드(EO/IR 등)를 같이 기록해 두면 디버깅에 도움됨
    current_mode = _STATE.get("mode", None)

    _STATE["autofocus_fired"] = True
    _STATE["autofocus_last_mode"] = current_mode

    return {
        "ok": True,
        "autofocus_fired": True,
        "mode": current_mode,
    }


# =========================
# 추가 도구: 영상 녹화 (Start/Stop)
# =========================
@app.tool(
    name="eots.record",
    description="Start or stop video recording (영상 녹화 시작/종료)"
)
def eots_record(
    action: Literal["start", "stop"],
    mode: Literal["manual", "track_session"] = "manual",
    filename_hint: Optional[str] = None,
):
    """
    영상 녹화를 시작하거나(stop) 종료하는 도구.

    - action:
        - "start" : 녹화 시작
        - "stop"  : 녹화 종료
    - mode:
        - "manual"       : 일반 수동 녹화
        - "track_session": '자동 추적 종료 시점까지 녹화' 같은 용도로 사용
    - filename_hint:
        - 파일 이름에 힌트를 주고 싶을 때 사용 (예: "target123_session1")
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


from typing import Optional  # 이미 있으시면 중복 import는 제거해도 됩니다.
import time

# =========================
# 추가 도구: 스냅샷 캡처 (이미지 캡처)
# =========================
@app.tool(
    name="eots.capture",
    description="Capture a still image frame (스냅샷 캡처)"
)
def eots_capture():
    """
    현재 영상에서 1프레임 캡처(스냅샷)를 수행하는 도구.

    - 추가 인자는 받지 않는다.
    - 현재 보이는 화면을 그대로 캡처해서 저장한다고 가정한다.
    - 실제 시스템에서는 여기서 프레임 저장 후 파일 경로/ID를 리턴하도록 연동.
    """
    # 실제 구현에서는 캡처된 이미지 경로나 ID를 생성해야 함
    # 여기서는 예시로만 placeholder 사용
    capture_id = f"capture_{int(time.time())}"

    _STATE["last_capture_id"] = capture_id
    _STATE["last_capture_timestamp"] = time.time()

    return {
        "ok": True,
        "capture_id": capture_id,
    }




