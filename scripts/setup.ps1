# Setup moi truong AI tren Windows
# Usage: .\scripts\setup.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "=== SmartMeet AI - Windows Setup ===" -ForegroundColor Cyan

# 1. Python venv
if (-not (Test-Path ".\.venv")) {
    Write-Host "Tao virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip

# 2. Dependencies co ban
Write-Host "Cai dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# 3. PyTorch (CPU — on dinh nhat tren Windows native)
Write-Host "Cai PyTorch (CPU)..." -ForegroundColor Yellow
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# 4. NeMo ASR
Write-Host "Cai NeMo toolkit..." -ForegroundColor Yellow
pip install "nemo_toolkit[asr]"

# 5. Thu muc model
$modelDir = Join-Path $ProjectRoot "data\nemo_models"
New-Item -ItemType Directory -Force -Path $modelDir | Out-Null

Write-Host ""
Write-Host "=== Setup xong ===" -ForegroundColor Green
Write-Host "Buoc tiep theo:"
Write-Host "  1. Cai ffmpeg:  winget install Gyan.FFmpeg"
Write-Host "  2. Dat model:   data\nemo_models\parakeet-ctc-0.6b-vi.nemo"
Write-Host "  3. Chay server: .\scripts\run.ps1"
Write-Host ""
Write-Host "Neu co GPU NVIDIA, xem README.md de cai PyTorch CUDA."
