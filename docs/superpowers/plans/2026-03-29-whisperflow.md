# WhisperFlow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a macOS menu bar app that transcribes speech (English/Hungarian) via local Whisper and types the result into the focused app on Ctrl+Space toggle.

**Architecture:** Python app using rumps for the menu bar, pynput for global hotkey, sounddevice for audio capture, faster-whisper for offline transcription, and PyObjC/Quartz for text injection and a floating overlay HUD.

**Tech Stack:** Python 3.11+, faster-whisper, sounddevice, pynput, rumps, pyobjc, numpy, pytest, py2app

---

## File Map

| File | Responsibility |
|------|---------------|
| `src/audio_recorder.py` | Mic capture via sounddevice, returns numpy float32 array |
| `src/transcriber.py` | faster-whisper inference, auto language detect, returns string |
| `src/hotkey_listener.py` | pynput GlobalHotKeys Ctrl+Space, fires callback |
| `src/text_injector.py` | CGEventCreateKeyboardEvent to type into focused app |
| `src/overlay.py` | NSPanel floating pill HUD, show/hide with message |
| `src/app.py` | rumps App controller, state machine, wires all components |
| `tests/test_audio_recorder.py` | Unit tests with mocked sounddevice |
| `tests/test_transcriber.py` | Unit tests with mocked WhisperModel |
| `tests/test_hotkey_listener.py` | Unit tests with mocked pynput |
| `tests/test_text_injector.py` | Unit tests with mocked Quartz |
| `requirements.txt` | Runtime dependencies |
| `requirements-dev.txt` | Test/dev dependencies |
| `setup.py` | py2app packaging config |
| `.claude/launch.json` | Dev server launch configuration |

---

## Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `src/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Install system dependency (portaudio)**

```bash
brew install portaudio
```

Expected: portaudio installed (or already installed message).

- [ ] **Step 2: Create `requirements.txt`**

```
faster-whisper==1.1.1
sounddevice==0.5.1
pynput==1.7.7
rumps==0.4.0
pyobjc-core==11.0
pyobjc-framework-Cocoa==11.0
pyobjc-framework-Quartz==11.0
numpy==2.2.4
```

- [ ] **Step 3: Create `requirements-dev.txt`**

```
pytest==8.3.5
pytest-mock==3.14.0
```

- [ ] **Step 4: Create Python virtual environment and install dependencies**

```bash
cd /Users/peterszanto/Documents/Claude/Whisperflow
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

Expected: All packages install without errors. PyObjC may take a minute.

- [ ] **Step 5: Create `src/__init__.py` and `tests/__init__.py`**

Both files are empty.

- [ ] **Step 6: Create `tests/conftest.py`**

```python
import sys
import types

# Stub out AppKit/Quartz/Cocoa at import time so tests run without a display
for mod in [
    "AppKit", "Quartz", "Cocoa", "objc",
    "AppKit.NSColor", "AppKit.NSFont", "AppKit.NSScreen",
]:
    if mod not in sys.modules:
        sys.modules[mod] = types.ModuleType(mod)
```

- [ ] **Step 7: Commit**

```bash
cd /Users/peterszanto/Documents/Claude/Whisperflow
git init
git add requirements.txt requirements-dev.txt src/__init__.py tests/__init__.py tests/conftest.py
git commit -m "chore: project scaffold with dependencies"
```

---

## Task 2: AudioRecorder

**Files:**
- Create: `src/audio_recorder.py`
- Create: `tests/test_audio_recorder.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_audio_recorder.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/peterszanto/Documents/Claude/Whisperflow
source .venv/bin/activate
pytest tests/test_audio_recorder.py -v
```

Expected: `ModuleNotFoundError` or `ImportError` — `src.audio_recorder` does not exist yet.

- [ ] **Step 3: Write `src/audio_recorder.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_audio_recorder.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/audio_recorder.py tests/test_audio_recorder.py
git commit -m "feat: AudioRecorder captures mic to numpy array"
```

---

## Task 3: Transcriber

**Files:**
- Create: `src/transcriber.py`
- Create: `tests/test_transcriber.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_transcriber.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_transcriber.py -v
```

Expected: `ModuleNotFoundError` — `src.transcriber` does not exist yet.

- [ ] **Step 3: Write `src/transcriber.py`**

```python
import numpy as np
from faster_whisper import WhisperModel


