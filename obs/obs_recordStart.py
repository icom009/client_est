import obsws_python as obs
import time
import win32gui
import win32con

WEBSOCKET_HOST = "localhost"
WEBSOCKET_PORT = 4455
WEBSOCKET_PASSWORD = "gsD35D5WctVDY6lH"

OBS_TITLE_KEYWORD = "OBS"  # 로그 보고 필요하면 조정

def minimize_obs():
    targets = []

    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if OBS_TITLE_KEYWORD.lower() in title.lower():
                targets.append((hwnd, title))

    win32gui.EnumWindows(callback, None)

    if not targets:
        print("OBS 창을 찾지 못했습니다.")
        return

    hwnd, title = targets[0]
    print(f"찾은 OBS 창 제목: {title} (hwnd={hwnd})")

    # 포커스 맞춰주기 시도
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass

    time.sleep(0.1)

    # 여러 방식으로 최소화 시도
    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
    time.sleep(0.1)
    win32gui.ShowWindow(hwnd, win32con.SW_SHOWMINIMIZED)
    time.sleep(0.1)
    win32gui.PostMessage(hwnd, win32con.WM_SYSCOMMAND, win32con.SC_MINIMIZE, 0)

    print("OBS 창 최소화 명령들을 전송했습니다.")

def start_recording():
    """OBS WebSocket으로 녹화 시작"""
    try:
        ws = obs.ReqClient(
            host=WEBSOCKET_HOST,
            port=WEBSOCKET_PORT,
            password=WEBSOCKET_PASSWORD,
            timeout=3
        )
        print("OBS WebSocket에 연결되었습니다.")

        ws.start_record()
        print("녹화를 시작했습니다.")

        ws.disconnect()
        print("WebSocket 연결을 종료했습니다.")

        # 녹화 시작 후 OBS가 본격적으로 반응할 시간 조금 주고
        time.sleep(1.5)
        minimize_obs()

    except Exception as e:
        print(f"녹화 시작 실패 또는 WebSocket 연결 오류: {e}")

if __name__ == "__main__":
    # 실행 직후 여유 10초
    time.sleep(10)
    start_recording()
