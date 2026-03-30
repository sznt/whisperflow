import sys
import types
import threading
import numpy as np
import pytest
from unittest.mock import MagicMock, call


@pytest.fixture(autouse=True)
def mock_all_deps(monkeypatch):
    rumps_mod = types.ModuleType("rumps")
    rumps_mod.App = object
    rumps_mod.MenuItem = MagicMock
    rumps_mod.alert = MagicMock()
    rumps_mod.clicked = lambda *a, **kw: (lambda f: f)
    rumps_mod.Timer = MagicMock()
    monkeypatch.setitem(sys.modules, "rumps", rumps_mod)
    yield


def _make_app():
    """Return a WhisperFlowApp instance with all components mocked."""
    from src.app import WhisperFlowApp
    app = WhisperFlowApp.__new__(WhisperFlowApp)
    app._state = "idle"
    app._recorder = MagicMock()
    app._recorder.last_rms = 0.0
    app._recorder.get_snapshot.return_value = np.zeros(16000, dtype="float32")
    app._overlay = MagicMock()
    app._transcriber = MagicMock()
    app._transcriber.transcribe.return_value = ""
    app._injector = MagicMock()
    app._level_timer = MagicMock()
    app._vad_thread = None
    app._injected_up_to = 0
    app._partial_text = ""
    return app


# ── toggle / state machine ─────────────────────────────────────────────────────

def test_toggle_starts_recording_when_idle():
    app = _make_app()
    app._on_toggle()
    assert app._state == "recording"
    app._recorder.start.assert_called_once()
    # Overlay is shown with "● Recording…" (level bar follows via timer)
    assert app._overlay.show.call_args[0][0].startswith("● Recording")


def test_toggle_stops_recording_when_recording():
    app = _make_app()
    app._state = "recording"
    app._on_toggle()
    assert app._state in ("transcribing", "idle")
    app._recorder.stop.assert_called_once()


def test_toggle_ignored_when_transcribing():
    app = _make_app()
    app._state = "transcribing"
    app._on_toggle()
    app._recorder.start.assert_not_called()
    app._recorder.stop.assert_not_called()


# ── _process_new_audio ────────────────────────────────────────────────────────

def test_process_new_audio_injects_text_and_advances_pointer():
    app = _make_app()
    app._state = "recording"
    app._injected_up_to = 0
    audio = np.zeros(16000, dtype="float32")  # 1 second
    app._recorder.get_snapshot.return_value = audio
    app._transcriber.transcribe.return_value = "szia"

    app._process_new_audio()

    app._injector.type_text.assert_called_once_with("szia")
    assert app._injected_up_to == 16000
    assert app._partial_text == "szia"


def test_process_new_audio_prepends_space_after_first_injection():
    app = _make_app()
    app._state = "recording"
    app._injected_up_to = 16000   # already injected one second
    audio = np.zeros(32000, dtype="float32")  # 2 seconds total
    app._recorder.get_snapshot.return_value = audio
    app._transcriber.transcribe.return_value = "world"

    app._process_new_audio()

    app._injector.type_text.assert_called_once_with(" world")


def test_process_new_audio_skips_short_clips():
    app = _make_app()
    app._state = "recording"
    app._injected_up_to = 0
    # Only 0.3 seconds — below _MIN_SEGMENT_SECS (0.6)
    app._recorder.get_snapshot.return_value = np.zeros(4800, dtype="float32")

    app._process_new_audio()

    app._injector.type_text.assert_not_called()


def test_process_new_audio_skips_empty_transcription():
    app = _make_app()
    app._state = "recording"
    app._injected_up_to = 0
    app._recorder.get_snapshot.return_value = np.zeros(16000, dtype="float32")
    app._transcriber.transcribe.return_value = ""

    app._process_new_audio()

    app._injector.type_text.assert_not_called()


# ── _finalize ─────────────────────────────────────────────────────────────────

def test_finalize_injects_remaining_audio_and_hides_overlay():
    app = _make_app()
    app._state = "transcribing"
    app._injected_up_to = 0
    app._transcriber.transcribe.return_value = "hello world"

    audio = np.zeros(16000, dtype="float32")
    app._finalize(audio)

    app._injector.type_text.assert_called_once_with("hello world")
    app._overlay.hide.assert_called_once()
    assert app._state == "idle"


def test_finalize_skips_inject_when_nothing_new():
    app = _make_app()
    app._state = "transcribing"
    audio = np.zeros(16000, dtype="float32")
    app._injected_up_to = len(audio)   # everything already injected

    app._finalize(audio)

    app._injector.type_text.assert_not_called()
    app._overlay.hide.assert_called_once()
    assert app._state == "idle"


# ── level bar helper ──────────────────────────────────────────────────────────

def test_level_bar_returns_five_chars():
    from src.app import _level_bar
    assert len(_level_bar(0.0)) == 5
    assert len(_level_bar(0.5)) == 5
    assert len(_level_bar(1.0)) == 5
