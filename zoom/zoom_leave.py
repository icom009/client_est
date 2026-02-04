"""
Zoom 회의 나가기 및 종료

사용법:
    python zoom_leave.py           # 회의 나가기 + Zoom 종료
    python zoom_leave.py --quiet   # 로그 없이 실행
    python zoom_leave.py --keep    # Zoom 앱은 종료하지 않음

플로우:
    1. 회의 창 찾기
    2. Leave/나가기 버튼 클릭
    3. Leave Meeting 확인
    4. Zoom 앱 종료 (선택)
"""

import sys
from pathlib import Path

# 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from zoom_utils import leave_meeting, get_config, CONFIG_PATH


def main():
    verbose = "--quiet" not in sys.argv and "-q" not in sys.argv
    keep_app = "--keep" in sys.argv or "-k" in sys.argv

    config = get_config()
    close_app = not keep_app and config["close_app"]

    if verbose:
        print("=" * 50)
        print("Zoom 회의 나가기 및 종료")
        print("=" * 50)
        print()
        print(f"설정 파일: {CONFIG_PATH}")
        print(f"앱 종료: {close_app}")
        print()

    success = leave_meeting(close_app=close_app, verbose=verbose)

    if verbose:
        print()
        print("=" * 50)
        if success:
            print("완료!")
        else:
            print("실패!")
        print("=" * 50)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
