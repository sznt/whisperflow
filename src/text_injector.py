import time
import sys


class TextInjector:
    DELAY = 0.001  # seconds between keystrokes

    def type_text(self, text: str) -> None:
        for char in text:
            self._type_char(char)

    def _type_char(self, char: str) -> None:
        Quartz = sys.modules["Quartz"]
        event_down = Quartz.CGEventCreateKeyboardEvent(None, 0, True)
        event_up = Quartz.CGEventCreateKeyboardEvent(None, 0, False)
        Quartz.CGEventKeyboardSetUnicodeString(event_down, len(char), char)
        Quartz.CGEventKeyboardSetUnicodeString(event_up, len(char), char)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)
        time.sleep(self.DELAY)
