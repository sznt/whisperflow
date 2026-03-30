import sys
import types

# Stub out AppKit/Quartz/Cocoa at import time so tests run without a display
for mod in [
    "AppKit", "Quartz", "Cocoa", "objc",
    "AppKit.NSColor", "AppKit.NSFont", "AppKit.NSScreen",
]:
    if mod not in sys.modules:
        sys.modules[mod] = types.ModuleType(mod)

# Add NSEvent + NSEventMaskKeyDown to the AppKit stub so hotkey_listener imports cleanly.
from unittest.mock import MagicMock as _MagicMock
_appkit = sys.modules["AppKit"]
if not hasattr(_appkit, "NSEvent"):
    _appkit.NSEvent = _MagicMock()
if not hasattr(_appkit, "NSEventMaskKeyDown"):
    _appkit.NSEventMaskKeyDown = 1024

# Stub out faster_whisper and its transitive dependencies so tests run without
# the full ML stack installed.
for mod in [
    "faster_whisper",
    "faster_whisper.transcribe",
    "faster_whisper.utils",
    "requests",
    "ctranslate2",
    "tokenizers",
    "huggingface_hub",
]:
    if mod not in sys.modules:
        sys.modules[mod] = types.ModuleType(mod)

# Provide a real-looking WhisperModel name on the stub module so patch() works.
import types as _types
_fw = sys.modules["faster_whisper"]
if not hasattr(_fw, "WhisperModel"):
    _fw.WhisperModel = type("WhisperModel", (), {})

# Stub out pynput so tests run without a system keyboard backend.
# The Quartz stub above breaks pynput's macOS backend, so we must pre-stub
# pynput before src.hotkey_listener is imported.
for mod in ["pynput", "pynput.keyboard"]:
    if mod not in sys.modules:
        sys.modules[mod] = types.ModuleType(mod)

# Provide a GlobalHotKeys class on the stub so patch() can target it.
_kb = sys.modules["pynput.keyboard"]
if not hasattr(_kb, "GlobalHotKeys"):
    _kb.GlobalHotKeys = type("GlobalHotKeys", (), {})

# Make pynput.keyboard accessible as an attribute of the pynput stub.
_pynput = sys.modules["pynput"]
if not hasattr(_pynput, "keyboard"):
    _pynput.keyboard = _kb
