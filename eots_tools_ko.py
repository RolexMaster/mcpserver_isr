# eots_tools_ko.py
from __future__ import annotations

from typing import Dict

# core 의 tool name 기준으로 한국어 설명만 관리
TOOL_DESCRIPTIONS_KO: Dict[str, str] = {
    "eots.set_mode": "EO / IR / SWIR 모드를 전환합니다.",
    "eots.zoom": "EO/IR 카메라의 줌 배율을 조정합니다.",
    "eots.set_ir_polarity": "IR 카메라의 흑상/백상 모드를 전환합니다.",
    "eots.set_pan": "카메라의 수평(Pan) 각도를 설정합니다.",
    "eots.set_tilt": "카메라의 수직(Tilt) 각도를 설정합니다.",
    "eots.set_azimuth": "카메라의 절대 방위각(0~360도)을 설정합니다.",
    "eots.stop": "카메라 움직임과 추적을 정지합니다.",
    "eots.stabilization": "주간/열상 카메라의 흔들림 보정을 켜거나 끕니다.",
    "eots.pan_speed": "팬(Pan) 속도를 증가 또는 감소시킵니다.",
    "eots.tilt_speed": "틸트(Tilt) 속도를 증가 또는 감소시킵니다.",
    "eots.power": "주간/열상 카메라 및 LRF 전원을 켜거나 끕니다.",
    "eots.lrf_fire": "LRF를 1회 발사하여 거리 및 표적 좌표를 측정합니다.",
    "eots.autofocus": "지정된 센서(주간/열상)에 대해 자동초점을 실행합니다.",
    "eots.enhance": "주간/열상 카메라 영상 개선 기능을 시작/종료합니다.",
    "eots.goto_latlon": "지정된 위도/경도로 카메라 조준점을 이동합니다.",
    "eots.goto_preset": "지정된 이름의 프리셋 위치로 카메라를 이동합니다.",
    "eots.objects_list": "최근 탐지된 객체 목록을 반환합니다.",
    "eots.auto_detect": "자동 탐지 모드를 시작/종료합니다.",
    "eots.auto_track": "자동 추적 모드를 시작/종료합니다.",
    "eots.auto_scan_list": "오토 스캔 패턴 목록을 반환합니다.",
    "eots.auto_scan": "오토 스캔/자동 감시 모드를 시작/종료합니다.",
    "eots.record": "영상 녹화를 시작/종료합니다.",
    "eots.capture": "현재 화면을 스냅샷(정지 영상)으로 캡처합니다.",
}


def get_tool_description_ko(tool_name: str) -> str:
    """
    BridgeSession.build_tools_block 에서,
    language == 'ko' 인 경우 이 함수를 사용해서
    description(한국어)을 끌어다 쓰는 용도로 사용할 수 있습니다.
    """
    return TOOL_DESCRIPTIONS_KO.get(
        tool_name,
        tool_name,  # 기본값: 이름 그대로
    )
