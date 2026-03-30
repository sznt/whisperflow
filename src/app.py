import threading
import time
import numpy as np
import rumps

# ── VAD constants ──────────────────────────────────────────────────────────────
_SILENCE_RMS = 0.012        # RMS below this = silence
_SILENCE_SECS = 0.55        # seconds of silence needed to trigger a segment
_MIN_SEGMENT_SECS = 0.6     # don't transcribe clips shorter than this
_LEVEL_INTERVAL = 0.05      # seconds between level-bar refreshes
_LEVEL_CHARS = "▁▂▃▄▅▆▇█"  # unicode block elements for the bar


def _level_bar(rms: float) -> str:
    """Convert an RMS value to a 5-character unicode bar."""
    idx = min(int(rms * 120), len(_LEVEL_CHARS) - 1)
    bar = ""
    for i in range(5):
        bar += _LEVEL_CHARS[max(0, idx - (4 - i))]
    return bar


class WhisperFlowApp(rumps.App):

    def __init__(self):
        super().__init__("WhisperFlow", title="🎤", quit_button="Quit")
        self.menu = ["About WhisperFlow"]

        self._state = "idle"

        # Components — populated in _deferred_init
        self._recorder = None
        self._overlay = None
        self._injector = None
        self._transcriber = None
        self._listener = None

        # Streaming state
        self._level_timer = None        # rumps.Timer — updates level bar on main thread
        self._vad_thread = None         # background VAD + segment transcription
        self._injected_up_to = 0        # samples already injected (avoid double-inject)
        self._partial_text = ""         # accumulated preview text for overlay

        self._init_timer = rumps.Timer(self._deferred_init, 0.5)
        self._init_timer.start()

    # ── startup ────────────────────────────────────────────────────────────────

    def _deferred_init(self, _timer) -> None:
        self._init_timer.stop()

        from src.permissions import check_and_request_permissions
        if not check_and_request_permissions():
            rumps.alert(
                title="Permissions Required",
                message=(
                    "WhisperFlow needs two permissions to work:\n\n"
                    "1. System Settings → Privacy & Security → Accessibility\n"
                    "   Add Terminal (or WhisperFlow.app) and enable it.\n\n"
                    "2. System Settings → Privacy & Security → Input Monitoring\n"
                    "   Add Terminal (or WhisperFlow.app) and enable it.\n\n"
                    "After granting both, relaunch the app."
                ),
            )
            rumps.quit_application()
            return

        from src.audio_recorder import AudioRecorder
        from src.transcriber import Transcriber
        from src.hotkey_listener import HotkeyListener
        from src.text_injector import TextInjector
        from src.overlay import Overlay

        self._recorder = AudioRecorder()
        self._overlay = Overlay()
        self._injector = TextInjector()
        self._transcriber = Transcriber(model_size="medium")
        self._listener = HotkeyListener(on_toggle=self._on_toggle)
        self._listener.start()

    # ── hotkey handler ─────────────────────────────────────────────────────────

    def _on_toggle(self) -> None:
        if self._state == "idle":
            self._start_recording()
        elif self._state == "recording":
            self._stop_recording()
        # "transcribing": ignore extra presses

    # ── recording start ────────────────────────────────────────────────────────

    def _start_recording(self) -> None:
        self._state = "recording"
        self._injected_up_to = 0
        self._partial_text = ""
        self._recorder.start()
        self._overlay.show("● Recording…")

        # Level-bar timer on main thread (50 ms)
        self._level_timer = rumps.Timer(self._tick_level, _LEVEL_INTERVAL)
        self._level_timer.start()

        # VAD thread — detects pauses and transcribes segments in real time
        self._vad_thread = threading.Thread(target=self._vad_loop, daemon=True)
        self._vad_thread.start()

    # ── level bar (main thread, called by rumps.Timer) ─────────────────────────

    def _tick_level(self, _timer) -> None:
        if self._state != "recording":
            self._level_timer.stop()
            return
        bar = _level_bar(self._recorder.last_rms)
        self._overlay.show(f"● Recording  {bar}", self._partial_text)

    # ── VAD loop (background thread) ───────────────────────────────────────────

    def _vad_loop(self) -> None:
        """
        Runs while recording. Detects speech pauses via RMS and fires a
        transcription for each detected utterance, injecting text immediately.
        """
        silence_frames = 0
        needed = int(_SILENCE_SECS / _LEVEL_INTERVAL)

        while self._state == "recording":
            time.sleep(_LEVEL_INTERVAL)

            rms = self._recorder.last_rms
            if rms < _SILENCE_RMS:
                silence_frames += 1
            else:
                silence_frames = 0

            if silence_frames == needed:   # trigger once per pause, not repeatedly
                silence_frames = 0
                self._process_new_audio()

    def _process_new_audio(self) -> None:
        """Transcribe audio accumulated since last injection and inject it."""
        if self._state != "recording":
            return

        audio = self._recorder.get_snapshot()
        new_audio = audio[self._injected_up_to:]

        min_samples = int(_MIN_SEGMENT_SECS * 16000)
        if len(new_audio) < min_samples:
            return

        text = self._transcriber.transcribe(new_audio)
        if not text or self._state != "recording":
            return

        # Prepend a space if we're not at the start
        inject = (" " + text) if self._injected_up_to > 0 else text
        self._injector.type_text(inject)
        self._injected_up_to = len(audio)
        self._partial_text += inject

    # ── recording stop ─────────────────────────────────────────────────────────

    def _stop_recording(self) -> None:
        self._state = "transcribing"
        if self._level_timer:
            self._level_timer.stop()

        self._overlay.show("⟳ Finalizing…")
        audio = self._recorder.stop()

        threading.Thread(
            target=self._finalize,
            args=(audio,),
            daemon=True,
        ).start()

    def _finalize(self, audio: np.ndarray) -> None:
        """Transcribe any audio not yet injected during the VAD loop."""
        remaining = audio[self._injected_up_to:]
        min_samples = int(_MIN_SEGMENT_SECS * 16000)
        if len(remaining) >= min_samples:
            text = self._transcriber.transcribe(remaining)
            if text:
                inject = (" " + text) if self._injected_up_to > 0 else text
                self._injector.type_text(inject)

        self._overlay.hide()
        self._state = "idle"

    # ── about menu ─────────────────────────────────────────────────────────────

    @rumps.clicked("About WhisperFlow")
    def about(self, _):
        rumps.alert(
            title="WhisperFlow",
            message=(
                "Dictate in English or Hungarian — or mix both freely.\n\n"
                "Press Ctrl+Space to start recording.\n"
                "Text is injected in real time as you pause between sentences.\n"
                "Press Ctrl+Space again to stop.\n\n"
                "Transcription is fully offline using Whisper medium."
            ),
        )
