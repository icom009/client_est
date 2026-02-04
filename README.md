# EST 강의장 자동화 클라이언트

강의장 녹화 및 출결 관리를 위한 자동화 스크립트 모음입니다.

- **녹화 파일 업로드**: rclone으로 SFTP 서버에 자동 업로드
- **출결 화면 캡처**: 교시별 Zoom 화면 자동 스크린샷
- **Zoom 자동화**: 회의 자동 참가/퇴장, 네트워크 끊김 자동 복구
- **OBS 녹화 제어**: WebSocket으로 녹화 시작/중지

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

자세한 설치 과정은 `설치가이드.txt` 참고

## 업데이트

```batch
cd client_est
git pull
```

또는 `update.bat` 실행

## 사용법

### 자동 업로드 (작업 스케줄러)
- `register_task.bat` 실행하여 작업 스케줄러에 등록
- 10분마다 + 로그온 시 자동 실행

### 수동 업로드
- `run_upload.bat` 실행

### 설정 변경
- `run_init.bat` 실행

## 파일 구조

```
client_est/
├── install.bat          # 전체 설치 마법사
├── setup.bat            # 환경 설치 (Miniconda, rclone)
├── setup_rclone.bat     # rclone SFTP 설정
├── register_task.bat    # 작업 스케줄러 등록
├── run_upload.bat       # 수동 업로드
├── run_upload_auto.bat  # 자동 업로드 (스케줄러용)
├── run_init.bat         # 설정 변경
├── update.bat           # 업데이트 (git pull)
├── config.yaml          # 설정 파일 (설치 후 생성)
├── logs/                # 로그 폴더
│
├── 설치가이드.txt       # Windows 설치 안내
├── OBS_설정가이드.txt   # OBS 상세 설정 안내
│
├── capture/             # 출결 화면 캡처
│   ├── estcapture.py    # 교시별 스크린샷
│   └── flask_server.py  # 캡처 API 서버
│
├── obs/                 # OBS 녹화 제어
│   ├── obs_start.ps1    # OBS 실행
│   ├── obs_recordStart.py  # 녹화 시작
│   └── obs_recordStop.py   # 녹화 중지
│
├── task_scheduler/      # 작업 스케줄러 XML
│   └── 녹화파일_자동업로드.xml
│
└── zoom/                # Zoom 자동화 (출결용 특수 케이스)
    ├── zoom_utils.py    # 핵심 유틸리티 모듈
    ├── zoom_check.py    # 사전 체크 (캡처 15분 전)
    ├── zoom_join.py     # 회의 참가
    ├── zoom_leave.py    # 회의 나가기
    ├── move_videos.py   # 녹화 파일 이동
    └── config.example.yaml  # 설정 예시
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

---

## 출결 화면 캡처 (capture/)

교시별 출결 화면을 자동으로 스크린샷합니다.

### 스크린샷 (estcapture.py)
```bash
# 자동 모드 (트리거 시간에만 촬영)
python capture/estcapture.py

# 강제 모드 (즉시 촬영)
python capture/estcapture.py --force

# 7교시 단축 스케줄
python capture/estcapture.py 7
```

저장 위치: `C:\Users\{username}\Desktop\출결\YYYYMMDD\`

### Flask 서버 (flask_server.py)
```bash
# 서버 실행 (포트 8000)
python capture/flask_server.py
```

- `GET /ui` - 캡처 버튼 UI
- `POST /capture` - 스크린샷 촬영
- `GET /health` - 헬스체크

---

## OBS 녹화 제어 (obs/)

OBS WebSocket을 통해 녹화를 제어합니다.

### 사전 설정
1. OBS에서 WebSocket 서버 활성화
2. 포트: 4455, 비밀번호 설정

### 사용법
```bash
# OBS 실행
powershell -File obs/obs_start.ps1

# 녹화 시작
python obs/obs_recordStart.py

# 녹화 중지
python obs/obs_recordStop.py
```

---

## Zoom 자동화 (zoom/)

> **특수 케이스**: 이 모듈은 EST 출결 시스템 전용입니다.
> 원격 강의 출결 확인을 위해 Zoom 회의 화면을 캡처해야 하는 환경에서 사용됩니다.
> - 네트워크 불안정 시 자동 재연결
> - 캡처 전 회의 상태 사전 체크
> - 회의 창 자동 활성화

### 파일 구조
```
zoom/
├── zoom_utils.py        # 핵심 유틸리티 모듈
├── zoom_check.py        # 사전 체크 (캡처 15분 전 실행)
├── zoom_join.py         # 회의 참가
├── zoom_leave.py        # 회의 나가기
├── move_videos.py       # 녹화 파일 이동
└── config.example.yaml  # 설정 예시
```

### 설정
```bash
# config.example.yaml을 config.yaml로 복사 후 수정
cp zoom/config.example.yaml zoom/config.yaml
```

### 사용법
```bash
# 회의 상태 사전 체크 (캡처 전에 실행)
python zoom/zoom_check.py

# 회의 참가
python zoom/zoom_join.py

# 회의 나가기
python zoom/zoom_leave.py

# 녹화 파일 이동
python zoom/move_videos.py
```

### 네트워크 끊김 자동 복구

`zoom_check.py` 또는 `estcapture.py` 실행 시:
1. 연결 끊김 경고창 감지 → 자동으로 닫기
2. Zoom 앱 정리 후 회의 재참가
3. 회의 창 활성화 + 회의 탭 클릭

### 작업 스케줄러 예시

```
08:55  zoom_check.py     ← 사전 체크
09:10  estcapture.py     ← 캡처

09:45  zoom_check.py
10:00  estcapture.py
...
```

---

## 의존성

```bash
pip install pillow flask pyyaml obsws-python pywinauto pyautogui pywin32
```
