import sys
# modulegraph has a recursion issue with Python 3.13 and complex dependency graphs
sys.setrecursionlimit(10000)

from setuptools import setup

APP = ["main.py"]
DATA_FILES = []
OPTIONS = {
    "argv_emulation": False,
    "plist": {
        "CFBundleName": "WhisperFlow",
        "CFBundleDisplayName": "WhisperFlow",
        "CFBundleIdentifier": "com.whisperflow.app",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "LSUIElement": True,
        "NSMicrophoneUsageDescription": "WhisperFlow needs microphone access to record your voice.",
        "NSAppleEventsUsageDescription": "WhisperFlow needs Accessibility access to type transcribed text.",
    },
    "packages": [
        "faster_whisper",
        "sounddevice",
        "pynput",
        "rumps",
        "AppKit",
        "Quartz",
        "numpy",
        "src",
        "ctranslate2",
        "requests",
        "urllib3",
        "charset_normalizer",
        "certifi",
        "idna",
        "huggingface_hub",
        "tokenizers",
        "tqdm",
        "av",
        "onnxruntime",
        "httpx",
        "filelock",
        "fsspec",
        "packaging",
        "typing_extensions",
    ],
    "includes": [],
    "excludes": ["tkinter"],
}

setup(
    app=APP,
    name="WhisperFlow",
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
