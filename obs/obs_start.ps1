# OBS 실행 파일 경로
$obsPath = "C:\Program Files\obs-studio\bin\64bit\obs64.exe"

# OBS 실행 폴더 (Working Directory)
$obsWorkingDir = "C:\Program Files\obs-studio\bin\64bit"

# OBS가 실행 중인지 확인
function Is-OBSRunning {
    Get-Process | Where-Object { $_.ProcessName -eq "obs64" } | ForEach-Object {
        return $true
    }
    return $false
}

# OBS 실행 함수
function Start-OBS {
    if (Test-Path $obsPath) {
        Start-Process -FilePath $obsPath -WorkingDirectory $obsWorkingDir
        Write-Output "OBS를 실행했습니다. 시작 폴더: $obsWorkingDir"
    } else {
        Write-Output "OBS 실행 파일을 찾을 수 없습니다: $obsPath"
    }
}

# 메인 로직
if (-not (Is-OBSRunning)) {
    Write-Output "OBS가 실행 중이지 않습니다. 실행을 시도합니다..."
    Start-OBS
} else {
    Write-Output "OBS가 이미 실행 중입니다."
}

