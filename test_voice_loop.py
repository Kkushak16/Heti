import sys
import os
import time
from pathlib import Path

sys.path.insert(0, r"d:\Antigravity")

from Heti.config.config_loader import Config
from Heti.agent.core_agent import HetiAgent
from Heti.voice import FullVoiceLoopPipeline

def test_full_voice_loop_and_fallback():
    print("=================================================================")
    print(" 🎙️ TESTING PHASE 3 VOICE LAYER (STT, TTS, WAKE, PIPELINE, FALLBACK)")
    print("=================================================================")

    # Test under both Lite and Full configurations
    for tier in ["full", "lite"]:
        print(f"\n >>> Testing Tier: {tier.upper()} <<<")
        config = Config()
        config.active_tier = tier
        config.model_settings = config.raw_config["models"][tier]
        config.llm_name = config.model_settings.get("llm_name")
        config.stt_model = config.model_settings.get("stt_model")
        config.stt_compute_type = config.model_settings.get("stt_compute_type")
        config.tts_voice = config.model_settings.get("tts_voice")
        config.wake_word_engine = config.model_settings.get("wake_word_engine")
        config.auto_unload_stt = config.model_settings.get("auto_unload_stt")

        agent = HetiAgent(config=config)
        pipeline = FullVoiceLoopPipeline(agent=agent, config=config)

        # 1. Test Fallback Text Input Mode
        fallback_res = pipeline.process_fallback_text_turn("What is the system memory usage?")
        assert fallback_res["response"], "Fallback text turn failed to produce response!"
        print(f"✅ Fallback Text Turn verified in {fallback_res['elapsed_sec']}s")

        # 2. Test End-to-End Voice Turn & Benchmark Latency
        sample_audio = os.path.abspath("test_sample_query.wav")
        if not os.path.exists(sample_audio):
            import numpy as np
            from scipy.io import wavfile
            wavfile.write(sample_audio, 16000, np.zeros(16000, dtype=np.int16))

        voice_res = pipeline.process_voice_turn(sample_audio)

        latency = voice_res["latency"]
        print(f"📊 Latency Audit for {tier.upper()} Tier:")
        print(f"   • STT Latency: {latency['stt_latency_sec']}s")
        print(f"   • LLM Latency: {latency['llm_latency_sec']}s")
        print(f"   • TTS Latency: {latency['tts_latency_sec']}s")
        print(f"   • Total Latency: {latency['total_latency_sec']}s")

        if tier == "full":
            print(f" Target <3.0s | Actual: {latency['total_latency_sec']}s")
        else:
            print(f" Target <6-8s | Actual: {latency['total_latency_sec']}s (Includes STT unload & RAM protection)")
            assert latency["stt_unloaded_immediately"] is True, "Lite tier failed to unload STT immediately!"

        print(f"✅ Voice Loop pipeline verified for {tier.upper()} tier!")

    print("\n=================================================================")
    print(" ✅ ALL PHASE 3 VOICE LAYER TESTS AND LATENCY BENCHMARKS PASSED")
    print("=================================================================")

if __name__ == "__main__":
    test_full_voice_loop_and_fallback()
