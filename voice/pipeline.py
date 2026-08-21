import time
import os
import sys
from typing import Dict, Any, Optional, Tuple

from Heti.config.safe_io import setup_safe_io, safe_print
from Heti.voice.stt_service import FasterWhisperSTT
from Heti.voice.tts_service import PiperTTSService
from Heti.voice.wake_word import WakeWordDetector

setup_safe_io()



class FullVoiceLoopPipeline:
    """
    Complete Voice Loop Architecture:
    Wake Word -> Record/Audio Input -> STT Transcribe -> Agent LLM -> TTS Response.

    Lite Tier Optimizations:
    - Auto-unloads STT model immediately after transcription to maximize RAM headroom for LLM.
    - Uses lightweight low/x-low Piper ONNX voices (~20-60MB).
    - Near-zero RAM wake word detector.
    - Fallback text input mode available if voice is unavailable/disabled.
    """
    def __init__(self, agent, config):
        self.agent = agent
        self.config = config

        self.stt = FasterWhisperSTT(
            model_size=config.stt_model,
            compute_type=config.stt_compute_type,
            auto_unload=config.auto_unload_stt
        )
        self.tts = PiperTTSService(voice_name=config.tts_voice)
        self.wake_detector = WakeWordDetector(
            engine=config.wake_word_engine,
            wake_words=config.wake_words,
            on_wake_callback=self._handle_wake_event
        )

    def _handle_wake_event(self):
        print(" 🎤 [Voice Pipeline] Listening for user query...")

    def process_voice_turn(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Executes an end-to-end voice turn and tracks latency metrics.
        Returns latency breakdown and agent response.
        """
        t_total_start = time.time()
        print(f"\n========================================================")
        print(f" 🎙️ STARTING VOICE TURN (Tier: {self.config.active_tier.upper()})")
        print(f"========================================================")

        # Step 1: STT Transcription
        t_stt_start = time.time()
        transcript, stt_latency = self.stt.transcribe(audio_file_path)
        t_stt_end = time.time()

        print(f" 📝 Transcribed Input: \"{transcript}\" (STT Latency: {stt_latency}s)")

        # Step 2: Agent LLM Processing & Tool Execution
        t_llm_start = time.time()
        agent_response = self.agent.run_turn(transcript)
        t_llm_end = time.time()
        llm_latency = round(t_llm_end - t_llm_start, 3)
        print(f" 🤖 Agent Response: \"{agent_response[:100]}...\" (LLM Latency: {llm_latency}s)")

        # Step 3: TTS Speech Synthesis
        t_tts_start = time.time()
        tts_res = self.tts.speak(agent_response)
        tts_latency = tts_res["elapsed_sec"]

        t_total_end = time.time()
        total_latency = round(t_total_end - t_total_start, 3)

        latency_breakdown = {
            "tier": self.config.active_tier,
            "stt_latency_sec": stt_latency,
            "llm_latency_sec": llm_latency,
            "tts_latency_sec": tts_latency,
            "total_latency_sec": total_latency,
            "stt_unloaded_immediately": self.config.auto_unload_stt
        }

        print(f"\n ⏱️ [LATENCY BENCHMARK RESULT]")
        print(f" • STT Time  : {stt_latency}s")
        print(f" • LLM Time  : {llm_latency}s")
        print(f" • TTS Time  : {tts_latency}s")
        print(f" • TOTAL TIME: {total_latency}s (Target: <3s Full | <6-8s Lite)")
        print(f"========================================================\n")

        return {
            "transcript": transcript,
            "response": agent_response,
            "audio_output": tts_res["output_wav"],
            "latency": latency_breakdown
        }

    def process_fallback_text_turn(self, text_input: str) -> Dict[str, Any]:
        """Fallback text input handler when voice hardware is unavailable or fails."""
        t0 = time.time()
        print(f"\n ⌨️ [Text Fallback Turn] User: \"{text_input}\"")
        agent_response = self.agent.run_turn(text_input)
        tts_res = self.tts.speak(agent_response)
        elapsed = round(time.time() - t0, 3)

        return {
            "input": text_input,
            "response": agent_response,
            "audio_output": tts_res["output_wav"],
            "elapsed_sec": elapsed
        }

    def _get_username(self) -> str:

        try:
            import getpass
            return getpass.getuser()
        except Exception:
            return "User"

    def _handle_wake_event(self):
        username = os.environ.get("USERNAME") or os.environ.get("USER") or "User"
        greeting = f"Hi {username}, I'm Heti. How can I help you?"
        print(f"\n ⚡ [WAKE WORD DETECTED!] Heti: \"{greeting}\"")
        self.tts.speak(greeting, play_audio=True, sync=True)

    def listen_microphone_and_transcribe(self, duration_sec: float = 4.0) -> Tuple[str, float]:
        """Captures real microphone audio input via sounddevice and transcribes using FasterWhisper."""
        try:
            import sounddevice as sd
            import numpy as np
            from scipy.io import wavfile
            import tempfile
            import time as time_module

            samplerate = 16000

            safe_print(f" 🎙️ Recording", end="", flush=True)
            recording = sd.rec(int(duration_sec * samplerate), samplerate=samplerate, channels=1, dtype='int16')
            for i in range(int(duration_sec)):
                time_module.sleep(1)
                safe_print(".", end="", flush=True)
            sd.wait()
            safe_print(" done!")

            max_amp = np.max(np.abs(recording))
            if max_amp < 10:
                safe_print(" ⚠️ [STT] Silence detected — no voice captured.")
                return "", 0.0

            # Normalize soft recordings so whisper receives clean audio level
            if max_amp < 22000 and max_amp > 0:
                recording = (recording.astype(np.float32) * (26000.0 / max(float(max_amp), 1.0))).clip(-32768, 32767).astype(np.int16)

            temp_wav = os.path.join(tempfile.gettempdir(), "heti_mic_input.wav")
            wavfile.write(temp_wav, samplerate, recording)

            safe_print(" 🔄 Transcribing speech...", end="", flush=True)
            transcript, latency = self.stt.transcribe(temp_wav)
            safe_print(f" done! ({latency}s)")

            if os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except Exception:
                    pass

            # Filter out whisper halluncinations on near silence
            clean_text = transcript.strip()
            if clean_text in [".", ",", "!", "?", "...", "[BLANK_AUDIO]", "[MUSIC]", "[NOISE]"]:
                clean_text = ""

            return clean_text, latency

        except Exception as err:
            safe_print(f"\n ⚠️ [Microphone Error] {err}")
            return "", 0.0

    def run_voice_loop(self):
        """Runs the continuous wake word -> record -> transcribe -> response loop."""
        username = os.environ.get("USERNAME") or os.environ.get("USER") or "User"
        print(f" 🎙️ [Voice Loop Active] Engine: '{self.config.wake_word_engine}' | Voice: '{self.config.tts_voice}'")
        print(f" 💡 Live Microphone Recording active. Press Enter to record voice turn (or type your query).")
        print(" Press Ctrl+C or type 'exit' to return to CLI.")

        wake_list = [
            "hey heti", "heti", "hey jarvis", "jarvis",
            "heeti", "hey heeti", "hety", "hey hety",
            "hetty", "hey hetty", "hedi", "headi", "hady",
            "haeti", "hay tea", "hey tea", "hi heti", "ok heti", "hello heti"
        ]

        try:
            while True:
                user_input = input(f"\n🎙️ [Press Enter to Record Mic, or type text ({username})] > ").strip()
                if user_input.lower() in ["exit", "quit"]:
                    print(" Exiting voice mode loop...")
                    break

                if user_input == "":
                    # Real microphone recording mode
                    transcript, stt_latency = self.listen_microphone_and_transcribe(duration_sec=4.0)
                    if not transcript:
                        safe_print(" ⚠️ [STT] No speech detected from microphone.")
                        continue
                    user_audio_prompt = transcript
                else:
                    user_audio_prompt = user_input

                # Immediately stop any ongoing audio speaking when new speech is received
                self.tts.stop_speaking()

                # 1. Echo what was transcribed/said
                safe_print(f" 📝 [STT Transcribed Speech]: \"{user_audio_prompt}\"")

                # 2. Check for Wake Word greeting trigger
                if any(w in user_audio_prompt.lower() for w in wake_list):
                    cleaned_cmd = user_audio_prompt.lower()
                    for w in wake_list:
                        cleaned_cmd = cleaned_cmd.replace(w, "").strip()
                    if not cleaned_cmd:
                        self._handle_wake_event()
                        continue
                    user_audio_prompt = cleaned_cmd

                # 3. Process Turn & Output Response
                safe_print(f" 🤖 Heti is processing your request...")
                res = self.process_fallback_text_turn(user_audio_prompt)
                print(f"\n 💬 [Heti] {res['response']}\n")

                # 4. Speak Closing Phrase
                self.tts.speak("For any other help, I'm here Heti.", play_audio=True, sync=True)

        except KeyboardInterrupt:
            print("\n Voice loop stopped.")



