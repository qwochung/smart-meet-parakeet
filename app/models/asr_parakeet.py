import os

import nemo.collections.asr as nemo_asr
import torch

_model= None

def load_model():
    global _model
    if _model is None:
        print("Đang nạp Parakeet-VI vào bộ nhớ ...")

        model_path = "data/nemo_models/parakeet-ctc-0.6b-vi.nemo"
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Không tìm thấy model tại {model_path}. Hãy kiểm tra lại!")

        _model = nemo_asr.models.EncDecCTCModelBPE.restore_from(model_path)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _model = _model.to(device)
        _model.eval()

    return _model

def transcribe(file_path: str) -> str :
    model = load_model()
    transcription = model.transcribe(file_path)
    return transcription[0]