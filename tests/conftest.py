import sys
import types

# Stub out AppKit/Quartz/Cocoa at import time so tests run without a display
for mod in [
    "AppKit", "Quartz", "Cocoa", "objc",
    "AppKit.NSColor", "AppKit.NSFont", "AppKit.NSScreen",
]:
    if mod not in sys.modules:
        sys.modules[mod] = types.ModuleType(mod)

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
