import sys
import types
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def mock_all_deps(monkeypatch):
    # stub rumps
    rumps_mod = types.ModuleType("rumps")
    rumps_mod.App = object
    rumps_mod.MenuItem = MagicMock
    rumps_mod.alert = MagicMock()
    rumps_mod.clicked = lambda *a, **kw: (lambda f: f)  # no-op decorator
    monkeypatch.setitem(sys.modules, "rumps", rumps_mod)
    yield


def test_toggle_starts_recording_when_idle():
    from src.app import WhisperFlowApp
    app = WhisperFlowApp.__new__(WhisperFlowApp)
    app._state = "idle"
    app._recorder = MagicMock()
    app._overlay = MagicMock()
    app._transcriber = MagicMock()
    app._injector = MagicMock()

    app._on_toggle()

    assert app._state == "recording"
    app._recorder.start.assert_called_once()
    app._overlay.show.assert_called_once_with("● Recording...")


def test_toggle_stops_recording_when_recording():
    from src.app import WhisperFlowApp
    app = WhisperFlowApp.__new__(WhisperFlowApp)
    app._state = "recording"
    app._recorder = MagicMock()
    app._recorder.stop.return_value = MagicMock()
    app._overlay = MagicMock()
    app._transcriber = MagicMock()
    app._transcriber.transcribe.return_value = "hello"
    app._injector = MagicMock()

    app._on_toggle()

    assert app._state in ("transcribing", "idle")
    app._recorder.stop.assert_called_once()
    app._overlay.show.assert_called_with("⟳ Transcribing...")


def test_toggle_ignored_when_transcribing():
    from src.app import WhisperFlowApp
    app = WhisperFlowApp.__new__(WhisperFlowApp)
    app._state = "transcribing"
    app._recorder = MagicMock()
    app._overlay = MagicMock()

    app._on_toggle()

    app._recorder.start.assert_not_called()
    app._recorder.stop.assert_not_called()


def test_transcribe_and_type_injects_text_and_hides_overlay():
    import numpy as np
    from src.app import WhisperFlowApp
    app = WhisperFlowApp.__new__(WhisperFlowApp)
    app._state = "transcribing"
    app._transcriber = MagicMock()
    app._transcriber.transcribe.return_value = "szia világ"
    app._injector = MagicMock()
    app._overlay = MagicMock()

    audio = np.zeros(16000, dtype="float32")
    app._transcribe_and_type(audio)

    app._injector.type_text.assert_called_once_with("szia világ")
    app._overlay.hide.assert_called_once()
    assert app._state == "idle"


def test_transcribe_and_type_skips_inject_on_empty_text():
    import numpy as np
    from src.app import WhisperFlowApp
    app = WhisperFlowApp.__new__(WhisperFlowApp)
    app._state = "transcribing"
    app._transcriber = MagicMock()
    app._transcriber.transcribe.return_value = ""
    app._injector = MagicMock()
    app._overlay = MagicMock()

    audio = np.zeros(16000, dtype="float32")
    app._transcribe_and_type(audio)

    app._injector.type_text.assert_not_called()
    app._overlay.hide.assert_called_once()
    assert app._state == "idle"
