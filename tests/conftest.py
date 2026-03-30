import sys
import types

# Stub out AppKit/Quartz/Cocoa at import time so tests run without a display
for mod in [
    "AppKit", "Quartz", "Cocoa", "objc",
    "AppKit.NSColor", "AppKit.NSFont", "AppKit.NSScreen",
]:
    if mod not in sys.modules:
        sys.modules[mod] = types.ModuleType(mod)
