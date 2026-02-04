# 강의장 녹화 업로드 클라이언트 (EST/Jellyfin)

강의장 PC에서 녹화된 파일을 서버로 자동 업로드하는 클라이언트입니다.
Jellyfin이 폴더를 감시하여 업로드된 파일을 자동으로 인식합니다.

## 설치

### 방법 1: Git Clone (권장)
```batch
git clone https://github.com/icom009/client_est.git
cd client_est
install.bat
```

### 방법 2: ZIP 다운로드
1. [Download ZIP](https://github.com/icom009/client_est/archive/refs/heads/main.zip) 클릭
2. 압축 해제
3. `install.bat` 실행 (관리자 권한)

## 업데이트

```batch
cd client_est
git pull
```

또는 `update.bat` 실행

## 사용법

### 자동 업로드 (작업 스케줄러)
- `run_upload_auto.bat`를 Windows 작업 스케줄러에 등록
- 점심시간/퇴근 후 자동 실행

### 수동 업로드
- `run_upload.bat` 실행

### 설정 변경
- `run_init.bat` 실행

## 파일 구조

```
client_est/
├── install.bat          # 전체 설치 마법사
├── setup.bat            # 환경 설치 (Miniconda, rclone)
├── run_upload.bat       # 수동 업로드
├── run_upload_auto.bat  # 자동 업로드 (스케줄러용)
├── run_init.bat         # 설정 변경
├── update.bat           # 업데이트 (git pull)
├── config.yaml          # 설정 파일 (설치 후 생성)
└── logs/                # 로그 폴더
```

## 설정 파일 (config.yaml)

```yaml
classroom_name: "EST"
folder_name: ""              # 서버 업로드 폴더명
recording_folder: "D:\\OBS녹화"
uploaded_folder: "D:\\OBS녹화\\uploaded"
rclone:
  remote_name: "est-sftp"
  remote_path: "/recordings"
  bandwidth_limit: "0"
```

## rclone 설정

```batch
rclone\rclone.exe config
```

SFTP 리모트 예시:
- Type: sftp
- Host: 서버주소
- User: 사용자명
- Password: 비밀번호

## 문제 해결

### 로그 확인
`logs/upload_YYYYMMDD.log` 파일 확인
