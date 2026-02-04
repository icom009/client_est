#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
강의장 녹화 파일 업로드 (EST/Jellyfin용)

- 녹화 폴더에서 새 파일 감지
- rclone으로 서버 업로드 (진행률 표시)
- 업로드 완료 파일 이동

사용법:
  python upload_recording.py          # 대화형 모드
  python upload_recording.py --auto   # 자동 모드 (작업 스케줄러용)
"""

import os
import re
import sys
import time
import shutil
import logging
import argparse
import subprocess
import yaml
from pathlib import Path
from datetime import datetime

# 설정 파일 경로
SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "config.yaml"
LOG_DIR = SCRIPT_DIR / "logs"


def setup_logging(auto_mode=False):
    """로깅 설정"""
    LOG_DIR.mkdir(exist_ok=True)

    log_file = LOG_DIR / f"upload_{datetime.now().strftime('%Y%m%d')}.log"

    handlers = [logging.FileHandler(log_file, encoding='utf-8')]
    if not auto_mode:
        handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=handlers
    )
    return logging.getLogger(__name__)


def load_config():
    """설정 로드"""
    if not CONFIG_PATH.exists():
        print("✗ 설정 파일이 없습니다. init_config.py를 먼저 실행해주세요.")
        print("\n  python init_config.py")
        sys.exit(1)

    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_new_files(config):
    """업로드할 새 파일 목록"""
    recording_folder = config['recording_folder']
    uploaded_folder = config.get('uploaded_folder', os.path.join(recording_folder, 'uploaded'))
    extensions = config.get('extensions', ['.mp4', '.mkv'])

    # 업로드 완료 폴더 생성
    os.makedirs(uploaded_folder, exist_ok=True)

    # 이미 업로드된 파일 목록
    uploaded_files = set()
    if os.path.exists(uploaded_folder):
        uploaded_files = set(os.listdir(uploaded_folder))

    # 새 파일 찾기
    new_files = []
    for file in os.listdir(recording_folder):
        file_path = os.path.join(recording_folder, file)

        # 파일인지 확인
        if not os.path.isfile(file_path):
            continue

        # 확장자 확인
        ext = os.path.splitext(file)[1].lower()
        if ext not in extensions:
            continue

        # 이미 업로드된 파일 제외
        if file in uploaded_files:
            continue

        # 파일이 아직 쓰기 중인지 확인 (최근 수정 시간)
        mtime = os.path.getmtime(file_path)
        if time.time() - mtime < 60:  # 1분 이내 수정된 파일은 건너뜀
            print(f"  건너뜀 (쓰기 중): {file}")
            continue

        new_files.append({
            'name': file,
            'path': file_path,
            'size': os.path.getsize(file_path)
        })

    return new_files


def format_size(size_bytes):
    """파일 크기 포맷"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}PB"


def upload_with_rclone(config, file_info):
    """rclone으로 파일 업로드"""
    file_name = file_info['name']
    file_path = file_info['path']
    file_size = file_info['size']

    remote_name = config.get('rclone', {}).get('remote_name', 'est-sftp')
    bandwidth_limit = config.get('rclone', {}).get('bandwidth_limit', '0')
    remote_path_base = config.get('rclone', {}).get('remote_path', '/recordings')
    folder_name = config.get('folder_name', '')

    # 원격 경로
    if folder_name:
        remote_path = f"{remote_name}:{remote_path_base}/{folder_name}/"
    else:
        remote_path = f"{remote_name}:{remote_path_base}/"

    # rclone 명령어
    cmd = [
        'rclone', 'copy',
        file_path,
        remote_path,
        '--progress',
        '--stats-one-line',
        '--stats', '2s',
        '-v'
    ]

    if bandwidth_limit and bandwidth_limit != '0':
        cmd.extend(['--bwlimit', bandwidth_limit])

    print(f"\n업로드 시작: {file_name}")
    print(f"  크기: {format_size(file_size)}")
    print(f"  대상: {remote_path}")
    print("-" * 50)

    # 진행률 정규식
    progress_pattern = re.compile(
        r'Transferred:\s+[\d.]+\s+\w+\s*/\s*[\d.]+\s+\w+,\s*(\d+)%,\s*([\d.]+\s*\w+/s),\s*ETA\s*(\S+)'
    )

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in process.stdout:
            match = progress_pattern.search(line)
            if match:
                percent = int(match.group(1))
                speed = match.group(2)
                eta = match.group(3)

                # 콘솔 출력
                bar_width = 30
                filled = int(bar_width * percent / 100)
                bar = '█' * filled + '░' * (bar_width - filled)
                print(f"\r  [{bar}] {percent}% | {speed} | ETA: {eta}    ", end='', flush=True)

        process.wait()
        print()  # 줄바꿈

        if process.returncode == 0:
            return True, f"{remote_path}{file_name}"
        else:
            return False, f"rclone 오류 (코드: {process.returncode})"

    except FileNotFoundError:
        return False, "rclone이 설치되지 않았습니다. https://rclone.org/downloads/"
    except Exception as e:
        return False, str(e)


