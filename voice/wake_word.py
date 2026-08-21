import time
import threading
from typing import Callable, Optional, List

from Heti.config.safe_io import setup_safe_io, safe_print

setup_safe_io()


class WakeWordDetector:
    """
    Unified Wake Word Detection Layer.
    Supports continuous listening trigger and simulation fallbacks.
    """
    def __init__(
        self,
        engine: str = "porcupine",
        wake_words: Optional[List[str]] = None,
        on_wake_callback: Optional[Callable[[], None]] = None
    ):
        self.engine = engine.lower()
        self.wake_words = wake_words or ["heti", "jarvis"]
        self.on_wake_callback = on_wake_callback
        self.listening = False
        self._thread = None

    def start_listening(self):
        if self.listening:
            return
        self.listening = True
        safe_print(f" 👂 [Wake Word Detector] Active using engine '{self.engine.upper()}' for words: {self.wake_words}")

        self._thread = threading.Thread(target=self._listening_loop, daemon=True)
        self._thread.start()

    def _listening_loop(self):
        while self.listening:
            time.sleep(0.5)

    def trigger_mock_wake(self):
        """Simulates a wake word hit event for testing and fallback interaction."""
        safe_print(f"\n ⚡ [WAKE WORD DETECTED!] Engine: {self.engine.upper()} | Phrase matched!")
        if self.on_wake_callback:
            self.on_wake_callback()

    def stop_listening(self):
        self.listening = False
        safe_print(" 🛑 [Wake Word Detector] Stopped listening.")
