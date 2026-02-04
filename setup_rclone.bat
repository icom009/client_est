@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ============================================
echo   rclone SFTP 설정
echo ============================================
echo.

set "INSTALL_DIR=%~dp0"
set "RCLONE_EXE=%INSTALL_DIR%rclone\rclone.exe"
set "REMOTE_NAME=lms-sftp"
set "CONFIG_FILE=%INSTALL_DIR%config.yaml"

:: rclone 존재 확인
if not exist "%RCLONE_EXE%" (
    echo [오류] rclone이 설치되지 않았습니다.
    echo        먼저 setup.bat을 실행해주세요.
    pause
    exit /b 1
)

:: config.yaml에서 SFTP 정보 추출 시도
set "AUTO_CONFIG=0"
if exist "%CONFIG_FILE%" (
    echo config.yaml에서 SFTP 설정을 확인하는 중...

    :: Python으로 config.yaml 파싱
    for /f "tokens=*" %%i in ('python -c "import yaml; c=yaml.safe_load(open('%CONFIG_FILE%', encoding='utf-8')); s=c.get('sftp',{}); print(s.get('host','')+'|'+s.get('user','')+'|'+s.get('pass','')+'|'+s.get('path',''))" 2^>nul') do set "SFTP_INFO=%%i"

    if not "!SFTP_INFO!"=="|||" (
        for /f "tokens=1,2,3,4 delims=|" %%a in ("!SFTP_INFO!") do (
            set "SFTP_HOST=%%a"
            set "SFTP_USER=%%b"
            set "SFTP_PASS=%%c"
            set "SFTP_PATH=%%d"
        )

        if not "!SFTP_HOST!"=="" if not "!SFTP_USER!"=="" if not "!SFTP_PASS!"=="" (
            echo.
            echo [자동 설정 감지]
            echo   서버: !SFTP_HOST!
            echo   사용자: !SFTP_USER!
            echo   경로: !SFTP_PATH!
            echo.
            set "AUTO_CONFIG=1"
        )
    )
)

:: 기존 설정 확인
"%RCLONE_EXE%" listremotes | findstr /C:"%REMOTE_NAME%:" >nul 2>&1
if %errorLevel% equ 0 (
    echo [알림] '%REMOTE_NAME%' 설정이 이미 존재합니다.
    set /p "OVERWRITE=덮어쓰시겠습니까? (y/n): "
    if /i not "!OVERWRITE!"=="y" (
        echo 설정을 유지합니다.
        pause
        exit /b 0
    )
    "%RCLONE_EXE%" config delete %REMOTE_NAME%
)

:: 자동 설정 또는 수동 입력
if "%AUTO_CONFIG%"=="1" (
    echo 자동 설정을 사용합니다...
) else (
    echo.
    echo SFTP 서버 정보를 입력하세요.
    echo.

    set /p "SFTP_HOST=서버 주소 (예: mp.smhrd.or.kr): "
    set /p "SFTP_USER=사용자명: "
    set /p "SFTP_PASS=비밀번호: "
    set /p "SFTP_PATH=업로드 경로 (예: /mnt/data/KDT/녹화영상): "
)

echo.
echo 설정 생성 중...

:: rclone config 파일에 직접 추가
set "RCLONE_CONFIG=%APPDATA%\rclone\rclone.conf"
if not exist "%APPDATA%\rclone" mkdir "%APPDATA%\rclone"

:: 비밀번호 암호화
for /f "tokens=*" %%i in ('"%RCLONE_EXE%" obscure "!SFTP_PASS!"') do set "OBSCURED_PASS=%%i"

:: 설정 파일에 추가
(
echo.
echo [%REMOTE_NAME%]
echo type = sftp
echo host = !SFTP_HOST!
echo user = !SFTP_USER!
echo pass = !OBSCURED_PASS!
echo shell_type = unix
) >> "%RCLONE_CONFIG%"

echo.
echo 연결 테스트 중...
"%RCLONE_EXE%" lsd %REMOTE_NAME%:!SFTP_PATH! --max-depth 1 2>nul
if %errorLevel% neq 0 (
    echo.
    echo [경고] 연결 테스트 실패. 설정을 확인해주세요.
    echo        서버 주소, 사용자명, 비밀번호가 올바른지 확인하세요.
) else (
    echo.
    echo [성공] SFTP 연결 성공!
)

echo.
echo ============================================
echo   rclone SFTP 설정 완료
echo ============================================
echo.
echo Remote 이름: %REMOTE_NAME%
echo 설정 파일: %RCLONE_CONFIG%
echo.
echo 테스트 명령어:
echo   %RCLONE_EXE% ls %REMOTE_NAME%:!SFTP_PATH!/
echo.
pause