class Transcriber:
    def __init__(self, model_size: str = "medium"):
        self._model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def transcribe(self, audio: np.ndarray) -> str:
        segments, _info = self._model.transcribe(audio, language=None)
        return " ".join(seg.text for seg in segments).strip()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_transcriber.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/transcriber.py tests/test_transcriber.py
git commit -m "feat: Transcriber wraps faster-whisper medium model with auto language detection"
```

---

## Task 4: HotkeyListener

**Files:**
- Create: `src/hotkey_listener.py`
- Create: `tests/test_hotkey_listener.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_hotkey_listener.py`:

```python
import pytest
from unittest.mock import MagicMock, patch, call


def test_start_registers_hotkey(mock_pynput):
    from src.hotkey_listener import HotkeyListener
    callback = MagicMock()
    listener = HotkeyListener(on_toggle=callback)
    listener.start()
    mock_pynput.keyboard.GlobalHotKeys.assert_called_once_with(
        {"<ctrl>+<space>": callback}
    )
    mock_pynput.keyboard.GlobalHotKeys.return_value.start.assert_called_once()


def test_stop_calls_stop_on_hotkey(mock_pynput):
    from src.hotkey_listener import HotkeyListener
    callback = MagicMock()
    listener = HotkeyListener(on_toggle=callback)
    listener.start()
    listener.stop()
    mock_pynput.keyboard.GlobalHotKeys.return_value.stop.assert_called_once()


def test_stop_without_start_does_not_raise(mock_pynput):
    from src.hotkey_listener import HotkeyListener
    callback = MagicMock()
    listener = HotkeyListener(on_toggle=callback)
    listener.stop()  # Should not raise


@pytest.fixture
def mock_pynput():
    with patch("src.hotkey_listener.keyboard") as mock_kb:
        hotkey_instance = MagicMock()
        mock_kb.GlobalHotKeys.return_value = hotkey_instance
        yield mock_kb
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_hotkey_listener.py -v
```

Expected: `ModuleNotFoundError` — `src.hotkey_listener` does not exist yet.

- [ ] **Step 3: Write `src/hotkey_listener.py`**

```python
from pynput import keyboard


class HotkeyListener:
    HOTKEY = "<ctrl>+<space>"

    def __init__(self, on_toggle):
        self._on_toggle = on_toggle
        self._hotkey = None

    def start(self) -> None:
        self._hotkey = keyboard.GlobalHotKeys({self.HOTKEY: self._on_toggle})
        self._hotkey.start()

    def stop(self) -> None:
        if self._hotkey:
            self._hotkey.stop()
            self._hotkey = None
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_hotkey_listener.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/hotkey_listener.py tests/test_hotkey_listener.py
git commit -m "feat: HotkeyListener registers Ctrl+Space global hotkey via pynput"
```

---

## Task 5: TextInjector

**Files:**
- Create: `src/text_injector.py`
- Create: `tests/test_text_injector.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_text_injector.py`:

```python
import sys
import types
import pytest
from unittest.mock import MagicMock, patch, call


@pytest.fixture(autouse=True)
def mock_quartz(monkeypatch):
    quartz = types.ModuleType("Quartz")
    quartz.CGEventCreateKeyboardEvent = MagicMock(return_value=MagicMock())
    quartz.CGEventKeyboardSetUnicodeString = MagicMock()
    quartz.CGEventPost = MagicMock()
    quartz.kCGHIDEventTap = 0
    monkeypatch.setitem(sys.modules, "Quartz", quartz)
    yield quartz


def test_type_text_creates_events_for_each_char(mock_quartz):
    from src.text_injector import TextInjector
    injector = TextInjector()
    injector.type_text("hi")
    # 2 chars × 2 events (down + up) = 4 CGEventCreateKeyboardEvent calls
    assert mock_quartz.CGEventCreateKeyboardEvent.call_count == 4


def test_type_text_posts_all_events(mock_quartz):
    from src.text_injector import TextInjector
    injector = TextInjector()
    injector.type_text("ab")
    assert mock_quartz.CGEventPost.call_count == 4


def test_type_text_sets_unicode_string_for_each_event(mock_quartz):
    from src.text_injector import TextInjector
    injector = TextInjector()
    injector.type_text("h")
    assert mock_quartz.CGEventKeyboardSetUnicodeString.call_count == 2


