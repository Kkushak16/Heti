"""
Heti Voice Agent — System Tray & Background Assistant App
Runs silently as a background service in the Windows System Tray (bottom-right taskbar).
Voice listening remains active even when UI window is closed.
"""
import sys
import os
import threading
import subprocess
import webbrowser

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
    """Load heti_logo.ico or fallback to custom PIL icon."""
    ico_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "heti_logo.ico"))
    png_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "heti_logo.png"))

    if os.path.exists(ico_path):
        try:
            return Image.open(ico_path)
        except Exception:
            pass
    if os.path.exists(png_path):
        try:
            return Image.open(png_path)
        except Exception:
            pass

    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, size - 4, size - 4], fill=(59, 130, 246), outline=(30, 64, 175), width=3)
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
    """
    [ignoring loop detection]
    Voice Loop Thread handling two distinct phases:
    1. Passive mode: listens for wake words. Logs transcripts heard to console.
    2. Active Conversation mode: executes command, then stays in an active listening state
       without wake words for up to 15 seconds. Only speaks ending phrase after silence timeout.
    """
    global voice_running, _last_command, _last_command_time
    import time as _time
    username = os.environ.get("USERNAME") or "User"
    _notify(icon, "Heti Ready", f"Say 'Hey Heti' to activate me!")
    safe_print(" 🎙️ [Voice Loop] Passive mode — waiting for wake word...")

    COOLDOWN_SEC = 5

    while voice_running:
        _wait_tts_done()
        # Passive listening block - 4.5 seconds long
        transcript, _ = voice_pipeline.listen_microphone_and_transcribe(duration_sec=4.5)
        if not voice_running:
            break
        if not transcript:
            continue

        # Print all detected speech in passive mode to console for visibility
        safe_print(f" 🔍 [Passive Heard]: \"{transcript}\"")

        if not _contains_wake_word(transcript):
            continue

        # Wake word detected! Stop any TTS immediately
        voice_pipeline.tts.stop_speaking()
        safe_print(f" 🔔 [Wake Word Detected]: \"{transcript}\"")

        command = _strip_wake_words(transcript)

        if not command:
            # Greet user and wait for command
            greeting = f"Hi {username}, how can I help you?"
            _notify(icon, "Heti", greeting)
            voice_pipeline.tts.speak(greeting, play_audio=True, sync=True)
            _time.sleep(0.5)

            _wait_tts_done()
            command_transcript, _ = voice_pipeline.listen_microphone_and_transcribe(duration_sec=5.0)
            if not command_transcript:
                voice_pipeline.tts.speak("I'm here when you need me Heti.", play_audio=True, sync=True)
                _time.sleep(1)
                safe_print(" 🔇 [Voice Loop] No command received — back to passive mode.")
                continue
            command = _strip_wake_words(command_transcript) or command_transcript

        conversation_active = True
        while conversation_active and voice_running:
            now = _time.time()
            cmd_lower = command.lower().strip()
            
            # Prevent command loops
            if cmd_lower == _last_command and (now - _last_command_time) < COOLDOWN_SEC:
                safe_print(f" ⏭️ [Dedup] Skipping duplicate: \"{command}\"")
                conversation_active = False
                break

            _last_command = cmd_lower
            _last_command_time = now

            safe_print(f" 📝 [Command]: \"{command}\"")
            _notify(icon, "Heti Heard", f"\"{command}\"")
            _notify(icon, "Heti Working", "Processing...")
            
            # Run the agent turn
            response = agent.run_turn(command)

            safe_print(f" 🤖 [Response]: {response}")
            _notify(icon, "Heti", response[:200])
            voice_pipeline.tts.speak(response, play_audio=True, sync=True)
            _time.sleep(0.5)
            _wait_tts_done()

            # Entering active listening window: wait up to 15 seconds (3 cycles of 5s)
            # Do NOT say the outro line immediately.
            silence_counter = 0
            max_silence_cycles = 3  # 3 * 5.0 seconds = 15 seconds total window
            followup_detected = False

            while silence_counter < max_silence_cycles and voice_running:
                safe_print(f" 🎙️ [Active Listening] No wake word needed (Cycle {silence_counter + 1}/{max_silence_cycles})...")
                followup, _ = voice_pipeline.listen_microphone_and_transcribe(duration_sec=5.0)
                
                if followup:
                    # Strip wake words just in case the user said it anyway
                    followup_cleaned = _strip_wake_words(followup) or followup
                    if followup_cleaned:
                        safe_print(f" 🔊 [Follow-up Detected]: \"{followup_cleaned}\"")
                        command = followup_cleaned
                        followup_detected = True
                        break

                silence_counter += 1
                safe_print(f" ⏳ Silence duration: {silence_counter * 5} seconds...")

            if followup_detected:
                # Reset silence counter and execute the new command
                continue
            else:
                # User stayed silent for the entire 15 seconds -> speak ending phrase and exit to passive
                safe_print(" 🔇 [Active Listening] 15 seconds of silence. Closing conversation loop.")
                voice_pipeline.tts.speak("For any other help, I'm here Heti.", play_audio=True, sync=True)
                _time.sleep(1)
                conversation_active = False
                break

    safe_print(" 🛑 [Voice Loop] Stopped.")


