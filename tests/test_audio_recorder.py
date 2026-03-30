import numpy as np
import pytest
from unittest.mock import MagicMock, patch, call


def test_start_opens_stream(mock_sounddevice):
    from src.audio_recorder import AudioRecorder
    recorder = AudioRecorder()
    recorder.start()
    mock_sounddevice.InputStream.assert_called_once_with(
        samplerate=16000,
        channels=1,
        dtype="float32",
        callback=recorder._callback,
    )
    mock_sounddevice.InputStream.return_value.__enter__ = MagicMock()
    mock_sounddevice.InputStream.return_value.start.assert_called_once()


def test_stop_returns_concatenated_audio(mock_sounddevice):
    from src.audio_recorder import AudioRecorder
    recorder = AudioRecorder()
    recorder.start()
    # Simulate two callback calls
    chunk1 = np.array([[0.1], [0.2]], dtype="float32")
    chunk2 = np.array([[0.3], [0.4]], dtype="float32")
    recorder._callback(chunk1, 2, None, None)
    recorder._callback(chunk2, 2, None, None)
    audio = recorder.stop()
    expected = np.array([0.1, 0.2, 0.3, 0.4], dtype="float32")
    np.testing.assert_array_almost_equal(audio, expected)


def test_stop_with_no_audio_returns_empty(mock_sounddevice):
    from src.audio_recorder import AudioRecorder
    recorder = AudioRecorder()
    recorder.start()
    audio = recorder.stop()
    assert isinstance(audio, np.ndarray)
    assert len(audio) == 0


@pytest.fixture
def mock_sounddevice():
    with patch("src.audio_recorder.sd") as mock_sd:
        stream = MagicMock()
        mock_sd.InputStream.return_value = stream
        yield mock_sd
