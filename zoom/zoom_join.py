"""
Zoom 회의 참가 전체 플로우 (통합)

플로우:
    0. Zoom 실행 (꺼져있으면)
    1. Join 버튼 클릭 (메인 화면)
    2. 회의 ID 입력
    3. 오디오 연결 안함 체크
    4. 참가 클릭
    5. 비밀번호 입력
    6. 회의 참가 클릭
    7. 연결 확인
    8. 창 최대화
    9. 보기 모드 전환
   10. 회의 탭 클릭
"""

import os
import subprocess
import time
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
MEETING_ID = CONFIG.get("meeting", {}).get("id", "")
PASSWORD = CONFIG.get("meeting", {}).get("password", "")
NO_AUDIO = CONFIG.get("meeting", {}).get("no_audio", True)

MAXIMIZE = CONFIG.get("window", {}).get("maximize", True)
VIEW_MODE = CONFIG.get("window", {}).get("view_mode", "gallery")

DIALOG_WAIT = CONFIG.get("timing", {}).get("dialog_wait", 10)
PASSWORD_WAIT = CONFIG.get("timing", {}).get("password_wait", 3)
CONNECT_WAIT = CONFIG.get("timing", {}).get("connect_wait", 30)
STEP_DELAY = CONFIG.get("timing", {}).get("step_delay", 0.5)

# Zoom 창 클래스명
CLASS_MAIN = "ZPPTMainFrmWndClassEx"        # 메인 화면
CLASS_DIALOG = "zWaitingMeetingIDWndClass"  # 참가/비밀번호 다이얼로그
CLASS_MEETING = "ConfMultiTabContentWndClass"  # 회의 중 창

# Zoom 실행 경로
ZOOM_PATH = r"C:\Users\{}\AppData\Roaming\Zoom\bin\Zoom.exe".format(os.environ.get("USERNAME", ""))


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


def is_zoom_running():
    """Zoom이 실행 중인지 확인"""
    try:
        app = Application(backend="uia").connect(class_name=CLASS_MAIN, timeout=1)
        return True
    except:
        return False


def step0_launch_zoom():
    """Zoom 실행 (꺼져있으면)"""
    print_step(0, "Zoom 실행 확인")

    if is_zoom_running():
        print("[O] Zoom이 이미 실행 중입니다.")
        return True

    print("[*] Zoom이 실행되지 않았습니다. 실행 중...")

    # Zoom 실행
    if os.path.exists(ZOOM_PATH):
        subprocess.Popen([ZOOM_PATH])
        print(f"[O] Zoom 실행: {ZOOM_PATH}")
    else:
        # 다른 경로 시도
        alt_paths = [
            r"C:\Program Files\Zoom\bin\Zoom.exe",
            r"C:\Program Files (x86)\Zoom\bin\Zoom.exe",
        ]
        launched = False
        for path in alt_paths:
            if os.path.exists(path):
                subprocess.Popen([path])
                print(f"[O] Zoom 실행: {path}")
                launched = True
                break

        if not launched:
            # 시작 메뉴에서 실행 시도
            try:
                os.startfile("zoom")
                print("[O] Zoom 실행 (시작 메뉴)")
                launched = True
            except:
                pass

        if not launched:
            print("[X] Zoom 실행 파일을 찾을 수 없습니다.")
            return False

    # 메인 창 대기
    print("[*] Zoom 메인 창 대기 중...")
    for i in range(30):
        time.sleep(1)
        if is_zoom_running():
            print(f"[O] Zoom 메인 창 확인! ({i+1}초)")
            time.sleep(1)  # 안정화 대기
            return True
        if i % 5 == 4:
            print(f"    {i+1}초 경과...")

    print("[X] Zoom 메인 창이 나타나지 않았습니다.")
    return False


def step1_click_join():
    """메인 화면에서 Join 버튼 클릭"""
    print_step(1, "Join 버튼 클릭")

    win = find_window(CLASS_MAIN)
    if not win:
        print("[X] Zoom 메인 창을 찾을 수 없습니다.")
        return False

    print(f"[O] 메인 창 발견: {win.window_text()}")

    join_titles = ["Join", "참가", "Join a Meeting", "회의 참가"]

    for title in join_titles:
        try:
            btn = win.child_window(title=title, control_type="Button")
            if btn.exists(timeout=2):
                print(f"[O] '{title}' 버튼 발견")
                btn.click_input()
                print("[O] 클릭 완료!")
                return True
        except:
            continue

    print("[X] Join 버튼을 찾을 수 없습니다.")
    return False


