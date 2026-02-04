import os
import sys
from datetime import datetime, time

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
    # 필요 시 실제 운영 시간표에 맞게 경계값을 조정하세요.
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

    # 기본 9교시 스케줄 (요구사항: 10:05는 2차시가 되어야 하므로 10:00~10:50을 2차시로)
    # 필요 시 실제 운영 시간표에 맞게 경계값을 조정하세요.
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
        # 17:50 이후(또는 스케줄 밖)는 "끝"으로 처리 (원하시면 None으로 바꿔도 됩니다)
        return "끝"


def is_capture_time(now, schedule_type="default"):
    """
    '자동 캡처 트리거 시간'인지 여부만 판단.
    - force=True면 이 검사를 무시하고 촬영함.
    - 기존 코드의 "짧은 구간(약 3분)" 트리거를 유지.
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
            or time(16, 49) <= t < time(16, 52)  # 종료
        )

    # 기본(9교시)
    # ✅ 월요일만 16:50에도 '끝'을 추가로 찍는 기존 규칙 유지
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
        or (time(16, 59) <= t < time(17, 2))  # 8차시 트리거
        or (time(17, 49) <= t < time(17, 52))  # 끝 트리거
    )


def take_screenshot(schedule_type="default", force=False, label_prefix=None):
    """
    전체 화면 스크린샷을 찍고 저장.
    - force=False: 자동 트리거 시간에만 촬영
    - force=True : 트리거 시간 무시하고 촬영
    - 파일명 세션(차시)은 항상 '현재 시각이 속한 차시'로 계산
    - label_prefix: 파일명에 추가 라벨을 붙이고 싶을 때 사용 (예: "강제")
    """
    now = datetime.now()

    # 자동 트리거가 아니면 종료 (단, force면 무시)
    if (not force) and (not is_capture_time(now, schedule_type)):
        print(f"[{now.strftime('%H:%M:%S')}] 스크린샷 시간이 아닙니다. 종료합니다.")
        return

    # 파일명에 들어갈 차시: 항상 '속한 차시'
    session_name = get_belonging_session(now, schedule_type)
    if session_name is None:
        # 스케줄 밖이면 파일명 최소 보장
        session_name = "기타"

    # 1) 날짜 폴더 생성
    date_folder_name = now.strftime("%Y%m%d")
    date_folder_path = os.path.join(BASE_FOLDER, date_folder_name)
    try:
        os.makedirs(date_folder_path, exist_ok=True)
    except OSError as e:
        print(f"폴더 생성 실패: {e}")
        return

    # 2) 파일명 생성
    file_date = now.strftime("%m%d")
    file_time = now.strftime("%H%M")
    date_time_part = f"({file_date}_{file_time})"

    # 라벨(선택): 강제 호출임을 남기고 싶으면 label_prefix="강제"로 호출
    # 요구사항상 차시는 그대로 노출되어야 하므로, "강제"는 선택(원하시면 제거 가능)
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
    except Exception as e:
        print(f"스크린샷 저장 실패: {e}")


if __name__ == "__main__":
    schedule_type = "default"  # 기본 9교시
    force = False
    label_prefix = None

    args = [arg.lower() for arg in sys.argv[1:]]

    # 7교시 단축
    if "7" in args:
        schedule_type = "7"
        print("7교시 단축 스케줄로 실행합니다...")

    # 강제 캡처 (트리거 시간 무시)
    # ※ 요구사항: 강제여도 '차시'는 현재 시간의 차시로 들어가야 함 -> 이미 반영됨
    if "--force" in args or "force" in args:
        force = True
        # 강제 호출 로그/라벨이 필요하면 아래를 사용
        # label_prefix = "강제"
        print("강제 모드로 스크린샷을 실행합니다...")

    # 테스트용(언제든 찍되, 차시는 현재 시간 소속 차시)
    # 기존 코드의 '테스트'는 파일명에 _테스트를 넣는 방식이었는데,
    # 현재 요구사항은 '차시가 그대로 노출'이 우선이라, 테스트도 차시를 유지합니다.
    if "test" in args:
        force = True
        # label_prefix = "테스트"  # 필요 시만 켜세요
        print("테스트 모드로 스크린샷을 실행합니다...")

    take_screenshot(schedule_type=schedule_type, force=force, label_prefix=label_prefix)
