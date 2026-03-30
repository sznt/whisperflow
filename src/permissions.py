import sys


def check_and_request_permissions() -> bool:
    """
    Check that Accessibility permission is granted (required for CGEvent
    text injection and global hotkey capture via pynput).

    Returns True if trusted, False if not (prints guidance and returns False).
    The app should exit if this returns False.
    """
    try:
        from ApplicationServices import AXIsProcessTrustedWithOptions
        options = {"AXTrustedCheckOptionPrompt": True}
        trusted = AXIsProcessTrustedWithOptions(options)
    except Exception:
        # If ApplicationServices isn't available fall back to Quartz
        try:
            from Quartz import AXIsProcessTrustedWithOptions
            options = {"AXTrustedCheckOptionPrompt": True}
            trusted = AXIsProcessTrustedWithOptions(options)
        except Exception:
            # Cannot check — assume not trusted, show instructions
            trusted = False

    if not trusted:
        print(
            "\n⚠️  WhisperFlow needs Accessibility permission.\n\n"
            "  1. Open System Settings → Privacy & Security → Accessibility\n"
            "     Add Terminal (or WhisperFlow.app) and enable it.\n\n"
            "  2. Open System Settings → Privacy & Security → Input Monitoring\n"
            "     Add Terminal (or WhisperFlow.app) and enable it.\n\n"
            "After granting permissions, restart the app.\n"
        )
        return False

    return True