def step2_input_meeting_id():
    """회의 ID 입력"""
    print_step(2, "회의 ID 입력")

    print("[*] 참가 다이얼로그 대기 중...")
    win = None
    for i in range(DIALOG_WAIT):
        time.sleep(1)
        win = find_window(CLASS_DIALOG, timeout=1)
        if win:
            break
        print(f"    {i+1}초...")

    if not win:
        print("[X] 참가 다이얼로그를 찾을 수 없습니다.")
        return False

    print(f"[O] 다이얼로그 발견: {win.window_text()}")

    try:
        edit = win.child_window(control_type="Edit", found_index=0)
        if edit.exists(timeout=2):
            edit.click_input()
            time.sleep(0.1)
            edit.type_keys("^a")
            time.sleep(0.05)
            edit.type_keys(MEETING_ID, with_spaces=True)
            print(f"[O] 회의 ID 입력 완료: {MEETING_ID}")
            return True
    except Exception as e:
        print(f"[X] 입력 실패: {e}")

    return False


def step3_check_no_audio():
    """오디오 연결 안함 체크"""
    print_step(3, "오디오 연결 안함 체크")

    if not NO_AUDIO:
        print("[*] 설정에서 비활성화됨 (건너뜀)")
        return True

    win = find_window(CLASS_DIALOG)
    if not win:
        return True

    try:
        chk = win.child_window(title="오디오에 연결하지 않음", control_type="CheckBox")
        if chk.exists(timeout=2):
            toggle_state = chk.get_toggle_state()
            print(f"    현재 상태: {'체크됨' if toggle_state else '체크 안됨'}")

            if not toggle_state:
                chk.click_input()
                print("[O] 체크 완료!")
            else:
                print("[O] 이미 체크됨")
            return True
    except:
        pass

    try:
        chk = win.child_window(title="Don't connect to audio", control_type="CheckBox")
        if chk.exists(timeout=1):
            if not chk.get_toggle_state():
                chk.click_input()
            print("[O] 체크 완료!")
            return True
    except:
        pass

    print("[!] 체크박스 없음 (계속 진행)")
    return True


def step4_click_join_dialog():
    """참가 다이얼로그에서 참가 버튼 클릭"""
    print_step(4, "참가 버튼 클릭")

    win = find_window(CLASS_DIALOG)
    if not win:
        print("[X] 다이얼로그를 찾을 수 없습니다.")
        return False

    join_titles = ["참가", "Join", "Join Meeting", "회의 참가"]

    for title in join_titles:
        try:
            btn = win.child_window(title=title, control_type="Button")
            if btn.exists(timeout=1):
                print(f"[O] '{title}' 버튼 발견")
                btn.click_input()
                print("[O] 클릭 완료!")
                return True
        except:
            continue

    print("[X] 참가 버튼을 찾을 수 없습니다.")
    return False


def step5_input_password():
    """비밀번호 입력"""
    print_step(5, "비밀번호 입력")

    if not PASSWORD:
        print("[*] 비밀번호 없음 (건너뜀)")
        return True

    print(f"[*] 비밀번호 창 대기 중... ({PASSWORD_WAIT}초)")
    time.sleep(PASSWORD_WAIT)

    win = find_window(CLASS_DIALOG)
    if not win:
        print("[X] 비밀번호 창을 찾을 수 없습니다.")
        return False

    print(f"[O] 비밀번호 창 발견: {win.window_text()}")

    try:
        edit = win.child_window(control_type="Edit")
        if edit.exists(timeout=2):
            edit.click_input()
            time.sleep(0.1)
            edit.type_keys(PASSWORD)
            print(f"[O] 비밀번호 입력 완료")
            return True
    except Exception as e:
        print(f"[X] 입력 실패: {e}")

    return False


def step6_click_join_password():
    """비밀번호 창에서 회의 참가 클릭"""
    print_step(6, "회의 참가 버튼 클릭")

    win = find_window(CLASS_DIALOG)
    if not win:
        print("[X] 비밀번호 창을 찾을 수 없습니다.")
        return False

    join_titles = ["회의 참가", "Join Meeting", "참가", "Join"]

    for title in join_titles:
        try:
            btn = win.child_window(title=title, control_type="Button")
            if btn.exists(timeout=1):
                print(f"[O] '{title}' 버튼 발견")
                btn.click_input()
                print("[O] 클릭 완료!")
                return True
        except:
            continue

    print("[X] 회의 참가 버튼을 찾을 수 없습니다.")
    return False


