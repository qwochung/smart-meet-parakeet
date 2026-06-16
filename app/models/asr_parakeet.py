import os
import tempfile
from pathlib import Path
from typing import List
from loguru import logger

import nemo.collections.asr as nemo_asr
import torch
from pydub import AudioSegment
from pydub.silence import split_on_silence

_model = None
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "data" / "nemo_models" / "parakeet-ctc-0.6b-vi.nemo"


def _resolve_model_path() -> Path:
    env_path = os.getenv("PARAKEET_MODEL_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_MODEL_PATH


def load_model():
    global _model
    if _model is None:
        logger.info("Loading Parakeet model...")

        model_path = _resolve_model_path()
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model not found: {model_path}. "
                "Download parakeet-ctc-0.6b-vi.nemo into data/nemo_models/ "
                "or set PARAKEET_MODEL_PATH."
            )

        _model = nemo_asr.models.EncDecCTCModelBPE.restore_from(str(model_path))

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _model = _model.to(device)
        _model.eval()

    return _model


def _split_audio(audio: AudioSegment) -> List[AudioSegment]:
    MIN_CHUNK_MS = 1000
    MIN_SILENCE_LEN = 500
    KEEP_SILENCE_MS = 200
    logger.info("Start splitting audio")

    silence_thresh = audio.dBFS - 16
    logger.debug(
        "Audio info: duration={}ms, dBFS={}, silence_thresh={}",
        len(audio),
        audio.dBFS,
        silence_thresh,
    )

    chunks = split_on_silence(
        audio,
        min_silence_len=MIN_SILENCE_LEN,
        silence_thresh=silence_thresh,
        keep_silence=KEEP_SILENCE_MS,
    )

    chunks = [c for c in chunks if len(c) >= MIN_CHUNK_MS]
    logger.info("Split by silence completed: found {} raw chunks", len(chunks))

    if not chunks:
        logger.warning("No valid chunks found after silence split, fallback to fixed-size chunking")

        chunk_len_ms = 15_000
        total_ms = len(audio)
        chunks = [
            audio[i : i + chunk_len_ms]
            for i in range(0, total_ms, chunk_len_ms)
        ]
        chunks = [c for c in chunks if len(c) >= MIN_CHUNK_MS]

    logger.success("Audio splitting finished successfully")
    return chunks


def _save_chunks(chunks: List[AudioSegment]) -> List[str]:
    paths: List[str] = []
    for i, chunk in enumerate(chunks):
        fd, path = tempfile.mkstemp(suffix=".wav", prefix=f"parakeet_{i:04d}_")
        os.close(fd)
        chunk.export(path, format="wav")
        paths.append(path)
    return paths


def _extract_text(result) -> str:
    """NeMo mới trả về Hypothesis object thay vì str — lấy .text an toàn."""
    if result is None:
        return ""
    if isinstance(result, (list, tuple)):
        if not result:
            return ""
        return _extract_text(result[0])
    if isinstance(result, str):
        return result.strip()
    text = getattr(result, "text", None)
    if text is not None:
        return str(text).strip()
    return str(result).strip()


def transcribe(file_path: str) -> str:
    audio = AudioSegment.from_file(file_path)

    chunks = _split_audio(audio)
    chunk_paths = _save_chunks(chunks)

    model = load_model()
    try:
        raw_results = model.transcribe(chunk_paths, batch_size=2)

        texts = []
        for r in raw_results:
            text = _extract_text(r)
            if text:
                texts.append(text)
        return " ".join(texts)
    finally:
        for p in chunk_paths:
            if os.path.exists(p):
                os.remove(p)


def transcribe_chunk(file_path: str) -> str:
    model = load_model()
    raw_results = model.transcribe([file_path])

    if not raw_results:
        return ""
    return _extract_text(raw_results[0])
