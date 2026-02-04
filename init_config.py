#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
강의장 클라이언트 초기 설정 (EST/Jellyfin용)

간단한 설정만 필요:
- 강의장 이름
- 녹화 폴더
- rclone 리모트 설정
"""

import os
import sys
import yaml
from pathlib import Path

# 설정 파일 경로
CONFIG_PATH = Path(__file__).parent / "config.yaml"


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(title="강의장 녹화 업로드 클라이언트 (EST)"):
    clear_screen()
    print("=" * 60)
    print(f"     {title}")
    print("=" * 60)
    print()


def load_config():
    """설정 로드"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return None


def save_config(config):
    """설정 저장"""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(config, allow_unicode=True, default_flow_style=False, sort_keys=False, stream=f)
    print(f"\n✓ 설정이 저장되었습니다: {CONFIG_PATH}")


def get_input(prompt, default=None):
    """입력 받기 (기본값 지원)"""
    if default:
        result = input(f"{prompt} [{default}]: ").strip()
        return result if result else default
    return input(f"{prompt}: ").strip()


def ensure_folder(folder_path):
    """폴더 존재 확인 및 생성"""
    if not os.path.exists(folder_path):
        create = input(f"\n폴더가 존재하지 않습니다. 생성할까요? (Y/n): ").strip().lower()
        if create != 'n':
            os.makedirs(folder_path, exist_ok=True)
            print(f"✓ 폴더 생성됨: {folder_path}")


def edit_config_menu(config):
    """설정 수정 메뉴"""
    while True:
        print_header("설정 수정")

        print("현재 설정:")
        print("-" * 40)
        print(f"  1. 강의장 이름: {config.get('classroom_name', 'N/A')}")
        print(f"  2. 폴더 이름: {config.get('folder_name', 'N/A')}")
        print(f"  3. 녹화 폴더: {config.get('recording_folder', 'N/A')}")
        print(f"  4. 업로드 완료 폴더: {config.get('uploaded_folder', 'N/A')}")
        print(f"  5. rclone 리모트: {config.get('rclone', {}).get('remote_name', 'N/A')}")
        print(f"  6. rclone 경로: {config.get('rclone', {}).get('remote_path', 'N/A')}")
        print(f"  7. 대역폭 제한: {config.get('rclone', {}).get('bandwidth_limit', '0')} (0=무제한)")
        print()
        print("-" * 40)
        print("  0. 저장 후 종료")
        print("  q. 저장하지 않고 종료")
        print()

        choice = input("수정할 항목 (번호): ").strip().lower()

        if choice == '0':
            save_config(config)
            return True
        elif choice == 'q':
            print("\n변경 사항이 저장되지 않았습니다.")
            return False
        elif choice == '1':
            config['classroom_name'] = get_input("강의장 이름", config.get('classroom_name', 'EST'))
        elif choice == '2':
            config['folder_name'] = get_input("폴더 이름 (서버 업로드 경로)", config.get('folder_name', ''))
        elif choice == '3':
            new_folder = get_input("녹화 폴더 경로", config.get('recording_folder', 'D:\\OBS녹화'))
            config['recording_folder'] = new_folder
            ensure_folder(new_folder)
        elif choice == '4':
            new_folder = get_input("업로드 완료 폴더 경로", config.get('uploaded_folder', 'D:\\OBS녹화\\uploaded'))
            config['uploaded_folder'] = new_folder
            ensure_folder(new_folder)
        elif choice == '5':
            if 'rclone' not in config:
                config['rclone'] = {}
            config['rclone']['remote_name'] = get_input("rclone 리모트 이름", config.get('rclone', {}).get('remote_name', 'est-sftp'))
        elif choice == '6':
            if 'rclone' not in config:
                config['rclone'] = {}
            config['rclone']['remote_path'] = get_input("rclone 원격 경로", config.get('rclone', {}).get('remote_path', '/recordings'))
        elif choice == '7':
            if 'rclone' not in config:
                config['rclone'] = {}
            bw = get_input("대역폭 제한 (0=무제한, 예: 50M)", config.get('rclone', {}).get('bandwidth_limit', '0'))
            config['rclone']['bandwidth_limit'] = bw


def initial_setup():
    """초기 설정"""
    print_header("초기 설정")

    print("EST/Jellyfin용 녹화 업로드 클라이언트입니다.")
    print("녹화 파일을 서버에 업로드하면 Jellyfin이 자동으로 인식합니다.")
    print()

    # 1. 강의장 이름
    classroom_name = get_input("강의장 이름", "EST")
    if not classroom_name:
        classroom_name = "EST"

    # 2. 폴더 이름 (서버 경로)
    folder_name = get_input("서버 업로드 폴더명 (빈칸=루트)", "")

    # 3. 녹화 폴더
    print("\n녹화 폴더 설정")
    print("-" * 40)
    recording_folder = get_input("녹화 파일 폴더", "D:\\OBS녹화")
    ensure_folder(recording_folder)

    uploaded_folder = get_input("업로드 완료 폴더", "D:\\OBS녹화\\uploaded")
    ensure_folder(uploaded_folder)

    # 4. rclone 설정
    print("\nrclone 설정")
    print("-" * 40)
    print("rclone 리모트를 미리 설정해두세요 (rclone config)")
    remote_name = get_input("rclone 리모트 이름", "est-sftp")
    remote_path = get_input("원격 경로", "/recordings")

    # 설정 저장
    config = {
        'classroom_name': classroom_name,
        'folder_name': folder_name,
        'recording_folder': recording_folder,
        'uploaded_folder': uploaded_folder,
        'extensions': ['.mp4', '.mkv', '.avi', '.mov'],
        'rclone': {
            'remote_name': remote_name,
            'remote_path': remote_path,
            'bandwidth_limit': '0',
        }
    }

    save_config(config)
    print("\n✓ 초기 설정 완료!")
    print("\n다음 단계:")
    print("  1. rclone config로 리모트 설정 (아직 안했다면)")
    print("  2. run_upload.bat로 업로드 테스트")


def main():
    config = load_config()

    if config:
        # config.yaml 있음 → 수정 모드
        print_header("설정 관리")
        print("기존 설정이 있습니다.")
        print()
        print(f"  강의장: {config.get('classroom_name', 'N/A')}")
        print(f"  녹화 폴더: {config.get('recording_folder', 'N/A')}")
        print()

        choice = input("설정을 수정하시겠습니까? (y/N): ").strip().lower()
        if choice == 'y':
            edit_config_menu(config)
        else:
            print("\n현재 설정을 유지합니다.")
    else:
        # config.yaml 없음 → 초기 설정
        initial_setup()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n취소되었습니다.")
        sys.exit(1)
