# SmartMeet AI (Parakeet ASR)

API transcribe tiếng Việt cho SmartMeet. BE gọi endpoint:

```
POST http://localhost:8000/api/transcribe/chunk
```

## Yêu cầu

| Thành phần | Ghi chú |
|---|---|
| Python | 3.10 hoặc 3.11 (khuyến nghị; tránh 3.12+ nếu NeMo lỗi) |
| ffmpeg | Bắt buộc cho pydub |
| Model `.nemo` | `data/nemo_models/parakeet-ctc-0.6b-vi.nemo` |
| RAM | ~4GB+ (CPU), ~6GB+ VRAM nếu dùng GPU |

## Chạy trên Windows (PowerShell)

### Bước 1 — Cài ffmpeg

```powershell
winget install Gyan.FFmpeg
```

Đóng/mở lại terminal, kiểm tra:

```powershell
ffmpeg -version
```

### Bước 2 — Setup Python env

```powershell
cd E:\KhoaLuan\AI\smart-meet-parakeet
.\scripts\setup.ps1
```

### Bước 3 — Đặt file model

Copy model vào:

```
E:\KhoaLuan\AI\smart-meet-parakeet\data\nemo_models\parakeet-ctc-0.6b-vi.nemo
```

Hoặc set biến môi trường:

```powershell
$env:PARAKEET_MODEL_PATH = "D:\path\to\parakeet-ctc-0.6b-vi.nemo"
```

### Bước 4 — Chạy server

```powershell
.\scripts\run.ps1
```

Mở trình duyệt / curl:

```powershell
curl http://127.0.0.1:8000/
# {"message":"Server is running"}
```

Lần đầu startup sẽ **load model** (có thể mất 1–3 phút).

### Bước 5 — Test endpoint chunk

```powershell
curl -X POST "http://127.0.0.1:8000/api/transcribe/chunk" `
  -F "audio_bytes=@test.wav"
```

## Chạy thủ công (không dùng script)

```powershell
cd E:\KhoaLuan\AI\smart-meet-parakeet
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## GPU NVIDIA (tuỳ chọn, nhanh hơn)

Trong venv, cài lại PyTorch CUDA (ví dụ CUDA 12.1):

```powershell
pip uninstall torch torchaudio -y
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

Server tự chọn `cuda` nếu `torch.cuda.is_available()` = true.

## Kết nối với BE

Trong `BE/smart-meet-be/src/main/resources/application.yml`:

```yaml
ai-server:
  transcribe-url: http://localhost:8000/api/transcribe/chunk
```

## Lưu ý Windows

- **Đã sửa** hardcode ffmpeg macOS (`/opt/homebrew/bin/ffmpeg`) → tự tìm trên PATH.
- **NeMo trên Windows native** có thể gặp lỗi phụ thuộc. Nếu `pip install nemo_toolkit[asr]` fail:
  - Dùng **WSL2 Ubuntu** + GPU, hoặc
  - Python 3.10 trong venv riêng.
- Folder `data/` bị gitignore — model không commit lên repo.

## API

| Method | Path | Mô tả |
|---|---|---|
| GET | `/` | Health check |
| POST | `/api/transcribe` | Transcribe file dài (upload) |
| POST | `/api/transcribe/chunk` | Transcribe chunk realtime (BE dùng) |
