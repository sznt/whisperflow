import numpy as np
import sounddevice as sd


class AudioRecorder:
    SAMPLE_RATE = 16000
    CHANNELS = 1

    def __init__(self):
        self._frames: list[np.ndarray] = []
        self._stream = None

    def start(self) -> None:
        self._frames = []
        self._stream = sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def _callback(self, indata: np.ndarray, frames: int, time, status) -> None:
        self._frames.append(indata.copy())

    def stop(self) -> np.ndarray:
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if self._frames:
            return np.concatenate(self._frames, axis=0).flatten()
        return np.array([], dtype="float32")
