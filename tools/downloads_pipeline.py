import time
import threading
from typing import List, Dict, Any, Optional
from pathlib import Path

from Heti.tools.system_tools import DownloadsFolderMonitor, InspectDownloadedFileTool

# Cross-platform toast notification engine
def send_desktop_notification(title: str, message: str):
    print(f"\n🔔 [DESKTOP NOTIFICATION] --- {title} ---")
    print(f"   {message}\n")
    try:
        import platform
        if platform.system() == "Windows":
            # Native PowerShell Toast notification
            ps_script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
            $xml = @"
            <toast>
                <visual>
                    <binding template="ToastGeneric">
                        <text>{title}</text>
                        <text>{message}</text>
                    </binding>
                </visual>
            </toast>
"@
            $xmlDoc = [Windows.Data.Xml.Dom.XmlDocument]::new()
            $xmlDoc.LoadXml($xml)
            $toast = [Windows.UI.Notifications.ToastNotification]::new($xmlDoc)
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Heti Agent").Show($toast)
            '''
            import subprocess
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, timeout=5)
    except Exception:
        pass


class DownloadsPipelineController:
    """
    Wires DownloadsFolderMonitor -> Inspection & LLM Summarization -> Desktop Notification.
    Lite Tier Strategy: Batches and delays LLM summarization (e.g. every batch_interval_sec)
    to avoid repeated model load overheads on memory-constrained devices.
    Strictly passive: NO auto-execution.
    """
    def __init__(
        self,
        heti_agent,
        folder_path: Optional[str] = None,
        batch_interval_sec: float = 300.0  # Default: 5 minutes (300 sec)
    ):
        self.agent = heti_agent
        self.inspector = InspectDownloadedFileTool()
        self.batch_interval_sec = batch_interval_sec

        self.pending_queue: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self.running = False
        self._timer_thread = None

        self.monitor = DownloadsFolderMonitor(
            folder_path=folder_path,
            callback=self._on_file_detected
        )

    def _on_file_detected(self, file_path: str, event_type: str):
        print(f" 📥 [Pipeline] Download detected: {file_path}")
        inspection_result = self.inspector.execute(file_path)

        with self._lock:
            self.pending_queue.append({
                "file_path": file_path,
                "event_type": event_type,
                "inspection": inspection_result,
                "timestamp": time.time()
            })

    def start(self):
        if self.running:
            return
        self.running = True
        self.monitor.start()

        self._timer_thread = threading.Thread(target=self._batch_processing_loop, daemon=True)
        self._timer_thread.start()
        print(f" 🚀 [Pipeline Controller] Started. Lite Tier LLM batch interval: {self.batch_interval_sec}s")

    def _batch_processing_loop(self):
        while self.running:
            time.sleep(self.batch_interval_sec)
            self.process_batch_now()

    def process_batch_now(self):
        with self._lock:
            if not self.pending_queue:
                return
            current_batch = list(self.pending_queue)
            self.pending_queue.clear()

        print(f"\n 🧠 [Pipeline Controller] Processing LLM batch summary for {len(current_batch)} downloaded files...")
        batch_summary_prompt = self._build_llm_prompt(current_batch)

        # Call agent LLM for safety & utility summarization
        try:
            summary_response = self.agent.run_turn(batch_summary_prompt)
        except Exception as e:
            summary_response = f"Summary Error: {e}"

        # Trigger Desktop Notification (Passive notification, no auto-action)
        send_desktop_notification(
            title=f"Heti Download Summary ({len(current_batch)} files)",
            message=summary_response[:200]
        )

    def _build_llm_prompt(self, batch: List[Dict[str, Any]]) -> str:
        items_text = []
        for idx, item in enumerate(batch, 1):
            insp = item.get("inspection", {})
            fname = insp.get("file_name", Path(item["file_path"]).name)
            size_mb = round(insp.get("size_bytes", 0) / (1024 * 1024), 2)
            sha = insp.get("hashes", {}).get("sha256", "N/A")[:12]
            sig = insp.get("digital_signature", {}).get("signature_status", "Unknown")

            items_text.append(
                f"{idx}. File: {fname} | Size: {size_mb}MB | Ext: {insp.get('extension')} | SHA256: {sha}... | Signature: {sig}"
            )

        prompt = (
            "You are Heti Security Assistant. A batch of new files was downloaded to the system. "
            "Inspect the file details below and provide a concise 2-sentence safety and file category summary for the user. "
            "DO NOT suggest auto-executing these files.\n\n"
            + "\n".join(items_text)
        )
        return prompt

    def stop(self):
        self.running = False
        self.monitor.stop()
        print(" 🛑 [Pipeline Controller] Stopped.")
