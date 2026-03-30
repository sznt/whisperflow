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
