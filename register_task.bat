@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ============================================
echo   Windows 작업 스케줄러 등록
echo ============================================
echo.

set "INSTALL_DIR=%~dp0"
set "TASK_NAME=LMS_녹화파일_자동업로드"

:: 관리자 권한 확인
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [오류] 관리자 권한으로 실행해주세요.
    echo        이 파일을 우클릭 ^> "관리자 권한으로 실행"
    pause
    exit /b 1
)

:: config.yaml 존재 확인
if not exist "%INSTALL_DIR%config.yaml" (
    echo [오류] config.yaml이 없습니다.
    echo        먼저 run_init.bat을 실행하여 설정을 완료해주세요.
    pause
    exit /b 1
)

:: 기존 작업 삭제 (있으면)
schtasks /Query /TN "%TASK_NAME%" >nul 2>&1
if %errorLevel% equ 0 (
    echo 기존 작업 '%TASK_NAME%' 삭제 중...
    schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1
)

:: run_upload_auto.bat 존재 확인
if not exist "%INSTALL_DIR%run_upload_auto.bat" (
    echo [오류] run_upload_auto.bat이 없습니다.
    echo        먼저 setup.bat을 실행해주세요.
    pause
    exit /b 1
)

:: XML 파일 경로 수정을 위한 임시 파일 생성
set "TEMP_XML=%TEMP%\lms_task.xml"
set "ORIGINAL_XML=%INSTALL_DIR%task_scheduler\녹화파일_자동업로드.xml"

:: XML 파일 복사 및 경로 수정
powershell -Command "(Get-Content '%ORIGINAL_XML%' -Raw) -replace 'C:\\lms_client', '%INSTALL_DIR:\=\\%'.TrimEnd('\\') | Set-Content '%TEMP_XML%' -Encoding Unicode"

echo 작업 스케줄러에 등록 중...
schtasks /Create /TN "%TASK_NAME%" /XML "%TEMP_XML%" /F

if %errorLevel% neq 0 (
    echo.
    echo [오류] 작업 등록 실패
    del "%TEMP_XML%" 2>nul
    pause
    exit /b 1
)

del "%TEMP_XML%" 2>nul

echo.
echo ============================================
echo   작업 스케줄러 등록 완료!
echo ============================================
echo.
echo 작업 이름: %TASK_NAME%
echo 실행 주기: 10분마다 + 로그온 시
echo.
echo 작업 확인: taskschd.msc
echo 수동 실행: schtasks /Run /TN "%TASK_NAME%"
echo 작업 삭제: schtasks /Delete /TN "%TASK_NAME%" /F
echo.
pause
