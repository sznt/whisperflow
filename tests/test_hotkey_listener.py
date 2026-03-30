import pytest
from unittest.mock import MagicMock, patch, call


def test_start_registers_hotkey(mock_pynput):
    from src.hotkey_listener import HotkeyListener
    callback = MagicMock()
    listener = HotkeyListener(on_toggle=callback)
    listener.start()
    mock_pynput.GlobalHotKeys.assert_called_once_with(
        {"<ctrl>+<space>": callback}
    )
    mock_pynput.GlobalHotKeys.return_value.start.assert_called_once()


def test_stop_calls_stop_on_hotkey(mock_pynput):
    from src.hotkey_listener import HotkeyListener
    callback = MagicMock()
    listener = HotkeyListener(on_toggle=callback)
    listener.start()
    listener.stop()
    mock_pynput.GlobalHotKeys.return_value.stop.assert_called_once()


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
