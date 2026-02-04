@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: 자동 모드 확인 (install.bat에서 호출 시)
set "AUTO_MODE=0"
if "%~1"=="/auto" set "AUTO_MODE=1"

echo ============================================
echo   강의장 녹화 업로드 클라이언트 설치 (EST)
echo ============================================
echo.

:: 설정 변수
set "INSTALL_DIR=%~dp0"
set "MINICONDA_DIR=%USERPROFILE%\Miniconda3"
set "ENV_NAME=est_upload"
set "RCLONE_DIR=%INSTALL_DIR%rclone"

:: 관리자 권한 확인
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [오류] 관리자 권한으로 실행해주세요.
    echo        이 파일을 우클릭 ^> "관리자 권한으로 실행"
    if "%AUTO_MODE%"=="0" pause
    exit /b 1
)

echo [1/5] Miniconda 설치 확인...
if exist "%MINICONDA_DIR%\Scripts\conda.exe" (
    echo       Miniconda 이미 설치됨: %MINICONDA_DIR%
) else (
    echo       Miniconda 다운로드 중...

    :: Miniconda 다운로드
    set "MINICONDA_URL=https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"
    set "MINICONDA_INSTALLER=%TEMP%\Miniconda3-latest-Windows-x86_64.exe"

    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%MINICONDA_URL%' -OutFile '%MINICONDA_INSTALLER%'}"

    if not exist "%MINICONDA_INSTALLER%" (
        echo [오류] Miniconda 다운로드 실패
        if "%AUTO_MODE%"=="0" pause
        exit /b 1
    )

    echo       Miniconda 설치 중... (2-3분 소요)
    start /wait "" "%MINICONDA_INSTALLER%" /InstallationType=JustMe /RegisterPython=0 /S /D=%MINICONDA_DIR%

    if not exist "%MINICONDA_DIR%\Scripts\conda.exe" (
        echo [오류] Miniconda 설치 실패
        if "%AUTO_MODE%"=="0" pause
        exit /b 1
    )

    del "%MINICONDA_INSTALLER%"
    echo       Miniconda 설치 완료
)

echo.
echo [2/5] Conda 환경 생성...

:: conda 초기화
call "%MINICONDA_DIR%\Scripts\activate.bat"

:: 환경 존재 여부 확인
conda env list | findstr /C:"%ENV_NAME%" >nul 2>&1
if %errorLevel% equ 0 (
    echo       환경 '%ENV_NAME%' 이미 존재함
) else (
    echo       환경 '%ENV_NAME%' 생성 중...
    call conda create -n %ENV_NAME% python=3.10 -y
    if %errorLevel% neq 0 (
        echo [오류] Conda 환경 생성 실패
        if "%AUTO_MODE%"=="0" pause
        exit /b 1
    )
    echo       환경 생성 완료
)

echo.
echo [3/5] Python 패키지 설치...
call conda activate %ENV_NAME%

pip install pyyaml --quiet
if %errorLevel% neq 0 (
    echo [오류] 패키지 설치 실패
    if "%AUTO_MODE%"=="0" pause
    exit /b 1
)
echo       패키지 설치 완료: pyyaml

echo.
echo [4/5] rclone 설치 확인...

if exist "%RCLONE_DIR%\rclone.exe" (
    echo       rclone 이미 설치됨: %RCLONE_DIR%
) else (
    echo       rclone 다운로드 중...

    set "RCLONE_URL=https://downloads.rclone.org/rclone-current-windows-amd64.zip"
    set "RCLONE_ZIP=%TEMP%\rclone.zip"
    set "RCLONE_TEMP=%TEMP%\rclone_temp"

    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%RCLONE_URL%' -OutFile '%RCLONE_ZIP%'}"

    if not exist "%RCLONE_ZIP%" (
        echo [오류] rclone 다운로드 실패
        if "%AUTO_MODE%"=="0" pause
        exit /b 1
    )

    echo       rclone 압축 해제 중...
    powershell -Command "Expand-Archive -Path '%RCLONE_ZIP%' -DestinationPath '%RCLONE_TEMP%' -Force"

    :: rclone 폴더 생성 및 복사
    if not exist "%RCLONE_DIR%" mkdir "%RCLONE_DIR%"
    for /d %%i in ("%RCLONE_TEMP%\rclone-*") do (
        copy "%%i\rclone.exe" "%RCLONE_DIR%\" >nul
    )

    :: 정리
    del "%RCLONE_ZIP%"
    rmdir /s /q "%RCLONE_TEMP%"

    if not exist "%RCLONE_DIR%\rclone.exe" (
        echo [오류] rclone 설치 실패
        if "%AUTO_MODE%"=="0" pause
        exit /b 1
    )
    echo       rclone 설치 완료
)

echo.
echo [5/5] 실행 스크립트 생성...

:: run_upload.bat 생성 (대화형)
(
echo @echo off
echo chcp 65001 ^>nul
echo call "%MINICONDA_DIR%\Scripts\activate.bat"
echo call conda activate %ENV_NAME%
echo cd /d "%INSTALL_DIR%"
echo python upload_recording.py %%*
echo pause
) > "%INSTALL_DIR%run_upload.bat"

:: run_upload_auto.bat 생성 (작업 스케줄러용)
(
echo @echo off
echo chcp 65001 ^>nul
echo call "%MINICONDA_DIR%\Scripts\activate.bat"
echo call conda activate %ENV_NAME%
echo cd /d "%INSTALL_DIR%"
echo python upload_recording.py --auto
) > "%INSTALL_DIR%run_upload_auto.bat"

:: run_init.bat 생성
(
echo @echo off
echo chcp 65001 ^>nul
echo call "%MINICONDA_DIR%\Scripts\activate.bat"
echo call conda activate %ENV_NAME%
echo cd /d "%INSTALL_DIR%"
echo python init_config.py
echo pause
) > "%INSTALL_DIR%run_init.bat"

:: update.bat 생성 (git pull)
(
echo @echo off
echo chcp 65001 ^>nul
echo cd /d "%INSTALL_DIR%"
echo echo 업데이트 확인 중...
echo git pull
echo echo.
echo echo 업데이트 완료!
echo pause
) > "%INSTALL_DIR%update.bat"

echo       실행 스크립트 생성 완료

echo.
echo ============================================
echo   설치 완료!
echo ============================================
echo.
echo 다음 단계:
echo   1. run_init.bat 실행하여 설정
echo   2. rclone 설정 (rclone config)
echo   3. run_upload.bat로 업로드 테스트
echo.
echo 업데이트:
echo   - update.bat 실행 (git pull)
echo.
if "%AUTO_MODE%"=="0" pause
