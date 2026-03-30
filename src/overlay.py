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
    NSLeftTextAlignment,
    NSObject,
)

NSBorderlessWindowMask = 0
kCGBackingStoreBuffered = 2

# Overlay dimensions — wide enough for a sentence of partial text
_WIDTH = 520.0
_STATUS_H = 28.0   # top row: status emoji + level bar
_TEXT_H = 36.0     # bottom row: partial transcription text
_PAD = 10.0        # vertical padding inside panel
_TOTAL_H = _PAD + _STATUS_H + _TEXT_H + _PAD


class _Runner(NSObject):
    """Marshals show/hide calls onto the main AppKit thread."""

    @objc.python_method
    def initWithOverlay_(self, overlay):
        self = objc.super(_Runner, self).init()
        self._overlay = overlay
        return self

    def doUpdate_(self, args):
        # args is a tuple packed as a list: [status, partial_text]
        self._overlay._do_update(args[0], args[1])

    def doHide_(self, _sender):
        self._overlay._do_hide()


class Overlay:
    def __init__(self):
        self._panel = None
        self._status_label = None   # top: "● Recording  ▁▃▅"
        self._text_label = None     # bottom: partial transcription
        self._runner = None

    # ── public API (thread-safe) ───────────────────────────────────────────

    def show(self, status: str, partial: str = "") -> None:
        """Update the overlay. Can be called from any thread."""
        self._ensure_runner()
        self._runner.performSelectorOnMainThread_withObject_waitUntilDone_(
            "doUpdate:", [status, partial], False
        )

    def hide(self) -> None:
        if self._runner is None:
            return
        self._runner.performSelectorOnMainThread_withObject_waitUntilDone_(
            "doHide:", None, False
        )

    # ── main-thread implementations ────────────────────────────────────────

    def _do_update(self, status: str, partial: str) -> None:
        self._ensure_panel()
        self._status_label.setStringValue_(status)
        if partial:
            # Show last ~60 chars with a blinking-cursor feel
            display = ("…" + partial[-58:]) if len(partial) > 60 else partial
            self._text_label.setStringValue_(display + "▌")
            self._text_label.setHidden_(False)
        else:
            self._text_label.setHidden_(True)
        self._panel.orderFrontRegardless()

    def _do_hide(self) -> None:
        if self._panel:
            self._panel.orderOut_(None)

    # ── lazy init ──────────────────────────────────────────────────────────

    def _ensure_runner(self) -> None:
        if self._runner is None:
            self._runner = _Runner.alloc().initWithOverlay_(self)

    def _ensure_panel(self) -> None:
        if self._panel is not None:
            return
        screen = NSScreen.mainScreen()
        sr = screen.frame()
        x = (sr.size.width - _WIDTH) / 2.0
        y = sr.size.height * 0.12

        self._panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, _WIDTH, _TOTAL_H),
            NSBorderlessWindowMask,
            kCGBackingStoreBuffered,
            False,
        )
        self._panel.setLevel_(NSFloatingWindowLevel)
        self._panel.setBackgroundColor_(
            NSColor.colorWithRed_green_blue_alpha_(0.08, 0.08, 0.08, 0.90)
        )
        self._panel.setOpaque_(False)
        self._panel.setHasShadow_(True)
        self._panel.setIgnoresMouseEvents_(True)
        cv = self._panel.contentView()

        # ── status label (top, centered) ──────────────────────────────────
        sy = _PAD + _TEXT_H
        self._status_label = NSTextField.alloc().initWithFrame_(
            NSMakeRect(12.0, sy, _WIDTH - 24.0, _STATUS_H)
        )
        self._status_label.setEditable_(False)
        self._status_label.setBordered_(False)
        self._status_label.setDrawsBackground_(False)
        self._status_label.setTextColor_(NSColor.whiteColor())
        self._status_label.setFont_(NSFont.systemFontOfSize_(13.0))
        self._status_label.setAlignment_(NSCenterTextAlignment)
        cv.addSubview_(self._status_label)

        # ── partial text label (bottom, left-aligned, smaller) ─────────────
        self._text_label = NSTextField.alloc().initWithFrame_(
            NSMakeRect(14.0, _PAD, _WIDTH - 28.0, _TEXT_H)
        )
        self._text_label.setEditable_(False)
        self._text_label.setBordered_(False)
        self._text_label.setDrawsBackground_(False)
        self._text_label.setTextColor_(
            NSColor.colorWithRed_green_blue_alpha_(0.85, 0.85, 0.85, 1.0)
        )
        self._text_label.setFont_(NSFont.systemFontOfSize_(12.0))
        self._text_label.setAlignment_(NSLeftTextAlignment)
        self._text_label.setHidden_(True)
        cv.addSubview_(self._text_label)
