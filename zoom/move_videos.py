import os
import shutil
from pathlib import Path

# 경로 설정
source_dir = Path(r"C:\Users\smhrd\Videos")
dest_dir = Path(r"C:\Users\smhrd\Desktop\출결\obs녹화")

# 비디오 파일 확장자
video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}

# 대상 폴더가 없으면 생성
dest_dir.mkdir(parents=True, exist_ok=True)

# 이동한 파일 수
moved_count = 0

# 비디오 파일 찾아서 이동
for file in source_dir.iterdir():
    if file.is_file() and file.suffix.lower() in video_extensions:
        dest_path = dest_dir / file.name

        # 동일한 이름의 파일이 있으면 번호 추가
        if dest_path.exists():
            base = file.stem
            ext = file.suffix
            counter = 1
            while dest_path.exists():
                dest_path = dest_dir / f"{base}_{counter}{ext}"
                counter += 1

        shutil.move(str(file), str(dest_path))
        print(f"이동 완료: {file.name} -> {dest_path}")
        moved_count += 1

print(f"\n총 {moved_count}개의 비디오 파일을 이동했습니다.")
