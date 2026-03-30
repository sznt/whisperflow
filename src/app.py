import sys
import threading
import numpy as np
import rumps


class WhisperFlowApp(rumps.App):
    def __init__(self):
        from src.permissions import check_and_request_permissions
        if not check_and_request_permissions():
            sys.exit(1)

        from src.audio_recorder import AudioRecorder
        from src.transcriber import Transcriber
        from src.hotkey_listener import HotkeyListener
        from src.text_injector import TextInjector
        from src.overlay import Overlay

        super().__init__("WhisperFlow", title="🎤", quit_button="Quit")
        self.menu = ["About WhisperFlow"]

        self._state = "idle"  # idle | recording | transcribing
        self._recorder = AudioRecorder()
        self._overlay = Overlay()
        self._injector = TextInjector()
        self._transcriber = Transcriber(model_size="medium")
        self._listener = HotkeyListener(on_toggle=self._on_toggle)
        self._listener.start()

    def _on_toggle(self) -> None:
        if self._state == "idle":
            self._state = "recording"
            self._recorder.start()
            self._overlay.show("● Recording...")
        elif self._state == "recording":
            self._state = "transcribing"
            audio = self._recorder.stop()
            self._overlay.show("⟳ Transcribing...")
            threading.Thread(
                target=self._transcribe_and_type,
                args=(audio,),
                daemon=True,
            ).start()
        # transcribing: ignore

    def _transcribe_and_type(self, audio: np.ndarray) -> None:
        text = self._transcriber.transcribe(audio)
        if text:
            self._injector.type_text(text)
        self._overlay.hide()
        self._state = "idle"

    @rumps.clicked("About WhisperFlow")
    def about(self, _):
        rumps.alert(
            title="WhisperFlow",
            message=(
                "Dictate in English or Hungarian.\n\n"
                "Press Ctrl+Space to start/stop recording.\n"
                "Transcription happens locally using Whisper medium."
            ),
        )
