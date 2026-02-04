"""
EST 출결 화면 캡처

캡처 전에 Zoom 회의 상태를 확인하고 필요시 재참가합니다.

사용법:
    python estcapture.py           # 자동 모드 (트리거 시간에만)
    python estcapture.py --force   # 강제 캡처
    python estcapture.py 7         # 7교시 단축 스케줄
    python estcapture.py --no-zoom # Zoom 체크 안함
"""

import os
import sys
from datetime import datetime, time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

try:
    from PIL import ImageGrab
except ImportError:
    print("Pillow 라이브러리가 설치되지 않았습니다.")
    print("터미널에서 'pip install Pillow'를 실행해주세요.")
    sys.exit(1)

# zoom_utils import
sys.path.insert(0, str(Path(__file__).parent.parent / "zoom"))
try:
    from zoom_utils import ensure_meeting
    ZOOM_AVAILABLE = True
except ImportError:
    ZOOM_AVAILABLE = False
    print("[!] zoom_utils를 찾을 수 없습니다. Zoom 체크 비활성화.")

# --- 설정 ---
BASE_FOLDER = r"C:\Users\smhrd\Desktop\출결"
# --- 설정 끝 ---


def get_belonging_session(now, schedule_type="default"):
    """
    '현재 시각이 속한 차시'를 반환 (파일명/기록용).
    - 강제 호출(force) 여부와 무관하게 항상 이 기준을 사용.
    - 예) 10:05 -> 2차시 (10:00~10:50 범위로 가정)
    """
    t = now.time()

    # 7교시 단축 스케줄(예시: 09:00~16:50까지 7차시로 운영)
    if schedule_type == "7":
        if time(9, 0) <= t < time(10, 0):
            return "1차시"
        elif time(10, 0) <= t < time(11, 0):
            return "2차시"
        elif time(11, 0) <= t < time(12, 0):
            return "3차시"
        elif time(12, 0) <= t < time(13, 0):
            return "4차시"
        elif time(13, 0) <= t < time(14, 0):
            return "5차시"
        elif time(14, 0) <= t < time(15, 0):
            return "6차시"
        elif time(15, 0) <= t < time(16, 50):
            return "7차시"
        else:
            return None

    # 기본 9교시 스케줄
    if time(9, 0) <= t < time(10, 0):
        return "1차시"
    elif time(10, 0) <= t < time(10, 50):
        return "2차시"
    elif time(10, 50) <= t < time(11, 50):
        return "3차시"
    elif time(11, 50) <= t < time(12, 50):
        return "4차시"
    elif time(13, 50) <= t < time(14, 50):
        return "5차시"
    elif time(14, 50) <= t < time(15, 50):
        return "6차시"
    elif time(15, 50) <= t < time(16, 50):
        return "7차시"
    elif time(16, 50) <= t < time(17, 50):
        return "8차시"
    else:
        return "끝"


def is_capture_time(now, schedule_type="default"):
    """
    '자동 캡처 트리거 시간'인지 여부만 판단.
    """
    t = now.time()
    weekday = now.weekday()  # 0 = 월요일

    if schedule_type == "7":
        return (
            time(9, 9) <= t < time(9, 12)
            or time(9, 59) <= t < time(10, 2)
            or time(10, 59) <= t < time(11, 2)
            or time(11, 59) <= t < time(12, 2)
            or time(13, 59) <= t < time(14, 2)
            or time(14, 59) <= t < time(15, 2)
            or time(15, 59) <= t < time(16, 2)
            or time(16, 49) <= t < time(16, 52)
        )

    # 기본(9교시)
    monday_extra_end = (weekday == 0 and (time(16, 49) <= t < time(16, 52)))

    return (
        monday_extra_end
        or (time(9, 9) <= t < time(9, 12))
        or (time(9, 59) <= t < time(10, 2))
        or (time(10, 59) <= t < time(11, 2))
        or (time(11, 59) <= t < time(12, 2))
        or (time(13, 59) <= t < time(14, 2))
        or (time(14, 59) <= t < time(15, 2))
        or (time(15, 59) <= t < time(16, 2))
        or (time(16, 59) <= t < time(17, 2))
        or (time(17, 49) <= t < time(17, 52))
    )


def take_screenshot(schedule_type="default", force=False, label_prefix=None, check_zoom=True):
    """
    전체 화면 스크린샷을 찍고 저장.

    Args:
        schedule_type: "default" (9교시) 또는 "7" (7교시)
        force: True면 트리거 시간 무시하고 촬영
        label_prefix: 파일명에 추가 라벨
        check_zoom: True면 캡처 전 Zoom 회의 상태 확인
    """
    now = datetime.now()

    # 자동 트리거가 아니면 종료 (단, force면 무시)
    if (not force) and (not is_capture_time(now, schedule_type)):
        print(f"[{now.strftime('%H:%M:%S')}] 스크린샷 시간이 아닙니다. 종료합니다.")
        return False

    # Zoom 회의 상태 확인 및 필요시 재참가
    if check_zoom and ZOOM_AVAILABLE:
        print(f"[{now.strftime('%H:%M:%S')}] Zoom 회의 상태 확인 중...")
        if not ensure_meeting(verbose=True):
            print("[X] Zoom 회의 연결 실패. 캡처를 건너뜁니다.")
            return False
        print("[O] Zoom 회의 준비 완료")
        print()

    # 파일명에 들어갈 차시
    session_name = get_belonging_session(now, schedule_type)
    if session_name is None:
        session_name = "기타"

    # 1) 날짜 폴더 생성
    date_folder_name = now.strftime("%Y%m%d")
    date_folder_path = os.path.join(BASE_FOLDER, date_folder_name)
    try:
        os.makedirs(date_folder_path, exist_ok=True)
    except OSError as e:
        print(f"폴더 생성 실패: {e}")
        return False

    # 2) 파일명 생성
    file_date = now.strftime("%m%d")
    file_time = now.strftime("%H%M")
    date_time_part = f"({file_date}_{file_time})"

    if label_prefix:
        session_part = f"_{session_name}_{label_prefix}"
    else:
        session_part = f"_{session_name}"

    file_name = f"{date_time_part}{session_part}.jpg"
    file_path = os.path.join(date_folder_path, file_name)

    # 3) 캡처 및 저장
    try:
        img = ImageGrab.grab()
        img.save(file_path, "JPEG")
        print(f"SAVED:{file_path}")
        return True
    except Exception as e:
        print(f"스크린샷 저장 실패: {e}")
        return False


if __name__ == "__main__":
    schedule_type = "default"
    force = False
    label_prefix = None
    check_zoom = True

    args = [arg.lower() for arg in sys.argv[1:]]

    # 7교시 단축
    if "7" in args:
        schedule_type = "7"
        print("7교시 단축 스케줄로 실행합니다...")

    # 강제 캡처
    if "--force" in args or "force" in args:
        force = True
        print("강제 모드로 스크린샷을 실행합니다...")

    # Zoom 체크 비활성화
    if "--no-zoom" in args or "no-zoom" in args:
        check_zoom = False
        print("Zoom 체크를 비활성화합니다...")

    # 테스트 모드
    if "test" in args:
        force = True
        print("테스트 모드로 스크린샷을 실행합니다...")

    take_screenshot(
        schedule_type=schedule_type,
        force=force,
        label_prefix=label_prefix,
        check_zoom=check_zoom
    )
