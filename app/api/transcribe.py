import asyncio
import time

from typing import Optional
from app.services.audio_service import process_audio_file, process_audio_chunk, cleanup_temp_file
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.models.asr_parakeet import transcribe, transcribe_chunk

router = APIRouter(
    prefix="/api/transcribe",
    tags=["Transcription"]
)

_transcribe_lock = asyncio.Lock()


@router.post("")
async def transcribe_meeting_audio(audio_file: UploadFile = File(...)):
    start_time = time.time()
    clean_wav_path = ""

    try:
        async with _transcribe_lock:
            clean_wav_path = await process_audio_file(audio_file)
            result = await asyncio.to_thread(transcribe, clean_wav_path)
        process_time = round(time.time() - start_time, 2)

        return {
            "status": "success",
            "file_name": audio_file.filename,
            "text": result,
            "process_time_seconds": process_time
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if clean_wav_path:
            cleanup_temp_file(clean_wav_path)


@router.post("/chunk")
async def transcribe_audio_chunk(
    audio_bytes: UploadFile = File(...),
    sample_rate: Optional[int] = Form(None),
    channels: Optional[int] = Form(None),
):
    wav_path = None
    try:
        async with _transcribe_lock:
            wav_path = await process_audio_chunk(audio_bytes)
            text = await asyncio.to_thread(transcribe_chunk, wav_path)
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if wav_path:
            cleanup_temp_file(wav_path)