# ─── Tray Menu Actions ───────────────────────────────────────────────────────
def action_open_dashboard(icon=None, item=None):
    """Open the Desktop GUI dashboard window (closing this window will NOT stop voice assistant)."""
    html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "heti_ui.html"))
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    if os.path.exists(edge_path):
        subprocess.Popen([edge_path, f"--app=file:///{html_path}", "--window-size=520,820"])
    elif os.path.exists(chrome_path):
        subprocess.Popen([chrome_path, f"--app=file:///{html_path}", "--window-size=520,820"])
    else:
        webbrowser.open(f"file:///{html_path}")


def action_start_voice(icon, item):
    global voice_thread, voice_running
    if voice_running:
        _notify(icon, "Heti", "Voice mode is already active!")
        return
    voice_running = True
    voice_thread = threading.Thread(target=_voice_loop_thread, args=(icon,), daemon=True)
    voice_thread.start()
    if icon:
        icon.title = "Heti Agent [LISTENING]"
    _notify(icon, "Heti", "Voice listening started. Speak 'Hey Heti' anytime!")


def action_stop_voice(icon, item):
    global voice_running
    voice_running = False
    if icon:
        icon.title = "Heti Agent [Idle]"
    _notify(icon, "Heti", "Voice listening paused.")


def action_system_stats(icon, item):
    from Heti.tools.system_tools import SystemStatsTool
    stats = SystemStatsTool().execute(detailed=False)
    msg = (
        f"CPU: {stats.get('cpu_percent', '?')}%  |  "
        f"RAM Free: {stats.get('memory', {}).get('free_mb', '?')}MB  |  "
        f"Disk Free: {stats.get('disk', {}).get('free_gb', '?')}GB"
    )
    _notify(icon, "System Stats", msg)
    if voice_pipeline and voice_pipeline.tts:
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
    if icon:
        icon.stop()


# ─── Build & Run Tray ────────────────────────────────────────────────────────
def run_tray_app():
    _initialize_agent()

    menu = pystray.Menu(
        pystray.MenuItem("🖥️ Open Dashboard UI", action_open_dashboard),
        pystray.Menu.SEPARATOR,
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
        title="Heti Agent [Active]",
        menu=menu
    )

    def _on_launch():
        _notify(icon, "Heti Agent Ready", f"Tier: {config.active_tier.upper()} | Say 'Hey Heti' anytime!")
        action_start_voice(icon, None)

    threading.Timer(1.5, _on_launch).start()

    icon.run()


if __name__ == "__main__":
    run_tray_app()
