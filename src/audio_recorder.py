import threading
import numpy as np
import sounddevice as sd


class AudioRecorder:
    SAMPLE_RATE = 16000
    CHANNELS = 1
    # Small blocks so last_rms updates frequently for smooth level visualization
    BLOCK_DURATION = 0.05  # 50 ms

    def __init__(self):
        self._frames: list[np.ndarray] = []
        self._stream = None
        self._lock = threading.Lock()
        self.last_rms: float = 0.0

    def start(self) -> None:
        with self._lock:
            self._frames = []
        self.last_rms = 0.0
        blocksize = int(self.SAMPLE_RATE * self.BLOCK_DURATION)
        self._stream = sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            dtype="float32",
            blocksize=blocksize,
            callback=self._callback,
        )
        self._stream.start()

    def _callback(self, indata: np.ndarray, frames: int, time, status) -> None:
        chunk = indata.copy()
        with self._lock:
            self._frames.append(chunk)
        self.last_rms = float(np.sqrt(np.mean(chunk ** 2)))

    def get_snapshot(self) -> np.ndarray:
        """Return the full accumulated audio so far without stopping."""
        with self._lock:
            if self._frames:
                return np.concatenate(self._frames, axis=0).flatten()
        return np.array([], dtype="float32")

    def stop(self) -> np.ndarray:
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        with self._lock:
            if self._frames:
                return np.concatenate(self._frames, axis=0).flatten()
        return np.array([], dtype="float32")
