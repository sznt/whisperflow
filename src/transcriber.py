import numpy as np
from faster_whisper import WhisperModel


class Transcriber:
    def __init__(self, model_size: str = "medium"):
        self._model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def transcribe(self, audio: np.ndarray) -> str:
        if len(audio) < int(0.1 * 16000):  # ignore clips under 100 ms
            return ""
        segments, _info = self._model.transcribe(
            audio,
            language=None,          # auto-detect per clip
            task="transcribe",      # never translate — always write in spoken language
            condition_on_previous_text=False,  # KEY: prevents biasing toward first detected language
            beam_size=5,
        )
        return "".join(seg.text for seg in segments).strip()
