import time
import os
import gc
import warnings
from typing import Optional, Tuple

from Heti.config.safe_io import setup_safe_io, safe_print

setup_safe_io()

# Suppress all HuggingFace Hub noise before anything loads
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")



try:
    from faster_whisper import WhisperModel
    HAS_FASTER_WHISPER = True
except ImportError:
    WhisperModel = None
    HAS_FASTER_WHISPER = False


class FasterWhisperSTT:
    """
    STT Service powered by Faster-Whisper.
    Supports:
    - Full tier: 'small' / 'medium' model with float16 / int8 computation.
    - Lite tier: 'tiny' / 'base' with int8 quantization.
    - Immediate RAM unloading (auto_unload_stt) to optimize memory headroom on resource-constrained devices.
    """
    def __init__(self, model_size: str = "tiny", compute_type: str = "int8", device: str = "cpu", auto_unload: bool = True):
        self.model_size = model_size
        self.compute_type = compute_type
        self.device = device
        self.auto_unload = auto_unload
        self._model: Optional[WhisperModel] = None

    def _load_model(self):
        if self._model is not None:
            return

        if not HAS_FASTER_WHISPER:
            safe_print(" ⚠️ [STT Warning] `faster-whisper` package not installed. Running in mock STT mode.")
            return

        # Silence HuggingFace symlinks and Hub warnings
        os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

        # CPU fallback: float16 is not supported natively on many CPUs, fallback to int8 or float32
        actual_compute_type = self.compute_type
        if self.device == "cpu" and self.compute_type == "float16":
            actual_compute_type = "int8"

        safe_print(f" 🎙️ [STT] Loading Faster-Whisper model '{self.model_size}' (compute_type: {actual_compute_type})...")
        t0 = time.time()
        self._model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=actual_compute_type,
            cpu_threads=2
        )
        safe_print(f" 🎙️ [STT] Model loaded in {round(time.time() - t0, 3)}s")


    def unload_model(self):
        """Immediately unloads STT model from RAM to free memory for LLM inference."""
        if self._model is not None:
            safe_print(" 🧹 [STT Memory Headroom] Unloading Faster-Whisper model from RAM...")
            del self._model
            self._model = None
            gc.collect()

    def transcribe(self, audio_input: str) -> Tuple[str, float]:
        """
        Transcribes audio file or audio array.
        Returns: (transcribed_text, elapsed_transcription_time_sec)
        """
        t0 = time.time()
        self._load_model()

        if not HAS_FASTER_WHISPER or self._model is None:
            # Fallback mock transcription for environments without faster-whisper C++ binary runtime
            text = f"[Mock Transcribed Text for {os.path.basename(audio_input)}]"
            elapsed = round(time.time() - t0, 3)
            return text, elapsed

        try:
            prompt_hint = (
                "Heti, Hey Heti, Jarvis, Hey Jarvis. "
                "open camera, open the camera application, close camera, "
                "open file manager, open file explorer, open explorer, open files, close file manager, "
                "open notepad, open text editor, close notepad, "
                "open calculator, open calc, close calculator, "
                "open browser, open web browser, close browser, "
                "new tab, search for, google, web search, "
                "take screenshot, capture screen, system stats."
            )
            segments, info = self._model.transcribe(
                audio_input,
                beam_size=3,
                initial_prompt=prompt_hint,
                language="en"
            )
            transcribed_text = " ".join([segment.text for segment in segments]).strip()
            elapsed = round(time.time() - t0, 3)
        finally:
            if self.auto_unload:
                self.unload_model()

        return transcribed_text, elapsed
