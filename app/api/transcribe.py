import asyncio
import os
import time

from typing import Optional
from app.services.audio_service import process_audio_file, process_audio_chunk, cleanup_temp_file
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from loguru import logger
from app.models.asr_parakeet import prepare_chunk_paths, transcribe_batch, transcribe_chunk

router = APIRouter(
    prefix="/api/transcribe",
    tags=["Transcription"]
)

# Lock bảo vệ model (GPU) — chỉ giữ trong lúc inference, không giữ suốt cả request
_transcribe_lock = asyncio.Lock()

# Số chunk xử lý mỗi lần giữ lock khi transcribe file dài,
# để các chunk realtime (/chunk) chen vào giữa được thay vì chờ cả file
_FILE_BATCH_SIZE = 2


@router.post("")
async def transcribe_meeting_audio(audio_file: UploadFile = File(...)):
    start_time = time.time()
    clean_wav_path = ""
    chunk_paths = []

    try:
        clean_wav_path = await process_audio_file(audio_file)
        chunk_paths = await asyncio.to_thread(prepare_chunk_paths, clean_wav_path)

        texts = []
        for i in range(0, len(chunk_paths), _FILE_BATCH_SIZE):
            batch = chunk_paths[i:i + _FILE_BATCH_SIZE]
            async with _transcribe_lock:
                texts.extend(await asyncio.to_thread(transcribe_batch, batch))

        process_time = round(time.time() - start_time, 2)

        return {
            "status": "success",
            "file_name": audio_file.filename,
            "text": " ".join(texts),
            "process_time_seconds": process_time,
        }

    except Exception as e:
        logger.exception("Transcription failed for file {}: {}", audio_file.filename, e)
        raise HTTPException(status_code=500, detail="Transcription failed")

    finally:
        for p in chunk_paths:
            cleanup_temp_file(p)
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
        wav_path = await process_audio_chunk(audio_bytes)
        async with _transcribe_lock:
            text = await asyncio.to_thread(transcribe_chunk, wav_path)
        return {"text": text}
    except Exception as e:
        logger.exception("Chunk transcription failed: {}", e)
        raise HTTPException(status_code=500, detail="Transcription failed")
    finally:
        if wav_path:
            cleanup_temp_file(wav_path)
