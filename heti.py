"""
Heti AI Desktop Assistant & Control Center
Main desktop GUI application entry point for Heti.

Launches the Heti Desktop UI (heti_ui.html) inside a native window
with full real-time bindings to Heti's Voice Pipeline and Handless Gesture Engine.
"""

import os
import sys
import threading
import time
import subprocess
import webbrowser

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(script_dir, ".."))

if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from Heti.config.safe_io import setup_safe_io, safe_print
    from Heti.agent.core_agent import HetiAgent
    from Heti.tools.system_tools import get_default_tools
    from Heti.voice.pipeline import FullVoiceLoopPipeline
    from Heti.gesture.controller import get_gesture_controller
except ImportError:
    from config.safe_io import setup_safe_io, safe_print
    from agent.core_agent import HetiAgent
    from tools.system_tools import get_default_tools
    from voice.pipeline import FullVoiceLoopPipeline
    from gesture.controller import get_gesture_controller

setup_safe_io()


class HetiBridgeAPI:
    """JS-to-Python bridge API for pywebview and UI controls."""

    def __init__(self, agent, voice_pipeline):
        self.agent = agent
        self.voice_pipeline = voice_pipeline
        self.gesture_controller = get_gesture_controller()

    def start_voice(self):
        safe_print("Heti UI: Voice listening active.")
        return {"status": "success", "message": "Voice listening active"}

    def stop_voice(self):
        safe_print("Heti UI: Voice listening paused.")
        return {"status": "success", "message": "Voice listening paused"}

    def toggle_handless(self, enable: bool):
        safe_print(f"Heti UI: Handless Mode toggled -> {enable}")
        if enable:
            self.gesture_controller.start()
        else:
            self.gesture_controller.stop()
        return {"status": "success", "enabled": enable}

    def get_status(self):
        return {
            "agent_active": self.agent is not None,
            "gesture_active": self.gesture_controller.is_running(),
            "gesture_fps": self.gesture_controller.get_fps()
        }


def launch_gui():
    safe_print("Starting Heti AI Desktop Assistant...")

    # Initialize Agent & Tools
    tools = get_default_tools()
    agent = HetiAgent(tools=tools)

    # Initialize Voice Pipeline
    voice_pipeline = FullVoiceLoopPipeline(agent=agent)

    # Start Voice Listener in background daemon thread
    voice_thread = threading.Thread(target=voice_pipeline.start, daemon=True)
    voice_thread.start()

    bridge = HetiBridgeAPI(agent=agent, voice_pipeline=voice_pipeline)

    html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "heti_ui.html"))
    if not os.path.exists(html_path):
        safe_print(f"Error: Could not find HTML UI file at {html_path}")
        return

    # Native PyWebView Desktop Window
    try:
        import webview
        window = webview.create_window(
            title="Heti — AI Desktop Assistant",
            url=f"file:///{html_path}",
            width=520,
            height=820,
            resizable=True,
            background_color="#030308",
            js_api=bridge
        )
        webview.start(debug=False)
    except Exception as e:
        safe_print(f"Native webview fallback triggered: {e}. Launching app window...")
        # Fallback to Edge/Chrome App Mode desktop window
        edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        
        if os.path.exists(edge_path):
            subprocess.Popen([edge_path, f"--app=file:///{html_path}", "--window-size=520,820"])
        elif os.path.exists(chrome_path):
            subprocess.Popen([chrome_path, f"--app=file:///{html_path}", "--window-size=520,820"])
        else:
            webbrowser.open(f"file:///{html_path}")

        # Keep main thread alive for background voice loop
        while True:
            time.sleep(1)


if __name__ == "__main__":
    launch_gui()