def test_type_text_handles_unicode_hungarian(mock_quartz):
    from src.text_injector import TextInjector
    injector = TextInjector()
    # Should not raise for Hungarian characters
    injector.type_text("áéíóöőúüű")
    assert mock_quartz.CGEventPost.call_count == 9 * 2
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_text_injector.py -v
```

Expected: `ModuleNotFoundError` — `src.text_injector` does not exist yet.

- [ ] **Step 3: Write `src/text_injector.py`**

```python
import time
import Quartz


class TextInjector:
    DELAY = 0.001  # seconds between keystrokes

    def type_text(self, text: str) -> None:
        for char in text:
            self._type_char(char)

    def _type_char(self, char: str) -> None:
        event_down = Quartz.CGEventCreateKeyboardEvent(None, 0, True)
        event_up = Quartz.CGEventCreateKeyboardEvent(None, 0, False)
        Quartz.CGEventKeyboardSetUnicodeString(event_down, len(char), char)
        Quartz.CGEventKeyboardSetUnicodeString(event_up, len(char), char)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)
        time.sleep(self.DELAY)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_text_injector.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/text_injector.py tests/test_text_injector.py
git commit -m "feat: TextInjector types unicode text via CGEvent keystrokes"
```

---

## Task 6: Overlay HUD

**Files:**
- Create: `src/overlay.py`

Note: NSPanel/AppKit requires a running NSApp on the main thread. This component is tested manually (Task 9). Unit tests would require a full AppKit process. We skip unit tests here and test it live in Task 9.

- [ ] **Step 1: Write `src/overlay.py`**

```python
import threading
from AppKit import (
    NSPanel,
    NSTextField,
    NSColor,
    NSFont,
    NSScreen,
    NSMakeRect,
    NSBorderlessWindowMask,
    NSFloatingWindowLevel,
    NSCenterTextAlignment,
    NSObject,
)
from Quartz import kCGBackingStoreBuffered


def _run_on_main_thread(fn):
    """Decorator to dispatch a method call onto the main AppKit thread."""
    def wrapper(self, *args, **kwargs):
        from AppKit import NSApp
        NSApp.performSelectorOnMainThread_withObject_waitUntilDone_(
            "noop:", None, False
        )
        # Use objc dispatch
        import objc
        _MainThreadRunner.alloc().initWithFn_args_(fn, (self,) + args).run()
    return wrapper


class _FnRunner(NSObject):
    def initWithBlock_(self, block):
        self = objc.super(_FnRunner, self).init()
        self._block = block
        return self

    def run(self):
        self._block()


class Overlay:
    def __init__(self):
        self._panel = None
        self._label = None
        # Deferred: panel created on first show() to ensure NSApp is running

    def _ensure_panel(self):
        if self._panel is not None:
            return
        screen = NSScreen.mainScreen()
        screen_rect = screen.frame()
        width, height = 220.0, 44.0
        x = (screen_rect.size.width - width) / 2.0
        y = screen_rect.size.height * 0.12

        self._panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, width, height),
            NSBorderlessWindowMask,
            kCGBackingStoreBuffered,
            False,
        )
        self._panel.setLevel_(NSFloatingWindowLevel)
        self._panel.setBackgroundColor_(
            NSColor.colorWithRed_green_blue_alpha_(0.08, 0.08, 0.08, 0.88)
        )
        self._panel.setOpaque_(False)
        self._panel.setHasShadow_(True)
        self._panel.setIgnoresMouseEvents_(True)

        self._label = NSTextField.alloc().initWithFrame_(
            NSMakeRect(0.0, 10.0, width, 24.0)
        )
        self._label.setEditable_(False)
        self._label.setBordered_(False)
        self._label.setDrawsBackground_(False)
        self._label.setTextColor_(NSColor.whiteColor())
        self._label.setFont_(NSFont.systemFontOfSize_(14.0))
        self._label.setAlignment_(NSCenterTextAlignment)
        self._panel.contentView().addSubview_(self._label)

    def show(self, message: str) -> None:
        self._ensure_panel()
        self._label.setStringValue_(message)
        self._panel.orderFrontRegardless()

    def hide(self) -> None:
        if self._panel:
            self._panel.orderOut_(None)
```

- [ ] **Step 2: Commit**

```bash
git add src/overlay.py
git commit -m "feat: Overlay NSPanel floating HUD for recording/transcribing state"
```

---

## Task 7: App Controller

**Files:**
- Create: `src/app.py`
- Create: `tests/test_app.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_app.py`:

```python
import sys
import types
import pytest
from unittest.mock import MagicMock, patch, call


