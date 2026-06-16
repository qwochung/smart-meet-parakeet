import io
import os
import shutil
import sys
import tempfile

from fastapi import UploadFile
from loguru import logger
from pydub import AudioSegment, effects

PADDING_MS = 400

# Windows / Linux: dùng ffmpeg trên PATH.
# macOS: fallback Homebrew nếu chưa có trong PATH.
def _configure_ffmpeg() -> None:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")

    if not ffmpeg and sys.platform == "darwin":
        for candidate in ("/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"):
            if os.path.isfile(candidate):
                ffmpeg = candidate
                break

    if not ffprobe and sys.platform == "darwin":
        for candidate in ("/opt/homebrew/bin/ffprobe", "/usr/local/bin/ffprobe"):
            if os.path.isfile(candidate):
                ffprobe = candidate
                break

    if ffmpeg:
        AudioSegment.converter = ffmpeg
    else:
        logger.warning(
            "ffmpeg not found on PATH. Install ffmpeg and add it to PATH "
            "(Windows: winget install Gyan.FFmpeg)."
        )

    if ffprobe:
        AudioSegment.ffprobe = ffprobe


_configure_ffmpeg()


def apply_silence_padding(audio: AudioSegment, padding_duration_ms: int = PADDING_MS) -> AudioSegment:
    silence = AudioSegment.silent(duration=padding_duration_ms, frame_rate=audio.frame_rate)
    return silence + audio + silence


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
        audio = effects.normalize(audio)
        audio = audio.set_sample_width(2)
        audio.export(clean_wav_path, format="wav", codec="pcm_s16le")
        return clean_wav_path

    finally:
        if os.path.exists(raw_path):
            os.remove(raw_path)


async def process_audio_chunk(audio_bytes: UploadFile) -> str:
    """Xử lý chunk audio real-time: padding silence, convert 16kHz mono, lưu file tạm"""
    bytes_data = await audio_bytes.read()

    audio = AudioSegment.from_file(io.BytesIO(bytes_data))
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)
    audio = effects.normalize(audio)
    audio = audio.set_sample_width(2)
    audio = apply_silence_padding(audio)

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp_path = tmp.name
    audio.export(tmp_path, format="wav", codec="pcm_s16le")
    tmp.close()

    return tmp_path


def cleanup_temp_file(file_path: str):
    """Xóa file tạm sau khi đã sử dụng xong"""
    if os.path.exists(file_path):
        os.remove(file_path)
