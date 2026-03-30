#!/usr/bin/env python3
"""WhisperFlow — voice dictation for macOS."""
import sys
import os

# Ensure src/ is on the path when running from the project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import WhisperFlowApp

if __name__ == "__main__":
    WhisperFlowApp().run()
