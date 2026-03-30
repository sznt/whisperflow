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
    # 2 chars x 2 events (down + up) = 4 CGEventCreateKeyboardEvent calls
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