def move_to_uploaded(config, file_info):
    """업로드 완료 파일 이동"""
    uploaded_folder = config.get('uploaded_folder')
    if not uploaded_folder:
        return

    os.makedirs(uploaded_folder, exist_ok=True)
    src = file_info['path']
    dst = os.path.join(uploaded_folder, file_info['name'])

    try:
        shutil.move(src, dst)
        print(f"  파일 이동됨: {uploaded_folder}")
    except Exception as e:
        print(f"  파일 이동 실패: {e}")


def main():
    # 명령행 인자 파싱
    parser = argparse.ArgumentParser(description='강의장 녹화 파일 업로드 (EST)')
    parser.add_argument('--auto', action='store_true', help='자동 모드 (작업 스케줄러용)')
    args = parser.parse_args()

    auto_mode = args.auto
    logger = setup_logging(auto_mode)

    if not auto_mode:
        print("=" * 60)
        print("     강의장 녹화 파일 업로드 (EST)")
        print("=" * 60)
        print()

    logger.info("=" * 40)
    logger.info("업로드 작업 시작")

    # 설정 로드
    config = load_config()

    logger.info(f"강의장: {config.get('classroom_name', 'N/A')}")
    logger.info(f"녹화 폴더: {config['recording_folder']}")

    if not auto_mode:
        print(f"강의장: {config.get('classroom_name', 'N/A')}")
        print(f"녹화 폴더: {config['recording_folder']}")
        print()

    # 새 파일 찾기
    if not auto_mode:
        print("새 파일 검색 중...")
    new_files = get_new_files(config)

    if not new_files:
        logger.info("업로드할 새 파일 없음")
        if not auto_mode:
            print("\n업로드할 새 파일이 없습니다.")
        return

    logger.info(f"발견된 파일: {len(new_files)}개")
    for f in new_files:
        logger.info(f"  - {f['name']} ({format_size(f['size'])})")

    if not auto_mode:
        print(f"\n발견된 파일: {len(new_files)}개")
        for f in new_files:
            print(f"  - {f['name']} ({format_size(f['size'])})")

        # 대화형 모드에서만 확인
        print()
        confirm = input("업로드를 시작할까요? (Y/n): ").strip().lower()
        if confirm == 'n':
            print("취소되었습니다.")
            logger.info("사용자가 취소함")
            return

    # 업로드 시작
    success_count = 0
    fail_count = 0

    for file_info in new_files:
        logger.info(f"업로드 시작: {file_info['name']}")

        # 업로드
        success, result = upload_with_rclone(config, file_info)

        if success:
            logger.info(f"업로드 완료: {file_info['name']}")
            if not auto_mode:
                print(f"✓ 업로드 완료: {file_info['name']}")

            # 파일 이동
            move_to_uploaded(config, file_info)
            success_count += 1
        else:
            logger.error(f"업로드 실패: {file_info['name']} - {result}")
            if not auto_mode:
                print(f"✗ 업로드 실패: {file_info['name']}")
                print(f"  오류: {result}")
            fail_count += 1

    # 결과 요약
    logger.info(f"작업 완료: {success_count}개 성공, {fail_count}개 실패")
    logger.info("=" * 40)

    if not auto_mode:
        print()
        print("=" * 60)
        print(f"  완료: {success_count}개 성공, {fail_count}개 실패")
        print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n취소되었습니다.")
        sys.exit(1)
    except Exception as e:
        logging.exception(f"예기치 않은 오류: {e}")
        sys.exit(1)
