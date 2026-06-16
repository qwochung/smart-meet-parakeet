# Chạy AI server trên Windows (PowerShell)
# Usage: .\scripts\run.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (-not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
    Write-Host "Chua co .venv. Chay scripts\setup.ps1 truoc." -ForegroundColor Red
    exit 1
}

. .\.venv\Scripts\Activate.ps1

$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ffmpeg) {
    Write-Host "Canh bao: ffmpeg chua co tren PATH." -ForegroundColor Yellow
    Write-Host "Cai dat: winget install Gyan.FFmpeg" -ForegroundColor Yellow
    Write-Host "Sau do mo lai terminal." -ForegroundColor Yellow
}

$modelPath = Join-Path $ProjectRoot "data\nemo_models\parakeet-ctc-0.6b-vi.nemo"
if (-not (Test-Path $modelPath)) {
    Write-Host "Canh bao: chua tim thay model tai:" -ForegroundColor Yellow
    Write-Host "  $modelPath" -ForegroundColor Yellow
}

Write-Host "Starting SmartMeet AI at http://127.0.0.1:8000" -ForegroundColor Green
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
