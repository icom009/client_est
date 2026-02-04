"""
Zoom 자동화 유틸리티 모듈

다른 스크립트에서 import해서 사용:
    from zoom_utils import ensure_meeting, is_in_meeting, activate_meeting_window
"""

import os
import subprocess
import time
from pathlib import Path

import yaml
from pywinauto import Application, Desktop
import pyautogui

# ============================================
# 설정
# ============================================
CONFIG_PATH = Path(__file__).parent / "config.yaml"

# Zoom 창 클래스명
CLASS_MAIN = "ZPPTMainFrmWndClassEx"        # 메인 화면
CLASS_DIALOG = "zWaitingMeetingIDWndClass"  # 참가/비밀번호 다이얼로그
CLASS_MEETING = "ConfMultiTabContentWndClass"  # 회의 중 창

# Zoom 실행 경로
ZOOM_PATH = r"C:\Users\{}\AppData\Roaming\Zoom\bin\Zoom.exe".format(
    os.environ.get("USERNAME", "")
)


def load_config():
    """config.yaml 로드"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def get_config():
    """설정값 가져오기"""
    config = load_config()
    return {
        "meeting_id": config.get("meeting", {}).get("id", ""),
        "password": config.get("meeting", {}).get("password", ""),
        "no_audio": config.get("meeting", {}).get("no_audio", True),
        "maximize": config.get("window", {}).get("maximize", True),
        "view_mode": config.get("window", {}).get("view_mode", "gallery"),
        "dialog_wait": config.get("timing", {}).get("dialog_wait", 10),
        "password_wait": config.get("timing", {}).get("password_wait", 3),
        "connect_wait": config.get("timing", {}).get("connect_wait", 30),
        "step_delay": config.get("timing", {}).get("step_delay", 0.5),
        "close_app": config.get("leave", {}).get("close_app", True),
    }


# ============================================
# 창 찾기 유틸리티
# ============================================
def find_window(class_name, timeout=5):
    """클래스명으로 창 찾기"""
    try:
        app = Application(backend="uia").connect(class_name=class_name, timeout=timeout)
        return app.top_window()
    except:
        return None


def find_meeting_window(timeout=2):
    """회의 창 찾기"""
    return find_window(CLASS_MEETING, timeout=timeout)


def find_main_window(timeout=2):
    """메인 창 찾기"""
    return find_window(CLASS_MAIN, timeout=timeout)


def find_dialog_window(timeout=2):
    """다이얼로그 창 찾기"""
    return find_window(CLASS_DIALOG, timeout=timeout)


# ============================================
# 상태 확인 함수
# ============================================
def is_zoom_running():
    """Zoom이 실행 중인지 확인"""
    try:
        Application(backend="uia").connect(class_name=CLASS_MAIN, timeout=1)
        return True
    except:
        return False


def is_in_meeting():
    """현재 회의 중인지 확인"""
    # 회의 창 존재 확인
    win = find_meeting_window(timeout=1)
    if win:
        return True

    # Leave 버튼이 있는지 확인 (회의 중 표시)
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


def check_meeting_active():
    """회의 창이 활성화되어 있고 정상 상태인지 확인"""
    win = find_meeting_window(timeout=1)
    if not win:
        return False, "회의 창 없음"

    # 회의 창이 있으면 추가 확인 (음소거/나가기 버튼 존재)
    try:
        indicators = ["Mute", "음소거", "Leave", "나가기"]
        for title in indicators:
            try:
                elem = win.child_window(title_re=f".*{title}.*", control_type="Button")
                if elem.exists(timeout=0.5):
                    return True, "정상"
            except:
                continue
    except:
        pass

    return True, "창 존재 (상태 미확인)"


# ============================================
# 경고창/팝업 처리 함수
# ============================================
def check_disconnect_alert():
    """
    네트워크 끊김 경고창이 있는지 확인

    Returns:
        bool: 경고창 존재 여부
    """
    disconnect_keywords = [
        # 한글
        "연결이 끊어", "연결 끊김", "연결이 불안정", "네트워크 연결",
        "회의에서 연결", "재연결", "인터넷 연결",
        # 영문
        "disconnected", "connection", "unstable", "reconnect",
        "network", "internet", "lost connection"
    ]

    try:
        desktop = Desktop(backend="uia")
        for win in desktop.windows():
            try:
                title = win.window_text().lower()
                for keyword in disconnect_keywords:
                    if keyword.lower() in title:
                        return True

                # 창 내부 텍스트도 확인
                try:
                    texts = win.descendants(control_type="Text")
                    for t in texts[:10]:  # 최대 10개만 확인
                        text = t.window_text().lower()
                        for keyword in disconnect_keywords:
                            if keyword.lower() in text:
                                return True
                except:
                    pass
            except:
                continue
    except:
        pass

    return False


def dismiss_disconnect_alert():
    """
    네트워크 끊김 경고창 닫기

    Returns:
        bool: 경고창을 닫았는지 여부
    """
    dismiss_buttons = [
        # 한글
        "확인", "닫기", "나가기", "회의 나가기", "종료",
        # 영문
        "OK", "Close", "Leave", "Leave Meeting", "End", "Got it"
    ]

    dismissed = False

    try:
        desktop = Desktop(backend="uia")
        for win in desktop.windows():
            try:
                # 버튼 찾아서 클릭
                for btn_title in dismiss_buttons:
                    try:
                        btn = win.child_window(title=btn_title, control_type="Button")
                        if btn.exists(timeout=0.3):
                            btn.click_input()
                            time.sleep(0.5)
                            dismissed = True
                    except:
                        continue

                # title_re로도 시도
                for btn_title in dismiss_buttons:
                    try:
                        btn = win.child_window(title_re=f".*{btn_title}.*", control_type="Button")
                        if btn.exists(timeout=0.3):
                            btn.click_input()
                            time.sleep(0.5)
                            dismissed = True
                    except:
                        continue
            except:
                continue
    except:
        pass

    return dismissed


def cleanup_zoom():
    """
    Zoom 앱 완전 종료 (깔끔한 재시작을 위해)

    Returns:
        bool: 성공 여부
    """
    # 경고창 닫기 시도
    for _ in range(3):
        dismiss_disconnect_alert()
        time.sleep(0.3)

    # 모든 Zoom 창 닫기
    try:
        desktop = Desktop(backend="uia")
        for win in desktop.windows():
            try:
                class_name = win.class_name()
                if "zoom" in class_name.lower() or class_name.startswith("ZP"):
                    try:
                        win.close()
                    except:
                        pass
            except:
                continue
    except:
        pass

    time.sleep(1)

    # taskkill로 프로세스 강제 종료
    try:
        subprocess.run(
            ["taskkill", "/f", "/im", "Zoom.exe"],
            capture_output=True,
            text=True
        )
    except:
        pass

    time.sleep(1)
    return True


# ============================================
# 창 제어 함수
# ============================================
def activate_meeting_window():
    """회의 창 활성화 및 최대화"""
    win = find_meeting_window(timeout=2)
    if not win:
        return False

    try:
        # 창 활성화
        win.set_focus()
        time.sleep(0.3)

        # 최대화
        win.maximize()
        time.sleep(0.3)

        return True
    except Exception as e:
        print(f"[!] 창 활성화 실패: {e}")
        return False


def click_meeting_tab():
    """회의 탭 클릭 (화면 공유 시 회의 화면으로 전환)"""
    win = find_meeting_window(timeout=2)
    if not win:
        return False

    try:
        rect = win.rectangle()

        # "회의" 탭 위치 (x=254, y=22)
        tab_x = rect.left + 254
        tab_y = rect.top + 22

        pyautogui.click(tab_x, tab_y, clicks=3, interval=0.3)
        time.sleep(0.3)

        # 마우스를 화면 구석으로 이동
        screen_width, screen_height = pyautogui.size()
        pyautogui.moveTo(1, screen_height - 1)

        return True
    except Exception as e:
        print(f"[!] 탭 클릭 실패: {e}")
        return False


# ============================================
# Zoom 실행 함수
# ============================================
def launch_zoom():
    """Zoom 실행 (꺼져있으면)"""
    if is_zoom_running():
        return True

    # Zoom 실행
    if os.path.exists(ZOOM_PATH):
        subprocess.Popen([ZOOM_PATH])
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
                launched = True
                break

        if not launched:
            try:
                os.startfile("zoom")
            except:
                return False

    # 메인 창 대기
    for i in range(30):
        time.sleep(1)
        if is_zoom_running():
            time.sleep(1)
            return True

    return False


# ============================================
# 회의 참가 함수
# ============================================
def join_meeting(meeting_id=None, password=None, no_audio=True, verbose=True):
    """
    회의 참가 전체 플로우

    Args:
        meeting_id: 회의 ID (None이면 config에서 로드)
        password: 비밀번호 (None이면 config에서 로드)
        no_audio: 오디오 연결 안함
        verbose: 로그 출력 여부

    Returns:
        bool: 성공 여부
    """
    config = get_config()

    if meeting_id is None:
        meeting_id = config["meeting_id"]
    if password is None:
        password = config["password"]

    step_delay = config["step_delay"]
    dialog_wait = config["dialog_wait"]
    password_wait = config["password_wait"]
    connect_wait = config["connect_wait"]

    def log(msg):
        if verbose:
            print(msg)

    # Step 0: Zoom 실행
    log("[Step 0] Zoom 실행 확인")
    if not launch_zoom():
        log("[X] Zoom 실행 실패")
        return False
    log("[O] Zoom 실행됨")
    time.sleep(step_delay)

    # Step 1: Join 버튼 클릭
    log("[Step 1] Join 버튼 클릭")
    win = find_main_window()
    if not win:
        log("[X] 메인 창 없음")
        return False

    join_titles = ["Join", "참가", "Join a Meeting", "회의 참가"]
    clicked = False
    for title in join_titles:
        try:
            btn = win.child_window(title=title, control_type="Button")
            if btn.exists(timeout=2):
                btn.click_input()
                clicked = True
                break
        except:
            continue

    if not clicked:
        log("[X] Join 버튼 없음")
        return False
    log("[O] Join 클릭 완료")
    time.sleep(step_delay)

    # Step 2: 회의 ID 입력
    log("[Step 2] 회의 ID 입력")
    win = None
    for i in range(dialog_wait):
        time.sleep(1)
        win = find_dialog_window(timeout=1)
        if win:
            break

    if not win:
        log("[X] 다이얼로그 없음")
        return False

    try:
        edit = win.child_window(control_type="Edit", found_index=0)
        if edit.exists(timeout=2):
            edit.click_input()
            time.sleep(0.1)
            edit.type_keys("^a")
            time.sleep(0.05)
            edit.type_keys(meeting_id, with_spaces=True)
            log(f"[O] 회의 ID 입력: {meeting_id}")
    except Exception as e:
        log(f"[X] ID 입력 실패: {e}")
        return False

    time.sleep(step_delay)

    # Step 3: 오디오 연결 안함 체크
    if no_audio:
        log("[Step 3] 오디오 연결 안함 체크")
        win = find_dialog_window()
        if win:
            try:
                chk = win.child_window(title="오디오에 연결하지 않음", control_type="CheckBox")
                if chk.exists(timeout=2):
                    if not chk.get_toggle_state():
                        chk.click_input()
                    log("[O] 체크 완료")
            except:
                try:
                    chk = win.child_window(title="Don't connect to audio", control_type="CheckBox")
                    if chk.exists(timeout=1):
                        if not chk.get_toggle_state():
                            chk.click_input()
                        log("[O] 체크 완료")
                except:
                    pass

    time.sleep(step_delay)

    # Step 4: 참가 버튼 클릭
    log("[Step 4] 참가 버튼 클릭")
    win = find_dialog_window()
    if not win:
        log("[X] 다이얼로그 없음")
        return False

    join_titles = ["참가", "Join", "Join Meeting", "회의 참가"]
    clicked = False
    for title in join_titles:
        try:
            btn = win.child_window(title=title, control_type="Button")
            if btn.exists(timeout=1):
                btn.click_input()
                clicked = True
                break
        except:
            continue

    if not clicked:
        log("[X] 참가 버튼 없음")
        return False
    log("[O] 참가 클릭 완료")

    # Step 5: 비밀번호 입력
    if password:
        log("[Step 5] 비밀번호 입력")
        time.sleep(password_wait)

        win = find_dialog_window()
        if win:
            try:
                edit = win.child_window(control_type="Edit")
                if edit.exists(timeout=2):
                    edit.click_input()
                    time.sleep(0.1)
                    edit.type_keys(password)
                    log("[O] 비밀번호 입력 완료")
            except Exception as e:
                log(f"[X] 비밀번호 입력 실패: {e}")
                return False

            time.sleep(step_delay)

            # Step 6: 회의 참가 클릭
            log("[Step 6] 회의 참가 클릭")
            join_titles = ["회의 참가", "Join Meeting", "참가", "Join"]
            for title in join_titles:
                try:
                    btn = win.child_window(title=title, control_type="Button")
                    if btn.exists(timeout=1):
                        btn.click_input()
                        log("[O] 회의 참가 클릭 완료")
                        break
                except:
                    continue

    # Step 7: 연결 확인
    log("[Step 7] 연결 확인 중...")
    for i in range(connect_wait):
        time.sleep(1)

        # 녹화 알림 팝업 닫기
        _dismiss_popups()

        if is_in_meeting():
            log(f"[O] 회의 연결 확인! ({i+1}초)")
            break

        if (i + 1) % 10 == 0:
            log(f"    {i+1}초 경과...")
    else:
        log("[!] 연결 확인 타임아웃")
        return False

    time.sleep(1)

    # Step 8: 창 최대화
    log("[Step 8] 창 최대화")
    activate_meeting_window()
    time.sleep(step_delay)

    # Step 9: 회의 탭 클릭
    log("[Step 9] 회의 탭 클릭")
    click_meeting_tab()

    log("[완료] 회의 참가 성공!")
    return True


def _dismiss_popups():
    """녹화 알림 등 팝업 닫기"""
    try:
        desktop = Desktop(backend="uia")
        for win in desktop.windows():
            try:
                title = win.window_text()
                if "녹화" in title or "recording" in title.lower():
                    for btn_title in ["확인", "OK", "Got it", "알겠습니다"]:
                        try:
                            btn = win.child_window(title=btn_title, control_type="Button")
                            if btn.exists(timeout=0.5):
                                btn.click_input()
                                return True
                        except:
                            continue
            except:
                continue

        # 회의 창 내부 팝업
        win = find_meeting_window(timeout=1)
        if win:
            for btn_title in ["확인", "OK", "Got it", "알겠습니다"]:
                try:
                    btn = win.child_window(title=btn_title, control_type="Button")
                    if btn.exists(timeout=0.5):
                        btn.click_input()
                        time.sleep(0.3)
                        return True
                except:
                    continue
    except:
        pass
    return False


# ============================================
# 회의 나가기 함수
# ============================================
def leave_meeting(close_app=None, verbose=True):
    """
    회의 나가기

    Args:
        close_app: Zoom 앱도 종료할지 (None이면 config에서 로드)
        verbose: 로그 출력 여부

    Returns:
        bool: 성공 여부
    """
    config = get_config()

    if close_app is None:
        close_app = config["close_app"]

    step_delay = config["step_delay"]

    def log(msg):
        if verbose:
            print(msg)

    # Step 1: 회의 창 찾기
    log("[Step 1] 회의 창 찾기")
    win = find_meeting_window(timeout=2)
    if not win:
        win = find_dialog_window(timeout=2)
    if not win:
        win = find_main_window(timeout=2)

    if not win:
        log("[INFO] Zoom이 실행 중이 아닙니다.")
        return True

    log(f"[O] 창 발견: {win.window_text()}")
    time.sleep(step_delay)

    # 회의 중인지 확인
    if is_in_meeting():
        # Step 2: Leave 버튼 클릭
        log("[Step 2] Leave 버튼 클릭")

        # 마우스를 화면 하단으로 이동 (툴바 표시)
        screen_width, screen_height = pyautogui.size()
        pyautogui.moveTo(screen_width // 2, screen_height - 100)
        time.sleep(0.5)

        leave_titles = ["Leave", "나가기", "End", "종료", "Leave Meeting", "회의 나가기"]
        clicked = False
        for title in leave_titles:
            try:
                btn = win.child_window(title_re=f".*{title}.*", control_type="Button")
                if btn.exists(timeout=1):
                    btn.click_input()
                    clicked = True
                    log(f"[O] '{title}' 클릭 완료")
                    break
            except:
                continue

        if clicked:
            time.sleep(step_delay)

            # Step 3: 확인 클릭
            log("[Step 3] 확인 클릭")
            time.sleep(0.5)

            desktop = Desktop(backend="uia")
            confirm_titles = [
                "Leave Meeting", "회의 나가기", "Leave", "나가기",
                "End Meeting", "회의 종료"
            ]

            for attempt in range(5):
                try:
                    for w in desktop.windows():
                        try:
                            for title in confirm_titles:
                                try:
                                    btn = w.child_window(title=title, control_type="Button")
                                    if btn.exists(timeout=0.5):
                                        btn.click_input()
                                        log(f"[O] '{title}' 확인 완료")
                                        break
                                except:
                                    continue
                        except:
                            continue
                except:
                    pass
                time.sleep(0.3)

            # Enter 키 시도
            pyautogui.press("enter")
    else:
        log("[INFO] 현재 회의 중이 아닙니다.")

    time.sleep(step_delay)

    # Step 4: Zoom 앱 종료
    if close_app:
        log("[Step 4] Zoom 앱 종료")
        time.sleep(2)

        win = find_main_window(timeout=2)
        if win:
            try:
                win.close()
                time.sleep(1)
            except:
                pass

        try:
            subprocess.run(["taskkill", "/f", "/im", "Zoom.exe"],
                         capture_output=True, text=True)
            log("[O] Zoom 종료 완료")
        except:
            pass

    log("[완료] 회의 나가기 성공!")
    return True


# ============================================
# 핵심 함수: ensure_meeting
# ============================================
def ensure_meeting(verbose=True):
    """
    회의 연결 상태 확인 및 필요시 재참가

    캡처 전에 호출하면 됨:
        if ensure_meeting():
            take_screenshot()

    처리 흐름:
        1. 연결 끊김 경고창 확인 → 있으면 Zoom 정리 후 재참가
        2. 회의 중인지 확인 → 회의 중이면 창 활성화
        3. 회의 중 아님 → 재참가

    Args:
        verbose: 로그 출력 여부

    Returns:
        bool: 회의 활성화 여부
    """
    def log(msg):
        if verbose:
            print(msg)

    log("=" * 50)
    log("회의 상태 확인")
    log("=" * 50)

    need_rejoin = False

    # 1. 연결 끊김 경고창 확인 → 있으면 닫고 재참가 필요
    if check_disconnect_alert():
        log("[!] 연결 끊김 경고창 감지")
        log("[*] 경고창 닫는 중...")
        dismiss_disconnect_alert()
        time.sleep(0.5)
        need_rejoin = True

    # 2. 회의 중인지 확인
    elif not is_in_meeting():
        log("[X] 회의 연결 안됨")
        need_rejoin = True

    # 3. 재참가 필요하면 Zoom 정리 후 재참가
    if need_rejoin:
        log("[*] Zoom 정리 중...")
        cleanup_zoom()
        log("[O] Zoom 정리 완료")
        log("")
        log("회의 참가 시작...")

        if not join_meeting(verbose=verbose):
            log("[X] 회의 재참가 실패")
            return False
        log("[O] 회의 재참가 성공!")
    else:
        log("[O] 회의 연결 중")

    # 4. 공통: 창 활성화 + 탭 클릭 (재참가 여부와 무관하게 항상 실행)
    log("")
    log("[*] 창 활성화 중...")
    if activate_meeting_window():
        log("[O] 창 활성화 완료")
    else:
        log("[!] 창 활성화 실패")

    click_meeting_tab()
    log("[O] 회의 탭 클릭 완료")

    return True


# ============================================
# 테스트
# ============================================
if __name__ == "__main__":
    print("Zoom 유틸리티 테스트")
    print("=" * 50)
    print()

    print(f"설정 파일: {CONFIG_PATH}")
    print(f"Zoom 실행 중: {is_zoom_running()}")
    print(f"회의 중: {is_in_meeting()}")

    active, status = check_meeting_active()
    print(f"회의 창 상태: {status}")
    print()

    # ensure_meeting 테스트
    # result = ensure_meeting()
    # print(f"\nensure_meeting 결과: {result}")
