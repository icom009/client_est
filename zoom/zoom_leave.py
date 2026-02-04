"""
Zoom 회의 나가기 및 종료

플로우:
    1. 회의 창 찾기
    2. Leave/나가기 버튼 클릭
    3. Leave Meeting 확인
    4. Zoom 앱 종료 (선택)
"""

import os
import time
import subprocess
from pathlib import Path

import yaml
from pywinauto import Application, Desktop
import pyautogui

# ============================================
# 설정 로드
# ============================================
CONFIG_PATH = Path(__file__).parent / "config.yaml"

def load_config():
    """config.yaml 로드"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}

CONFIG = load_config()

# 설정값
CLOSE_APP = CONFIG.get("leave", {}).get("close_app", True)  # Zoom 앱도 종료할지
STEP_DELAY = CONFIG.get("timing", {}).get("step_delay", 0.5)

# Zoom 창 클래스명
CLASS_MAIN = "ZPPTMainFrmWndClassEx"        # 메인 화면
CLASS_MEETING = "ConfMultiTabContentWndClass"  # 회의 중 창
CLASS_DIALOG = "zWaitingMeetingIDWndClass"  # 다이얼로그


def print_step(step_num, title):
    print()
    print(f"[Step {step_num}] {title}")
    print("-" * 40)


def find_window(class_name, timeout=5):
    """클래스명으로 창 찾기"""
    try:
        app = Application(backend="uia").connect(class_name=class_name, timeout=timeout)
        return app.top_window()
    except:
        return None


def find_all_zoom_windows():
    """모든 Zoom 관련 창 찾기"""
    windows = []
    try:
        desktop = Desktop(backend="uia")
        for win in desktop.windows():
            try:
                class_name = win.class_name()
                if "zoom" in class_name.lower() or "zp" in class_name.lower():
                    windows.append(win)
            except:
                continue
    except:
        pass
    return windows


def step1_find_meeting_window():
    """회의 창 찾기"""
    print_step(1, "회의 창 찾기")

    # 먼저 회의 창 찾기
    win = find_window(CLASS_MEETING, timeout=2)
    if win:
        print(f"[O] 회의 창 발견: {win.window_text()}")
        return win

    # 다이얼로그 창 확인
    win = find_window(CLASS_DIALOG, timeout=2)
    if win:
        print(f"[O] 다이얼로그 창 발견: {win.window_text()}")
        return win

    # 메인 창 확인
    win = find_window(CLASS_MAIN, timeout=2)
    if win:
        print(f"[O] 메인 창 발견 (회의 중 아님): {win.window_text()}")
        return win

    print("[X] Zoom 창을 찾을 수 없습니다.")
    return None


def step2_click_leave_button(win):
    """Leave/나가기 버튼 클릭"""
    print_step(2, "Leave 버튼 클릭")

    # 마우스를 화면 하단 중앙으로 이동 (툴바 표시)
    screen_width, screen_height = pyautogui.size()
    pyautogui.moveTo(screen_width // 2, screen_height - 100)
    time.sleep(0.5)

    # Leave 버튼 찾기
    leave_titles = ["Leave", "나가기", "End", "종료", "Leave Meeting", "회의 나가기"]

    for title in leave_titles:
        try:
            btn = win.child_window(title_re=f".*{title}.*", control_type="Button")
            if btn.exists(timeout=1):
                print(f"[O] '{title}' 버튼 발견")
                btn.click_input()
                print("[O] 클릭 완료!")
                return True
        except:
            continue

    print("[X] Leave 버튼을 찾을 수 없습니다.")
    return False


def step3_confirm_leave():
    """Leave Meeting 확인 클릭"""
    print_step(3, "Leave Meeting 확인")

    time.sleep(0.5)

    # 확인 다이얼로그 찾기
    desktop = Desktop(backend="uia")

    confirm_titles = [
        "Leave Meeting", "회의 나가기", "Leave", "나가기",
        "End Meeting", "회의 종료", "End Meeting for All", "모두에게 회의 종료"
    ]

    # 모든 창에서 확인 버튼 찾기
    for attempt in range(5):
        try:
            for win in desktop.windows():
                try:
                    for title in confirm_titles:
                        try:
                            btn = win.child_window(title=title, control_type="Button")
                            if btn.exists(timeout=0.5):
                                print(f"[O] '{title}' 버튼 발견")
                                btn.click_input()
                                print("[O] 확인 완료!")
                                return True
                        except:
                            continue
                except:
                    continue
        except:
            pass

        time.sleep(0.3)

    # Enter 키 시도 (기본 선택된 버튼 클릭)
    print("[*] 버튼을 찾지 못함, Enter 키 시도...")
    pyautogui.press("enter")
    print("[O] Enter 키 전송")
    return True


def step4_close_zoom_app():
    """Zoom 앱 완전 종료"""
    print_step(4, "Zoom 앱 종료")

    if not CLOSE_APP:
        print("[*] 설정에서 비활성화됨 (건너뜀)")
        return True

    # 잠시 대기 (회의 나가기 완료 대기)
    time.sleep(2)

    # 방법 1: 메인 창 찾아서 닫기
    win = find_window(CLASS_MAIN, timeout=2)
    if win:
        try:
            win.close()
            print("[O] 메인 창 닫기 완료")
            time.sleep(1)
        except:
            pass

    # 방법 2: taskkill로 프로세스 종료
    try:
        result = subprocess.run(
            ["taskkill", "/f", "/im", "Zoom.exe"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("[O] Zoom 프로세스 종료 완료")
            return True
        else:
            # 이미 종료되었거나 실행 중이 아님
            print("[*] Zoom이 이미 종료되었거나 실행 중이 아닙니다.")
            return True
    except Exception as e:
        print(f"[!] 프로세스 종료 실패: {e}")

    return True


def is_in_meeting():
    """현재 회의 중인지 확인"""
    win = find_window(CLASS_MEETING, timeout=1)
    if win:
        return True

    # Leave 버튼이 있는지 확인
    try:
        desktop = Desktop(backend="uia")
        for win in desktop.windows():
            try:
                for title in ["Leave", "나가기"]:
                    btn = win.child_window(title_re=f".*{title}.*", control_type="Button")
                    if btn.exists(timeout=0.3):
                        return True
            except:
                continue
    except:
        pass

    return False


def main():
    print("=" * 50)
    print("Zoom 회의 나가기 및 종료")
    print("=" * 50)
    print()
    print(f"설정 파일: {CONFIG_PATH}")
    print(f"앱 종료: {CLOSE_APP}")
    print()

    # Step 1: 회의 창 찾기
    win = step1_find_meeting_window()
    if not win:
        print("\n[INFO] Zoom이 실행 중이 아닙니다.")
        return

    time.sleep(STEP_DELAY)

    # 회의 중인지 확인
    if is_in_meeting():
        # Step 2: Leave 버튼 클릭
        if step2_click_leave_button(win):
            time.sleep(STEP_DELAY)

            # Step 3: 확인 클릭
            step3_confirm_leave()
    else:
        print("\n[INFO] 현재 회의 중이 아닙니다.")

    time.sleep(STEP_DELAY)

    # Step 4: Zoom 앱 종료
    step4_close_zoom_app()

    print()
    print("=" * 50)
    print("완료!")
    print("=" * 50)


if __name__ == "__main__":
    main()
