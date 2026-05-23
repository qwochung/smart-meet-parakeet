import os
import tempfile
from typing import List
from loguru import logger

import nemo.collections.asr as nemo_asr
import torch
from pydub import AudioSegment
from pydub.silence import split_on_silence

_model = None


def load_model():
    global _model
    if _model is None:
        logger.info("Loading Parakeet model...")

        model_path = "data/nemo_models/parakeet-ctc-0.6b-vi.nemo"
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"File not found: {model_path}")

        _model = nemo_asr.models.EncDecCTCModelBPE.restore_from(model_path)

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


def transcribe(file_path: str) -> str:
    audio = AudioSegment.from_file(file_path)

    chunks = _split_audio(audio)
    chunk_paths = _save_chunks(chunks)

    model = load_model()
    try:
        raw_results = model.transcribe(chunk_paths, batch_size=2)

        texts = []
        for r in raw_results:
            if r is not None:
                texts.append(r.strip())
        return " ".join(texts)
    finally:
        for p in chunk_paths:
            if os.path.exists(p):
                os.remove(p)


def transcribe_chunk(file_path: str) -> str:
    model = load_model()
    raw_results = model.transcribe([file_path])

    if raw_results and raw_results[0] is not None:
        return raw_results[0].strip()
    return ""