def dismiss_recording_popup():
    """녹화 알림 팝업 닫기"""
    try:
        desktop = Desktop(backend="uia")
        windows = desktop.windows()

        for win in windows:
            try:
                title = win.window_text()
                # 녹화 관련 팝업 감지
                if "녹화" in title or "recording" in title.lower():
                    print(f"[*] 녹화 알림 팝업 발견: {title}")
                    # 확인 버튼 찾기
                    for btn_title in ["확인", "OK", "Got it", "알겠습니다"]:
                        try:
                            btn = win.child_window(title=btn_title, control_type="Button")
                            if btn.exists(timeout=1):
                                btn.click_input()
                                print(f"[O] 녹화 알림 닫기 완료 ('{btn_title}')")
                                return True
                        except:
                            continue
            except:
                continue

        # 회의 창 내부의 팝업도 확인
        win = find_window(CLASS_MEETING, timeout=1)
        if win:
            for btn_title in ["확인", "OK", "Got it", "알겠습니다"]:
                try:
                    btn = win.child_window(title=btn_title, control_type="Button")
                    if btn.exists(timeout=1):
                        btn.click_input()
                        print(f"[O] 팝업 닫기 완료 ('{btn_title}')")
                        time.sleep(0.5)
                        return True
                except:
                    continue

    except Exception as e:
        print(f"[!] 팝업 처리 오류: {e}")

    return False


def step7_verify_connection():
    """회의 연결 확인"""
    print_step(7, "회의 연결 확인")

    print(f"[*] 회의 연결 대기 중... (최대 {CONNECT_WAIT}초)")

    for i in range(CONNECT_WAIT):
        time.sleep(1)

        # 녹화 알림 팝업 있으면 닫기
        dismiss_recording_popup()

        # 회의 창 찾기
        win = find_window(CLASS_MEETING, timeout=1)
        if not win:
            win = find_window(CLASS_DIALOG, timeout=1)
        if not win:
            continue

        # 회의 중 표시 요소 확인
        indicators = ["Mute", "음소거", "Leave", "나가기"]

        for title in indicators:
            try:
                elem = win.child_window(title_re=f".*{title}.*", control_type="Button")
                if elem.exists(timeout=0.5):
                    print(f"[O] 회의 연결 확인! ('{title}' 발견)")
                    return True
            except:
                continue

        if i % 5 == 4:
            print(f"    {i+1}초 경과...")

    print("[!] 연결 확인 타임아웃 (수동 확인 필요)")
    return False


def step8_maximize_window():
    """창 최대화"""
    print_step(8, "창 최대화")

    if not MAXIMIZE:
        print("[*] 설정에서 비활성화됨 (건너뜀)")
        return True

    # 방법 1: Win+Up 단축키
    try:
        pyautogui.hotkey("win", "up")
        time.sleep(0.5)
        print("[O] 최대화 완료 (Win+Up)")
        return True
    except Exception as e:
        print(f"[!] Win+Up 실패: {e}")

    # 방법 2: pywinauto maximize
    try:
        win = find_window(CLASS_MEETING, timeout=2)
        if win:
            win.maximize()
            print("[O] 최대화 완료 (pywinauto)")
            return True
    except:
        pass

    print("[!] 최대화 실패")
    return False


