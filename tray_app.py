"""
Heti Voice Agent — System Tray App
Runs as a background system tray icon (bottom-right taskbar).
Right-click the tray icon to access all controls.
No terminal needed once started.
"""
import sys
import os
import threading

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from Heti.config.safe_io import setup_safe_io, safe_print

setup_safe_io()

import pystray
from PIL import Image, ImageDraw

from Heti.config.config_loader import Config
from Heti.agent.core_agent import HetiAgent
from Heti.tools.system_tools import get_default_tools
from Heti.voice.pipeline import FullVoiceLoopPipeline
from Heti.rag import LocalRAGStore, KnowledgeBaseWatcher, RAGRetrievalHook


# ─── Global State ────────────────────────────────────────────────────────────
config = None
agent = None
rag_hook = None
voice_pipeline = None
kb_watcher = None
voice_thread = None
voice_running = False


def _build_icon_image():
    """Creates a simple blue circle tray icon with H logo."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, size - 4, size - 4], fill=(59, 130, 246), outline=(30, 64, 175), width=3)
    # Draw letter "H"
    draw.line([16, 16, 16, 48], fill="white", width=5)
    draw.line([48, 16, 48, 48], fill="white", width=5)
    draw.line([16, 32, 48, 32], fill="white", width=4)
    return img


def _notify(icon, title: str, message: str):
    """Send a Windows toast/balloon notification from the tray."""
    try:
        if icon:
            icon.notify(message, title)
    except Exception:
        pass


def _initialize_agent():
    global config, agent, rag_hook, voice_pipeline, kb_watcher

    config = Config()

    kb_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "trusted_kb"))
    os.makedirs(kb_dir, exist_ok=True)

    rag_store = LocalRAGStore(
        persist_directory=os.path.abspath(os.path.join(os.path.dirname(__file__), f"chroma_{config.active_tier}")),
        embedding_model_name=config.embedding_model,
        persist_mode=config.rag_persist_mode,
        trusted_subfolder="trusted_kb"
    )

    kb_watcher = KnowledgeBaseWatcher(
        kb_folder=kb_dir,
        rag_store=rag_store,
        poll_interval_sec=10.0,
        max_chunk_tokens=config.rag_chunk_size
    )
    kb_watcher.start()

    agent = HetiAgent(config=config)
    for tool in get_default_tools():
        agent.register_tool(tool)

    rag_hook = RAGRetrievalHook(rag_store=rag_store, agent=agent, config=config)
    voice_pipeline = FullVoiceLoopPipeline(agent=agent, config=config)


# ─── Voice Loop Thread ───────────────────────────────────────────────────────
WAKE_WORDS = [
    "hey heti", "heti", "hey jarvis", "jarvis",
    "heeti", "hey heeti", "hety", "hey hety",
    "hetty", "hey hetty", "hedi", "headi", "hady",
    "haeti", "hay tea", "hey tea", "hi heti", "ok heti", "hello heti",
    "hey heavy", "hey eddy", "hey hit me", "hey sweetie", "hey heaty",
    "hey 80", "hey eighty", "hay heti", "hey hiti", "hey city", "hey ready",
    "hey hit", "hey high tea", "hey hatchi", "hey hate"
]
_last_command = ""
_last_command_time = 0

def _contains_wake_word(text):
    """Check if text contains a wake word."""
    lower = text.lower()
    return any(w in lower for w in WAKE_WORDS)

def _strip_wake_words(text):
    """Remove wake words from text."""
    cleaned = text.lower()
    for w in WAKE_WORDS:
        cleaned = cleaned.replace(w, "").strip()
    return cleaned

def _wait_tts_done():
    """Block until TTS finishes speaking."""
    import time as _t
    try:
        while voice_pipeline.tts._active_proc and voice_pipeline.tts._active_proc.poll() is None:
            _t.sleep(0.3)
    except Exception:
        pass

def _voice_loop_thread(icon):
    global voice_running, _last_command, _last_command_time
    import time as _time
    username = os.environ.get("USERNAME") or "User"
    _notify(icon, "Heti Ready", f"Say 'Hey Heti' to activate me!")
    safe_print(" 🎙️ [Voice Loop] Passive mode — waiting for wake word...")

    COOLDOWN_SEC = 5

    while voice_running:
        # ═══════════════════════════════════════════════════════════════
        # PHASE 1: PASSIVE MODE — only listen for wake word
        # ═══════════════════════════════════════════════════════════════
        _wait_tts_done()
        transcript, _ = voice_pipeline.listen_microphone_and_transcribe(duration_sec=3.0)
        if not transcript or not voice_running:
            continue

        if not _contains_wake_word(transcript):
            # Not a wake word → ignore and keep listening passively
            continue

        # Wake word detected!
        voice_pipeline.tts.stop_speaking()
        safe_print(f" 🔔 [Wake Word Detected]: \"{transcript}\"")

        # Check if command was included with the wake word
        command = _strip_wake_words(transcript)

        if not command:
            # Pure wake word with no command — greet and ask
            greeting = f"Hi {username}, how can I help you?"
            _notify(icon, "Heti", greeting)
            voice_pipeline.tts.speak(greeting, play_audio=True, sync=True)
            _time.sleep(0.5)

            # Wait for actual command
            _wait_tts_done()
            command_transcript, _ = voice_pipeline.listen_microphone_and_transcribe(duration_sec=5.0)
            if not command_transcript:
                voice_pipeline.tts.speak("I'm here when you need me Heti.", play_audio=True, sync=True)
                _time.sleep(1)
                safe_print(" 🔇 [Voice Loop] No command received — back to passive mode.")
                continue
            command = _strip_wake_words(command_transcript)
            if not command:
                command = command_transcript

        # ═══════════════════════════════════════════════════════════════
        # PHASE 2: ACTIVE MODE — execute command, offer follow-up
        # ═══════════════════════════════════════════════════════════════
        conversation_active = True
        while conversation_active and voice_running:
            # Dedup check
            now = _time.time()
            cmd_lower = command.lower().strip()
            if cmd_lower == _last_command and (now - _last_command_time) < COOLDOWN_SEC:
                safe_print(f" ⏭️ [Dedup] Skipping duplicate: \"{command}\"")
                conversation_active = False
                break

            _last_command = cmd_lower
            _last_command_time = now

            safe_print(f" 📝 [Command]: \"{command}\"")
            _notify(icon, "Heti Heard", f"\"{command}\"")

            # Execute the command
            _notify(icon, "Heti Working", "Processing...")
            response = agent.run_turn(command)

            safe_print(f" 🤖 [Response]: {response}")
            _notify(icon, "Heti", response[:200])
            voice_pipeline.tts.speak(response, play_audio=True, sync=True)
            _time.sleep(0.5)

            # Offer follow-up with exact phrase requested by user
            _wait_tts_done()
            voice_pipeline.tts.speak("For any other help, I'm here Heti.", play_audio=True, sync=True)
            _time.sleep(0.5)

            # Wait for follow-up command with 2-stage active listening window
            _wait_tts_done()
            safe_print(" 🎙️ [Active Conversation Mode] Listening for follow-up (no wake word needed)...")
            followup, _ = voice_pipeline.listen_microphone_and_transcribe(duration_sec=4.5)
            if not followup:
                # Stage 2 retry window
                safe_print(" ⏳ [Active Conversation Mode] Still listening for follow-up...")
                followup, _ = voice_pipeline.listen_microphone_and_transcribe(duration_sec=4.5)

            if not followup:
                # Silence — end conversation, go back to passive mode
                safe_print(" 🔇 [Voice Loop] No follow-up detected — conversation closed. Reverting to passive wake-word mode.")
                conversation_active = False
                break

            # Check if it's a new wake word (restart conversation) or a direct command
            if _contains_wake_word(followup):
                command = _strip_wake_words(followup)
                if not command:
                    # Just said "Heti" again with no command
                    voice_pipeline.tts.speak("Yes? What can I do for you?", play_audio=True, sync=True)
                    _time.sleep(0.5)
                    _wait_tts_done()
                    next_cmd, _ = voice_pipeline.listen_microphone_and_transcribe(duration_sec=5.0)
                    if next_cmd:
                        command = _strip_wake_words(next_cmd) or next_cmd
                    else:
                        conversation_active = False
                        break
                # else command already extracted, loop continues
            else:
                # Direct follow-up command without wake word
                command = followup

    safe_print(" 🛑 [Voice Loop] Stopped.")


# ─── Tray Menu Actions ───────────────────────────────────────────────────────
def action_start_voice(icon, item):
    global voice_thread, voice_running
    if voice_running:
        _notify(icon, "Heti", "Voice mode is already active!")
        return
    voice_running = True
    voice_thread = threading.Thread(target=_voice_loop_thread, args=(icon,), daemon=True)
    voice_thread.start()
    icon.title = "Heti Agent [LISTENING]"
    _notify(icon, "Heti", "Voice listening started. Speak your command!")


def action_stop_voice(icon, item):
    global voice_running
    voice_running = False
    icon.title = "Heti Agent [Idle]"
    _notify(icon, "Heti", "Voice listening stopped.")


def action_system_stats(icon, item):
    from Heti.tools.system_tools import SystemStatsTool
    stats = SystemStatsTool().execute(detailed=False)
    msg = (
        f"CPU: {stats.get('cpu_percent', '?')}%  |  "
        f"RAM Free: {stats.get('memory', {}).get('free_mb', '?')}MB  |  "
        f"Disk Free: {stats.get('disk', {}).get('free_gb', '?')}GB"
    )
    _notify(icon, "System Stats", msg)
    voice_pipeline.tts.speak(f"CPU is at {stats.get('cpu_percent')} percent. RAM free: {stats.get('memory', {}).get('free_mb')} megabytes.", play_audio=True)


def action_toggle_handless(icon, item):
    from Heti.gesture import HandlessGestureController
    controller = HandlessGestureController()
    if controller.is_active():
        res = controller.stop()
        _notify(icon, "Handless Mode", "Handless gesture mode stopped.")
    else:
        res = controller.start()
        if res.get("status") == "success":
            _notify(icon, "Handless Mode", "Handless gesture mode active! Move your hand in front of camera.")
        else:
            _notify(icon, "Handless Mode Error", res.get("message", "Failed to start camera gesture service."))


def action_quit(icon, item):
    global voice_running
    voice_running = False
    try:
        from Heti.gesture import HandlessGestureController
        HandlessGestureController().stop()
    except Exception:
        pass
    if kb_watcher:
        kb_watcher.stop()
    icon.stop()


# ─── Build & Run Tray ────────────────────────────────────────────────────────
def run_tray_app():
    _initialize_agent()

    menu = pystray.Menu(
        pystray.MenuItem("🎙️ Start Voice Listening", action_start_voice),
        pystray.MenuItem("🛑 Stop Voice Listening", action_stop_voice),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("🖐️ Toggle Handless Mode", action_toggle_handless),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("📊 System Stats", action_system_stats),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("❌ Quit Heti", action_quit)
    )

    icon_img = _build_icon_image()
    icon = pystray.Icon(
        name="HetiAgent",
        icon=icon_img,
        title="Heti Agent [Idle]",
        menu=menu
    )

    # Auto-notify on launch and auto-start voice listening thread
    def _on_launch():
        _notify(icon, "Heti Agent Ready", f"Tier: {config.active_tier.upper()} | Voice listening active.")
        action_start_voice(icon, None)

    threading.Timer(2.0, _on_launch).start()

    icon.run()


if __name__ == "__main__":
    run_tray_app()
