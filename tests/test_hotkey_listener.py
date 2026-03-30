import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_nsevent(monkeypatch):
    nsevent_mock = MagicMock()
    nsevent_mock.addGlobalMonitorForEventsMatchingMask_handler_ = MagicMock(
        return_value=MagicMock()
    )
    nsevent_mock.removeMonitor_ = MagicMock()
    monkeypatch.setattr("src.hotkey_listener.NSEvent", nsevent_mock)
    monkeypatch.setattr("src.hotkey_listener.NSEventMaskKeyDown", 1024)
    yield nsevent_mock


def test_start_registers_global_monitor(mock_nsevent):
    from src.hotkey_listener import HotkeyListener
    listener = HotkeyListener(on_toggle=MagicMock())
    listener.start()
    mock_nsevent.addGlobalMonitorForEventsMatchingMask_handler_.assert_called_once_with(
        1024, listener._handle_event
    )


def test_stop_removes_monitor(mock_nsevent):
    from src.hotkey_listener import HotkeyListener
    listener = HotkeyListener(on_toggle=MagicMock())
    listener.start()
    listener.stop()
    mock_nsevent.removeMonitor_.assert_called_once()


def test_stop_without_start_does_not_raise(mock_nsevent):
    from src.hotkey_listener import HotkeyListener
    listener = HotkeyListener(on_toggle=MagicMock())
    listener.stop()  # must not raise


def test_handle_event_calls_toggle_on_ctrl_space(mock_nsevent):
    from src.hotkey_listener import HotkeyListener, _SPACE_KEY_CODE, _CONTROL_FLAG
    callback = MagicMock()
    listener = HotkeyListener(on_toggle=callback)

    event = MagicMock()
    event.keyCode.return_value = _SPACE_KEY_CODE
    event.modifierFlags.return_value = _CONTROL_FLAG

    listener._handle_event(event)
    callback.assert_called_once()


def test_handle_event_ignores_other_keys(mock_nsevent):
    from src.hotkey_listener import HotkeyListener, _CONTROL_FLAG
    callback = MagicMock()
    listener = HotkeyListener(on_toggle=callback)

    event = MagicMock()
    event.keyCode.return_value = 0  # not Space
    event.modifierFlags.return_value = _CONTROL_FLAG

    listener._handle_event(event)
    callback.assert_not_called()


def test_handle_event_ignores_space_without_ctrl(mock_nsevent):
    from src.hotkey_listener import HotkeyListener, _SPACE_KEY_CODE
    callback = MagicMock()
    listener = HotkeyListener(on_toggle=callback)

    event = MagicMock()
    event.keyCode.return_value = _SPACE_KEY_CODE
    event.modifierFlags.return_value = 0  # no modifiers

    listener._handle_event(event)
    callback.assert_not_called()
