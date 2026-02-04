"""
Zoom 회의 참가

사용법:
    python zoom_join.py           # config.yaml 설정으로 참가
    python zoom_join.py --quiet   # 로그 없이 실행

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
    9. 회의 탭 클릭
"""

import sys
from pathlib import Path

# 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from zoom_utils import join_meeting, get_config, CONFIG_PATH


def main():
    verbose = "--quiet" not in sys.argv and "-q" not in sys.argv

    if verbose:
        config = get_config()

        print("=" * 50)
        print("Zoom 회의 참가")
        print("=" * 50)
        print()
        print(f"설정 파일: {CONFIG_PATH}")
        print(f"회의 ID: {config['meeting_id']}")
        print(f"비밀번호: {'*' * len(config['password']) if config['password'] else '(없음)'}")
        print(f"오디오 끄기: {config['no_audio']}")
        print(f"최대화: {config['maximize']}")
        print(f"보기 모드: {config['view_mode']}")
        print()

    success = join_meeting(verbose=verbose)

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