def step9_switch_view_mode():
    """보기 모드 전환 (화면 공유 중일 때만 필요)"""
    print_step(9, f"보기 모드 전환 ({VIEW_MODE})")

    win = find_window(CLASS_MEETING, timeout=2)
    if not win:
        print("[!] 회의 창을 찾을 수 없습니다.")
        return False

    print(f"[O] 회의 창 발견: {win.window_text()}")

    # 마우스를 상단으로 이동해서 메뉴 표시
    screen_width, screen_height = pyautogui.size()
    pyautogui.moveTo(screen_width // 2, 50)
    time.sleep(0.5)

    if VIEW_MODE == "gallery":
        view_titles = ["Gallery View", "갤러리 보기", "Gallery", "갤러리"]
    else:
        view_titles = ["Speaker View", "발표자 보기", "Speaker", "발표자"]

    # 버튼으로 시도
    for title in view_titles:
        try:
            btn = win.child_window(title_re=f".*{title}.*", control_type="Button")
            if btn.exists(timeout=1):
                print(f"[O] '{title}' 버튼 발견")
                btn.click_input()
                print("[O] 보기 모드 전환 완료!")
                return True
        except:
            continue

    # View 메뉴로 시도
    try:
        view_btn = win.child_window(title_re=".*View.*|.*보기.*", control_type="Button")
        if view_btn.exists(timeout=1):
            view_btn.click_input()
            time.sleep(0.5)
            for title in view_titles:
                try:
                    item = win.child_window(title_re=f".*{title}.*", control_type="MenuItem")
                    if item.exists(timeout=1):
                        item.click_input()
                        print(f"[O] '{title}' 메뉴 선택 완료!")
                        return True
                except:
                    continue
    except:
        pass

    # 버튼이 없으면 - 혼자이거나 이미 해당 모드임
    print("[*] 보기 모드 버튼 없음 (혼자이거나 이미 설정됨)")
    print("[O] 건너뜀")
    return True  # 실패가 아님


def step10_click_meeting_tab():
    """회의 탭 클릭 (좌표 기반)"""
    print_step(10, "회의 탭 클릭")

    win = find_window(CLASS_MEETING, timeout=5)
    if not win:
        print("[X] 회의 창을 찾을 수 없습니다.")
        return False

    print(f"[O] 창: {win.window_text()}")

    rect = win.rectangle()
    print(f"    창 위치: ({rect.left}, {rect.top})")
    print(f"    창 크기: {rect.width()} x {rect.height()}")

    # "회의" 탭 위치 (x=254, y=22)
    tab_x = rect.left + 254
    tab_y = rect.top + 22

    print(f"[*] 클릭 위치: ({tab_x}, {tab_y})")
    pyautogui.click(tab_x, tab_y, clicks=3, interval=0.3)
    print("[O] 3회 클릭 완료!")

    # 마우스를 왼쪽 하단 모서리 끝으로 이동
    time.sleep(0.3)
    screen_width, screen_height = pyautogui.size()
    pyautogui.moveTo(1, screen_height - 1)
    print(f"[O] 마우스 이동: (1, {screen_height - 1})")

    return True


def main():
    print("=" * 50)
    print("Zoom 회의 참가 전체 플로우")
    print("=" * 50)
    print()
    print(f"설정 파일: {CONFIG_PATH}")
    print(f"회의 ID: {MEETING_ID}")
    print(f"비밀번호: {'*' * len(PASSWORD) if PASSWORD else '(없음)'}")
    print(f"오디오 끄기: {NO_AUDIO}")
    print(f"최대화: {MAXIMIZE}")
    print(f"보기 모드: {VIEW_MODE}")
    print()

    #input("준비되면 Enter를 누르세요...")

    # Step 0: Zoom 실행
    if not step0_launch_zoom():
        print("\n[FAIL] Step 0 실패")
        return

    time.sleep(STEP_DELAY)

    # Step 1: Join 버튼 클릭
    if not step1_click_join():
        print("\n[FAIL] Step 1 실패")
        return

    time.sleep(STEP_DELAY)

    # Step 2: 회의 ID 입력
    if not step2_input_meeting_id():
        print("\n[FAIL] Step 2 실패")
        return

    time.sleep(STEP_DELAY)

    # Step 3: 오디오 연결 안함 체크
    step3_check_no_audio()

    time.sleep(STEP_DELAY)

    # Step 4: 참가 버튼 클릭
    if not step4_click_join_dialog():
        print("\n[FAIL] Step 4 실패")
        return

    # Step 5: 비밀번호 입력
    if not step5_input_password():
        print("\n[FAIL] Step 5 실패")
        return

    time.sleep(STEP_DELAY)

    # Step 6: 회의 참가 클릭
    if not step6_click_join_password():
        print("\n[FAIL] Step 6 실패")
        return

    # Step 7: 연결 확인
    if not step7_verify_connection():
        print("\n[WARN] 연결 확인 실패 (계속 진행)")

    time.sleep(1)

    # Step 8: 창 최대화
    step8_maximize_window()

    time.sleep(STEP_DELAY)

    # Step 9: 보기 모드 전환
    step9_switch_view_mode()

    time.sleep(STEP_DELAY)

    # Step 10: 회의 탭 클릭
    step10_click_meeting_tab()

    print()
    print("=" * 50)
    print("완료!")
    print("=" * 50)


if __name__ == "__main__":
    main()
