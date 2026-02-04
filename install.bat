@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║                                                          ║
echo  ║     강의장 녹화 업로드 클라이언트 설치 (EST/Jellyfin)    ║
echo  ║                                                          ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

set "INSTALL_DIR=%~dp0"

:: 관리자 권한 확인
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [오류] 관리자 권한으로 실행해주세요.
    echo.
    echo        이 파일을 우클릭 후 "관리자 권한으로 실행" 선택
    echo.
    pause
    exit /b 1
)

echo 이 설치 프로그램은 다음을 수행합니다:
echo.
echo   [1] Miniconda (Python 환경) 설치
echo   [2] 필요한 Python 패키지 설치
echo   [3] rclone (파일 전송 도구) 설치
echo   [4] 설정 (강의장, 녹화 폴더 등)
echo.
echo ──────────────────────────────────────────────────────────────
set /p "CONTINUE=설치를 시작하시겠습니까? (y/n): "
if /i not "%CONTINUE%"=="y" (
    echo 설치가 취소되었습니다.
    pause
    exit /b 0
)

:: ═══════════════════════════════════════════════════════════════
:: 단계 1-3: 기본 설치 (setup.bat 호출)
:: ═══════════════════════════════════════════════════════════════
echo.
echo ══════════════════════════════════════════════════════════════
echo  [단계 1-3] 기본 환경 설치
echo ══════════════════════════════════════════════════════════════

call "%INSTALL_DIR%setup.bat" /auto
if %errorLevel% neq 0 (
    echo [오류] 기본 설치 실패
    pause
    exit /b 1
)

:: ═══════════════════════════════════════════════════════════════
:: 단계 4: 설정
:: ═══════════════════════════════════════════════════════════════
echo.
echo ══════════════════════════════════════════════════════════════
echo  [단계 4] 설정
echo ══════════════════════════════════════════════════════════════
echo.

if exist "%INSTALL_DIR%config.yaml" (
    echo config.yaml이 이미 존재합니다.
    set /p "REINIT=다시 설정하시겠습니까? (y/n): "
    if /i not "!REINIT!"=="y" (
        echo 기존 설정을 유지합니다.
        goto DONE
    )
)

call "%INSTALL_DIR%run_init.bat"

:: ═══════════════════════════════════════════════════════════════
:: 설치 완료
:: ═══════════════════════════════════════════════════════════════
:DONE
echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║                                                          ║
echo  ║                    설치가 완료되었습니다!                ║
echo  ║                                                          ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.
echo  설치 위치: %INSTALL_DIR%
echo.
echo  주요 파일:
echo    - run_upload.bat  : 수동 업로드 실행
echo    - run_init.bat    : 설정 변경
echo    - update.bat      : 스크립트 업데이트 (git pull)
echo    - config.yaml     : 설정 파일
echo.
echo  rclone 설정이 필요하면:
echo    rclone\rclone.exe config
echo.
pause
