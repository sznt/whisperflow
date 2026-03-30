from AppKit import NSEvent, NSEventMaskKeyDown

# Key code for Space bar
_SPACE_KEY_CODE = 49
# NSEventModifierFlagControl = 1 << 18
_CONTROL_FLAG = 1 << 18


class HotkeyListener:
    """Listens for Ctrl+Space globally using NSEvent (Python 3.13 compatible)."""

    def __init__(self, on_toggle):
        self._on_toggle = on_toggle
        self._monitor = None

    def start(self) -> None:
        self._monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            NSEventMaskKeyDown,
            self._handle_event,
        )

    def _handle_event(self, event) -> None:
        if (event.keyCode() == _SPACE_KEY_CODE and
                event.modifierFlags() & _CONTROL_FLAG):
            self._on_toggle()

    def stop(self) -> None:
        if self._monitor:
            NSEvent.removeMonitor_(self._monitor)
            self._monitor = None
