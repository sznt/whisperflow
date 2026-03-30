import objc
from AppKit import (
    NSPanel,
    NSTextField,
    NSColor,
    NSFont,
    NSScreen,
    NSMakeRect,
    NSFloatingWindowLevel,
    NSCenterTextAlignment,
    NSObject,
    NSApp,
)

# NSBorderlessWindowMask = 0 in modern macOS
NSBorderlessWindowMask = 0
# kCGBackingStoreBuffered = 2
kCGBackingStoreBuffered = 2


class _ShowRunner(NSObject):
    """Runs show/hide on the main thread via performSelectorOnMainThread."""

    @objc.python_method
    def initWithOverlay_(self, overlay):
        self = objc.super(_ShowRunner, self).init()
        self._overlay = overlay
        return self

    def doShow_(self, message):
        self._overlay._do_show(message)

    def doHide_(self, sender):
        self._overlay._do_hide()


class Overlay:
    def __init__(self):
        self._panel = None
        self._label = None
        self._runner = None

    def show(self, message: str) -> None:
        if self._runner is None:
            self._runner = _ShowRunner.alloc().initWithOverlay_(self)
        self._runner.performSelectorOnMainThread_withObject_waitUntilDone_(
            "doShow:", message, False
        )

    def hide(self) -> None:
        if self._runner is None:
            return
        self._runner.performSelectorOnMainThread_withObject_waitUntilDone_(
            "doHide:", None, False
        )

    def _do_show(self, message: str) -> None:
        self._ensure_panel()
        self._label.setStringValue_(message)
        self._panel.orderFrontRegardless()

    def _do_hide(self) -> None:
        if self._panel:
            self._panel.orderOut_(None)

    def _ensure_panel(self) -> None:
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
