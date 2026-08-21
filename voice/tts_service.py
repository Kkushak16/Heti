import time
import os
import sys
import subprocess
from typing import Optional, Dict, Any

from Heti.config.safe_io import setup_safe_io, safe_print

setup_safe_io()

try:
    import piper
    HAS_PIPER = True
except ImportError:
    HAS_PIPER = False


class PiperTTSService:
    """
    Text-To-Speech Service using Piper ONNX models or Windows Native SAPI fallback.
    Supports:
    - Piper ONNX model execution if piper binary is installed.
    - Native Windows SAPI SpeechSynthesizer fallback for instant offline speech output.
    - Active speech cancellation (stop_speaking) when new command is given.
    """
    def __init__(self, voice_name: str = "en_US-lessac-low", output_dir: str = "voice_output"):
        self.voice_name = voice_name
        self.output_dir = output_dir
        self._active_proc = None
        os.makedirs(self.output_dir, exist_ok=True)

    def stop_speaking(self):
        """Immediately stops any ongoing TTS audio output so Heti does not speak over user commands."""
        try:
            if sys.platform == "win32":
                import winsound
                winsound.PlaySound(None, 0)
                if self._active_proc and self._active_proc.poll() is None:
                    self._active_proc.terminate()
                    self._active_proc = None
                # Stop any active powershell SpeechSynthesizer process
                creationflags = 0x08000000
                subprocess.Popen(
                    ["powershell", "-NoProfile", "-Command", "Get-Process powershell -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like '*System.Speech*'} | Stop-Process -Force -ErrorAction SilentlyContinue"],
                    creationflags=creationflags
                )
        except Exception:
            pass

    def speak(self, text: str, play_audio: bool = True, sync: bool = False) -> Dict[str, Any]:
        """
        Synthesizes text into audio. Stops previous audio and speaks text.
        If sync=True, waits until speaking is complete before returning.
        Returns metadata: { "status", "output_wav", "elapsed_sec", "voice" }
        """
        self.stop_speaking()
        t0 = time.time()
        output_filename = f"response_{int(time.time())}.wav"
        output_path = os.path.join(self.output_dir, output_filename)

        safe_print(f" 🔊 [TTS] Synthesizing: \"{text[:80]}{'...' if len(text)>80 else ''}\"")

        success = False
        # 1. Try Piper CLI
        try:
            piper_cmd = ["piper", "--model", self.voice_name, "--output_file", output_path]
            proc = subprocess.run(
                piper_cmd,
                input=text,
                text=True,
                capture_output=True,
                timeout=15
            )
            if proc.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 100:
                success = True
        except Exception:
            success = False

        # 2. Fallback to Windows Native SAPI SpeechSynthesizer if Piper isn't available
        if not success and play_audio:
            self._speak_windows_sapi(text, sync=sync)

        elapsed = round(time.time() - t0, 3)

        if success and play_audio:
            self._play_wav(output_path)

        return {
            "status": "success",
            "output_wav": output_path if success else "",
            "elapsed_sec": elapsed,
            "voice": self.voice_name if success else "Windows SAPI Native"
        }

    def _speak_windows_sapi(self, text: str, sync: bool = False):
        """Uses Windows built-in System.Speech SpeechSynthesizer for instant, reliable voice output."""
        try:
            if sys.platform == "win32":
                safe_text = text.replace('"', "'").replace("`", "")
                ps_cmd = f'Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.Speak("{safe_text}");'
                creationflags = 0x08000000  # CREATE_NO_WINDOW
                if sync:
                    subprocess.run(
                        ["powershell", "-NoProfile", "-Command", ps_cmd],
                        creationflags=creationflags,
                        timeout=10
                    )
                else:
                    self._active_proc = subprocess.Popen(
                        ["powershell", "-NoProfile", "-Command", ps_cmd],
                        creationflags=creationflags
                    )
        except Exception as e:
            safe_print(f" ⚠️ [TTS Warning] Windows SAPI fallback error: {e}")

    def _play_wav(self, wav_path: str):
        try:
            if sys.platform == "win32" and os.path.exists(wav_path):
                import winsound
                with open(wav_path, "rb") as f:
                    header = f.read(4)
                if header == b"RIFF":
                    winsound.PlaySound(wav_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception as e:
            safe_print(f" ⚠️ [TTS Warning] Could not play audio: {e}")
