import time

from app.services.audio_service import process_audio_file, cleanup_temp_file
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.asr_parakeet import transcribe

router = APIRouter(
    prefix="/api/transcribe",
    tags=["Transcription"]
)

@router.post("/")
async def transcribe_meeting_audio(audio_file: UploadFile = File(...)):
    start_time = time.time()
    clean_wav_path = ""

    try:
        clean_wav_path = await process_audio_file(audio_file)
        result = transcribe(clean_wav_path)
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



