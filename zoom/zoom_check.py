"""
Zoom 회의 상태 사전 체크

캡처 시간 2~3분 전에 실행하여 Zoom 상태를 미리 확인합니다.
- 경고창 있으면 닫고 재참가
- 회의 연결 안됨 → 재참가
- 정상이면 창 활성화만

사용법:
    python zoom_check.py           # 상태 확인 + 필요시 재참가
    python zoom_check.py --quiet   # 로그 없이 실행
"""

import sys
from pathlib import Path

# 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from zoom_utils import ensure_meeting, is_in_meeting, check_disconnect_alert


def main():
    verbose = "--quiet" not in sys.argv and "-q" not in sys.argv

    if verbose:
        print("=" * 50)
        print("Zoom 회의 상태 사전 체크")
        print("=" * 50)
        print()

    success = ensure_meeting(verbose=verbose)

    if verbose:
        print()
        print("=" * 50)
        if success:
            print("결과: 회의 준비 완료")
        else:
            print("결과: 회의 연결 실패")
        print("=" * 50)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
