import numpy as np
import pytest
from unittest.mock import MagicMock, patch


def test_transcribe_joins_segments(mock_whisper_model):
    from src.transcriber import Transcriber
    seg1 = MagicMock()
    seg1.text = " Hello"
    seg2 = MagicMock()
    seg2.text = " world"
    mock_whisper_model.return_value.transcribe.return_value = ([seg1, seg2], MagicMock())

    t = Transcriber(model_size="medium")
    audio = np.zeros(16000, dtype="float32")
    result = t.transcribe(audio)

    assert result == "Hello world"


def test_transcribe_empty_audio_returns_empty(mock_whisper_model):
    from src.transcriber import Transcriber
    mock_whisper_model.return_value.transcribe.return_value = ([], MagicMock())

    t = Transcriber(model_size="medium")
    audio = np.array([], dtype="float32")
    result = t.transcribe(audio)

    assert result == ""


def test_transcribe_calls_with_auto_language(mock_whisper_model):
    from src.transcriber import Transcriber
    mock_whisper_model.return_value.transcribe.return_value = ([], MagicMock())

    t = Transcriber(model_size="medium")
    audio = np.zeros(16000, dtype="float32")
    t.transcribe(audio)

    mock_whisper_model.return_value.transcribe.assert_called_once_with(audio, language=None)


def test_transcriber_loads_medium_model(mock_whisper_model):
    from src.transcriber import Transcriber
    Transcriber(model_size="medium")
    mock_whisper_model.assert_called_once_with("medium", device="cpu", compute_type="int8")


@pytest.fixture
def mock_whisper_model():
    with patch("src.transcriber.WhisperModel") as mock:
        yield mock