@pytest.fixture(autouse=True)
def mock_all_deps(monkeypatch):
    # rumps
    rumps_mod = types.ModuleType("rumps")
    rumps_mod.App = MagicMock
    rumps_mod.MenuItem = MagicMock
    rumps_mod.alert = MagicMock()
    monkeypatch.setitem(sys.modules, "rumps", rumps_mod)

    # AppKit / Quartz stubs already in conftest
    yield


def test_toggle_starts_recording_when_idle():
    from src.app import WhisperFlowApp
    app = WhisperFlowApp.__new__(WhisperFlowApp)
    app._state = "idle"
    app._recorder = MagicMock()
    app._overlay = MagicMock()
    app._listener = MagicMock()
    app._transcriber = MagicMock()
    app._injector = MagicMock()

    app._on_toggle()

    assert app._state == "recording"
    app._recorder.start.assert_called_once()
    app._overlay.show.assert_called_once_with("● Recording...")


def test_toggle_stops_recording_when_recording():
    import threading
    from src.app import WhisperFlowApp
    app = WhisperFlowApp.__new__(WhisperFlowApp)
    app._state = "recording"
    app._recorder = MagicMock()
    app._recorder.stop.return_value = MagicMock()
    app._overlay = MagicMock()
    app._listener = MagicMock()
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
    app._listener = MagicMock()

    app._on_toggle()

    app._recorder.start.assert_not_called()
    app._recorder.stop.assert_not_called()


def test_transcribe_and_type_injects_text_and_hides_overlay():
    from src.app import WhisperFlowApp
    import numpy as np
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
    from src.app import WhisperFlowApp
    import numpy as np
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_app.py -v
```

Expected: `ModuleNotFoundError` — `src.app` does not exist yet.

- [ ] **Step 3: Write `src/app.py`**

```python
import threading
import rumps

from src.audio_recorder import AudioRecorder
from src.transcriber import Transcriber
from src.hotkey_listener import HotkeyListener
from src.text_injector import TextInjector
from src.overlay import Overlay

import numpy as np


class WhisperFlowApp(rumps.App):
    def __init__(self):
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
        # If transcribing: ignore

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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_app.py -v
```

Expected: 5 tests PASS.

- [ ] **Step 5: Run all tests**

```bash
pytest tests/ -v
```

Expected: All tests PASS (12+ tests total).

- [ ] **Step 6: Commit**

```bash
git add src/app.py tests/test_app.py
git commit -m "feat: WhisperFlowApp controller wires all components with idle/recording/transcribing state machine"
```

---

## Task 8: Permissions Helper

**Files:**
- Create: `src/permissions.py`

This module checks and guides the user to grant microphone and accessibility permissions on first launch.

- [ ] **Step 1: Write `src/permissions.py`**

```python
import subprocess
import sys


def check_and_request_permissions() -> bool:
    """
    Check that required permissions are granted.
    Returns True if all permissions are available, False otherwise.
    Prints guidance if permissions are missing.
    """
    missing = []

    # Check Accessibility (required for CGEvent text injection and global hotkeys)
    try:
        from Quartz import AXIsProcessTrustedWithOptions
        from Foundation import NSDictionary
        options = NSDictionary.dictionaryWithObject_forKey_(True, "AXTrustedCheckOptionPrompt")
        trusted = AXIsProcessTrustedWithOptions(options)
        if not trusted:
            missing.append("Accessibility")
    except Exception:
        # If we can't import, assume we need to check manually
        missing.append("Accessibility")

    if missing:
        print("\n⚠️  WhisperFlow needs the following permissions:\n")
        if "Accessibility" in missing:
            print(
                "  • Accessibility: System Settings → Privacy & Security → Accessibility\n"
                "    Add Terminal (or WhisperFlow.app) and enable it.\n"
                "    Also add to: Input Monitoring (for global hotkey capture).\n"
            )
        print("After granting permissions, restart the app.\n")
        return False

    return True
```

- [ ] **Step 2: Update `src/app.py` to call permissions check on startup**

In `src/app.py`, add the import at the top:

```python
from src.permissions import check_and_request_permissions
```

And add this at the start of `__init__` before starting the listener:

```python
        if not check_and_request_permissions():
            import sys
            sys.exit(1)
