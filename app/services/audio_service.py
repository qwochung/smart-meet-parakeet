import os
import tempfile


from fastapi import UploadFile
from pydub import AudioSegment

# CHỈ ĐIỂM ĐÍCH DANH CHO MÁY MAC M4:
AudioSegment.converter = "/opt/homebrew/bin/ffmpeg"
AudioSegment.ffprobe   = "/opt/homebrew/bin/ffprobe"

async def process_audio_file(upload_file: UploadFile) -> str:
    """Xử lý file âm thanh thô thành file .wav chuẩn 16kHz cho Parakeet"""
    bytes_data = await upload_file.read()

    file_ext = os.path.splitext(upload_file.filename)[1] or ".webm"
    _, raw_path = tempfile.mkstemp(suffix=file_ext)

    with open(raw_path, "wb") as f:
        f.write(bytes_data)

    _, clean_wav_path = tempfile.mkstemp(suffix=".wav")

    try:
        audio = AudioSegment.from_file(raw_path)
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(16000)
        audio.export(clean_wav_path, format="wav")
        return clean_wav_path

    finally:
        if os.path.exists(raw_path):
            os.remove(raw_path)

def cleanup_temp_file(file_path: str):
    """Xóa file tạm sau khi đã sử dụng xong"""
    if os.path.exists(file_path):
        os.remove(file_path)