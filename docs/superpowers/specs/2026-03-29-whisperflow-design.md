# WhisperFlow Mac App — Design Spec
**Date:** 2026-03-29
**Status:** Approved

---

## Overview

A macOS menu bar dictation app that lets the user speak in English or Hungarian and have transcribed text typed directly into whatever app is currently focused. Inspired by Whispr Flow. Runs entirely offline using a local Whisper model.

---

## Requirements

- **Trigger:** Global hotkey `Ctrl+Space` — toggle (press once to start, press again to stop)
- **Languages:** English and Hungarian — auto-detected per recording, no manual switching required
- **Output:** Transcribed text is auto-typed into the currently focused app via simulated keystrokes
- **Transcription:** Local `faster-whisper` using the `medium` Whisper model (~1.5GB, best accuracy for Hungarian)
- **No internet required:** All processing happens on-device
- **Platform:** macOS 12 Monterey and later, Apple Silicon and Intel

---

## Architecture

Four focused components wired by a thin App controller:

### 1. HotkeyListener
- Uses `pynput` to register `Ctrl+Space` as a global hotkey
- Fires `on_start` and `on_stop` events to the App controller
- Runs on a background thread, does not block the UI

### 2. AudioRecorder
- Uses `sounddevice` to capture microphone input at 16kHz (Whisper's native sample rate)
- Accumulates audio into an in-memory buffer while recording is active
- Returns a numpy array on stop

### 3. Transcriber
- Loads `faster-whisper` with the `medium` model at startup
- Accepts audio buffer, runs inference with `language=None` (auto-detect)
- Returns transcribed text string
- Runs in a background thread to avoid blocking the UI

### 4. TextInjector
- Uses `CGEventCreateKeyboardEvent` via PyObjC/Quartz to simulate keystrokes
- Types the transcribed text into the currently focused macOS app
- Works with browsers, native apps, Electron apps, terminal, etc.

### App Controller
- Built with `rumps` (menu bar framework)
- Manages state machine: `idle → recording → transcribing → idle`
- Wires the four components together
- Shows/hides the overlay UI based on state

---

## UI

### Menu Bar Icon
| State | Icon |
|-------|------|
| Idle | Microphone icon |
| Recording | Animated red dot |
| Transcribing | Spinning indicator |

### Menu Items
- About WhisperFlow
- Quit

### Floating Overlay
- Small pill-shaped HUD that appears on screen during recording and transcribing
- Shows "Recording..." (red) while mic is active
- Shows "Transcribing..." (gray) while processing
- Disappears when text is injected
- Implemented as a borderless, always-on-top `NSPanel` via PyObjC

### No dock icon, no main window — pure menu bar app.

---

## Permissions

On first launch the app requests:
1. **Microphone access** — required for audio capture
2. **Accessibility access** — required for typing into other apps via CGEvent

The app guides the user to grant both in System Settings if not already granted.

---

## Tech Stack

| Component | Library |
|-----------|---------|
| Menu bar | `rumps` |
| Global hotkey | `pynput` |
| Audio capture | `sounddevice` |
| Transcription | `faster-whisper` |
| Text injection | `PyObjC` + `Quartz` |
| Overlay UI | `PyObjC` + `AppKit` (NSPanel) |
| Packaging | `py2app` |

---

## Whisper Model

- **Model:** `medium` (~1.5GB)
- **Language detection:** Automatic (`language=None`) — detects English vs Hungarian per recording
- **Compute type:** `int8` for speed on both Apple Silicon and Intel

---

## File Structure

```
WhisperFlow/
├── src/
│   ├── app.py              # App controller, rumps menu bar
│   ├── hotkey_listener.py  # pynput global hotkey
│   ├── audio_recorder.py   # sounddevice recording
│   ├── transcriber.py      # faster-whisper inference
│   ├── text_injector.py    # CGEvent keystroke injection
│   └── overlay.py          # NSPanel floating HUD
├── setup.py                # py2app packaging config
├── requirements.txt
└── docs/
    └── superpowers/specs/
        └── 2026-03-29-whisperflow-design.md
```

---

## User Flow

1. App launches → loads Whisper `medium` model in background → menu bar icon appears
2. User presses `Ctrl+Space` → overlay shows "Recording..." → mic starts
3. User speaks in English or Hungarian
4. User presses `Ctrl+Space` → mic stops → overlay shows "Transcribing..."
5. Transcribed text is typed into the focused app → overlay disappears
6. Back to idle

---

## Out of Scope

- Manual language override
- Settings window
- Clipboard fallback
- Multiple hotkey options
- Cloud transcription
- Windows/Linux support