```

- [ ] **Step 3: Commit**

```bash
git add src/permissions.py src/app.py
git commit -m "feat: permissions helper checks Accessibility/Input Monitoring on startup"
```

---

## Task 9: Entry Point and Manual Smoke Test

**Files:**
- Create: `main.py`

- [ ] **Step 1: Create `main.py`**

```python
#!/usr/bin/env python3
"""WhisperFlow — voice dictation for macOS."""
import sys
import os

# Ensure src/ is on the path when running from project root
sys.path.insert(0, os.path.dirname(__file__))

from src.app import WhisperFlowApp

if __name__ == "__main__":
    WhisperFlowApp().run()
```

- [ ] **Step 2: Run all unit tests one final time**

```bash
cd /Users/peterszanto/Documents/Claude/Whisperflow
source .venv/bin/activate
pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 3: Manual smoke test — launch the app**

```bash
source .venv/bin/activate
python main.py
```

Expected:
- Menu bar icon 🎤 appears
- No crash on startup
- Whisper medium model downloads/loads (first run: ~1-2 min download, subsequent runs: ~15s load)
- If permissions are missing, instructions are printed and app exits cleanly

- [ ] **Step 4: Test hotkey and dictation**

With the app running:
1. Open TextEdit or any text editor
2. Press Ctrl+Space — overlay shows "● Recording..."
3. Say "Hello, this is a test" (English) or "Szia, ez egy teszt" (Hungarian)
4. Press Ctrl+Space — overlay shows "⟳ Transcribing..."
5. Text appears typed in the editor

Expected: Transcribed text is typed correctly in both languages.

- [ ] **Step 5: Commit**

```bash
git add main.py
git commit -m "feat: main.py entry point, app ready to run"
```

---

## Task 10: py2app Packaging

**Files:**
- Create: `setup.py`

- [ ] **Step 1: Install py2app**

```bash
source .venv/bin/activate
pip install py2app
```

- [ ] **Step 2: Create `setup.py`**

```python
from setuptools import setup

APP = ["main.py"]
DATA_FILES = []
OPTIONS = {
    "argv_emulation": False,
    "plist": {
        "CFBundleName": "WhisperFlow",
        "CFBundleDisplayName": "WhisperFlow",
        "CFBundleIdentifier": "com.whisperflow.app",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "LSUIElement": True,  # Hides dock icon — menu bar only
        "NSMicrophoneUsageDescription": "WhisperFlow needs microphone access to record your voice.",
        "NSAppleEventsUsageDescription": "WhisperFlow needs Accessibility access to type transcribed text.",
    },
    "packages": [
        "faster_whisper",
        "sounddevice",
        "pynput",
        "rumps",
        "AppKit",
        "Quartz",
        "numpy",
        "src",
    ],
    "includes": ["ctranslate2"],
    "excludes": ["tkinter"],
}

setup(
    app=APP,
    name="WhisperFlow",
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
```

- [ ] **Step 3: Build the app**

```bash
source .venv/bin/activate
python setup.py py2app
```

Expected: `dist/WhisperFlow.app` created. Build may take 2-5 minutes.

- [ ] **Step 4: Test the built app**

```bash
open dist/WhisperFlow.app
```

Expected: Menu bar icon appears. Test Ctrl+Space dictation as in Task 9 Step 4.

- [ ] **Step 5: Commit**

```bash
git add setup.py
git commit -m "chore: py2app packaging config for WhisperFlow.app bundle"
```

---

## Task 11: Launch Config

**Files:**
- Create: `.claude/launch.json`

- [ ] **Step 1: Create `.claude/launch.json`**

```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "WhisperFlow (dev)",
      "runtimeExecutable": "python",
      "runtimeArgs": ["main.py"],
      "port": 0
    }
  ]
}
```

- [ ] **Step 2: Commit**

```bash
mkdir -p .claude
git add .claude/launch.json
git commit -m "chore: add launch.json for Claude Code preview runner"
```

---

## Final Checklist

- [ ] All unit tests pass: `pytest tests/ -v`
- [ ] App launches from `python main.py`
- [ ] Menu bar icon appears (no dock icon)
- [ ] Ctrl+Space starts recording (overlay appears)
- [ ] Ctrl+Space again stops and transcribes
- [ ] Text typed into focused app
- [ ] Works in English and Hungarian
- [ ] `dist/WhisperFlow.app` builds and runs
